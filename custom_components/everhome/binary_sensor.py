"""Support for Everhome binary sensors."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BINARY_SENSOR_SUBTYPES, DOMAIN
from .coordinator import EverhomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_DEVICE_CLASS_MAP: dict[str, BinarySensorDeviceClass] = {
    "door": BinarySensorDeviceClass.DOOR,
    "window": BinarySensorDeviceClass.WINDOW,
    "motiondetector": BinarySensorDeviceClass.MOTION,
    "smokedetector": BinarySensorDeviceClass.SMOKE,
    "waterdetector": BinarySensorDeviceClass.MOISTURE,
}

# Subtypes that use states.state ("open"/"closed") instead of states.general
_CONTACT_SUBTYPES = {"door", "window"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Everhome binary sensors based on a config entry."""
    coordinator: EverhomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EverhomeBinarySensor(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
        if device_data.get("subtype") in BINARY_SENSOR_SUBTYPES
    )


class EverhomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Everhome binary sensor."""

    coordinator: EverhomeDataUpdateCoordinator

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = device_data.get("name", f"Sensor {device_id}")
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{device_id}"

        subtype = device_data.get("subtype", "")
        self._attr_device_class = _DEVICE_CLASS_MAP.get(subtype)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="Everhome",
            model=device_data.get("model", subtype.replace("_", " ").title()),
            sw_version=device_data.get("firmware_version", "Unknown"),
        )

    @property
    def device_data(self) -> dict[str, Any]:
        """Return the device data."""
        return cast(dict[str, Any], self.coordinator.data.get(self._device_id, {}))

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device_id in self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        """Return True if the sensor is triggered."""
        data = self.device_data
        subtype = data.get("subtype", "")

        if subtype in _CONTACT_SUBTYPES:
            state = data.get("states", {}).get("state")
            if state == "open":
                return True
            if state == "closed":
                return False
            return None

        general = data.get("states", {}).get("general")
        if general == "on":
            return True
        if general == "off":
            return False
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return battery state attributes if present."""
        attrs: dict[str, Any] = {}
        states = self.device_data.get("states", {})

        battery_bool = states.get("batteryboolean")
        if battery_bool is not None:
            attrs["battery_low"] = battery_bool == "battery-low"

        battery_pct = states.get("batterypercentage")
        if battery_pct is not None:
            attrs["battery_level"] = int(battery_pct)

        return attrs
