# Tasks: Binary Sensor Platform

## Implementation Tasks

- [x] **1. Extend coordinator device filter**
  - [x] 1.1 Add `COVER_SUBTYPES` and `BINARY_SENSOR_SUBTYPES` sets to `const.py`
  - [x] 1.2 Update `coordinator.py` `_get_devices()` to filter by `COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES` instead of an inline list
  - [x] 1.3 Update `coordinator.py` imports to use the new constants
  - [x] 1.4 Update `tests/test_coordinator.py` — add `door`, `window`, `motiondetector`, `smokedetector`, `waterdetector` to the filter test; verify they are included and unknown subtypes are still excluded

- [x] **2. Register binary_sensor platform**
  - [x] 2.1 Add `"binary_sensor"` to `PLATFORMS` list in `const.py`
  - [x] 2.2 Verify `__init__.py` forwards setup/unload to all platforms via `PLATFORMS` (no change needed if already generic)

- [x] **3. Implement `binary_sensor.py`**
  - [x] 3.1 Create `custom_components/everhome/binary_sensor.py`
  - [x] 3.2 Implement `async_setup_entry` — iterate `coordinator.data`, filter to `BINARY_SENSOR_SUBTYPES`, create `EverhomeBinarySensor` entities
  - [x] 3.3 Implement `EverhomeBinarySensor.__init__` — unique ID, device info, device class from `_DEVICE_CLASS_MAP`
  - [x] 3.4 Implement `device_data` property (cast pattern from `cover.py`)
  - [x] 3.5 Implement `available` property
  - [x] 3.6 Implement `is_on` property with subtype-aware state field selection (see design)
  - [x] 3.7 Implement `extra_state_attributes` for `battery_low` and `battery_level`

- [x] **4. Write tests**
  - [x] 4.1 Create `tests/test_binary_sensor.py`
  - [x] 4.2 Test `async_setup_entry` creates correct number of entities for mixed device list
  - [x] 4.3 Test `is_on` returns `True`/`False`/`None` for all state combinations per subtype
  - [x] 4.4 Test `device_class` for each of the five subtypes
  - [x] 4.5 Test `battery_low` attribute for `battery-low`, `battery-ok`, and absent
  - [x] 4.6 Test `battery_level` attribute present/absent
  - [x] 4.7 Test `available` is `False` when device ID missing from coordinator data

- [x] **5. Code quality & CI**
  - [x] 5.1 Run `black` and `isort` on changed files
  - [x] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [x] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [x] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes (87%, 90 tests)
  - [x] 5.5 Push to `claude/binary-sensors` branch and confirm CI green
