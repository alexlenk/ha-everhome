# Everhome Integration: Expansion Opportunities

This document summarises what the Everhome platform supports beyond the shutters/covers
currently implemented, and maps each device category to its natural Home Assistant entity
type.

---

## What Is Currently Supported

The integration filters `GET /device` responses to cover-type subtypes only:

| API subtype  | HA device class      |
|-------------|----------------------|
| `shutter`   | `CoverDeviceClass.SHUTTER` |
| `blind`     | `CoverDeviceClass.BLIND`   |
| `curtain`   | `CoverDeviceClass.BLIND`   |
| `awning`    | `CoverDeviceClass.AWNING`  |
| `garage_door` | `CoverDeviceClass.GARAGE` |

> **Known bug**: the coordinator filters for `"garage_door"` (with underscore) but the
> Everhome API returns the subtype as `"garagedoor"` (no underscore). Garage doors are
> therefore silently ignored at the moment.

---

## Full List of API Device Subtypes

The following subtypes were confirmed from the Everhome developer API documentation
(`https://everhome.cloud/en/developer/api`):

```
heating, cooling,
door, window, sensor, waterdetector, mobile,
light, socket, watering,
shutter, awning, blind, curtain,
speaker, bell, impulse, wakeonlan, httprequest,
motiondetector, smokedetector, voicecontrol, lightsensor, ipcamera,
gateway, sender, entrancecontrol,
electricitymeter, solar, inverter, garagedoor
```

---

## Device State Fields (API Schema)

The `states` object on a device can contain:

| Field               | Type    | Example values                  |
|---------------------|---------|---------------------------------|
| `general`           | string  | `on`, `off`, `up`, `down`, `in`, `out` |
| `temperature`       | float   | `21.5` (°C)                     |
| `humidity`          | integer | `55` (%)                        |
| `state`             | string  | `open`, `closed`, `bright`, `dark` |
| `batteryboolean`    | string  | `battery-ok`, `battery-low`     |
| `valve`             | numeric | 0–100 (%)                       |
| `luminance`         | numeric | lux                             |
| `power`             | numeric | watts                           |
| `brightness`        | numeric | 0–100 (%)                       |
| `rain`              | numeric |                                 |
| `wind`              | numeric |                                 |
| `co2`               | numeric | ppm                             |
| `noise`             | numeric | dB                              |
| `pressure`          | numeric | hPa                             |
| `batterypercentage` | numeric | 0–100                           |
| `temperaturetarget` | float   | °C                              |

StateDefinition types: `options`, `float`, `color`, `bool`

---

## Expansion Opportunities by Category

### 1. Light — `light` platform

| API subtype   | HA entity type | Notes |
|---------------|----------------|-------|
| `light`       | `LightEntity`  | `states.general` = `on`/`off`; `states.brightness` for dimming |
| `lightsensor` | `SensorEntity` | `states.luminance` in lux |

**Effort**: Low. The `general` on/off state maps directly to `LightEntity`. Brightness
and colour (if the `color` StateDefinition is present) add dimmer/RGB support.

---

### 2. Climate / Heating — `climate` platform

| API subtype | HA entity type  | Notes |
|-------------|-----------------|-------|
| `heating`   | `ClimateEntity` | `states.temperature` (current), `states.temperaturetarget` (set point), `states.valve` (%) |
| `cooling`   | `ClimateEntity` | Same fields; HVAC mode `cool` instead of `heat` |

Supported API actions for room temperature: `override-begin` and `override-cancel`.

**Effort**: Medium. Requires mapping `temperaturetarget` writes to the execute endpoint
and handling the `override` actions for temporary setpoint changes.

---

### 3. Binary Sensors — `binary_sensor` platform

| API subtype      | HA device class    | Trigger field / value |
|------------------|--------------------|-----------------------|
| `door`           | `BinarySensorDeviceClass.DOOR`     | `states.state` = `open`/`closed` |
| `window`         | `BinarySensorDeviceClass.WINDOW`   | `states.state` = `open`/`closed` |
| `motiondetector` | `BinarySensorDeviceClass.MOTION`   | `states.general` = `on`/`off` |
| `smokedetector`  | `BinarySensorDeviceClass.SMOKE`    | `states.general` = `on`/`off` |
| `waterdetector`  | `BinarySensorDeviceClass.MOISTURE` | `states.general` = `on`/`off` |

**Effort**: Low. All are read-only; just map the relevant state field to `is_on`.

---

### 4. Sensors — `sensor` platform

| API subtype      | Measurement     | Unit | State field |
|------------------|-----------------|------|-------------|
| `sensor`         | varies          | —    | context-dependent |
| `lightsensor`    | illuminance     | lx   | `states.luminance` |
| `electricitymeter` | energy / power | kWh / W | `states.power` |
| `solar`          | solar energy    | W / kWh | `states.power` |
| `inverter`       | inverter output | W    | `states.power` |

Temperature and humidity from `heating`/`cooling` devices can also be exposed as
additional `sensor` entities (secondary entities on the same device).

**Effort**: Low for read-only sensors. Energy platform integration (`recorder` support
for `total_increasing`) would add more value for `electricitymeter`/`solar`.

---

### 5. Switch — `switch` platform

| API subtype | HA entity type  | Notes |
|-------------|-----------------|-------|
| `socket`    | `SwitchEntity`  | `states.general` = `on`/`off`; actions `on`/`off` |
| `watering`  | `SwitchEntity`  | `states.general` = `on`/`off`; or use `valve` % |

**Effort**: Low. Straightforward on/off mapping identical to a basic light without
brightness.

---

### 6. Lock / Access Control — `lock` platform

| API subtype       | HA entity type | Notes |
|-------------------|----------------|-------|
| `entrancecontrol` | `LockEntity`   | `states.state` = `open`/`closed` |

**Effort**: Medium. Need to confirm available execute actions (likely `open`/`close`
or `lock`/`unlock`). May be read-only depending on device capability.

---

### 7. Camera — `camera` platform

| API subtype | HA entity type  | Notes |
|-------------|-----------------|-------|
| `ipcamera`  | `CameraEntity`  | Stream URL not yet confirmed in public API docs |

**Effort**: High. Requires the API to expose an MJPEG or RTSP stream URL, which is not
documented in the current public developer docs. Needs further investigation.

---

### 8. Media Player — `media_player` platform

| API subtype | HA entity type       | Notes |
|-------------|----------------------|-------|
| `speaker`   | `MediaPlayerEntity`  | Very limited — likely only on/off via `general` state |

**Effort**: High. Full media player features (volume, track, source) are unlikely to be
available through the generic Everhome execute API.

---

## Additional Cover Subtypes (Quick Win)

The current cover platform already works; the following subtypes just need to be added
to the coordinator filter and an appropriate `CoverDeviceClass` mapping:

| API subtype  | HA device class suggestion  |
|-------------|------------------------------|
| `garagedoor` | `CoverDeviceClass.GARAGE` (fix existing `garage_door` typo) |
| `door`       | `CoverDeviceClass.DOOR` (if motorised) |
| `window`     | `CoverDeviceClass.WINDOW` (if motorised) |

> Note: `door` and `window` appear in both the binary_sensor and cover categories.
> The distinction is whether the device is motorised (cover) or a contact sensor
> (binary_sensor). The API `subtype` field alone may not be sufficient to distinguish
> them; the `capabilities` array should be checked.

---

## Recommended Implementation Order

Based on effort vs. user value:

1. **Fix `garagedoor` subtype bug** — trivial, zero new code
2. **Binary sensors** (`door`, `window`, `motiondetector`, `smokedetector`, `waterdetector`) — low effort, high value for security/automation
3. **Light** (`light`) — low effort, very common device type
4. **Switch** (`socket`, `watering`) — low effort
5. **Sensors** (`electricitymeter`, `solar`, `lightsensor`, etc.) — low effort, useful for energy dashboard
6. **Climate** (`heating`, `cooling`) — medium effort, very common use case
7. **Lock** (`entrancecontrol`) — medium effort
8. **Camera** (`ipcamera`) — high effort, blocked on undocumented stream URL
9. **Media player** (`speaker`) — high effort, limited API capability

---

## Manufacturer Ecosystem

156 manufacturers are listed as compatible, including notable brands:
Aqara, FRITZ!, Gardena, Homematic, IKEA, Jarolift, Ledvance, Netatmo, Philips Hue,
Siemens, Sonoff, SolarEdge, Tuya, and many others.

Radio protocols supported by the CloudBox 4.0: **433 MHz, 868 MHz, 2.4 GHz ZigBee**.

---

## Gaps in Public API Documentation

- No documented list of valid `action` keys per subtype (confirmed only: `up`, `down`,
  `stop`, `on`, `off`, `set_position`, `override-begin`, `override-cancel`)
- No stream URL specification for `ipcamera`
- The `capabilities` array structure is referenced but not formally documented
- Colour/RGB control fields for lights are mentioned as a StateDefinition type (`color`)
  but no field names or value format are documented

---

*Sources: [Everhome developer docs](https://everhome.cloud/en/developer),
[Compatible devices](https://everhome.cloud/en/compatible-devices-in-package-basis)*
