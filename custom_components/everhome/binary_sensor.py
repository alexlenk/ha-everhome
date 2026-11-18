"""Support for Everhome binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import BINARY_SENSOR_SUBTYPES, STATE_OFF, STATE_ON
from .coordinator import EverhomeConfigEntry, EverhomeDataUpdateCoordinator
from .entity import EverhomeEntity, async_setup_platform_entities

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
    entry: EverhomeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Everhome binary sensors based on a config entry."""
    async_setup_platform_entities(
        entry, async_add_entities, BINARY_SENSOR_SUBTYPES, EverhomeBinarySensor
    )


class EverhomeBinarySensor(EverhomeEntity, BinarySensorEntity):
    """Representation of an Everhome binary sensor."""

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: int,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_id, device_data)
        self._subtype = device_data.get("subtype", "")
        self._attr_device_class = _DEVICE_CLASS_MAP.get(self._subtype)

    @property
    def is_on(self) -> bool | None:
        """Return True if the sensor is triggered."""
        if self._subtype in _CONTACT_SUBTYPES:
            state = self.states.get("state")
            if state == "open":
                return True
            if state == "closed":
                return False
            return None

        general = self.states.get("general")
        if general == STATE_ON:
            return True
        if general == STATE_OFF:
            return False
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return battery state attributes if present."""
        attrs: dict[str, Any] = {}
        states = self.states

        battery_bool = states.get("batteryboolean")
        if battery_bool is not None:
            attrs["battery_low"] = battery_bool == "battery-low"

        battery_pct = states.get("batterypercentage")
        if battery_pct is not None:
            attrs["battery_level"] = int(battery_pct)

        return attrs
