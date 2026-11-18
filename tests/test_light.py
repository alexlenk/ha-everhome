"""Tests for Everhome lights."""

from __future__ import annotations

from http import HTTPStatus

import pytest
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_SUPPORTED_COLOR_MODES,
    ColorMode,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from .conftest import DEVICE_URL, execute_url, make_device


@pytest.mark.usefixtures("setup_integration")
async def test_light_state(hass: HomeAssistant) -> None:
    """Lights are on/off only."""
    state = hass.states.get("light.flur")
    assert state.state == "on"
    assert state.attributes[ATTR_COLOR_MODE] == ColorMode.ONOFF
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]


@pytest.mark.parametrize(
    ("general", "expected"), [("on", "on"), ("off", "off"), (None, "unknown")]
)
async def test_light_state_mapping(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    general: str | None,
    expected: str,
) -> None:
    """states.general maps to the light state."""
    states = {"general": general} if general else {}
    aioclient_mock.get(DEVICE_URL, json=[make_device(1, "light", "Test", states)])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("light.test").state == expected


@pytest.mark.parametrize(
    ("service", "data", "action"),
    [
        ("turn_on", {}, "on"),
        # HA drops brightness for an on/off-only light; only "on" is sent
        ("turn_on", {ATTR_BRIGHTNESS: 128}, "on"),
        ("turn_off", {}, "off"),
    ],
)
async def test_light_services(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    service: str,
    data: dict,
    action: str,
) -> None:
    """Services send the matching action."""
    aioclient_mock.post(execute_url(20), text="")
    calls_before = len(aioclient_mock.mock_calls)

    await hass.services.async_call(
        "light", service, {ATTR_ENTITY_ID: "light.flur", **data}, blocking=True
    )
    assert aioclient_mock.mock_calls[calls_before][2] == {"action": action}


async def test_light_service_failure_raises(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A rejected command surfaces as an error in the service call."""
    aioclient_mock.post(execute_url(20), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "light", "turn_off", {ATTR_ENTITY_ID: "light.flur"}, blocking=True
        )
