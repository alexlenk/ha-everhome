# Tasks: Switch Platform

## Implementation Tasks

- [ ] **1. Update constants**
  - [ ] 1.1 Add `SWITCH_SUBTYPES = {"socket", "watering"}` to `const.py`
  - [ ] 1.2 Add `"switch"` to `PLATFORMS` in `const.py`
  - [ ] 1.3 Update `SUPPORTED_SUBTYPES` (or coordinator filter) to include `SWITCH_SUBTYPES`

- [ ] **2. Update coordinator device filter**
  - [ ] 2.1 Extend the subtype filter in `coordinator.py` to include `socket` and `watering`
  - [ ] 2.2 Update `tests/test_coordinator.py` — add `socket` and `watering` to the included-subtype assertions

- [ ] **3. Implement `switch.py`**
  - [ ] 3.1 Create `custom_components/everhome/switch.py`
  - [ ] 3.2 Implement `async_setup_entry` — filter coordinator data to `SWITCH_SUBTYPES`, create entities
  - [ ] 3.3 Implement `EverhomeSwitch.__init__` — unique ID, device info, device class from `_DEVICE_CLASS_MAP`, icon from `_ICON_MAP`
  - [ ] 3.4 Implement `device_data` and `available` properties (same pattern as `cover.py`)
  - [ ] 3.5 Implement `is_on` property — map `states.general` `"on"`/`"off"` to `bool | None`
  - [ ] 3.6 Implement `async_turn_on` — send `"on"` action then `async_request_refresh`
  - [ ] 3.7 Implement `async_turn_off` — send `"off"` action then `async_request_refresh`

- [ ] **4. Write tests**
  - [ ] 4.1 Create `tests/test_switch.py`
  - [ ] 4.2 Test entity creation — only `socket`/`watering` created, other subtypes excluded
  - [ ] 4.3 Test `is_on` for `"on"`, `"off"`, and missing `states.general`
  - [ ] 4.4 Test `device_class` for `socket` → `OUTLET` and `watering` → `SWITCH`
  - [ ] 4.5 Test icon `mdi:water` set for `watering`; no custom icon for `socket`
  - [ ] 4.6 Test `async_turn_on` — `execute_device_action("on")` called, then refresh
  - [ ] 4.7 Test `async_turn_off` — `execute_device_action("off")` called, then refresh
  - [ ] 4.8 Test `available` is `False` when device ID missing from coordinator data

- [ ] **5. Code quality & CI**
  - [ ] 5.1 Run `black` and `isort` on changed files
  - [ ] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [ ] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [ ] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes
  - [ ] 5.5 Push to `claude/switch-platform` branch and confirm CI green
