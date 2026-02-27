# Tasks: Switch Platform

## Implementation Tasks

- [x] **1. Update constants**
  - [x] 1.1 Add `SWITCH_SUBTYPES = {"socket", "watering"}` to `const.py`
  - [x] 1.2 Add `"switch"` to `PLATFORMS` in `const.py`
  - [x] 1.3 Update `SUPPORTED_SUBTYPES` (or coordinator filter) to include `SWITCH_SUBTYPES`

- [x] **2. Update coordinator device filter**
  - [x] 2.1 Extend the subtype filter in `coordinator.py` to include `socket` and `watering`
  - [x] 2.2 Update `tests/test_coordinator.py` — add `socket` and `watering` to the included-subtype assertions

- [x] **3. Implement `switch.py`**
  - [x] 3.1 Create `custom_components/everhome/switch.py`
  - [x] 3.2 Implement `async_setup_entry` — filter coordinator data to `SWITCH_SUBTYPES`, create entities
  - [x] 3.3 Implement `EverhomeSwitch.__init__` — unique ID, device info, device class from `_DEVICE_CLASS_MAP`, icon from `_ICON_MAP`
  - [x] 3.4 Implement `device_data` and `available` properties (same pattern as `cover.py`)
  - [x] 3.5 Implement `is_on` property — map `states.general` `"on"`/`"off"` to `bool | None`
  - [x] 3.6 Implement `async_turn_on` — send `"on"` action then `async_request_refresh`
  - [x] 3.7 Implement `async_turn_off` — send `"off"` action then `async_request_refresh`

- [x] **4. Write tests**
  - [x] 4.1 Create `tests/test_switch.py`
  - [x] 4.2 Test entity creation — only `socket`/`watering` created, other subtypes excluded
  - [x] 4.3 Test `is_on` for `"on"`, `"off"`, and missing `states.general`
  - [x] 4.4 Test `device_class` for `socket` → `OUTLET` and `watering` → `SWITCH`
  - [x] 4.5 Test icon `mdi:water` set for `watering`; no custom icon for `socket`
  - [x] 4.6 Test `async_turn_on` — `execute_device_action("on")` called, then refresh
  - [x] 4.7 Test `async_turn_off` — `execute_device_action("off")` called, then refresh
  - [x] 4.8 Test `available` is `False` when device ID missing from coordinator data

- [x] **5. Code quality & CI**
  - [x] 5.1 Run `black` and `isort` on changed files
  - [x] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [x] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [x] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes (100%, 147 tests)
  - [x] 5.5 Push to `claude/switch-platform` branch and confirm CI green
