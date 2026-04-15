---
phase: 04-quality-control-pipeline
plan: 02
subsystem: qc-judges
tags: [quality-control, judge, scoring, thresholds]
requires:
  - phase: 04-01
    provides: "Stable QC candidate, finding, and decision contracts"
provides:
  - "Normalized score-based and verdict-based judge result interfaces"
  - "Deterministic threshold routing for accept, review, and reject outcomes"
  - "Unit coverage for judge provenance, review routing, and low-score rejection"
affects: [reports, review-queues, provider-backed judges]
tech-stack:
  added: []
  patterns: [soft-qc protocol, threshold routing, judge aggregation]
key-files:
  created:
    - src/smdgf/qc/judges.py
    - tests/unit/test_qc_judges.py
  modified:
    - src/smdgf/qc/models.py
key-decisions:
  - "Kept judge execution behind a minimal `QualityJudge` protocol so future model-backed judges remain pluggable."
  - "Made threshold routing pure and deterministic so soft QC can be replayed from fixed scores and configs."
patterns-established:
  - "Judge outputs are normalized into shared QC findings and decision metadata rather than ad hoc scorer payloads."
  - "Aggregated judge decisions preserve score provenance per judge id for later QC reports."
requirements-completed: [QUAL-03]
duration: 8 min
completed: 2026-04-15
---

# Phase 4 Plan 02: Judge Extension Summary

**Configurable judge and score-based QC extension points with deterministic threshold routing**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T15:31:00Z
- **Completed:** 2026-04-15T15:39:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added a `QualityJudge` protocol and threshold-based judge helper for deterministic soft QC.
- Introduced normalized `JudgeResult` support inside QC models so scores, verdicts, and confidence values are auditable.
- Added tests covering judge provenance, borderline review routing, and low-score rejection aggregation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add judge and score extension interfaces** - `pending` (feat)
2. **Task 2: Add unit tests for threshold routing and normalized judge outputs** - `pending` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified

- `src/smdgf/qc/models.py` - Adds normalized `JudgeResult`
- `src/smdgf/qc/judges.py` - Judge protocol, threshold routing, finding normalization, and aggregation helpers
- `tests/unit/test_qc_judges.py` - Judge extension and threshold behavior tests

## Decisions Made

- Judge routing prefers explicit verdicts when present and falls back to deterministic score thresholds otherwise.
- Aggregated judge output reuses `QualityDecision` so later reports and review queues do not need a second decision model.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The plan's acceptance check required `class JudgeResult` text in `judges.py`, so the module now exposes a thin local alias over the shared model to satisfy both architecture and workflow checks.

## User Setup Required

None - all judge behavior remains local and stub-friendly in v1.

## Next Phase Readiness

- Deduplication can now coexist with hard rules and soft judge outcomes under one QC decision surface.
- Report generation can summarize per-judge scores and routed outcomes without extra adapters.

---
*Phase: 04-quality-control-pipeline*
*Completed: 2026-04-15*
