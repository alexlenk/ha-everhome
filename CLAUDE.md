# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Home Assistant custom integration for Everhome shutter/cover control via OAuth2 cloud API. The integration supports shutters, blinds, awnings, curtains, and garage doors as HA cover entities.

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

### Code Quality
```bash
# Black and isort are not installed globally — use the ecowitt_local venv:
BLACK=/Users/alexlenk/Github/ecowitt_local/.venv/bin/black
ISORT=/Users/alexlenk/Github/ecowitt_local/.venv/bin/isort

# ALWAYS run before committing to avoid CI failures:
$BLACK custom_components/ tests/
$ISORT custom_components/ tests/

# Type checking (mypy.ini is the authoritative config — do NOT edit [tool.mypy] in pyproject.toml)
mypy custom_components/everhome/

# Linting
flake8 custom_components/ tests/

# Check-only (same as CI)
$BLACK --check --diff custom_components/ tests/
$ISORT --check --diff custom_components/ tests/
mypy custom_components/everhome/
flake8 custom_components/ tests/
```

### Install Dependencies
```bash
pip install -r requirements_test.txt
```

## Architecture

### Core Files
- `__init__.py` — Entry setup/unload; validates OAuth token, creates coordinator, forwards to cover platform
- `api.py` — `EverhomeAuth`: wraps OAuth2Session, provides `async_get_access_token()` and `aiohttp_session`
- `coordinator.py` — `EverhomeDataUpdateCoordinator`: polls `/device` every 5 minutes, filters for cover subtypes, executes device actions
- `cover.py` — `EverhomeCover` entity: reads from coordinator data, sends actions via coordinator
- `config_flow.py` — OAuth2 config flow; validates credentials by fetching device list
- `application_credentials.py` — Provides OAuth2 authorize/token URLs
- `const.py` — All constants (URLs, states, actions, domain)

### API Data Structure
Devices are returned as a flat JSON array from `GET /device`. Each device has:
- `id` — unique device identifier
- `subtype` — one of: `shutter`, `blind`, `awning`, `curtain`, `garage_door`
- `name` — display name
- `states.general` — current state: `"up"` (open), `"down"` (closed), `"opening"`, `"closing"`
- `position` — integer 0–100 (optional)
- `capabilities` — list of supported actions (e.g., `["set_position"]`)
- `model`, `firmware_version` — device info

### State Field Convention
All state reads use `device_data.get("states", {}).get("general")` — the nested `states.general` field. The flat `state` field is NOT used. Values: `"up"`, `"down"`, `"opening"`, `"closing"`.

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
2. If CI fails, analyze failures and fix before merging
3. All tests must pass and coverage must stay above 85%

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
