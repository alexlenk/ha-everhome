"""Test Everhome binary sensor entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant

from custom_components.everhome.binary_sensor import (
    EverhomeBinarySensor,
    async_setup_entry,
)
from custom_components.everhome.const import DOMAIN


class TestEverhomeBinarySensor:
    """Test Everhome binary sensor entity."""

    @pytest.fixture
    def mock_coordinator(self, mock_config_entry):
        """Mock coordinator with a mixed set of device data."""
        coordinator = AsyncMock()
        coordinator.entry = mock_config_entry
        coordinator.data = {
            "door_001": {
                "id": "door_001",
                "name": "Front Door",
                "subtype": "door",
                "states": {"state": "closed"},
            },
            "window_001": {
                "id": "window_001",
                "name": "Kitchen Window",
                "subtype": "window",
                "states": {"state": "open"},
            },
            "motion_001": {
                "id": "motion_001",
                "name": "Hallway Motion",
                "subtype": "motiondetector",
                "states": {"general": "off"},
            },
            "smoke_001": {
                "id": "smoke_001",
                "name": "Living Room Smoke",
                "subtype": "smokedetector",
                "states": {"general": "off"},
            },
            "water_001": {
                "id": "water_001",
                "name": "Basement Water",
                "subtype": "waterdetector",
                "states": {"general": "off"},
            },
            # cover device — must NOT appear as binary sensor
            "shutter_001": {
                "id": "shutter_001",
                "name": "Bedroom Shutter",
                "subtype": "shutter",
                "states": {"general": "down"},
            },
        }
        return coordinator

    # ------------------------------------------------------------------
    # async_setup_entry
    # ------------------------------------------------------------------

    async def test_async_setup_entry_creates_only_binary_sensors(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Only binary-sensor subtypes become entities; covers are excluded."""
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        entities: list[EverhomeBinarySensor] = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        assert len(entities) == 5
        device_ids = {e._device_id for e in entities}
        assert "door_001" in device_ids
        assert "window_001" in device_ids
        assert "motion_001" in device_ids
        assert "smoke_001" in device_ids
        assert "water_001" in device_ids
        assert "shutter_001" not in device_ids

    # ------------------------------------------------------------------
    # device_class
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "subtype,expected_class",
        [
            ("door", BinarySensorDeviceClass.DOOR),
            ("window", BinarySensorDeviceClass.WINDOW),
            ("motiondetector", BinarySensorDeviceClass.MOTION),
            ("smokedetector", BinarySensorDeviceClass.SMOKE),
            ("waterdetector", BinarySensorDeviceClass.MOISTURE),
        ],
    )
    def test_device_class(self, mock_coordinator, subtype, expected_class):
        """Device class is correctly mapped for every subtype."""
        sensor = EverhomeBinarySensor(
            mock_coordinator,
            "test_id",
            {"name": "Test", "subtype": subtype},
        )
        assert sensor._attr_device_class == expected_class

    # ------------------------------------------------------------------
    # is_on — contact sensors (door / window)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("subtype", ["door", "window"])
    def test_is_on_contact_open(self, mock_coordinator, subtype):
        """Contact sensor: states.state = 'open' → is_on True."""
        sensor = EverhomeBinarySensor(
            mock_coordinator,
            "test_id",
            {"name": "Test", "subtype": subtype, "states": {"state": "open"}},
        )
        mock_coordinator.data = {
            "test_id": {"name": "Test", "subtype": subtype, "states": {"state": "open"}}
        }
        assert sensor.is_on is True

    @pytest.mark.parametrize("subtype", ["door", "window"])
    def test_is_on_contact_closed(self, mock_coordinator, subtype):
        """Contact sensor: states.state = 'closed' → is_on False."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": subtype,
                "states": {"state": "closed"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator,
            "test_id",
            mock_coordinator.data["test_id"],
        )
        assert sensor.is_on is False

    @pytest.mark.parametrize("subtype", ["door", "window"])
    def test_is_on_contact_no_state(self, mock_coordinator, subtype):
        """Contact sensor: missing state field → is_on None."""
        mock_coordinator.data = {
            "test_id": {"name": "Test", "subtype": subtype, "states": {}}
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.is_on is None

    # ------------------------------------------------------------------
    # is_on — general sensors (motion / smoke / water)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "subtype", ["motiondetector", "smokedetector", "waterdetector"]
    )
    def test_is_on_general_on(self, mock_coordinator, subtype):
        """General sensor: states.general = 'on' → is_on True."""
        mock_coordinator.data = {
            "test_id": {"name": "Test", "subtype": subtype, "states": {"general": "on"}}
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.is_on is True

    @pytest.mark.parametrize(
        "subtype", ["motiondetector", "smokedetector", "waterdetector"]
    )
    def test_is_on_general_off(self, mock_coordinator, subtype):
        """General sensor: states.general = 'off' → is_on False."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": subtype,
                "states": {"general": "off"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.is_on is False

    @pytest.mark.parametrize(
        "subtype", ["motiondetector", "smokedetector", "waterdetector"]
    )
    def test_is_on_general_no_state(self, mock_coordinator, subtype):
        """General sensor: missing general field → is_on None."""
        mock_coordinator.data = {
            "test_id": {"name": "Test", "subtype": subtype, "states": {}}
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.is_on is None

    # ------------------------------------------------------------------
    # Battery attributes
    # ------------------------------------------------------------------

    def test_battery_low_true(self, mock_coordinator):
        """battery-low string → battery_low attribute True."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": "motiondetector",
                "states": {"general": "off", "batteryboolean": "battery-low"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.extra_state_attributes["battery_low"] is True

    def test_battery_low_false(self, mock_coordinator):
        """battery-ok string → battery_low attribute False."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": "motiondetector",
                "states": {"general": "off", "batteryboolean": "battery-ok"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.extra_state_attributes["battery_low"] is False

    def test_battery_low_absent(self, mock_coordinator):
        """No batteryboolean → battery_low key not present in attributes."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": "motiondetector",
                "states": {"general": "off"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert "battery_low" not in sensor.extra_state_attributes

    def test_battery_level_present(self, mock_coordinator):
        """batterypercentage present → battery_level integer attribute."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": "motiondetector",
                "states": {"general": "off", "batterypercentage": 75},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert sensor.extra_state_attributes["battery_level"] == 75

    def test_battery_level_absent(self, mock_coordinator):
        """No batterypercentage → battery_level key not present."""
        mock_coordinator.data = {
            "test_id": {
                "name": "Test",
                "subtype": "motiondetector",
                "states": {"general": "off"},
            }
        }
        sensor = EverhomeBinarySensor(
            mock_coordinator, "test_id", mock_coordinator.data["test_id"]
        )
        assert "battery_level" not in sensor.extra_state_attributes

    # ------------------------------------------------------------------
    # availability
    # ------------------------------------------------------------------

    def test_available_when_device_present(self, mock_coordinator):
        """Entity is available when device ID is in coordinator data."""
        sensor = EverhomeBinarySensor(
            mock_coordinator, "door_001", mock_coordinator.data["door_001"]
        )
        assert sensor.available is True

    def test_available_false_when_device_missing(self, mock_coordinator):
        """Entity is unavailable when device ID is not in coordinator data."""
        sensor = EverhomeBinarySensor(
            mock_coordinator,
            "missing_device",
            {"name": "Gone", "subtype": "door"},
        )
        assert sensor.available is False

    # ------------------------------------------------------------------
    # unique_id and device_info
    # ------------------------------------------------------------------

    def test_unique_id_includes_entry_id(self, mock_coordinator):
        """Unique ID is scoped to the config entry to support multi-account."""
        sensor = EverhomeBinarySensor(
            mock_coordinator, "door_001", mock_coordinator.data["door_001"]
        )
        assert (
            sensor._attr_unique_id
            == f"{DOMAIN}_{mock_coordinator.entry.entry_id}_door_001"
        )
