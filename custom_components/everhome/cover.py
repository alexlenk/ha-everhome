"""Support for Everhome covers."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ACTION_OPEN,
    ACTION_CLOSE,
    ACTION_STOP,
    STATE_OPEN,
    STATE_CLOSED,
    STATE_OPENING,
    STATE_CLOSING,
)
from .coordinator import EverhomeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Everhome covers based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Add covers from the coordinator data
    covers = []
    for device_id, device_data in coordinator.data.items():
        covers.append(EverhomeCover(coordinator, device_id, device_data))

    async_add_entities(covers)


class EverhomeCover(CoordinatorEntity, CoverEntity):
    """Representation of an Everhome cover."""

    coordinator: EverhomeDataUpdateCoordinator

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: str,
        device_data: dict,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_name = device_data.get("name", f"Cover {device_id}")
        # Include the entry_id in the unique_id to support multiple accounts
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{device_id}"
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )

        # Add position support if available in the device data
        if "position" in device_data:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="Everhome",
            model=device_data.get("model", "Shutter"),
            sw_version=device_data.get("firmware_version", "Unknown"),
        )
        
        # Set entity icon
        self._attr_icon = "mdi:window-shutter"

    @property
    def device_data(self) -> dict:
        """Return the device data."""
        return self.coordinator.data.get(self._device_id, {})
        
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device_id in self.coordinator.data

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        # Since we can't reliably know the state, return None
        # This makes Home Assistant enable both open and close buttons
        return None
        
    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        state = self.device_data.get("state")
        return state == STATE_OPENING

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        state = self.device_data.get("state")
        return state == STATE_CLOSING
        
    @property
    def is_open(self) -> bool:
        """Return if the cover is open."""
        # Since we can't reliably know the state, return None
        # This makes Home Assistant enable both open and close buttons
        return None

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover."""
        position = self.device_data.get("position")
        if position is not None:
            # Convert to 0-100 scale if needed
            return int(position)
        # If no position is available, use a default value
        # that will keep both buttons enabled
        return 50

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_OPEN)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_CLOSE)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self.coordinator.execute_device_action(self._device_id, ACTION_STOP)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            # If API supports direct position setting
            if "set_position" in self.device_data.get("capabilities", []):
                await self.coordinator.execute_device_action(
                    self._device_id, "set_position", {"position": position}
                )
            else:
                # Fallback to open/close based on position
                if position > 50:
                    await self.async_open_cover()
                else:
                    await self.async_close_cover()
            
            await self.coordinator.async_request_refresh()