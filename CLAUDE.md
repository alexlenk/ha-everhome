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
# Type checking (mypy.ini is the authoritative config — do NOT edit [tool.mypy] in pyproject.toml)
mypy custom_components/everhome/

# Code formatting
black custom_components/ tests/

# Import sorting
isort custom_components/ tests/

# Linting
flake8 custom_components/ tests/

# Run all quality checks (same as CI)
black --check --diff custom_components/ tests/
isort --check --diff custom_components/ tests/
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
| `release-please.yml` | push to `main`, manual | Automated release PR creation via release-please |
| `release.yml` | GitHub release published | Final validation on release |
| `hacs-validation.yml` | push/PR to `main`, daily, manual | HACS validation |
| `hassfest.yml` | push/PR to `main`, daily, manual | Hassfest validation |

### CI Monitoring (MANDATORY)
After pushing changes on a `claude/**` branch:
1. Wait for CI to complete on the branch
2. If CI fails, analyze failures and fix before merging
3. All tests must pass and coverage must stay above 85%

## Release Process

This project uses [release-please](https://github.com/googleapis/release-please) for automated releases. Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/).

### Commit Message Format
```
<type>: <description>

Types that appear in CHANGELOG:
  feat / feature  → Features
  fix             → Bug Fixes
  perf            → Performance Improvements
  refactor        → Code Refactoring
  deps            → Dependencies
  docs            → Documentation

Types hidden in CHANGELOG (still trigger releases):
  test, build, ci, style, chore, revert
```

### Automated Release Flow
1. **Work on `claude/**` branch** — commit with conventional commits
2. **CI runs automatically** on `claude/**` branches — fix any failures
3. **Merge to `main`** (via PR)
4. **release-please triggers** on push to `main`:
   - Creates a Release PR that bumps version in `CHANGELOG.md` and `.release-please-manifest.json`
   - When Release PR is merged: creates GitHub Release + git tag (`v0.5.1`)
   - `release-please.yml` also updates `manifest.json` version on release
5. **HACS detects** new release via the git tag

### Version Files (keep in sync)
| File | Field |
|---|---|
| `custom_components/everhome/manifest.json` | `"version"` |
| `pyproject.toml` | `version` under `[project]` |
| `.release-please-manifest.json` | `"."` |

release-please manages `manifest.json` and `.release-please-manifest.json` automatically on release. Keep `pyproject.toml` in sync manually when bumping versions.

### Manual Release (fallback)
```bash
# 1. Update versions in all three files above
# 2. Update CHANGELOG.md
# 3. Commit and push
git add custom_components/everhome/manifest.json pyproject.toml .release-please-manifest.json CHANGELOG.md
git commit -m "chore: release v0.5.2"
git push origin claude/release-v0.5.2

# 4. Merge to main, then tag
git tag -a v0.5.2 -m "Release v0.5.2"
git push origin v0.5.2

# 5. Create GitHub Release
gh release create v0.5.2 --title "v0.5.2 - <title>" --notes-file CHANGELOG.md --latest
```

### Release Checklist
- [ ] All CI tests passing (≥85% coverage)
- [ ] Version bumped in `manifest.json`, `pyproject.toml`, `.release-please-manifest.json`
- [ ] `CHANGELOG.md` updated
- [ ] GitHub Release created with tag `vX.Y.Z`
- [ ] HACS validation passing

## HACS Requirements
- Git tags must follow `vX.Y.Z` format
- GitHub Release must exist (not just a tag)
- `hacs.json` must be valid
- `manifest.json` version must match tag

## mypy Configuration
`mypy.ini` is the authoritative mypy config — it takes precedence over `[tool.mypy]` in `pyproject.toml` (which has been removed). `mypy.ini` includes critical per-module ignores for `homeassistant.*` and `pytest_homeassistant_custom_component.*` to avoid false errors from unresolvable HA source types.
