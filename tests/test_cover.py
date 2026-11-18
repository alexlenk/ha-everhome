"""Tests for Everhome covers."""

from __future__ import annotations

from http import HTTPStatus

import pytest
from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.const import (
    ATTR_ASSUMED_STATE,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_SUPPORTED_FEATURES,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.everhome.const import DOMAIN

from .conftest import DEVICE_URL, execute_url, make_device


@pytest.mark.usefixtures("setup_integration")
async def test_cover_states_and_attributes(hass: HomeAssistant) -> None:
    """States map from states.general; awnings use out/in."""
    shutter = hass.states.get("cover.kinderzimmer")
    assert shutter.state == "open"  # general "up"
    assert shutter.attributes[ATTR_CURRENT_POSITION] == 100
    assert shutter.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.SHUTTER
    assert shutter.attributes[ATTR_ICON] == "mdi:window-shutter"
    assert shutter.attributes[ATTR_ASSUMED_STATE] is True
    assert shutter.attributes[ATTR_SUPPORTED_FEATURES] == (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    awning = hass.states.get("cover.terrasse")
    assert awning.state == "closed"  # general "in" = retracted
    assert awning.attributes[ATTR_CURRENT_POSITION] == 0
    assert awning.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.AWNING

    garage = hass.states.get("cover.garage")
    assert garage.state == "closed"
    assert garage.attributes[ATTR_DEVICE_CLASS] == CoverDeviceClass.GARAGE
    assert garage.attributes[ATTR_ICON] == "mdi:garage"


@pytest.mark.parametrize(
    ("subtype", "general", "state", "device_class", "icon"),
    [
        ("awning", "out", "open", CoverDeviceClass.AWNING, "mdi:awning-outline"),
        ("blind", "down", "closed", CoverDeviceClass.BLIND, "mdi:blinds"),
        ("curtain", "up", "open", CoverDeviceClass.BLIND, "mdi:curtains"),
        ("shutter", None, "unknown", CoverDeviceClass.SHUTTER, "mdi:window-shutter"),
        ("shutter", "on", "unknown", CoverDeviceClass.SHUTTER, "mdi:window-shutter"),
    ],
)
async def test_cover_state_mapping(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    subtype: str,
    general: str | None,
    state: str,
    device_class: CoverDeviceClass,
    icon: str,
) -> None:
    """Each subtype gets its device class/icon; unknown states stay unknown."""
    states = {"general": general} if general else {}
    aioclient_mock.get(DEVICE_URL, json=[make_device(1, subtype, "Test", states)])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("cover.test")
    assert entity.state == state
    assert entity.attributes[ATTR_DEVICE_CLASS] == device_class
    assert entity.attributes[ATTR_ICON] == icon
    if state == "unknown":
        assert ATTR_CURRENT_POSITION not in entity.attributes


@pytest.mark.parametrize(
    ("service", "action"),
    [("open_cover", "up"), ("close_cover", "down"), ("stop_cover", "stop")],
)
async def test_cover_services(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    service: str,
    action: str,
) -> None:
    """Services send the matching action and trigger a refresh."""
    aioclient_mock.post(execute_url(8), text="")
    calls_before = len(aioclient_mock.mock_calls)

    await hass.services.async_call(
        "cover", service, {ATTR_ENTITY_ID: "cover.kinderzimmer"}, blocking=True
    )
    await hass.async_block_till_done()

    new_calls = aioclient_mock.mock_calls[calls_before:]
    assert new_calls[0][2] == {"action": action}
    # A refresh of the device list follows the command
    assert any(str(call[1]) == DEVICE_URL for call in new_calls[1:])


async def test_cover_service_failure_raises(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A rejected command surfaces as an error in the service call (#22)."""
    aioclient_mock.post(execute_url(8), status=HTTPStatus.BAD_GATEWAY)

    with pytest.raises(HomeAssistantError, match="HTTP 502"):
        await hass.services.async_call(
            "cover",
            "close_cover",
            {ATTR_ENTITY_ID: "cover.kinderzimmer"},
            blocking=True,
        )


async def test_cover_registry_entries(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """unique_id keeps the existing format; device info uses documented fields."""
    entry = entity_registry.async_get("cover.kinderzimmer")
    assert entry.unique_id == f"{DOMAIN}_test_entry_id_8"

    device = device_registry.async_get(entry.device_id)
    assert (DOMAIN, 8) in device.identifiers
    assert device.name == "Kinderzimmer"
    assert device.manufacturer == "Everhome"
    assert device.model == "Shutter"
    assert device.sw_version is None
