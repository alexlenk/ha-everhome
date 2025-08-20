"""Test Everhome cover entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from custom_components.everhome.const import DOMAIN
from custom_components.everhome.cover import EverhomeCover, async_setup_entry


class TestEverhomeCover:
    """Test Everhome cover entity."""

    @pytest.fixture
    def mock_coordinator(self, mock_config_entry):
        """Mock coordinator with device data."""
        coordinator = AsyncMock()
        coordinator.entry = mock_config_entry
        coordinator.data = {
            "shutter_001": {
                "id": "shutter_001",
                "name": "Bedroom Shutter",
                "subtype": "shutter",
                "states": {"general": "down"},
                "position": 0,
            },
            "awning_001": {
                "id": "awning_001",
                "name": "Patio Awning",
                "subtype": "awning",
                "states": {"general": "up"},
                "position": 75,
            },
        }
        coordinator.execute_device_action = AsyncMock(return_value=True)
        coordinator.async_request_refresh = AsyncMock()
        return coordinator

    async def test_async_setup_entry(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Test setting up covers from config entry."""
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        entities = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        assert len(entities) == 2
        assert isinstance(entities[0], EverhomeCover)
        assert isinstance(entities[1], EverhomeCover)

        # Check device IDs
        device_ids = [entity._device_id for entity in entities]
        assert "shutter_001" in device_ids
        assert "awning_001" in device_ids

    def test_cover_initialization_shutter(self, mock_coordinator):
        """Test shutter cover initialization."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        assert cover._device_id == "shutter_001"
        assert cover._attr_name == "Bedroom Shutter"
        assert (
            cover._attr_unique_id
            == f"{DOMAIN}_{mock_coordinator.entry.entry_id}_shutter_001"
        )
        assert cover._attr_device_class == CoverDeviceClass.SHUTTER
        assert cover._attr_icon == "mdi:window-shutter"

        # Check supported features
        expected_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert cover._attr_supported_features == expected_features

    def test_cover_initialization_awning(self, mock_coordinator):
        """Test awning cover initialization."""
        device_data = mock_coordinator.data["awning_001"]
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)

        assert cover._attr_device_class == CoverDeviceClass.AWNING
        assert cover._attr_icon == "mdi:awning-outline"

    def test_cover_initialization_garage_door(self, mock_coordinator):
        """Test garage door cover initialization."""
        device_data = {
            "id": "garage_001",
            "name": "Garage Door",
            "subtype": "garage_door",
            "states": {"general": "down"},
        }
        cover = EverhomeCover(mock_coordinator, "garage_001", device_data)

        assert cover._attr_device_class == CoverDeviceClass.GARAGE
        assert cover._attr_icon == "mdi:garage"

    def test_cover_initialization_blind(self, mock_coordinator):
        """Test blind cover initialization."""
        device_data = {
            "id": "blind_001",
            "name": "Window Blind",
            "subtype": "blind",
            "states": {"general": "up"},
        }
        cover = EverhomeCover(mock_coordinator, "blind_001", device_data)

        assert cover._attr_device_class == CoverDeviceClass.BLIND
        assert cover._attr_icon == "mdi:blinds"

    def test_cover_initialization_curtain(self, mock_coordinator):
        """Test curtain cover initialization."""
        device_data = {
            "id": "curtain_001",
            "name": "Living Room Curtain",
            "subtype": "curtain",
            "states": {"general": "down"},
        }
        cover = EverhomeCover(mock_coordinator, "curtain_001", device_data)

        assert cover._attr_device_class == CoverDeviceClass.BLIND
        assert cover._attr_icon == "mdi:curtains"

    def test_cover_device_info(self, mock_coordinator):
        """Test cover device info."""
        device_data = {
            "id": "device_001",
            "name": "Test Device",
            "subtype": "shutter",
            "model": "Smart Shutter Pro",
            "firmware_version": "2.1.0",
        }
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        expected_device_info = DeviceInfo(
            identifiers={(DOMAIN, "device_001")},
            name="Test Device",
            manufacturer="Everhome",
            model="Smart Shutter Pro",
            sw_version="2.1.0",
        )
        assert cover._attr_device_info == expected_device_info

    def test_cover_device_info_defaults(self, mock_coordinator):
        """Test cover device info with defaults."""
        device_data = {
            "id": "device_002",
            "subtype": "shutter",
        }
        cover = EverhomeCover(mock_coordinator, "device_002", device_data)

        assert cover._attr_name == "Cover device_002"
        assert cover._attr_device_info["model"] == "Shutter"
        assert cover._attr_device_info["sw_version"] == "Unknown"

    def test_device_data_property(self, mock_coordinator):
        """Test device_data property."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        assert cover.device_data == device_data

    def test_device_data_property_missing_device(self, mock_coordinator):
        """Test device_data property when device is missing."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "missing_device", device_data)

        assert cover.device_data == {}

    def test_available_property(self, mock_coordinator):
        """Test available property."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        assert cover.available is True

        # Test unavailable device
        cover_unavailable = EverhomeCover(
            mock_coordinator, "missing_device", device_data
        )
        assert cover_unavailable.available is False

    def test_assumed_state_property(self, mock_coordinator):
        """Test assumed_state property."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        assert cover.assumed_state is True

    def test_is_closed_property_general_state(self, mock_coordinator):
        """Test is_closed property using general state."""
        # Test closed state
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)
        assert cover.is_closed is True

        # Test open state
        device_data = mock_coordinator.data["awning_001"]
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)
        assert cover.is_closed is False

    def test_is_closed_property_position_fallback(self, mock_coordinator):
        """Test is_closed property using position fallback."""
        device_data = {
            "id": "device_001",
            "position": 5,  # At threshold, should be closed
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.is_closed is True

        # Test position > threshold
        device_data["position"] = 10
        assert cover.is_closed is False

    def test_is_closed_property_unknown_state(self, mock_coordinator):
        """Test is_closed property with unknown state."""
        device_data = {
            "id": "device_001",
            # No states or position
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.is_closed is None

    def test_is_open_property_general_state(self, mock_coordinator):
        """Test is_open property using general state."""
        # Test open state
        device_data = mock_coordinator.data["awning_001"]
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)
        assert cover.is_open is True

        # Test closed state
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)
        assert cover.is_open is False

    def test_is_open_property_position_fallback(self, mock_coordinator):
        """Test is_open property using position fallback."""
        device_data = {
            "id": "device_001",
            "position": 95,  # At threshold, should be open
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.is_open is True

        # Test position < threshold
        device_data["position"] = 90
        assert cover.is_open is False

    def test_is_opening_property(self, mock_coordinator):
        """Test is_opening property."""
        device_data = {
            "id": "device_001",
            "state": "opening",
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.is_opening is True

        # Test non-opening state
        device_data["state"] = "stopped"
        assert cover.is_opening is False

    def test_is_closing_property(self, mock_coordinator):
        """Test is_closing property."""
        device_data = {
            "id": "device_001",
            "state": "closing",
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.is_closing is True

        # Test non-closing state
        device_data["state"] = "stopped"
        assert cover.is_closing is False

    def test_current_cover_position_with_position(self, mock_coordinator):
        """Test current_cover_position property with position data."""
        device_data = mock_coordinator.data["awning_001"]
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)

        assert cover.current_cover_position == 75

    def test_current_cover_position_boundary_values(self, mock_coordinator):
        """Test current_cover_position property with boundary values."""
        device_data = {
            "id": "device_001",
            "position": 150,  # Above max
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)
        assert cover.current_cover_position == 100

        # Test below min
        device_data["position"] = -10
        assert cover.current_cover_position == 0

    def test_current_cover_position_general_state_fallback(self, mock_coordinator):
        """Test current_cover_position property using general state fallback."""
        device_data = {
            "id": "device_001",
            "states": {"general": "down"},
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.current_cover_position == 0

        # Test open state
        device_data["states"]["general"] = "up"
        assert cover.current_cover_position == 100

    def test_current_cover_position_no_data(self, mock_coordinator):
        """Test current_cover_position property with no position data."""
        device_data = {
            "id": "device_001",
            # No position or states
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        assert cover.current_cover_position is None

    async def test_async_open_cover(self, mock_coordinator):
        """Test opening cover."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        await cover.async_open_cover()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "shutter_001", "up"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_close_cover(self, mock_coordinator):
        """Test closing cover."""
        device_data = mock_coordinator.data["awning_001"]
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)

        await cover.async_close_cover()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "awning_001", "down"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_stop_cover(self, mock_coordinator):
        """Test stopping cover."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        await cover.async_stop_cover()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "shutter_001", "stop"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_set_cover_position_with_capability(self, mock_coordinator):
        """Test setting cover position with set_position capability."""
        device_data = {
            "id": "device_001",
            "capabilities": ["set_position"],
        }
        mock_coordinator.data["device_001"] = device_data
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        await cover.async_set_cover_position(**{ATTR_POSITION: 50})

        mock_coordinator.execute_device_action.assert_called_once_with(
            "device_001", "set_position", {"position": 50}
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_async_set_cover_position_fallback_open(self, mock_coordinator):
        """Test setting cover position fallback to open."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        with patch.object(cover, "async_open_cover") as mock_open:
            await cover.async_set_cover_position(**{ATTR_POSITION: 75})
            mock_open.assert_called_once()

    async def test_async_set_cover_position_fallback_close(self, mock_coordinator):
        """Test setting cover position fallback to close."""
        device_data = mock_coordinator.data["shutter_001"]
        cover = EverhomeCover(mock_coordinator, "shutter_001", device_data)

        with patch.object(cover, "async_close_cover") as mock_close:
            await cover.async_set_cover_position(**{ATTR_POSITION: 25})
            mock_close.assert_called_once()

    def test_supported_features_without_position(self, mock_coordinator):
        """Test supported features without position support."""
        device_data = {
            "id": "device_001",
            "name": "Test Device",
            "subtype": "shutter",
            # No position field
        }
        cover = EverhomeCover(mock_coordinator, "device_001", device_data)

        expected_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        assert cover._attr_supported_features == expected_features

    def test_supported_features_with_position(self, mock_coordinator):
        """Test supported features with position support."""
        device_data = mock_coordinator.data["awning_001"]  # Has position
        cover = EverhomeCover(mock_coordinator, "awning_001", device_data)

        expected_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert cover._attr_supported_features == expected_features
