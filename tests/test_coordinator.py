"""Tests for the Everhome data update coordinator."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Any

import pytest
from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from .conftest import DEVICE_URL, execute_url, make_device


async def test_execute_sends_documented_body(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Execute posts {"action": ...} and logs the response at debug level."""
    aioclient_mock.post(execute_url(8), text="")
    caplog.set_level(logging.DEBUG, logger="custom_components.everhome")

    await setup_integration.runtime_data.execute_device_action(8, "up")

    method, url, data, headers = aioclient_mock.mock_calls[-1]
    assert method.upper() == "POST"
    assert str(url) == execute_url(8)
    assert data == {"action": "up"}
    assert headers["Authorization"] == "Bearer test_access_token"
    assert "Executed action up on device 8: 200" in caplog.text


@pytest.mark.parametrize(
    "mock_kwargs",
    [
        {"status": HTTPStatus.BAD_GATEWAY, "text": "Bad Gateway"},
        {"status": HTTPStatus.NOT_FOUND},
        {"exc": ClientError("boom")},
        {"exc": TimeoutError()},
    ],
)
async def test_execute_failure_raises(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict[str, Any],
) -> None:
    """A failed command raises HomeAssistantError instead of passing silently."""
    aioclient_mock.post(execute_url(8), **mock_kwargs)

    with pytest.raises(HomeAssistantError):
        await setup_integration.runtime_data.execute_device_action(8, "down")


async def test_update_failure_makes_entities_unavailable(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Entities go unavailable when polling fails, and recover afterwards."""
    coordinator = setup_integration.runtime_data
    assert hass.states.get("cover.kinderzimmer").state == "open"

    aioclient_mock.clear_requests()
    aioclient_mock.get(DEVICE_URL, status=HTTPStatus.BAD_GATEWAY)
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    for entity_id in (
        "cover.kinderzimmer",
        "light.flur",
        "switch.steckdose",
        "binary_sensor.fenster",
    ):
        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        DEVICE_URL, json=[make_device(8, "shutter", "Kinderzimmer", {"general": "up"})]
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("cover.kinderzimmer").state == "open"
    # Devices no longer returned by the API become unavailable
    assert hass.states.get("light.flur").state == STATE_UNAVAILABLE


async def test_unauthorized_poll_starts_reauth(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A 401 while polling (token revoked server-side) starts reauth."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(DEVICE_URL, status=HTTPStatus.UNAUTHORIZED)

    await setup_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


async def test_new_devices_are_added_without_reload(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    devices: list[dict[str, Any]],
) -> None:
    """Devices added in everHome after setup appear on the next poll."""
    assert hass.states.get("cover.bad") is None

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        DEVICE_URL,
        json=[
            *devices,
            make_device(70, "shutter", "Bad", {"general": "down"}),
            make_device(71, "socket", "Neue Steckdose", {"general": "on"}),
        ],
    )
    await setup_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("cover.bad").state == "closed"
    assert hass.states.get("switch.neue_steckdose").state == "on"
    # Existing entities are not duplicated
    assert len(hass.states.async_entity_ids("cover")) == 4
