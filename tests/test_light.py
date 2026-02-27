"""Test Everhome light entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode
from homeassistant.core import HomeAssistant

from custom_components.everhome.const import DOMAIN
from custom_components.everhome.light import EverhomeLight, async_setup_entry


class TestEverhomeLight:
    """Test Everhome light entity."""

    @pytest.fixture
    def mock_coordinator(self, mock_config_entry):
        """Mock coordinator with a mixed set of device data."""
        coordinator = AsyncMock()
        coordinator.entry = mock_config_entry
        coordinator.data = {
            "light_001": {
                "id": "light_001",
                "name": "Living Room Light",
                "subtype": "light",
                "states": {"general": "off"},
            },
            "dimmer_001": {
                "id": "dimmer_001",
                "name": "Bedroom Dimmer",
                "subtype": "light",
                "capabilities": ["set_brightness"],
                "states": {"general": "on", "brightness": 50},
            },
            # cover — must NOT appear as a light entity
            "shutter_001": {
                "id": "shutter_001",
                "name": "Bedroom Shutter",
                "subtype": "shutter",
                "states": {"general": "down"},
            },
        }
        coordinator.execute_device_action = AsyncMock(return_value=True)
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    # ------------------------------------------------------------------
    # async_setup_entry
    # ------------------------------------------------------------------

    async def test_async_setup_entry_creates_only_lights(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Only light subtypes become entities; covers are excluded."""
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        entities: list[EverhomeLight] = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        assert len(entities) == 2
        device_ids = {e._device_id for e in entities}
        assert "light_001" in device_ids
        assert "dimmer_001" in device_ids
        assert "shutter_001" not in device_ids

    # ------------------------------------------------------------------
    # is_on
    # ------------------------------------------------------------------

    def test_is_on_when_on(self, mock_coordinator):
        """states.general = 'on' → is_on True."""
        mock_coordinator.data = {
            "light_001": {
                "name": "Test",
                "subtype": "light",
                "states": {"general": "on"},
            }
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.is_on is True

    def test_is_on_when_off(self, mock_coordinator):
        """states.general = 'off' → is_on False."""
        mock_coordinator.data = {
            "light_001": {
                "name": "Test",
                "subtype": "light",
                "states": {"general": "off"},
            }
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.is_on is False

    def test_is_on_when_state_absent(self, mock_coordinator):
        """Missing states.general → is_on None."""
        mock_coordinator.data = {
            "light_001": {"name": "Test", "subtype": "light", "states": {}}
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.is_on is None

    # ------------------------------------------------------------------
    # brightness
    # ------------------------------------------------------------------

    def test_brightness_conversion(self, mock_coordinator):
        """API brightness 50 → HA brightness 128 (rounded)."""
        mock_coordinator.data = {
            "light_001": {
                "name": "Test",
                "subtype": "light",
                "capabilities": ["set_brightness"],
                "states": {"general": "on", "brightness": 50},
            }
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.brightness == round(50 * 255 / 100)

    def test_brightness_absent(self, mock_coordinator):
        """No brightness in states → brightness property returns None."""
        mock_coordinator.data = {
            "light_001": {
                "name": "Test",
                "subtype": "light",
                "states": {"general": "on"},
            }
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.brightness is None

    def test_brightness_full(self, mock_coordinator):
        """API brightness 100 → HA brightness 255."""
        mock_coordinator.data = {
            "light_001": {
                "name": "Test",
                "subtype": "light",
                "capabilities": ["set_brightness"],
                "states": {"general": "on", "brightness": 100},
            }
        }
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.brightness == 255

    # ------------------------------------------------------------------
    # color mode / feature flags
    # ------------------------------------------------------------------

    def test_color_mode_brightness_when_capable(self, mock_coordinator):
        """ColorMode.BRIGHTNESS when set_brightness is in capabilities."""
        device_data = {
            "name": "Dimmer",
            "subtype": "light",
            "capabilities": ["set_brightness"],
            "states": {},
        }
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)
        assert light.color_mode == ColorMode.BRIGHTNESS
        assert ColorMode.BRIGHTNESS in light.supported_color_modes

    def test_color_mode_onoff_when_not_dimmable(self, mock_coordinator):
        """ColorMode.ONOFF when capabilities list has no brightness entry."""
        device_data = {"name": "Bulb", "subtype": "light", "states": {}}
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)
        assert light.color_mode == ColorMode.ONOFF
        assert ColorMode.ONOFF in light.supported_color_modes

    # ------------------------------------------------------------------
    # async_turn_on
    # ------------------------------------------------------------------

    async def test_turn_on_without_brightness(self, mock_coordinator):
        """turn_on with no brightness arg sends action 'on'."""
        device_data = {"name": "Bulb", "subtype": "light", "states": {}}
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)

        await light.async_turn_on()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "light_001", "on"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_with_brightness_on_dimmable(self, mock_coordinator):
        """turn_on with HA brightness 255 → set_brightness with API value 100."""
        device_data = {
            "name": "Dimmer",
            "subtype": "light",
            "capabilities": ["set_brightness"],
            "states": {},
        }
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)

        await light.async_turn_on(**{ATTR_BRIGHTNESS: 255})

        mock_coordinator.execute_device_action.assert_called_once_with(
            "light_001", "set_brightness", {"brightness": 100}
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_on_with_brightness_on_non_dimmable(self, mock_coordinator):
        """turn_on with brightness on non-dimmable device → falls back to 'on'."""
        device_data = {"name": "Bulb", "subtype": "light", "states": {}}
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)

        await light.async_turn_on(**{ATTR_BRIGHTNESS: 128})

        mock_coordinator.execute_device_action.assert_called_once_with(
            "light_001", "on"
        )

    async def test_turn_on_with_half_brightness(self, mock_coordinator):
        """HA brightness 128 → API brightness ~50."""
        device_data = {
            "name": "Dimmer",
            "subtype": "light",
            "capabilities": ["set_brightness"],
            "states": {},
        }
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)

        await light.async_turn_on(**{ATTR_BRIGHTNESS: 128})

        expected_api = round(128 * 100 / 255)
        mock_coordinator.execute_device_action.assert_called_once_with(
            "light_001", "set_brightness", {"brightness": expected_api}
        )

    # ------------------------------------------------------------------
    # async_turn_off
    # ------------------------------------------------------------------

    async def test_turn_off(self, mock_coordinator):
        """turn_off sends action 'off' and triggers refresh."""
        device_data = {"name": "Bulb", "subtype": "light", "states": {}}
        mock_coordinator.data = {"light_001": device_data}
        light = EverhomeLight(mock_coordinator, "light_001", device_data)

        await light.async_turn_off()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "light_001", "off"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    # ------------------------------------------------------------------
    # availability and unique ID
    # ------------------------------------------------------------------

    def test_available_when_present(self, mock_coordinator):
        """Entity is available when device ID is in coordinator data."""
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert light.available is True

    def test_available_false_when_missing(self, mock_coordinator):
        """Entity is unavailable when device ID not in coordinator data."""
        light = EverhomeLight(
            mock_coordinator,
            "missing_id",
            {"name": "Gone", "subtype": "light"},
        )
        assert light.available is False

    def test_unique_id_includes_entry_id(self, mock_coordinator):
        """Unique ID is scoped to the config entry."""
        light = EverhomeLight(
            mock_coordinator, "light_001", mock_coordinator.data["light_001"]
        )
        assert (
            light._attr_unique_id
            == f"{DOMAIN}_{mock_coordinator.entry.entry_id}_light_001"
        )
