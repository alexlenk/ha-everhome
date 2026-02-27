"""Test Everhome switch entities."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.core import HomeAssistant

from custom_components.everhome.const import DOMAIN
from custom_components.everhome.switch import EverhomeSwitch, async_setup_entry


class TestEverhomeSwitch:
    """Test Everhome switch entity."""

    @pytest.fixture
    def mock_coordinator(self, mock_config_entry):
        """Mock coordinator with a mixed set of device data."""
        coordinator = AsyncMock()
        coordinator.entry = mock_config_entry
        coordinator.data = {
            "socket_001": {
                "id": "socket_001",
                "name": "Living Room Socket",
                "subtype": "socket",
                "states": {"general": "off"},
            },
            "watering_001": {
                "id": "watering_001",
                "name": "Garden Valve",
                "subtype": "watering",
                "states": {"general": "off"},
            },
            # cover — must NOT appear as a switch entity
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

    async def test_async_setup_entry_creates_only_switches(
        self, hass: HomeAssistant, mock_config_entry, mock_coordinator
    ):
        """Only switch subtypes become entities; other types are excluded."""
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        entities: list[EverhomeSwitch] = []

        def mock_add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, mock_config_entry, mock_add_entities)

        assert len(entities) == 2
        device_ids = {e._device_id for e in entities}
        assert "socket_001" in device_ids
        assert "watering_001" in device_ids
        assert "shutter_001" not in device_ids

    # ------------------------------------------------------------------
    # device_class and icon
    # ------------------------------------------------------------------

    def test_device_class_socket(self, mock_coordinator):
        """socket subtype → OUTLET device class."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert switch._attr_device_class == SwitchDeviceClass.OUTLET

    def test_device_class_watering(self, mock_coordinator):
        """watering subtype → SWITCH device class."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "watering_001",
            mock_coordinator.data["watering_001"],
        )
        assert switch._attr_device_class == SwitchDeviceClass.SWITCH

    def test_icon_watering(self, mock_coordinator):
        """watering subtype gets mdi:water icon."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "watering_001",
            mock_coordinator.data["watering_001"],
        )
        assert switch._attr_icon == "mdi:water"

    def test_icon_socket_none(self, mock_coordinator):
        """socket subtype has no custom icon (uses device class default)."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert switch._attr_icon is None

    # ------------------------------------------------------------------
    # is_on
    # ------------------------------------------------------------------

    def test_is_on_when_on(self, mock_coordinator):
        """states.general = 'on' → is_on True."""
        mock_coordinator.data["socket_001"]["states"]["general"] = "on"
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert switch.is_on is True

    def test_is_on_when_off(self, mock_coordinator):
        """states.general = 'off' → is_on False."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert switch.is_on is False

    def test_is_on_when_state_absent(self, mock_coordinator):
        """Missing states.general → is_on None."""
        mock_coordinator.data = {
            "socket_001": {"name": "Test", "subtype": "socket", "states": {}}
        }
        switch = EverhomeSwitch(
            mock_coordinator, "socket_001", mock_coordinator.data["socket_001"]
        )
        assert switch.is_on is None

    # ------------------------------------------------------------------
    # async_turn_on / async_turn_off
    # ------------------------------------------------------------------

    async def test_turn_on(self, mock_coordinator):
        """turn_on sends action 'on' then triggers refresh."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        await switch.async_turn_on()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "socket_001", "on"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    async def test_turn_off(self, mock_coordinator):
        """turn_off sends action 'off' then triggers refresh."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        await switch.async_turn_off()

        mock_coordinator.execute_device_action.assert_called_once_with(
            "socket_001", "off"
        )
        mock_coordinator.async_request_refresh.assert_called_once()

    # ------------------------------------------------------------------
    # availability and unique ID
    # ------------------------------------------------------------------

    def test_available_when_present(self, mock_coordinator):
        """Entity is available when device ID is in coordinator data."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert switch.available is True

    def test_available_false_when_missing(self, mock_coordinator):
        """Entity is unavailable when device ID is not in coordinator data."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "missing_id",
            {"name": "Gone", "subtype": "socket"},
        )
        assert switch.available is False

    def test_unique_id_includes_entry_id(self, mock_coordinator):
        """Unique ID is scoped to the config entry."""
        switch = EverhomeSwitch(
            mock_coordinator,
            "socket_001",
            mock_coordinator.data["socket_001"],
        )
        assert (
            switch._attr_unique_id
            == f"{DOMAIN}_{mock_coordinator.entry.entry_id}_socket_001"
        )
