# Design: Light Platform

- **Feature Name**: Light Platform
- **Version**: 1.0
- **Date**: 2026-02-27

## Overview

Add a `light.py` platform that exposes Everhome `light`-subtype devices as HA `LightEntity` instances. On/off control maps to `action: "on"/"off"` on the execute endpoint. Brightness (when supported) uses `action: "set_brightness"` with a `brightness` parameter.

---

## Architecture

### Component Interaction

```
HA Core
  └─ async_setup_entry (__init__.py)
       ├─ EverhomeDataUpdateCoordinator  (coordinator.py)
       │    └─ GET /device  →  all supported subtypes
       ├─ cover platform       (cover.py)
       ├─ binary_sensor platform (binary_sensor.py)
       └─ light platform       (light.py)  ← new
```

### Coordinator / const Changes

Add `"light"` to `SUPPORTED_SUBTYPES` in `const.py` (alongside the cover and binary sensor sets):

```python
LIGHT_SUBTYPES = {"light"}
SUPPORTED_SUBTYPES = COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES | LIGHT_SUBTYPES
```

Add `"light"` to `PLATFORMS`:

```python
PLATFORMS = ["cover", "binary_sensor", "light"]
```

---

## New File: `light.py`

### `async_setup_entry`

```python
async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        EverhomeLight(coordinator, device_id, device_data)
        for device_id, device_data in coordinator.data.items()
        if device_data.get("subtype") in LIGHT_SUBTYPES
    ]
    async_add_entities(entities)
```

### Class: `EverhomeLight`

Inherits `CoordinatorEntity` and `LightEntity`.

#### Brightness scale conversion

```
HA scale:  0–255  (integer)
API scale: 0–100  (integer)

api_brightness = round(ha_brightness * 100 / 255)
ha_brightness  = round(api_brightness * 255 / 100)
```

#### Feature flags

```python
self._attr_supported_features = LightEntityFeature(0)
self._attr_supported_color_modes = {ColorMode.ONOFF}
self._attr_color_mode = ColorMode.ONOFF

if "set_brightness" in device_data.get("capabilities", []) or \
   "brightness" in device_data.get("capabilities", []):
    self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    self._attr_color_mode = ColorMode.BRIGHTNESS
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

#### `brightness`

```python
@property
def brightness(self) -> int | None:
    api_val = self.device_data.get("states", {}).get("brightness")
    if api_val is None:
        return None
    return round(int(api_val) * 255 / 100)
```

#### `async_turn_on`

```python
async def async_turn_on(self, **kwargs: Any) -> None:
    if ATTR_BRIGHTNESS in kwargs and ColorMode.BRIGHTNESS in self._attr_supported_color_modes:
        api_brightness = round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)
        await self.coordinator.execute_device_action(
            self._device_id, "set_brightness", {"brightness": api_brightness}
        )
    else:
        await self.coordinator.execute_device_action(self._device_id, "on")
    await self.coordinator.async_request_refresh()
```

#### `async_turn_off`

```python
async def async_turn_off(self, **kwargs: Any) -> None:
    await self.coordinator.execute_device_action(self._device_id, "off")
    await self.coordinator.async_request_refresh()
```

---

## Files Changed

| File | Change |
|------|--------|
| `custom_components/everhome/light.py` | **New** |
| `custom_components/everhome/const.py` | Add `LIGHT_SUBTYPES`, `"light"` to `PLATFORMS` and `SUPPORTED_SUBTYPES` |
| `tests/test_light.py` | **New** — unit tests |
| `tests/test_coordinator.py` | Add `light` subtype to filter test |

---

## Testing Strategy

- `is_on` for `"on"`, `"off"`, and absent `states.general`
- `brightness` conversion from API 0–100 to HA 0–255, and `None` when absent
- `async_turn_on` without brightness — sends `"on"` action
- `async_turn_on` with brightness — sends `"set_brightness"` with converted value
- `async_turn_on` with brightness on a device that doesn't support it — sends only `"on"`
- `async_turn_off` — sends `"off"` action
- Feature flag set correctly based on `capabilities`
- `available` when device missing from coordinator data
