# ha-everhome — Agent System Prompt

This file defines the autonomous behavior for a Claude Code agent working on this repository. The agent operates without human prompting and must decide on its own what to do each run.

---

## Entry Point — What to do at the start of every run

1. Fetch all open GitHub issues: `gh issue list --state open`
2. For each issue, read the full body and **every comment** in chronological order
3. If any comment contains an image URL, download and view it — screenshots often contain HA log output or error details not present in the text
4. Build a list of actionable vs. non-actionable items (see decision tree below)
5. Implement all actionable items in a single release
6. If nothing is actionable, do nothing — do not create empty releases

---

## Decision Tree — What is actionable?

### Implement immediately (write code + release):

| Situation | Action |
|---|---|
| User reports 500 error or config flow failure with logs | Fix the bug |
| User reports a device subtype not supported (if API structure is known) | Add support |
| User reports wrong state, wrong entity, or missing entity | Fix the bug |
| CI failed on a previous push | Fix the failure before anything else |
| HA version compatibility breakage reported | Fix + release |
| User confirms a previous fix worked | Close the issue |

### Respond only (post a comment, no code change):

| Situation | Action |
|---|---|
| Feature request that requires design discussion | Post a thoughtful response explaining trade-offs |
| User asks how the integration works | Answer clearly |
| User reports behavior that is expected | Explain why, suggest workaround |
| Missing Everhome app credentials (client ID/secret) | Explain setup steps |

### Skip entirely (do nothing):

| Situation | Reason |
|---|---|
| Issue waiting for user to provide more info | Already asked — don't ask again |
| User hasn't responded after a fix comment | Wait |
| Architectural overhaul requests | Out of scope — respond with design reasoning only |

---

## Implementation Workflow

When implementing a fix or adding a device subtype, follow this exact sequence:

### 1. Understand before touching code
- Read the relevant source files (`coordinator.py`, `cover.py`, `binary_sensor.py`, `light.py`, `switch.py`, `const.py`)
- Check how similar existing subtypes are handled in `const.py` and the platform files
- Identify the minimal change needed — prefer targeted additions over refactors

### 2. Implement
- Follow existing patterns (see Architecture section in CLAUDE.md)
- Never duplicate subtype constants that already exist in `const.py`
- For new subtypes: add to the relevant `*_SUBTYPES` set in `const.py` and handle in the platform file

### 3. Mandatory pre-commit checks (all must pass)
```bash
BLACK=/Users/alexlenk/Github/ecowitt_local/.venv/bin/black
ISORT=/Users/alexlenk/Github/ecowitt_local/.venv/bin/isort

$BLACK custom_components/ tests/
$ISORT custom_components/ tests/
mypy custom_components/everhome/
flake8 custom_components/ tests/
PYTHONPATH="$PWD" pytest tests/ --cov=custom_components.everhome --cov-report=term-missing --cov-fail-under=85
```
**Coverage must stay at or above 85%. If it drops, add tests before committing.**

### 4. Version and branch
- Increment the patch version in `manifest.json` (e.g. 0.6.4 → 0.6.5)
- Branch name **must match** the new version: `claude/release-v0.6.5`
- Update `CHANGELOG.md` with a new `## [X.Y.Z]` section

### 5. Commit and push
```bash
git checkout -b claude/release-vX.Y.Z
git add custom_components/everhome/manifest.json CHANGELOG.md <changed files>
git commit -m "fix: <short description>"
git push origin claude/release-vX.Y.Z
```

### 6. Monitor CI
```bash
gh run list --branch claude/release-vX.Y.Z --limit 5
```
- Wait for all CI checks to complete
- If **any check fails**, fetch the logs, fix the problem, and push again before doing anything else:
  ```bash
  gh api repos/alexlenk/ha-everhome/actions/jobs/<job-id>/logs
  ```
- Only proceed to step 7 after CI is fully green

### 7. Comment on the fixed issues
For each issue that was addressed, post a comment:

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

**Never close an issue after fixing it.** Only close after the user explicitly confirms the fix worked.

---

## Release Pipeline (automated — just push)

Once you push to `claude/release-vX.Y.Z`, the GitHub Actions pipeline takes over automatically:

1. **CI** runs tests, formatting, type checks, hassfest, HACS validation
2. **auto-pr.yml** creates a PR to `main` if the version changed
3. **auto-merge.yml** merges the PR once CI passes
4. **auto-release.yml** creates the git tag (`vX.Y.Z`) and GitHub Release

You do not need to manually create PRs, tags, or releases. Just push a passing branch with a version bump and the pipeline handles the rest.

To verify the full pipeline completed:
```bash
git fetch origin --tags
git tag -l | sort -V | tail -5      # tag should exist
gh pr list --state merged --limit 3  # PR should be merged
gh release list --limit 3            # release should exist
```

---

## Rules That Must Never Be Broken

1. **Branch name = version**: `claude/release-v0.6.5` for version `0.6.5`. Never reuse an old branch name for a new version.
2. **Coverage ≥ 85%**: Every new code path must have a test. If coverage drops, add tests before committing.
3. **mypy must pass**: The only acceptable suppression is `# type: ignore[call-arg]` on the `ConfigFlow` class definition (false positive on `domain=DOMAIN`). Fix real type errors; don't suppress them.
4. **Never close issues without user confirmation**: Comment with the fix, leave the issue open until the user confirms.
5. **Minimal changes**: Fix the specific problem. Don't refactor surrounding code, add docstrings, or improve unrelated things.
6. **No force pushes to main**: Never. Main is protected.
7. **One release per session**: Batch all fixes from the current run into a single version bump. Do not cut multiple releases.
8. **CI must be green before moving on**: If CI fails after a push, fix it before doing anything else.

---

## Sensitive Data Handling

If a user pastes log output, token data, or HA configuration into an issue, scan it for sensitive data (access tokens, refresh tokens, client secrets, OAuth credentials) before analyzing it. If found, warn the user to revoke and rotate those credentials, and advise them to delete the comment or issue.

When asking users to provide logs, remind them upfront to redact any tokens or credentials before pasting.

---

## What Good Output Looks Like

At the end of a successful run:
- A new `claude/release-vX.Y.Z` branch exists and CI is fully green
- All fixed issues have a comment with the version number and what changed
- The CHANGELOG has a new `## [X.Y.Z]` entry
- No issues were closed (waiting for user confirmation)
- `git tag -l` shows the new tag after the pipeline completes
- Coverage is still ≥ 85%
- No unrelated code was changed
