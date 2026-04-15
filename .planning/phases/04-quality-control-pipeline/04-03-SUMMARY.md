---
phase: 04-quality-control-pipeline
plan: 03
subsystem: qc-dedup
tags: [quality-control, deduplication, similarity, canonical-fingerprint]
requires:
  - phase: 04-01
    provides: "Stable QC candidate wrapper around canonical samples"
provides:
  - "Stable exact-duplicate fingerprinting over canonical semantics"
  - "Deterministic near-duplicate grouping from token overlap"
  - "Unit coverage for exact and near-duplicate clustering"
affects: [reports, exporters, benchmark-diversity]
tech-stack:
  added: []
  patterns: [canonical fingerprinting, lightweight lexical similarity, structured duplicate clusters]
key-files:
  created:
    - src/smdgf/qc/dedup.py
    - tests/unit/test_qc_dedup.py
  modified: []
key-decisions:
  - "Used SHA-256 fingerprints over canonical task, question, answer, and latent-state signatures for exact duplicate detection."
  - "Kept near-duplicate detection lightweight and deterministic with token-overlap similarity rather than embedding infrastructure."
patterns-established:
  - "Duplicate outputs are represented as `DuplicateCluster` records with cluster ids, member ids, reason, and score."
  - "Dedup operates on canonical sample semantics instead of exporter-specific rows."
requirements-completed: [QUAL-04]
duration: 7 min
completed: 2026-04-15
---

# Phase 4 Plan 03: Dedup Summary

**Exact and near-duplicate detection over accepted canonical candidates**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-15T15:40:00Z
- **Completed:** 2026-04-15T15:47:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added stable exact-duplicate fingerprinting from canonical task, question, answer, and latent-state signatures.
- Implemented deterministic near-duplicate grouping with configurable token-overlap thresholds.
- Added tests covering exact duplicate detection, near-duplicate grouping, and cluster metadata integrity.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add exact and near-duplicate detection helpers** - `pending` (feat)
2. **Task 2: Add unit tests for duplicate clustering** - `pending` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified

- `src/smdgf/qc/dedup.py` - Exact fingerprinting and near-duplicate clustering helpers
- `tests/unit/test_qc_dedup.py` - Duplicate and near-duplicate tests

## Decisions Made

- Exact duplicate detection uses canonical semantics rather than prompt text alone, reducing false misses when prompt wording drifts.
- Near-duplicate detection remains deterministic and cheap so it can run as part of routine QC without extra services.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external dependencies or services required.

## Next Phase Readiness

- QC reports can now aggregate duplicate clusters as explicit audit artifacts.
- Exporters can consume dedup-filtered approved samples without inventing their own clustering logic.

---
*Phase: 04-quality-control-pipeline*
*Completed: 2026-04-15*
