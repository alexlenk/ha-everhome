"""Tests for Everhome binary sensors."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import ATTR_DEVICE_CLASS
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from .conftest import DEVICE_URL, make_device


@pytest.mark.parametrize(
    ("subtype", "states", "expected", "device_class"),
    [
        ("door", {"state": "open"}, "on", BinarySensorDeviceClass.DOOR),
        ("door", {"state": "closed"}, "off", BinarySensorDeviceClass.DOOR),
        ("window", {"state": "open"}, "on", BinarySensorDeviceClass.WINDOW),
        ("window", {}, "unknown", BinarySensorDeviceClass.WINDOW),
        # Contact sensors read states.state, not states.general
        ("window", {"general": "on"}, "unknown", BinarySensorDeviceClass.WINDOW),
        ("motiondetector", {"general": "on"}, "on", BinarySensorDeviceClass.MOTION),
        ("smokedetector", {"general": "off"}, "off", BinarySensorDeviceClass.SMOKE),
        (
            "waterdetector",
            {"general": "on"},
            "on",
            BinarySensorDeviceClass.MOISTURE,
        ),
        ("motiondetector", {}, "unknown", BinarySensorDeviceClass.MOTION),
    ],
)
async def test_binary_sensor_state_mapping(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    subtype: str,
    states: dict[str, Any],
    expected: str,
    device_class: BinarySensorDeviceClass,
) -> None:
    """Each subtype reads the documented state field."""
    aioclient_mock.get(DEVICE_URL, json=[make_device(1, subtype, "Test", states)])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")
    assert state.state == expected
    assert state.attributes[ATTR_DEVICE_CLASS] == device_class


@pytest.mark.parametrize(
    ("states", "attrs"),
    [
        ({"batteryboolean": "battery-low"}, {"battery_low": True}),
        ({"batteryboolean": "battery-ok"}, {"battery_low": False}),
        ({"batterypercentage": 42}, {"battery_level": 42}),
        ({}, {}),
    ],
)
async def test_binary_sensor_battery_attributes(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    states: dict[str, Any],
    attrs: dict[str, Any],
) -> None:
    """Battery states are exposed as attributes when present."""
    aioclient_mock.get(
        DEVICE_URL,
        json=[make_device(1, "door", "Test", {"state": "closed", **states})],
    )
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test")
    for key in ("battery_low", "battery_level"):
        assert state.attributes.get(key) == attrs.get(key)
