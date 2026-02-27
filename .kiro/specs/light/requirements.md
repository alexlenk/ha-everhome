# Requirements: Light Platform

- **Feature Name**: Light Platform
- **Version**: 1.0
- **Date**: 2026-02-27
- **Author**: Alex Lenk

## Introduction

### Feature Summary
Expose Everhome light devices (`light` subtype) as Home Assistant `light` entities, supporting on/off control and, where available, brightness adjustment.

### Business Value
Lighting is among the most common smart home use cases. Everhome already supports 156 manufacturers across lighting categories (bulbs, dimmers, LED controls). Surfacing them in HA enables unified control alongside covers and sensors without requiring users to manage separate apps.

### Scope
**Included:**
- Subtype: `light`
- On/off control via `action: "on"` / `action: "off"`
- Brightness control when `set_brightness` or `brightness` is listed in `capabilities`
- `states.general` (`on`/`off`) for current state
- `states.brightness` (0–100) for current brightness level
- Shared coordinator (no new polling)
- Unit tests ≥ 85 % coverage

**Excluded:**
- Colour/RGB control (StateDefinition type `color` is documented but field names are unconfirmed — deferred to a follow-up spec)
- `lightsensor` subtype (read-only sensor — covered by a separate sensor platform spec)
- Scene/group control

---

## Requirements

### Requirement 1: Device Discovery

**User Story:** As a Home Assistant user, I want Everhome lights to appear automatically after setup, so that I can control them without manual configuration.

#### Acceptance Criteria

1. WHEN the integration loads THEN the system SHALL discover all devices whose `subtype` is `light`.
2. WHEN a new light device is added to the Everhome account THEN the system SHALL add it on the next coordinator refresh.
3. WHEN a light device is removed THEN the system SHALL mark the entity as unavailable.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Coordinator must include `light` in its device filter

---

### Requirement 2: On/Off Control

**User Story:** As a Home Assistant user, I want to turn lights on and off from HA, so that I can include them in automations and dashboards.

#### Acceptance Criteria

1. WHEN the user calls `light.turn_on` THEN the system SHALL send `action: "on"` to `POST /device/{id}/execute`.
2. WHEN the user calls `light.turn_off` THEN the system SHALL send `action: "off"` to `POST /device/{id}/execute`.
3. WHEN `states.general` is `"on"` THEN the system SHALL report the entity state as `STATE_ON`.
4. WHEN `states.general` is `"off"` THEN the system SHALL report the entity state as `STATE_OFF`.
5. IF `states.general` is absent THEN the system SHALL report the entity as unavailable.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Requirement 1

---

### Requirement 3: Brightness Control

**User Story:** As a Home Assistant user, I want to set brightness on dimmable lights, so that I can create the right atmosphere.

#### Acceptance Criteria

1. WHEN `set_brightness` or `brightness` is in the device `capabilities` array THEN the system SHALL advertise `LightEntityFeature.BRIGHTNESS` support.
2. WHEN the user calls `light.turn_on` with a `brightness` value (0–255 HA scale) THEN the system SHALL convert it to the 0–100 API scale and send `action: "set_brightness"` with a `brightness` parameter.
3. WHEN `states.brightness` is present THEN the system SHALL return it converted from 0–100 to 0–255 as `brightness`.
4. IF the device does not support brightness THEN the system SHALL accept `light.turn_on` without a brightness argument and send only `action: "on"`.

#### Additional Details
- **Priority**: Medium
- **Complexity**: Low
- **Dependencies**: Requirement 2
- **Assumptions**: API brightness scale is 0–100; HA brightness scale is 0–255

---

### Requirement 4: Multi-Account Support

**User Story:** As a Home Assistant user with multiple Everhome accounts, I want each light entity to have a unique ID, so that there are no conflicts.

#### Acceptance Criteria

1. WHEN two config entries exist THEN the system SHALL use `{domain}_{entry_id}_{device_id}` as the unique ID for every light entity.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Assumptions**: Mirrors existing convention in `cover.py`

---

## Non-Functional Requirements

### Reliability
- WHEN the coordinator poll fails THEN the system SHALL mark all light entities as unavailable (inherited from `CoordinatorEntity`).

### Usability
- WHEN a light has no brightness capability THEN the system SHALL hide the brightness slider in the HA UI (by not advertising the feature flag).

---

## Constraints and Assumptions

- The API action key for brightness is assumed to be `"set_brightness"` based on the pattern seen in the cover `"set_position"` action. This must be confirmed against a real device during implementation.
- Colour/RGB control is out of scope until API field names are confirmed.

---

## Success Criteria

### Definition of Done
- [ ] All acceptance criteria pass
- [ ] ≥ 85 % test coverage maintained
- [ ] `black`, `isort`, `mypy`, `flake8` all pass
- [ ] HACS and Hassfest validation pass
- [ ] `"light"` added to `PLATFORMS` in `const.py`

---

## Glossary

| Term | Definition |
|------|-----------|
| `states.general` | API state field; `"on"` / `"off"` |
| `states.brightness` | API brightness 0–100 |
| `capabilities` | Array of action keys the device supports |
| `LightEntityFeature.BRIGHTNESS` | HA flag that enables the brightness slider |
