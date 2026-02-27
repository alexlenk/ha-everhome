# Design: Binary Sensor Platform

- **Feature Name**: Binary Sensor Platform
- **Version**: 1.0
- **Date**: 2026-02-27

## Overview

Add a `binary_sensor.py` platform that mirrors the structure of the existing `cover.py`, consuming the same `EverhomeDataUpdateCoordinator` and exposing Everhome contact, motion, smoke, and water-detection devices as HA binary sensor entities.

### Key Decisions
- **Reuse the existing coordinator** — no new polling or API calls; binary sensor devices will be included in the coordinator's device filter alongside cover subtypes.
- **Single new platform file** — `custom_components/everhome/binary_sensor.py`; no new coordinator subclass needed.
- **Routing by subtype** — the coordinator will return all relevant subtypes; each platform's `async_setup_entry` will filter to its own subtypes.

---

## Architecture

### Component Interaction

```
HA Core
  └─ async_setup_entry (__init__.py)
       ├─ EverhomeDataUpdateCoordinator  (coordinator.py)
       │    └─ GET /device  →  all subtypes for all platforms
       ├─ cover platform       (cover.py)         ← existing
       └─ binary_sensor platform (binary_sensor.py) ← new
```

### Coordinator Changes

`coordinator.py` — expand the subtype filter to include binary sensor subtypes:

```python
COVER_SUBTYPES = {"shutter", "blind", "awning", "curtain", "garagedoor"}
BINARY_SENSOR_SUBTYPES = {"door", "window", "motiondetector", "smokedetector", "waterdetector"}
SUPPORTED_SUBTYPES = COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES
```

The coordinator returns **all** supported devices; each platform's `async_setup_entry` iterates `coordinator.data` and picks its own subtypes.

### `const.py` Changes

```python
PLATFORMS = ["cover", "binary_sensor"]

BINARY_SENSOR_SUBTYPES = {"door", "window", "motiondetector", "smokedetector", "waterdetector"}
```

---

## New File: `binary_sensor.py`

### Class: `EverhomeBinarySensor`

Inherits from `CoordinatorEntity` and `BinarySensorEntity`.

```python
class EverhomeBinarySensor(CoordinatorEntity, BinarySensorEntity):
    coordinator: EverhomeDataUpdateCoordinator
```

### State Logic

| Subtype           | Source field      | `is_on` = True when |
|-------------------|-------------------|----------------------|
| `motiondetector`  | `states.general`  | `"on"`              |
| `smokedetector`   | `states.general`  | `"on"`              |
| `waterdetector`   | `states.general`  | `"on"`              |
| `door`            | `states.state`    | `"open"`            |
| `window`          | `states.state`    | `"open"`            |

Fallback: if neither field is present, `is_on` returns `None` (entity unavailable).

```python
@property
def is_on(self) -> bool | None:
    data = self.device_data
    subtype = data.get("subtype")
    if subtype in {"door", "window"}:
        state = data.get("states", {}).get("state")
        if state == "open":
            return True
        if state == "closed":
            return False
        return None
    # motiondetector, smokedetector, waterdetector
    general = data.get("states", {}).get("general")
    if general == "on":
        return True
    if general == "off":
        return False
    return None
```

### Device Class Mapping

```python
_DEVICE_CLASS_MAP: dict[str, BinarySensorDeviceClass] = {
    "door": BinarySensorDeviceClass.DOOR,
    "window": BinarySensorDeviceClass.WINDOW,
    "motiondetector": BinarySensorDeviceClass.MOTION,
    "smokedetector": BinarySensorDeviceClass.SMOKE,
    "waterdetector": BinarySensorDeviceClass.MOISTURE,
}
```

### Extra State Attributes (Battery)

```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    states = self.device_data.get("states", {})
    battery_bool = states.get("batteryboolean")
    if battery_bool is not None:
        attrs["battery_low"] = battery_bool == "battery-low"
    battery_pct = states.get("batterypercentage")
    if battery_pct is not None:
        attrs["battery_level"] = int(battery_pct)
    return attrs
```

### Unique ID & Device Info

Follows the same pattern as `cover.py`:

```python
self._attr_unique_id = f"{DOMAIN}_{entry_id}_{device_id}"
self._attr_device_info = DeviceInfo(
    identifiers={(DOMAIN, device_id)},
    name=...,
    manufacturer="Everhome",
    model=device_data.get("model", subtype.title()),
    sw_version=device_data.get("firmware_version", "Unknown"),
)
```

---

## Files Changed

| File | Change |
|------|--------|
| `custom_components/everhome/binary_sensor.py` | **New** — platform setup + `EverhomeBinarySensor` class |
| `custom_components/everhome/coordinator.py` | Add binary sensor subtypes to the device filter |
| `custom_components/everhome/const.py` | Add `"binary_sensor"` to `PLATFORMS`; add `BINARY_SENSOR_SUBTYPES` set |
| `tests/test_binary_sensor.py` | **New** — unit tests |
| `tests/test_coordinator.py` | Update filter test to include new subtypes |

---

## Testing Strategy

- **Unit tests** for `EverhomeBinarySensor`:
  - `is_on` property for each subtype and state value
  - `device_class` assignment for each subtype
  - Battery attribute presence/absence
  - `available` when device is/isn't in coordinator data
- **Coordinator test** — verify new subtypes are included in filter, cover subtypes still pass, unknown subtypes still excluded
