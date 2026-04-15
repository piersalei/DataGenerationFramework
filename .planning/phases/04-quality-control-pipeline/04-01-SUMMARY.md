---
phase: 04-quality-control-pipeline
plan: 01
subsystem: qc-core
tags: [quality-control, rule-engine, validation, canonical-samples]
requires:
  - phase: 03-04
    provides: "Provenance-rich generation artifacts and canonical samples ready for QC"
provides:
  - "Framework-owned QC candidate, finding, decision, and review contracts"
  - "Deterministic structural validation and rule-engine evaluation"
  - "Unit coverage for malformed samples, answer leakage, and latent inconsistency"
affects: [judges, dedup, reports, exporters]
tech-stack:
  added: []
  patterns: [canonical-first qc boundary, structured findings, deterministic hard filters]
key-files:
  created:
    - src/smdgf/qc/__init__.py
    - src/smdgf/qc/models.py
    - src/smdgf/qc/rules.py
    - tests/unit/test_qc_rules.py
  modified: []
key-decisions:
  - "Made QC operate on a framework-owned `QualityCandidate` wrapper around canonical samples instead of on raw provider payloads."
  - "Separated structural validation from rule execution but normalized both into shared `QualityFinding` and `QualityDecision` contracts."
patterns-established:
  - "Deterministic QC findings carry auditable source ids, severity, decision hints, and structured evidence."
  - "Rule-engine evaluation derives one normalized accept/reject/review decision from structural validation plus deterministic rules."
requirements-completed: [QUAL-01, QUAL-02]
duration: 10 min
completed: 2026-04-15
---

# Phase 4 Plan 01: QC Core Summary

**QC contracts, structural validation, and deterministic rule engine for canonical candidates**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-15T15:20:00Z
- **Completed:** 2026-04-15T15:30:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added the first `smdgf.qc` package with framework-owned contracts for candidates, findings, decisions, review dispositions, and duplicate clusters.
- Implemented deterministic structural validation for canonical questions and answers before any soft QC or export path.
- Added a rule engine with built-in leakage and latent-consistency checks plus unit tests covering rejection scenarios.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add QC contracts and package exports** - `pending` (feat)
2. **Task 2: Implement deterministic validation and rule engine with unit tests** - `pending` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified

- `src/smdgf/qc/__init__.py` - Public QC exports
- `src/smdgf/qc/models.py` - QC-facing candidate, finding, decision, review, and duplicate-cluster contracts
- `src/smdgf/qc/rules.py` - Structural validation helpers and deterministic rule engine
- `tests/unit/test_qc_rules.py` - Unit tests for malformed samples, answer leakage, and latent inconsistency

## Decisions Made

- Kept hard QC independent from any model call so structural and leakage failures stay reproducible.
- Normalized structural validation failures into the same finding format as rule failures so later report aggregation stays simple.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Local Python 3.9 rejected `X | None` in a new QC test helper, so the helper was normalized to `typing.Optional` to match the current runtime.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Judge-based QC can now build on stable `QualityDecision` and `QualityFinding` contracts.
- Deduplication and reporting plans can reuse the same QC candidate wrapper without introducing format-specific logic.

---
*Phase: 04-quality-control-pipeline*
*Completed: 2026-04-15*
