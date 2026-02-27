# Tasks: Light Platform

## Implementation Tasks

- [x] **1. Update constants**
  - [x] 1.1 Add `LIGHT_SUBTYPES = {"light"}` to `const.py`
  - [x] 1.2 Add `"light"` to `PLATFORMS` in `const.py`
  - [x] 1.3 Update `SUPPORTED_SUBTYPES` (or coordinator filter) to include `LIGHT_SUBTYPES`

- [x] **2. Update coordinator device filter**
  - [x] 2.1 Extend the subtype filter in `coordinator.py` to include `light`
  - [x] 2.2 Update `tests/test_coordinator.py` — add `light` to the included-subtype assertions

- [x] **3. Implement `light.py`**
  - [x] 3.1 Create `custom_components/everhome/light.py`
  - [x] 3.2 Implement `async_setup_entry` — filter coordinator data to `LIGHT_SUBTYPES`, create entities
  - [x] 3.3 Implement `EverhomeLight.__init__` — unique ID, device info, feature/color-mode flags based on `capabilities`
  - [x] 3.4 Implement `device_data` and `available` properties (same pattern as `cover.py`)
  - [x] 3.5 Implement `is_on` property — map `states.general` `"on"`/`"off"` to `bool | None`
  - [x] 3.6 Implement `brightness` property — convert API 0–100 to HA 0–255; return `None` if absent
  - [x] 3.7 Implement `async_turn_on` — send `set_brightness` with converted value if brightness arg present and supported; otherwise send `on`
  - [x] 3.8 Implement `async_turn_off` — send `off` action

- [x] **4. Write tests**
  - [x] 4.1 Create `tests/test_light.py`
  - [x] 4.2 Test entity creation from coordinator data (only `light` subtypes, not covers or sensors)
  - [x] 4.3 Test `is_on` for `"on"`, `"off"`, and missing state
  - [x] 4.4 Test `brightness` conversion: API `50` → HA `128` (rounded); absent → `None`
  - [x] 4.5 Test `async_turn_on` without brightness — `execute_device_action` called with `"on"`
  - [x] 4.6 Test `async_turn_on` with HA brightness `255` — sends `set_brightness` with API value `100`
  - [x] 4.7 Test `async_turn_on` with brightness on non-dimmable device — falls back to `"on"` only
  - [x] 4.8 Test `async_turn_off` — `execute_device_action` called with `"off"`
  - [x] 4.9 Test `ColorMode.BRIGHTNESS` set when `capabilities` includes `"set_brightness"`
  - [x] 4.10 Test `ColorMode.ONOFF` set when no brightness capability

- [x] **5. Code quality & CI**
  - [x] 5.1 Run `black` and `isort` on changed files
  - [x] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [x] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [x] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes (89%, 107 tests)
  - [x] 5.5 Push to `claude/light-platform` branch and confirm CI green
