"""Tests for Everhome setup and unload."""

from __future__ import annotations

import time
from http import HTTPStatus

import pytest
from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.everhome.const import DOMAIN

from .conftest import DEVICE_URL, TOKEN_URL


async def test_setup_and_unload(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Entry loads, creates entities for supported enabled devices, and unloads."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.data.keys() == {8, 9, 10, 20, 30, 40}

    # Unsupported (speaker) and disabled devices get no entities
    entity_ids = hass.states.async_entity_ids()
    assert "cover.disabled_shutter" not in entity_ids
    assert not any("unsupported" in entity_id for entity_id in entity_ids)
    assert len(entity_ids) == 6

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    "mock_kwargs",
    [
        {"status": HTTPStatus.INTERNAL_SERVER_ERROR},
        {"exc": ClientError()},
        {"exc": TimeoutError()},
    ],
)
async def test_setup_retry_on_api_error(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict,
) -> None:
    """API errors during the first refresh retry setup later."""
    aioclient_mock.get(DEVICE_URL, **mock_kwargs)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_unauthorized_starts_reauth(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 401 from GET /device fails setup with an auth error and starts reauth."""
    aioclient_mock.get(DEVICE_URL, status=HTTPStatus.UNAUTHORIZED)
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_setup_refresh_token_rejected_starts_reauth(
    hass: HomeAssistant,
    application_credentials: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An expired token whose refresh is rejected starts reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "old",
                "refresh_token": "revoked",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": time.time() - 60,
            },
        },
    )
    aioclient_mock.post(TOKEN_URL, status=HTTPStatus.BAD_REQUEST)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_setup_refreshes_expired_token(
    hass: HomeAssistant,
    application_credentials: None,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """An expired token is refreshed and the new one is stored and used."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "old",
                "refresh_token": "refresh",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": time.time() - 60,
            },
        },
    )
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "new",
            "refresh_token": "refresh2",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )
    aioclient_mock.get(DEVICE_URL, json=[])
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.data["token"]["access_token"] == "new"
    device_call = next(c for c in aioclient_mock.mock_calls if str(c[1]) == DEVICE_URL)
    assert device_call[3]["Authorization"] == "Bearer new"
