---
phase: 01-canonical-contracts
plan: 02
subsystem: api
tags: [pydantic, schema, registry, canonical-sample]
requires:
  - phase: 01-01
    provides: "Python package scaffold, importable src layout, and test harness"
provides:
  - "Ability taxonomy and task-definition contracts"
  - "Structured task specification contracts"
  - "Canonical sample representation and in-memory task registry"
affects: [sampling, generation, quality-control, exporters]
tech-stack:
  added: []
  patterns: [strict pydantic contracts, export-agnostic canonical sample, duplicate-id registry guard]
key-files:
  created:
    - src/smdgf/schemas/abilities.py
    - src/smdgf/schemas/task.py
    - src/smdgf/schemas/spec.py
    - src/smdgf/schemas/canonical.py
    - src/smdgf/registry.py
    - tests/unit/test_contract_models.py
  modified:
    - src/smdgf/schemas/__init__.py
key-decisions:
  - "Kept export-specific distractor fields out of `CanonicalSample` so later QA/MCQ/open-QA rendering stays downstream."
  - "Used strict in-memory registry semantics with duplicate `task_id` rejection."
patterns-established:
  - "Contract modules forbid extra fields through Pydantic `extra=\"forbid\"`."
  - "Canonical sample provenance is recorded as part of the core schema."
requirements-completed: [TASK-01, TASK-02, TASK-03, TASK-04]
duration: 18min
completed: 2026-04-15
---

# Phase 1 Plan 02: Contract Models Summary

**Strict Pydantic contract models for abilities, task specs, canonical samples, and duplicate-safe task registry**

## Performance

- **Duration:** 18 min
- **Started:** 2026-04-15T10:47:00Z
- **Completed:** 2026-04-15T11:05:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Implemented ability taxonomy, task-definition, and structured task-spec models.
- Added canonical sample, question, answer, and provenance contracts that remain export-agnostic.
- Implemented a duplicate-safe in-memory `TaskRegistry` and unit tests covering validation and registry behavior.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ability, task, and specification models** - `676cd6f` (feat)
2. **Task 2: Implement canonical sample model and in-memory task registry** - `676cd6f` (feat)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/schemas/abilities.py` - ability categories and descriptor model
- `src/smdgf/schemas/task.py` - task definition, export format, and latent-variable models
- `src/smdgf/schemas/spec.py` - structured scene/question/QC specification models
- `src/smdgf/schemas/canonical.py` - canonical sample, question, answer, and provenance contracts
- `src/smdgf/registry.py` - duplicate-safe in-memory task registry
- `src/smdgf/schemas/__init__.py` - public contract exports
- `tests/unit/test_contract_models.py` - validation, canonical, and registry tests

## Decisions Made
- Used explicit top-level ability categories with room for free-form sub-capabilities.
- Made canonical samples export-agnostic by design so exporters can remain downstream transforms.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Replaced Python 3.11-only `datetime.UTC` usage**
- **Found during:** Task 2 (Implement canonical sample model and in-memory task registry)
- **Issue:** The local execution environment is Python 3.9.6, and `datetime.UTC` is unavailable there.
- **Fix:** Switched to `datetime.now(timezone.utc)` in the provenance model.
- **Files modified:** `src/smdgf/schemas/canonical.py`
- **Verification:** `python3 -m pytest tests/unit/test_contract_models.py -q`
- **Committed in:** `676cd6f` (Task commit)

**2. [Rule 3 - Blocking] Replaced Python 3.10+ union syntax in runtime-loaded contracts**
- **Found during:** Task 2 (Implement canonical sample model and in-memory task registry)
- **Issue:** Python 3.9 cannot evaluate several `X | Y` annotations used in the canonical/spec/registry modules.
- **Fix:** Added `from __future__ import annotations` and replaced runtime-sensitive unions with `typing.Optional` / `typing.Union`.
- **Files modified:** `src/smdgf/schemas/canonical.py`, `src/smdgf/schemas/spec.py`, `src/smdgf/registry.py`
- **Verification:** `python3 -m pytest tests/unit/test_contract_models.py -q`
- **Committed in:** `676cd6f` (Task commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** No requirement drift. Fixes were compatibility repairs needed to run the approved plan in the current environment.

## Issues Encountered
- Local interpreter is Python 3.9.6 even though project metadata targets Python 3.11. The implementation was adjusted to remain testable on the current machine.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 can now build CLI validation directly on the contract layer.
- Later sampling and generation phases can import the contract modules as their source of truth.

---
*Phase: 01-canonical-contracts*
*Completed: 2026-04-15*
