# Requirements: Switch Platform

- **Feature Name**: Switch Platform
- **Version**: 1.0
- **Date**: 2026-02-27
- **Author**: Alex Lenk

## Introduction

### Feature Summary
Expose Everhome `socket` and `watering` devices as Home Assistant `switch` entities, enabling on/off control through HA automations, dashboards, and voice assistants.

### Business Value
Smart sockets and irrigation valves are common in Everhome installations. A simple on/off switch entity is the lowest-effort, highest-compatibility mapping for both device types. Once available in HA, users can schedule irrigation, control appliances, and build energy-saving automations.

### Scope
**Included:**
- Subtypes: `socket`, `watering`
- On/off control via `action: "on"` / `action: "off"`
- `states.general` (`on`/`off`) for current state
- Shared coordinator (no new polling)
- Unit tests ≥ 85 % coverage

**Excluded:**
- `watering` timer/duration control (deferred — requires confirmed API action schema)
- Power consumption attributes from `states.power` (deferred to sensor platform spec)
- Any subtype beyond `socket` and `watering`

---

## Requirements

### Requirement 1: Device Discovery

**User Story:** As a Home Assistant user, I want Everhome sockets and irrigation valves to appear automatically after setup, so that I do not need to configure them manually.

#### Acceptance Criteria

1. WHEN the integration loads THEN the system SHALL discover all devices whose `subtype` is `socket` or `watering`.
2. WHEN a new switch device is added to the Everhome account THEN the system SHALL add it on the next coordinator refresh.
3. WHEN a switch device is removed THEN the system SHALL mark the entity as unavailable.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Coordinator must include `socket` and `watering` in its device filter

---

### Requirement 2: On/Off Control

**User Story:** As a Home Assistant user, I want to turn sockets and irrigation valves on and off from HA, so that I can automate appliances and watering schedules.

#### Acceptance Criteria

1. WHEN the user calls `switch.turn_on` THEN the system SHALL send `action: "on"` to `POST /device/{id}/execute`.
2. WHEN the user calls `switch.turn_off` THEN the system SHALL send `action: "off"` to `POST /device/{id}/execute`.
3. WHEN `states.general` is `"on"` THEN the system SHALL report the entity as `STATE_ON`.
4. WHEN `states.general` is `"off"` THEN the system SHALL report the entity as `STATE_OFF`.
5. IF `states.general` is absent THEN the system SHALL return `None` (entity shown as unavailable in HA).

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Dependencies**: Requirement 1

---

### Requirement 3: Device Class Assignment

**User Story:** As a Home Assistant user, I want switch entities to display contextual icons so that I can distinguish sockets from irrigation valves at a glance.

#### Acceptance Criteria

1. WHEN a device has subtype `socket` THEN the system SHALL assign `SwitchDeviceClass.OUTLET`.
2. WHEN a device has subtype `watering` THEN the system SHALL assign `SwitchDeviceClass.SWITCH` and use icon `mdi:water`.

#### Additional Details
- **Priority**: Low
- **Complexity**: Low
- **Dependencies**: Requirement 1

---

### Requirement 4: Multi-Account Support

**User Story:** As a Home Assistant user with multiple Everhome accounts, I want each switch entity to have a unique ID, so that there are no conflicts.

#### Acceptance Criteria

1. WHEN two config entries exist THEN the system SHALL use `{domain}_{entry_id}_{device_id}` as the unique ID for every switch entity.

#### Additional Details
- **Priority**: High
- **Complexity**: Low
- **Assumptions**: Mirrors existing convention in `cover.py`

---

## Non-Functional Requirements

### Reliability
- WHEN the coordinator poll fails THEN the system SHALL mark all switch entities as unavailable (inherited from `CoordinatorEntity`).

---

## Constraints and Assumptions

- `watering` valve duration/timer control is excluded until the API action schema is confirmed from a real device.
- API on/off action keys are assumed to be `"on"` and `"off"` (consistent with the light platform).

---

## Success Criteria

### Definition of Done
- [ ] All acceptance criteria pass
- [ ] ≥ 85 % test coverage maintained
- [ ] `black`, `isort`, `mypy`, `flake8` all pass
- [ ] HACS and Hassfest validation pass
- [ ] `"switch"` added to `PLATFORMS` in `const.py`

---

## Glossary

| Term | Definition |
|------|-----------|
| `states.general` | API state field; `"on"` / `"off"` |
| `SwitchDeviceClass.OUTLET` | HA device class that displays a socket icon |
| `socket` | Everhome smart plug/socket subtype |
| `watering` | Everhome irrigation valve subtype |
