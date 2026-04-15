---
phase: 01-canonical-contracts
plan: 01
subsystem: infra
tags: [python, pytest, typer, pydantic, hydra]
requires: []
provides:
  - "Python package scaffold under src/smdgf"
  - "Project metadata and dependency pins in pyproject.toml"
  - "Baseline scaffold tests for package and CLI imports"
affects: [contracts, schemas, cli, testing]
tech-stack:
  added: [pytest, typer, pydantic, hydra-core, pyyaml]
  patterns: [src-layout Python package, pytest smoke tests for scaffold]
key-files:
  created:
    - pyproject.toml
    - src/smdgf/__init__.py
    - src/smdgf/cli/__init__.py
    - src/smdgf/cli/main.py
    - src/smdgf/config/__init__.py
    - src/smdgf/schemas/__init__.py
    - tests/conftest.py
    - tests/unit/test_contract_scaffold.py
  modified: []
key-decisions:
  - "Created a minimal `src/smdgf/cli/main.py` in Wave 1 so scaffold tests can import the CLI entrypoint immediately."
patterns-established:
  - "All framework code lives under `src/smdgf` with src-layout packaging."
  - "Every phase starts with executable scaffold tests before deeper implementation."
requirements-completed: [TASK-01, TASK-04]
duration: 9min
completed: 2026-04-15
---

# Phase 1 Plan 01: Package Scaffold Summary

**Python src-layout package scaffold with pinned contract-layer dependencies and smoke-tested CLI import root**

## Performance

- **Duration:** 9 min
- **Started:** 2026-04-15T10:38:11Z
- **Completed:** 2026-04-15T10:47:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `pyproject.toml` with Python package metadata, dependency pins, pytest config, and CLI entrypoint wiring.
- Created `src/smdgf` package structure for CLI, config, and schema layers.
- Added baseline scaffold tests that verify package and CLI modules import cleanly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Python project metadata and dependency pins** - `fe26d34` (chore)
2. **Task 2: Create package markers and baseline scaffold tests** - `fe26d34` (chore)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `pyproject.toml` - package metadata, dependency pins, setuptools config, and pytest config
- `src/smdgf/__init__.py` - top-level package marker and version export
- `src/smdgf/cli/__init__.py` - CLI package marker
- `src/smdgf/cli/main.py` - minimal Typer app entrypoint
- `src/smdgf/config/__init__.py` - config package marker
- `src/smdgf/schemas/__init__.py` - schemas package marker
- `tests/conftest.py` - adds `src` to import path during pytest runs
- `tests/unit/test_contract_scaffold.py` - smoke tests for package and CLI imports

## Decisions Made
- Added `src/smdgf/cli/main.py` during Wave 1 because the approved plan required `test_cli_entrypoint_module_exists` to import it successfully.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added CLI entrypoint module earlier than plan file listed**
- **Found during:** Task 2 (Create package markers and baseline scaffold tests)
- **Issue:** The plan's scaffold test required importing `smdgf.cli.main`, but the plan's modified-file list did not include `src/smdgf/cli/main.py`.
- **Fix:** Created a minimal `src/smdgf/cli/main.py` with a Typer app so the scaffold import test could pass immediately.
- **Files modified:** `src/smdgf/cli/main.py`
- **Verification:** `python3 -m pytest tests/unit/test_contract_scaffold.py -q`
- **Committed in:** `fe26d34` (Task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope creep. The fix was necessary to satisfy the plan's own verification path.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Schema and registry implementation can now build on a stable package and test scaffold.
- CLI foundation exists and can be expanded in Plan 03.

---
*Phase: 01-canonical-contracts*
*Completed: 2026-04-15*
