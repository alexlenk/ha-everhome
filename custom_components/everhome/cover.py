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
    ACTION_CLOSE,
    ACTION_OPEN,
    ACTION_STOP,
    DOMAIN,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
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
        # Set appropriate device class based on subtype
        subtype = device_data.get("subtype", "shutter")
        if subtype == "garage_door":
            self._attr_device_class = CoverDeviceClass.GARAGE
        elif subtype in ["blind", "curtain"]:
            self._attr_device_class = CoverDeviceClass.BLIND
        elif subtype == "awning":
            self._attr_device_class = CoverDeviceClass.AWNING
        else:
            self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

        # Add position support if available in the device data
        if "position" in device_data:
            self._attr_supported_features |= CoverEntityFeature.SET_POSITION

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._attr_name,
            manufacturer="Everhome",
            model=device_data.get("model", subtype.replace("_", " ").title()),
            sw_version=device_data.get("firmware_version", "Unknown"),
        )

        # Set appropriate icon based on device type
        if subtype == "garage_door":
            self._attr_icon = "mdi:garage"
        elif subtype == "blind":
            self._attr_icon = "mdi:blinds"
        elif subtype == "curtain":
            self._attr_icon = "mdi:curtains"
        elif subtype == "awning":
            self._attr_icon = "mdi:awning-outline"
        else:
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
    def assumed_state(self) -> bool:
        """Return True to keep all buttons available regardless of state."""
        return True

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed."""
        device_data = self.device_data

        # API uses states.general with "up"/"down" values
        general_state = device_data.get("states", {}).get("general")
        position = device_data.get("position")

        # Use actual API state format: "down" = closed, "up" = open
        if general_state == "down":
            return True
        elif general_state == "up":
            return False

        # Fallback to position if no explicit state
        if position is not None:
            return int(position) <= 5

        # Return None to keep all buttons active when state unknown
        # This ensures open, close, and stop are always available
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
    def is_open(self) -> bool | None:
        """Return if the cover is open."""
        device_data = self.device_data

        # API uses states.general with "up"/"down" values
        general_state = device_data.get("states", {}).get("general")
        position = device_data.get("position")

        # Use actual API state format: "up" = open, "down" = closed
        if general_state == "up":
            return True
        elif general_state == "down":
            return False

        # Fallback to position if no explicit state
        if position is not None:
            return int(position) >= 95

        # Return None to keep all buttons active when state unknown
        # This ensures open, close, and stop are always available
        return None

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover."""
        position = self.device_data.get("position")
        if position is not None:
            # Ensure position is within 0-100 range
            return max(0, min(100, int(position)))

        # If no position available, infer from general state
        general_state = self.device_data.get("states", {}).get("general")
        if general_state == "down":
            return 0  # Closed
        elif general_state == "up":
            return 100  # Open

        # Return None if no reliable position data
        # This will hide the position slider in HA UI
        return None

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
