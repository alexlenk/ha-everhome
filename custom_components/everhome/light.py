"""Support for Everhome lights."""

from __future__ import annotations

import logging
from typing import Any, cast

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LIGHT_SUBTYPES
from .coordinator import EverhomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# API brightness is 0-100; HA brightness is 0-255
_API_MAX = 100
_HA_MAX = 255

# Capability key that signals dimmer support
_BRIGHTNESS_CAPS = {"set_brightness", "brightness"}


def _api_to_ha_brightness(api_val: int) -> int:
    return round(api_val * _HA_MAX / _API_MAX)


def _ha_to_api_brightness(ha_val: int) -> int:
    return round(ha_val * _API_MAX / _HA_MAX)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Everhome lights based on a config entry."""
    coordinator: EverhomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EverhomeLight(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
        if device_data.get("subtype") in LIGHT_SUBTYPES
    )


class EverhomeLight(CoordinatorEntity, LightEntity):
    """Representation of an Everhome light."""

    coordinator: EverhomeDataUpdateCoordinator

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = device_data.get("name", f"Light {device_id}")
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{device_id}"

        caps = set(device_data.get("capabilities", []))
        if caps & _BRIGHTNESS_CAPS:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="Everhome",
            model=device_data.get("model", "Light"),
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
        """Return True if the light is on."""
        general = self.device_data.get("states", {}).get("general")
        if general == "on":
            return True
        if general == "off":
            return False
        return None

    @property
    def brightness(self) -> int | None:
        """Return current brightness in HA scale (0-255)."""
        api_val = self.device_data.get("states", {}).get("brightness")
        if api_val is None:
            return None
        return _api_to_ha_brightness(int(api_val))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, optionally setting brightness."""
        ha_brightness = kwargs.get(ATTR_BRIGHTNESS)
        if (
            ha_brightness is not None
            and ColorMode.BRIGHTNESS in self._attr_supported_color_modes
        ):
            api_brightness = _ha_to_api_brightness(int(ha_brightness))
            await self.coordinator.execute_device_action(
                self._device_id, "set_brightness", {"brightness": api_brightness}
            )
        else:
            await self.coordinator.execute_device_action(self._device_id, "on")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.execute_device_action(self._device_id, "off")
        await self.coordinator.async_request_refresh()
