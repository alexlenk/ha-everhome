# Tasks: Binary Sensor Platform

## Implementation Tasks

- [ ] **1. Extend coordinator device filter**
  - [ ] 1.1 Add `COVER_SUBTYPES` and `BINARY_SENSOR_SUBTYPES` sets to `const.py`
  - [ ] 1.2 Update `coordinator.py` `_get_devices()` to filter by `COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES` instead of an inline list
  - [ ] 1.3 Update `coordinator.py` imports to use the new constants
  - [ ] 1.4 Update `tests/test_coordinator.py` — add `door`, `window`, `motiondetector`, `smokedetector`, `waterdetector` to the filter test; verify they are included and unknown subtypes are still excluded

- [ ] **2. Register binary_sensor platform**
  - [ ] 2.1 Add `"binary_sensor"` to `PLATFORMS` list in `const.py`
  - [ ] 2.2 Verify `__init__.py` forwards setup/unload to all platforms via `PLATFORMS` (no change needed if already generic)

- [ ] **3. Implement `binary_sensor.py`**
  - [ ] 3.1 Create `custom_components/everhome/binary_sensor.py`
  - [ ] 3.2 Implement `async_setup_entry` — iterate `coordinator.data`, filter to `BINARY_SENSOR_SUBTYPES`, create `EverhomeBinarySensor` entities
  - [ ] 3.3 Implement `EverhomeBinarySensor.__init__` — unique ID, device info, device class from `_DEVICE_CLASS_MAP`
  - [ ] 3.4 Implement `device_data` property (cast pattern from `cover.py`)
  - [ ] 3.5 Implement `available` property
  - [ ] 3.6 Implement `is_on` property with subtype-aware state field selection (see design)
  - [ ] 3.7 Implement `extra_state_attributes` for `battery_low` and `battery_level`

- [ ] **4. Write tests**
  - [ ] 4.1 Create `tests/test_binary_sensor.py`
  - [ ] 4.2 Test `async_setup_entry` creates correct number of entities for mixed device list
  - [ ] 4.3 Test `is_on` returns `True`/`False`/`None` for all state combinations per subtype
  - [ ] 4.4 Test `device_class` for each of the five subtypes
  - [ ] 4.5 Test `battery_low` attribute for `battery-low`, `battery-ok`, and absent
  - [ ] 4.6 Test `battery_level` attribute present/absent
  - [ ] 4.7 Test `available` is `False` when device ID missing from coordinator data

- [ ] **5. Code quality & CI**
  - [ ] 5.1 Run `black` and `isort` on changed files
  - [ ] 5.2 Run `mypy custom_components/everhome/` — zero errors
  - [ ] 5.3 Run `flake8 custom_components/ tests/` — zero errors
  - [ ] 5.4 Run `pytest tests/ --cov-fail-under=85` — passes
  - [ ] 5.5 Push to `claude/binary-sensors` branch and confirm CI green
