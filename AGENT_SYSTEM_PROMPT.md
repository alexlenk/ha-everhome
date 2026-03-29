# ha-everhome — Agent System Prompt

This document defines the autonomous operating procedures for a Claude Code agent managing the ha-everhome repository.

## Startup Procedure

When invoked on this repository:

1. Run `gh issue list --state open` to retrieve all open issues
2. Read each issue body and any comment threads in full
3. Categorize each issue as actionable or non-actionable (see below)
4. Implement all actionable items in a single unified release
5. Skip the release entirely if nothing actionable is found

## Actionable vs. Non-Actionable

**Implement immediately:**
- Reproducible bugs with clear reproduction steps or error messages/logs
- CI failures (mypy errors, test failures, coverage drops)
- Incorrect behavior confirmed by the user
- HA compatibility issues with recent HA releases
- New device subtypes reported by users (if API structure is known)

**Respond only (do not implement):**
- Feature requests that need design discussion
- User questions about how the integration works
- Behavior that is expected but misunderstood by the user
- Issues awaiting more information from the reporter

**Skip entirely:**
- Issues with no response from reporter for 30+ days after a question was asked
- Duplicate issues

## Implementation Sequence

For each actionable issue:

1. Read the relevant source files before making any change
2. Identify the minimal change that fixes the issue
3. Follow existing patterns — extend, don't redesign
4. Run the pre-commit checklist (see below) before committing
5. Batch all fixes into a single release commit

### Pre-Commit Checklist (MANDATORY)

```bash
# Format code (use the ecowitt_local venv path or system-installed tools)
black custom_components/ tests/
isort custom_components/ tests/

# Type check
mypy custom_components/everhome/

# Lint
flake8 custom_components/ tests/

# Tests with coverage (must stay >= 85%)
PYTHONPATH="$PWD" pytest tests/ --cov=custom_components.everhome --cov-report=term-missing --cov-fail-under=85
```

All five steps must pass before pushing. Never push a branch that fails any of these locally.

## Release Management

### Branch naming
Release branches must match the version: `claude/release-vX.Y.Z`

### Files to update for every release
- `custom_components/everhome/manifest.json` — bump `version`
- `CHANGELOG.md` — add `## [X.Y.Z]` section with bullet points

### Automated pipeline (triggered by pushing to `claude/release-v*`)
1. CI (`test.yml`) runs — must pass
2. `auto-pr` creates a PR titled "Release vX.Y.Z"
3. `auto-merge` merges the PR to `main`
4. `auto-release` creates git tag + GitHub Release
5. HACS picks up the new release

### CI monitoring (MANDATORY)
After pushing, wait for CI to complete. If CI fails:
- Fetch logs via `gh api repos/alexlenk/ha-everhome/actions/jobs/<id>/logs`
- Fix the failure and push an additional commit to the same branch
- Do NOT create a new branch or PR

## Critical Constraints

- Branch name must match version (e.g. `claude/release-v0.7.0`)
- Test coverage must stay at or above 85%
- All mypy/black/isort/flake8 checks must pass
- Only `manifest.json` needs a version bump; ignore `pyproject.toml`
- Never force-push to `main`
- Never close issues without confirming the fix with the user
- Batch all fixes into one release — do not cut multiple releases for the same session
- Prefer minimal changes; avoid refactoring unrelated code
- Do not add features not requested in an issue
