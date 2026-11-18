"""Base entity and platform helpers for the Everhome integration."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, cast

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EverhomeConfigEntry, EverhomeDataUpdateCoordinator


class EverhomeEntity(CoordinatorEntity[EverhomeDataUpdateCoordinator]):
    """Common base for all Everhome entities (one entity per everHome device)."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: EverhomeDataUpdateCoordinator,
        device_id: int,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        # Include the entry_id in the unique_id to support multiple accounts
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.config_entry.entry_id}_{device_id}"
        )
        subtype = str(device_data.get("subtype", ""))
        self._attr_device_info = DeviceInfo(
            # Kept as the API's int id: changing it would orphan existing devices
            identifiers={(DOMAIN, device_id)},
            name=device_data.get("name") or f"Everhome {device_id}",
            manufacturer="Everhome",
            model=subtype.title() or None,
        )

    @property
    def device_data(self) -> dict[str, Any]:
        """Return the latest data of this device."""
        return cast(dict[str, Any], self.coordinator.data.get(self._device_id, {}))

    @property
    def states(self) -> dict[str, Any]:
        """Return the device's states object."""
        return cast(dict[str, Any], self.device_data.get("states") or {})

    @property
    def available(self) -> bool:
        """Return True if the last update succeeded and the device still exists."""
        return super().available and self._device_id in self.coordinator.data


def async_setup_platform_entities(
    entry: EverhomeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    subtypes: Iterable[str],
    factory: Callable[[EverhomeDataUpdateCoordinator, int, dict[str, Any]], Entity],
) -> None:
    """Add entities for matching devices, including devices added later."""
    coordinator = entry.runtime_data
    wanted = set(subtypes)
    known: set[int] = set()

    @callback
    def _add_new_devices() -> None:
        new = [
            (device_id, data)
            for device_id, data in coordinator.data.items()
            if device_id not in known and data.get("subtype") in wanted
        ]
        if not new:
            return
        known.update(device_id for device_id, _ in new)
        async_add_entities(
            factory(coordinator, device_id, data) for device_id, data in new
        )

    _add_new_devices()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_devices))
