"""Support for Everhome lights."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ACTION_OFF, ACTION_ON, LIGHT_SUBTYPES, STATE_OFF, STATE_ON
from .coordinator import EverhomeConfigEntry
from .entity import EverhomeEntity, async_setup_platform_entities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverhomeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Everhome lights based on a config entry."""
    async_setup_platform_entities(
        entry, async_add_entities, LIGHT_SUBTYPES, EverhomeLight
    )


class EverhomeLight(EverhomeEntity, LightEntity):
    """Representation of an Everhome light.

    The everHome execute endpoint only takes an action key, so lights are
    switched on/off; dimming is not documented and not supported.
    """

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self) -> bool | None:
        """Return True if the light is on."""
        general = self.states.get("general")
        if general == STATE_ON:
            return True
        if general == STATE_OFF:
            return False
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_OFF)
        await self.coordinator.async_request_refresh()
