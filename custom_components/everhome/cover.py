"""Support for Everhome covers."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ACTION_CLOSE,
    ACTION_OPEN,
    ACTION_STOP,
    COVER_CLOSED_STATES,
    COVER_OPEN_STATES,
    COVER_SUBTYPES,
)
from .coordinator import EverhomeConfigEntry, EverhomeDataUpdateCoordinator
from .entity import EverhomeEntity, async_setup_platform_entities

_DEVICE_CLASS_MAP: dict[str, CoverDeviceClass] = {
    "garagedoor": CoverDeviceClass.GARAGE,
    "blind": CoverDeviceClass.BLIND,
    "curtain": CoverDeviceClass.BLIND,
    "awning": CoverDeviceClass.AWNING,
}

_ICON_MAP: dict[str, str] = {
    "garagedoor": "mdi:garage",
    "blind": "mdi:blinds",
    "curtain": "mdi:curtains",
    "awning": "mdi:awning-outline",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EverhomeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Everhome covers based on a config entry."""
    async_setup_platform_entities(
        entry, async_add_entities, COVER_SUBTYPES, EverhomeCover
    )


class EverhomeCover(EverhomeEntity, CoverEntity):
    """Representation of an Everhome cover.

    The everHome API only reports "up"/"down" (or "out"/"in" for awnings) and
    accepts the actions up/down/stop, so there is no position control.
    """

    # everHome can't see a cover moved by a remote or wall switch, so its state
    # may be stale; keep open and close available at all times.
    _attr_assumed_state = True
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: int,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator, device_id, device_data)
        subtype = device_data.get("subtype", "shutter")
        self._attr_device_class = _DEVICE_CLASS_MAP.get(
            subtype, CoverDeviceClass.SHUTTER
        )
        self._attr_icon = _ICON_MAP.get(subtype, "mdi:window-shutter")

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed, or None if the state is unknown."""
        general = self.states.get("general")
        if general in COVER_CLOSED_STATES:
            return True
        if general in COVER_OPEN_STATES:
            return False
        return None

    @property
    def current_cover_position(self) -> int | None:
        """Return 100 (open) or 0 (closed), derived from states.general."""
        closed = self.is_closed
        if closed is None:
            return None
        return 0 if closed else 100

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._async_execute(ACTION_OPEN)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._async_execute(ACTION_CLOSE)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        await self._async_execute(ACTION_STOP)

    async def _async_execute(self, action: str) -> None:
        await self.coordinator.execute_device_action(self._device_id, action)
        await self.coordinator.async_request_refresh()
