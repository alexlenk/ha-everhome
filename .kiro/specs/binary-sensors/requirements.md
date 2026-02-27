# Requirements: Binary Sensor Platform

- **Feature Name**: Binary Sensor Platform
- **Version**: 1.0
- **Date**: 2026-02-27
- **Author**: Alex Lenk

## Introduction

### Feature Summary
Expose Everhome contact, motion, smoke, and water-detection devices as Home Assistant `binary_sensor` entities, enabling automations and dashboards based on sensor state.

### Business Value
Binary sensors are the most common secondary device type in Everhome systems after covers. Surfacing them in Home Assistant without any extra configuration unlocks security automations, presence detection, and alert notifications with no additional setup from users.

### Scope
**Included:**
- Subtypes: `door`, `window`, `motiondetector`, `smokedetector`, `waterdetector`
- Read-only state from `states.general` (`on`/`off`) or `states.state` (`open`/`closed`)
- Battery status attribute from `states.batteryboolean` / `states.batterypercentage`
- Correct HA device class per subtype
- Shared `EverhomeDataUpdateCoordinator` (no new polling logic)
- Unit tests ≥ 85 % coverage

**Excluded:**
- Writable/controllable sensors (no execute actions on these subtypes)
- `ipcamera`, `sensor` (generic), `mobile` subtypes (separate features)
- Adding new API endpoints

---

## Requirements

### Requirement 1: Device Discovery

**User Story:** As a Home Assistant user, I want Everhome binary sensor devices to appear automatically after setup, so that I do not need to configure them manually.

#### Acceptance Criteria

1. WHEN the integration loads THEN the system SHALL discover all devices whose `subtype` is one of `door`, `window`, `motiondetector`, `smokedetector`, or `waterdetector`.
2. WHEN a new binary sensor device is added to the Everhome account THEN the system SHALL add it to Home Assistant on the next coordinator refresh (within the configured poll interval).
3. WHEN a device is removed from the Everhome account THEN the system SHALL mark the corresponding entity as unavailable.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Coordinator must include binary-sensor subtypes in its device filter (currently it only includes cover subtypes)
- **Assumptions**: The Everhome API returns all device types from `GET /device` in a single flat array

---

### Requirement 2: State Mapping

**User Story:** As a Home Assistant user, I want binary sensor state to correctly reflect `on`/`off` in the HA UI, so that dashboards and automations work as expected.

#### Acceptance Criteria

1. WHEN `states.general` is `"on"` THEN the system SHALL report the entity as `STATE_ON` (triggered/detected).
2. WHEN `states.general` is `"off"` THEN the system SHALL report the entity as `STATE_OFF` (clear).
3. WHEN a `door` or `window` device reports `states.state` as `"open"` THEN the system SHALL report `STATE_ON`.
4. WHEN a `door` or `window` device reports `states.state` as `"closed"` THEN the system SHALL report `STATE_OFF`.
5. IF neither `states.general` nor `states.state` is present THEN the system SHALL report the entity as unavailable rather than returning an incorrect state.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Requirement 1
- **Assumptions**: `door`/`window` use `states.state` (`open`/`closed`); motion/smoke/water use `states.general` (`on`/`off`)

---

### Requirement 3: Device Class Assignment

**User Story:** As a Home Assistant user, I want each sensor to display the correct icon and label in the UI automatically, so that the dashboard is intuitive without customisation.

#### Acceptance Criteria

1. WHEN a device has subtype `door` THEN the system SHALL assign `BinarySensorDeviceClass.DOOR`.
2. WHEN a device has subtype `window` THEN the system SHALL assign `BinarySensorDeviceClass.WINDOW`.
3. WHEN a device has subtype `motiondetector` THEN the system SHALL assign `BinarySensorDeviceClass.MOTION`.
4. WHEN a device has subtype `smokedetector` THEN the system SHALL assign `BinarySensorDeviceClass.SMOKE`.
5. WHEN a device has subtype `waterdetector` THEN the system SHALL assign `BinarySensorDeviceClass.MOISTURE`.

#### Additional Details
- **Priority**: Medium
- **Complexity**: Low
- **Dependencies**: Requirement 1

---

### Requirement 4: Battery Status Attribute

**User Story:** As a Home Assistant user, I want to see battery status on battery-powered sensors, so that I can replace batteries before they run flat.

#### Acceptance Criteria

1. WHEN `states.batteryboolean` is `"battery-low"` THEN the system SHALL expose a `battery_low` extra state attribute set to `true`.
2. WHEN `states.batteryboolean` is `"battery-ok"` THEN the system SHALL expose `battery_low` as `false`.
3. WHEN `states.batterypercentage` is present THEN the system SHALL expose it as a `battery_level` extra state attribute (integer 0–100).
4. IF neither battery field is present THEN the system SHALL omit the battery attributes entirely.

#### Additional Details
- **Priority**: Low
- **Complexity**: Low
- **Dependencies**: Requirement 2

---

### Requirement 5: Multi-Account Support

**User Story:** As a Home Assistant user with multiple Everhome accounts, I want sensors from each account to have unique entity IDs, so that there are no conflicts between accounts.

#### Acceptance Criteria

1. WHEN two config entries exist THEN the system SHALL use `{domain}_{entry_id}_{device_id}` as the unique ID for every binary sensor entity.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Requirement 1
- **Assumptions**: Mirrors the existing convention in `cover.py`

---

## Non-Functional Requirements

### Reliability
- WHEN the coordinator poll fails THEN the system SHALL mark all binary sensor entities as unavailable (inherited from `CoordinatorEntity`).

### Maintainability
- WHEN the binary sensor platform is added THEN the system SHALL follow the same file and class conventions as `cover.py`.

---

## Constraints and Assumptions

### Technical Constraints
- The Everhome API provides no push/webhook mechanism — state is polled every 5 minutes.
- Binary sensors are read-only; no execute actions are available or required.

### Assumptions
- `door` and `window` subtypes may also exist as motorised covers; the coordinator will need to route them to the correct platform based on the presence of motor-related capabilities (e.g., `up`/`down` actions). For now, assume all `door`/`window` without cover capabilities are binary sensors.

---

## Success Criteria

### Definition of Done
- [ ] All five acceptance criteria groups pass
- [ ] ≥ 85 % test coverage maintained
- [ ] `black`, `isort`, `mypy`, `flake8` all pass
- [ ] HACS and Hassfest validation pass
- [ ] `binary_sensor` added to `PLATFORMS` in `const.py`

---

## Glossary

| Term | Definition |
|------|-----------|
| `states.general` | Top-level API state field; `"on"` means triggered, `"off"` means clear |
| `states.state` | Secondary state field used by contact sensors; `"open"`/`"closed"` |
| `BinarySensorDeviceClass` | HA enum that controls icon and label for binary sensor entities |
| `CoordinatorEntity` | HA base class that wires an entity to a `DataUpdateCoordinator` |
