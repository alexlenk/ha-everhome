"""Tests for the Everhome config flow."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

import pytest
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.everhome.const import API_BASE_URL, DOMAIN

from .conftest import CLIENT_ID, DEVICE_URL, TOKEN_URL, make_device

REDIRECT_URI = "https://example.com/auth/external/callback"
NEW_TOKEN = {
    "access_token": "new_access_token",
    "refresh_token": "new_refresh_token",
    "token_type": "Bearer",
    "expires_in": 3600,
}


async def _complete_oauth(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    aioclient_mock: AiohttpClientMocker,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Drive a started flow through the OAuth redirect and token exchange."""
    state = config_entry_oauth2_flow._encode_jwt(
        hass, {"flow_id": result["flow_id"], "redirect_uri": REDIRECT_URI}
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"].startswith(f"{API_BASE_URL}/oauth2/authorize")
    assert f"client_id={CLIENT_ID}" in result["url"]

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK

    aioclient_mock.post(TOKEN_URL, json=NEW_TOKEN)
    return await hass.config_entries.flow.async_configure(result["flow_id"])


@pytest.mark.usefixtures("current_request_with_host", "application_credentials")
async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """The user flow creates an entry after validating the token."""
    aioclient_mock.get(
        DEVICE_URL,
        json=[make_device(1, "shutter", "A"), make_device(2, "light", "B")],
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _complete_oauth(hass, hass_client_no_auth, aioclient_mock, result)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Everhome (2 devices)"
    assert result["data"]["auth_implementation"] == DOMAIN
    assert result["data"]["token"]["access_token"] == "new_access_token"
    # The device list was requested with the new token
    device_call = next(c for c in aioclient_mock.mock_calls if str(c[1]) == DEVICE_URL)
    assert device_call[3]["Authorization"] == "Bearer new_access_token"


@pytest.mark.usefixtures("current_request_with_host", "application_credentials")
@pytest.mark.parametrize(
    ("mock_kwargs", "reason"),
    [
        ({"status": HTTPStatus.UNAUTHORIZED}, "cannot_connect"),
        ({"status": HTTPStatus.BAD_GATEWAY}, "cannot_connect"),
        ({"exc": ClientError()}, "cannot_connect"),
        ({"exc": TimeoutError()}, "cannot_connect"),
    ],
)
async def test_flow_device_check_fails(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict[str, Any],
    reason: str,
) -> None:
    """The flow aborts when the token can't be validated against GET /device."""
    aioclient_mock.get(DEVICE_URL, **mock_kwargs)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _complete_oauth(hass, hass_client_no_auth, aioclient_mock, result)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason
    assert not hass.config_entries.async_entries(DOMAIN)


@pytest.mark.usefixtures("current_request_with_host", "application_credentials")
async def test_flow_invalid_json(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A JSON body that can't be decoded aborts with unknown."""
    aioclient_mock.get(
        DEVICE_URL, text="{broken", headers={"Content-Type": "application/json"}
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await _complete_oauth(hass, hass_client_no_auth, aioclient_mock, result)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unknown"


@pytest.mark.usefixtures("current_request_with_host", "application_credentials")
async def test_reauth_flow_updates_existing_entry(
    hass: HomeAssistant,
    hass_client_no_auth: Any,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reauth stores the new token on the existing entry and creates no new one."""
    aioclient_mock.get(DEVICE_URL, json=[make_device(1, "shutter", "A")])
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, hass_client_no_auth, aioclient_mock, result)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert mock_config_entry.data["token"]["access_token"] == "new_access_token"
    assert mock_config_entry.data["auth_implementation"] == DOMAIN
