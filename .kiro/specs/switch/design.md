# Design: Switch Platform

- **Feature Name**: Switch Platform
- **Version**: 1.0
- **Date**: 2026-02-27

## Overview

Add a `switch.py` platform that exposes Everhome `socket` and `watering` devices as HA `SwitchEntity` instances. On/off control maps directly to `action: "on"/"off"` on the execute endpoint — identical to the light platform, just without brightness.

---

## Architecture

### Component Interaction

```
HA Core
  └─ async_setup_entry (__init__.py)
       ├─ EverhomeDataUpdateCoordinator  (coordinator.py)
       │    └─ GET /device  →  all supported subtypes
       ├─ cover platform         (cover.py)
       ├─ binary_sensor platform (binary_sensor.py)
       ├─ light platform         (light.py)
       └─ switch platform        (switch.py)  ← new
```

### Coordinator / const Changes

```python
SWITCH_SUBTYPES = {"socket", "watering"}
SUPPORTED_SUBTYPES = COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES | LIGHT_SUBTYPES | SWITCH_SUBTYPES

PLATFORMS = ["cover", "binary_sensor", "light", "switch"]
```

---

## New File: `switch.py`

### `async_setup_entry`

```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        EverhomeSwitch(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
        if device_data.get("subtype") in SWITCH_SUBTYPES
    ]
    async_add_entities(entities)
```

### Class: `EverhomeSwitch`

Inherits `CoordinatorEntity` and `SwitchEntity`.

#### Device class and icon

```python
_DEVICE_CLASS_MAP: dict[str, SwitchDeviceClass] = {
    "socket": SwitchDeviceClass.OUTLET,
    "watering": SwitchDeviceClass.SWITCH,
}

_ICON_MAP: dict[str, str] = {
    "watering": "mdi:water",
}
```

In `__init__`:
```python
subtype = device_data.get("subtype", "socket")
self._attr_device_class = _DEVICE_CLASS_MAP.get(subtype)
self._attr_icon = _ICON_MAP.get(subtype)  # None → HA picks default from device class
```

#### `is_on`

```python
@property
def is_on(self) -> bool | None:
    general = self.device_data.get("states", {}).get("general")
    if general == "on":
        return True
    if general == "off":
        return False
    return None
```

#### `async_turn_on` / `async_turn_off`

```python
async def async_turn_on(self, **kwargs: Any) -> None:
    await self.coordinator.execute_device_action(self._device_id, "on")
    await self.coordinator.async_request_refresh()

async def async_turn_off(self, **kwargs: Any) -> None:
    await self.coordinator.execute_device_action(self._device_id, "off")
    await self.coordinator.async_request_refresh()
```

---

## Files Changed

| File | Change |
|------|--------|
| `custom_components/everhome/switch.py` | **New** |
| `custom_components/everhome/const.py` | Add `SWITCH_SUBTYPES`, `"switch"` to `PLATFORMS` and `SUPPORTED_SUBTYPES` |
| `tests/test_switch.py` | **New** — unit tests |
| `tests/test_coordinator.py` | Add `socket`, `watering` to filter test |

---

## Testing Strategy

- `is_on` for `"on"`, `"off"`, and absent `states.general`
- `device_class` for `socket` → `OUTLET`; `watering` → `SWITCH`
- Icon set for `watering`; `None` for `socket`
- `async_turn_on` — `execute_device_action` called with `"on"`, then `async_request_refresh`
- `async_turn_off` — `execute_device_action` called with `"off"`, then `async_request_refresh`
- Entity creation — only `socket`/`watering` subtypes included, others excluded
- `available` when device missing from coordinator data
