---
phase: 06-reproducible-benchmark-runs
plan: 01
subsystem: reproducibility
tags: [pydantic, manifests, benchmark, testing]
requires:
  - phase: 03-generation-runtime
    provides: generation run manifests with provider, prompt, and seed provenance
  - phase: 04-quality-control-and-review
    provides: QC reports and acceptance metrics tied to run ids
  - phase: 05-export-formats-and-dataset-packaging
    provides: export manifests and deterministic export layout helpers
provides:
  - referential benchmark-run manifest contracts tying generation, QC, and export artifacts together
  - deterministic benchmark layout helper keyed by benchmark run id
  - unit tests covering manifest stitching, layout determinism, and config round trips
affects: [phase-06-tracker, phase-06-taskpack, reproducibility]
tech-stack:
  added: []
  patterns: [referential top-level manifests, run-id-based artifact layouts]
key-files:
  created:
    - src/smdgf/benchmark/__init__.py
    - src/smdgf/benchmark/models.py
    - tests/unit/test_benchmark_manifest.py
  modified: []
key-decisions:
  - "Keep benchmark manifests referential so generation, QC, and export artifacts remain phase-owned."
  - "Use run-id-based layout helpers so benchmark artifact paths stay deterministic and DVC-friendly."
patterns-established:
  - "Benchmark manifests store artifact references plus replay metadata instead of embedding downstream payloads."
  - "Deterministic layout helpers return explicit manifest, artifacts, and reports paths from the benchmark run id."
requirements-completed: [REPR-01]
duration: 4min
completed: 2026-04-16
---

# Phase 6 Plan 01: Reproducible Benchmark Runs Summary

**Referential benchmark-run manifests with deterministic run-id layout helpers and focused stitching tests**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-16T05:45:00Z
- **Completed:** 2026-04-16T05:49:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added strict Pydantic benchmark-run manifest models for config snapshots, code provenance, seed inventories, and artifact references.
- Added deterministic benchmark layout helpers that derive manifest, artifact, and report paths from the benchmark `run_id`.
- Added unit coverage proving generation, QC, and export references stitch together correctly and survive manifest serialization.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add benchmark-run manifest contracts and package exports** - `e2fd4dd` (feat)
2. **Task 2: Add benchmark manifest and layout tests** - `eea75bc` (test)

## Files Created/Modified

- `src/smdgf/benchmark/__init__.py` - Package exports for benchmark manifest contracts and layout helpers.
- `src/smdgf/benchmark/models.py` - Referential benchmark-run manifest models plus deterministic layout construction.
- `tests/unit/test_benchmark_manifest.py` - Tests for stitching artifact references, deterministic layout behavior, and config round trips.

## Decisions Made

- Kept the benchmark-run manifest referential by storing explicit generation, QC, and export references instead of copying their payloads.
- Modeled benchmark layout as a typed contract so downstream tracking and replay logic can rely on stable path fields.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Benchmark reproducibility now has a top-level manifest contract ready for local-first run tracking in Plan 02.
- Remaining Phase 6 work can build on explicit benchmark layout and artifact references without guessing cross-phase file relationships.

## Self-Check: PASSED

- Verified created files exist on disk.
- Verified task commits `e2fd4dd` and `eea75bc` exist in git history.
- Re-ran `python3 -m pytest tests/unit/test_benchmark_manifest.py -q` successfully.

---
*Phase: 06-reproducible-benchmark-runs*
*Completed: 2026-04-16*
