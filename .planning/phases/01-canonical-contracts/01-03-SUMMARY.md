---
phase: 01-canonical-contracts
plan: 03
subsystem: cli
tags: [typer, yaml, validation, contracts]
requires:
  - phase: 01-02
    provides: "TaskDefinition, TaskSpecification, and TaskRegistry contracts"
provides:
  - "CLI `contracts validate` for task-definition and task-spec files"
  - "CLI `contracts inspect` for registry-backed task listing"
  - "Fixture-driven CLI integration tests"
affects: [researcher-workflow, task-authoring, contract-validation]
tech-stack:
  added: []
  patterns: [file-based contract validation via Pydantic, deterministic CLI success/failure output]
key-files:
  created:
    - src/smdgf/cli/contracts.py
    - tests/fixtures/task_definition_valid.yaml
    - tests/fixtures/task_definition_invalid.yaml
    - tests/fixtures/task_spec_valid.yaml
    - tests/unit/test_cli_contracts.py
  modified:
    - src/smdgf/cli/main.py
key-decisions:
  - "The CLI only parses YAML/JSON mappings and never executes user-provided files."
  - "Validation success is reported with a deterministic `VALID` string and non-zero exit on failures."
patterns-established:
  - "CLI commands are grouped under `contracts` and tested with Typer's `CliRunner`."
  - "Fixture-backed validation tests cover both valid and invalid task artifacts."
requirements-completed: [TASK-01, TASK-04]
duration: 12min
completed: 2026-04-15
---

# Phase 1 Plan 03: Contract CLI Summary

**Typer-based contract inspection and validation CLI with fixture-driven YAML checks and deterministic failure semantics**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-15T11:05:00Z
- **Completed:** 2026-04-15T11:17:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added `contracts inspect` and `contracts validate` subcommands to the CLI.
- Implemented safe YAML/JSON parsing and Pydantic-based validation for task definitions and task specs.
- Added CLI fixtures and tests that prove valid payloads pass and invalid payloads fail with non-zero exit codes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build Typer CLI entrypoint and contract subcommands** - `9eb72f3` (feat)
2. **Task 2: Add CLI fixtures and executable validation tests** - `9eb72f3` (feat)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/cli/main.py` - CLI root app plus contracts subcommand registration
- `src/smdgf/cli/contracts.py` - inspect and validate commands
- `tests/fixtures/task_definition_valid.yaml` - valid task-definition payload
- `tests/fixtures/task_definition_invalid.yaml` - invalid task-definition payload
- `tests/fixtures/task_spec_valid.yaml` - valid task-spec payload
- `tests/unit/test_cli_contracts.py` - fixture-driven CLI tests

## Decisions Made
- Restricted CLI validation to YAML/JSON mapping payloads to avoid arbitrary file execution.
- Kept `contracts inspect` deterministic even though the registry is currently empty.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Researchers can now validate authored task-definition and task-spec files before later scenario and generation phases.
- The CLI surface is ready for later commands that load registry-backed task packs.

---
*Phase: 01-canonical-contracts*
*Completed: 2026-04-15*
