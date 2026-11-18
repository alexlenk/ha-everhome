"""Support for Everhome switches."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ACTION_OFF, ACTION_ON, STATE_OFF, STATE_ON, SWITCH_SUBTYPES
from .coordinator import EverhomeConfigEntry, EverhomeDataUpdateCoordinator
from .entity import EverhomeEntity, async_setup_platform_entities

_DEVICE_CLASS_MAP: dict[str, SwitchDeviceClass] = {
    "socket": SwitchDeviceClass.OUTLET,
    "watering": SwitchDeviceClass.SWITCH,
}

_ICON_MAP: dict[str, str] = {
    "watering": "mdi:water",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverhomeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Everhome switches based on a config entry."""
    async_setup_platform_entities(
        entry, async_add_entities, SWITCH_SUBTYPES, EverhomeSwitch
    )


class EverhomeSwitch(EverhomeEntity, SwitchEntity):
    """Representation of an Everhome switch."""

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: int,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_id, device_data)
        subtype = device_data.get("subtype", "socket")
        self._attr_device_class = _DEVICE_CLASS_MAP.get(subtype)
        self._attr_icon = _ICON_MAP.get(subtype)

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        general = self.states.get("general")
        if general == STATE_ON:
            return True
        if general == STATE_OFF:
            return False
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_OFF)
        await self.coordinator.async_request_refresh()
