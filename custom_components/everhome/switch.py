"""Support for Everhome switches."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCH_SUBTYPES
from .coordinator import EverhomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

_DEVICE_CLASS_MAP: dict[str, SwitchDeviceClass] = {
    "socket": SwitchDeviceClass.OUTLET,
    "watering": SwitchDeviceClass.SWITCH,
}

_ICON_MAP: dict[str, str] = {
    "watering": "mdi:water",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Everhome switches based on a config entry."""
    coordinator: EverhomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EverhomeSwitch(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
        if device_data.get("subtype") in SWITCH_SUBTYPES
    )


class EverhomeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an Everhome switch."""

    coordinator: EverhomeDataUpdateCoordinator

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = device_data.get("name", f"Switch {device_id}")
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{device_id}"

        subtype = device_data.get("subtype", "socket")
        self._attr_device_class = _DEVICE_CLASS_MAP.get(subtype)
        self._attr_icon = _ICON_MAP.get(subtype)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="Everhome",
            model=device_data.get("model", subtype.title()),
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
        """Return True if the switch is on."""
        general = self.device_data.get("states", {}).get("general")
        if general == "on":
            return True
        if general == "off":
            return False
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.execute_device_action(self._device_id, "on")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.execute_device_action(self._device_id, "off")
        await self.coordinator.async_request_refresh()
