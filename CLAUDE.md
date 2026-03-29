# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

> For autonomous agent operating procedures (issue triage, release workflow, CI monitoring), see [AGENT_SYSTEM_PROMPT.md](./AGENT_SYSTEM_PROMPT.md).

## Project Overview

Home Assistant custom integration for Everhome shutter/cover control via OAuth2 cloud API. The integration supports shutters, blinds, awnings, curtains, garage doors, lights, switches, and binary sensors as HA entities.

## Development Commands

### Testing
```bash
# Run all tests with coverage
PYTHONPATH="$PWD" pytest tests/ -v

# Run specific test file
PYTHONPATH="$PWD" pytest tests/test_cover.py -v

# Run tests with coverage report (matches CI threshold of 85%)
PYTHONPATH="$PWD" pytest tests/ --cov=custom_components.everhome --cov-report=term-missing --cov-fail-under=85
```

### ⚠️ Mandatory Pre-Commit Checklist

Run ALL of these before every commit. CI will fail if any step is skipped.

```bash
# Black and isort are not installed globally — use the ecowitt_local venv:
BLACK=/Users/alexlenk/Github/ecowitt_local/.venv/bin/black
ISORT=/Users/alexlenk/Github/ecowitt_local/.venv/bin/isort

# 1. Format
$BLACK custom_components/ tests/

# 2. Sort imports
$ISORT custom_components/ tests/

# 3. Type check (mypy.ini is the authoritative config)
mypy custom_components/everhome/

# 4. Lint
flake8 custom_components/ tests/

# 5. Tests with coverage (must stay >= 85%)
PYTHONPATH="$PWD" pytest tests/ --cov=custom_components.everhome --cov-report=term-missing --cov-fail-under=85
```

All five steps must pass before pushing. Never push a branch that fails any of these locally.

### Install Dependencies
```bash
pip install -r requirements_test.txt
```

## Architecture

### Core Files
- `__init__.py` — Entry setup/unload; validates OAuth token, creates coordinator, forwards to all platforms
- `api.py` — `EverhomeAuth`: wraps OAuth2Session, provides `async_get_access_token()` and `aiohttp_session`
- `coordinator.py` — `EverhomeDataUpdateCoordinator`: polls `/device` every 5 minutes, filters for supported subtypes, executes device actions
- `cover.py` — `EverhomeCover` entity (shutters, blinds, awnings, curtains, garage doors)
- `binary_sensor.py` — `EverhomeBinarySensor` entity (door, window, motion, smoke, water sensors)
- `light.py` — `EverhomeLight` entity (dimmable and on/off lights)
- `switch.py` — `EverhomeSwitch` entity (sockets, watering)
- `config_flow.py` — OAuth2 config flow; validates credentials by fetching device list
- `application_credentials.py` — Provides OAuth2 authorize/token URLs
- `const.py` — All constants (URLs, states, actions, domain, subtype sets per platform)

### Platforms and Device Subtypes
| Platform | Subtypes |
|---|---|
| `cover` | `shutter`, `blind`, `awning`, `curtain`, `garagedoor` |
| `binary_sensor` | `door`, `window`, `motiondetector`, `smokedetector`, `waterdetector` |
| `light` | `light` |
| `switch` | `socket`, `watering` |

### API Data Structure
Devices are returned as a flat JSON array from `GET /device`. Each device has:
- `id` — unique device identifier
- `subtype` — determines which platform handles the device (see table above)
- `name` — display name
- `states.general` — current state (varies by platform)
- `position` — integer 0–100 (covers only, optional)
- `capabilities` — list of supported actions (e.g., `["set_position"]`, `["set_brightness"]`)
- `model`, `firmware_version` — device info

### State Field Convention
- Covers: `states.general` = `"up"` (open) / `"down"` (closed) / `"opening"` / `"closing"`
- Lights/switches: `states.general` = `"on"` / `"off"`
- Contact sensors (`door`, `window`): `states.state` = `"open"` / `"closed"`
- Motion/smoke/water sensors: `states.general` = `"on"` / `"off"`

The flat `state` field is NOT used.

## CI / GitHub Actions

### Workflows
| Workflow | Trigger | Purpose |
|---|---|---|
| `test.yml` | push to `main`/`dev`/`claude/**`, PRs to `main`, manual | Tests, type check, lint, HACS/Hassfest validation |
| `release-please.yml` | manual only (disabled) | Legacy — replaced by auto-release.yml |
| `release.yml` | GitHub release published | Final validation on release |
| `hacs-validation.yml` | push/PR to `main`, daily, manual | HACS validation |
| `hassfest.yml` | push/PR to `main`, daily, manual | Hassfest validation |

### CI Monitoring (MANDATORY)
After pushing changes on a `claude/**` branch:
1. Wait for CI to complete on the branch
2. If CI fails, fetch the logs and fix before merging:
   ```bash
   gh run list --branch <branch> --limit 5
   gh api repos/alexlenk/ha-everhome/actions/jobs/<job-id>/logs
   ```
3. All tests must pass and coverage must stay at or above 85%

## Release Process

Releases are fully automated via `auto-pr.yml` → `auto-merge.yml` → `auto-release.yml`.

### To cut a release (e.g. v0.7.0):
```bash
git checkout main && git pull origin main
git checkout -b claude/release-v0.7.0

# 1. Bump version in manifest.json
# 2. Add entry to CHANGELOG.md under ## [0.7.0]

git add custom_components/everhome/manifest.json CHANGELOG.md
git commit -m "chore: release v0.7.0"
git push -u origin claude/release-v0.7.0
```

### Automated chain (fully hands-off after push):
1. `Test` CI runs on `claude/release-v0.7.0`
2. **auto-pr** creates PR titled "Release v0.7.0" → triggers auto-merge
3. **auto-merge** finds and merges any open "Release v*" PR to main
4. **auto-release** creates git tag `v0.7.0` + GitHub Release
5. **HACS** detects the new release via the tag

### Verify the full pipeline completed:
```bash
git fetch origin --tags
git tag -l | sort -V | tail -5      # tag should exist
gh pr list --state merged --limit 3  # PR should be merged
gh release list --limit 3            # release should exist
```

### Version file
Only `custom_components/everhome/manifest.json` needs to be bumped. `pyproject.toml` and `.release-please-manifest.json` are no longer kept in sync.

### Release Checklist
- [ ] All CI tests passing (≥85% coverage)
- [ ] Version bumped in `manifest.json`
- [ ] `CHANGELOG.md` updated with `## [X.Y.Z]` section
- [ ] Pushed to `claude/release-vX.Y.Z` branch

## HACS Requirements
- Git tags must follow `vX.Y.Z` format
- GitHub Release must exist (not just a tag)
- `hacs.json` must be valid
- `manifest.json` version must match tag

## mypy Configuration
`mypy.ini` is the authoritative mypy config — it takes precedence over `[tool.mypy]` in `pyproject.toml` (which has been removed). `mypy.ini` includes critical per-module ignores for `homeassistant.*` and `pytest_homeassistant_custom_component.*` to avoid false errors from unresolvable HA source types.

Known acceptable suppression: `# type: ignore[call-arg]` on the `ConfigFlow` class definition to silence the false-positive mypy error on `domain=DOMAIN`.

## Issue Management Protocol

### Reading Issues
Always read the full issue body **and all comments** in chronological order. If a comment contains an image URL, download and view it — screenshots often contain HA log output or error details not present in the text.

### After Implementing a Fix
1. Create a release with the fix
2. Post a comment on the issue explaining what was fixed and asking for confirmation
3. **Do NOT close the issue** — leave it open for the user to confirm
4. Only close after the user explicitly confirms the fix resolved their problem

### Comment Template
```markdown
## Fix Available in vX.Y.Z — Please Test

I've released **vX.Y.Z** which should fix this.

### What was changed:
- [specific explanation]

### To test:
1. Update to vX.Y.Z via HACS
2. Restart Home Assistant
3. [specific thing to check]

Let me know if this resolves it.
```
