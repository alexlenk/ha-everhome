# Tasks: Light Platform

## Implementation Tasks

- [ ] **1. Update constants**
  - [ ] 1.1 Add `LIGHT_SUBTYPES = {"light"}` to `const.py`
  - [ ] 1.2 Add `"light"` to `PLATFORMS` in `const.py`
  - [ ] 1.3 Update `SUPPORTED_SUBTYPES` (or coordinator filter) to include `LIGHT_SUBTYPES`

- [ ] **2. Update coordinator device filter**
  - [ ] 2.1 Extend the subtype filter in `coordinator.py` to include `light`
  - [ ] 2.2 Update `tests/test_coordinator.py` — add `light` to the included-subtype assertions

- [ ] **3. Implement `light.py`**
  - [ ] 3.1 Create `custom_components/everhome/light.py`
  - [ ] 3.2 Implement `async_setup_entry` — filter coordinator data to `LIGHT_SUBTYPES`, create entities
  - [ ] 3.3 Implement `EverhomeLight.__init__` — unique ID, device info, feature/color-mode flags based on `capabilities`
  - [ ] 3.4 Implement `device_data` and `available` properties (same pattern as `cover.py`)
  - [ ] 3.5 Implement `is_on` property — map `states.general` `"on"`/`"off"` to `bool | None`
  - [ ] 3.6 Implement `brightness` property — convert API 0–100 to HA 0–255; return `None` if absent
  - [ ] 3.7 Implement `async_turn_on` — send `set_brightness` with converted value if brightness arg present and supported; otherwise send `on`
  - [ ] 3.8 Implement `async_turn_off` — send `off` action

- [ ] **4. Write tests**
  - [ ] 4.1 Create `tests/test_light.py`
  - [ ] 4.2 Test entity creation from coordinator data (only `light` subtypes, not covers or sensors)
  - [ ] 4.3 Test `is_on` for `"on"`, `"off"`, and missing state
  - [ ] 4.4 Test `brightness` conversion: API `50` → HA `128` (rounded); absent → `None`
  - [ ] 4.5 Test `async_turn_on` without brightness — `execute_device_action` called with `"on"`
  - [ ] 4.6 Test `async_turn_on` with HA brightness `255` — sends `set_brightness` with API value `100`
  - [ ] 4.7 Test `async_turn_on` with brightness on non-dimmable device — falls back to `"on"` only
  - [ ] 4.8 Test `async_turn_off` — `execute_device_action` called with `"off"`
  - [ ] 4.9 Test `ColorMode.BRIGHTNESS` set when `capabilities` includes `"set_brightness"`
  - [ ] 4.10 Test `ColorMode.ONOFF` set when no brightness capability

- [ ] **5. Code quality & CI**
  - [ ] 5.1 Run `black` and `isort` on changed files
  - [ ] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [ ] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [ ] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes
  - [ ] 5.5 Push to `claude/light-platform` branch and confirm CI green
