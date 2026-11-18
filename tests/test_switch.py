"""Tests for Everhome switches."""

from __future__ import annotations

from http import HTTPStatus

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ENTITY_ID, ATTR_ICON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from .conftest import DEVICE_URL, execute_url, make_device


@pytest.mark.parametrize(
    ("subtype", "general", "expected", "device_class", "icon"),
    [
        ("socket", "on", "on", SwitchDeviceClass.OUTLET, None),
        ("socket", "off", "off", SwitchDeviceClass.OUTLET, None),
        ("watering", "on", "on", SwitchDeviceClass.SWITCH, "mdi:water"),
        ("socket", None, "unknown", SwitchDeviceClass.OUTLET, None),
    ],
)
async def test_switch_state_mapping(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    subtype: str,
    general: str | None,
    expected: str,
    device_class: SwitchDeviceClass,
    icon: str | None,
) -> None:
    """states.general maps to the switch state; subtype sets class and icon."""
    states = {"general": general} if general else {}
    aioclient_mock.get(DEVICE_URL, json=[make_device(1, subtype, "Test", states)])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.test")
    assert state.state == expected
    assert state.attributes[ATTR_DEVICE_CLASS] == device_class
    assert state.attributes.get(ATTR_ICON) == icon


@pytest.mark.parametrize(
    ("service", "action"), [("turn_on", "on"), ("turn_off", "off")]
)
async def test_switch_services(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    service: str,
    action: str,
) -> None:
    """Services send the matching action."""
    aioclient_mock.post(execute_url(30), text="")
    calls_before = len(aioclient_mock.mock_calls)

    await hass.services.async_call(
        "switch", service, {ATTR_ENTITY_ID: "switch.steckdose"}, blocking=True
    )
    assert aioclient_mock.mock_calls[calls_before][2] == {"action": action}


async def test_switch_service_failure_raises(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A rejected command surfaces as an error in the service call."""
    aioclient_mock.post(execute_url(30), status=HTTPStatus.BAD_REQUEST)

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_on", {ATTR_ENTITY_ID: "switch.steckdose"}, blocking=True
        )
