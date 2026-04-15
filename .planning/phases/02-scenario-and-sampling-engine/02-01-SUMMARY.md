---
phase: 02-scenario-and-sampling-engine
plan: 01
subsystem: schemas
tags: [pydantic, scene-modeling, latent-state, role-graph]
requires:
  - phase: 01-02
    provides: "Strict task and canonical sample contracts that Phase 2 extends"
provides:
  - "Scene template contracts with typed slots and declarative constraints"
  - "Explicit role and relation graph structures"
  - "Structured latent-state specifications and sampled scenario container types"
affects: [sampling, preview-cli, generation-runtime]
tech-stack:
  added: []
  patterns: [strict pydantic scene contracts, template-vs-sampled separation]
key-files:
  created:
    - src/smdgf/schemas/scene.py
    - tests/unit/test_scene_models.py
  modified:
    - src/smdgf/schemas/__init__.py
key-decisions:
  - "Separated reusable SceneTemplate declarations from ScenarioSample instances so later sampling remains inspectable and deterministic."
  - "Modeled relations as explicit source-role to target-role edges instead of burying social structure inside per-role metadata."
patterns-established:
  - "Phase 2 scenario layers use strict Pydantic models with extra=forbid to fail fast on malformed templates."
  - "Latent mental-state requirements are represented as structured specs with owner_role and sampling_strategy fields."
requirements-completed: [SCEN-01, SCEN-02, SCEN-03]
duration: 10 min
completed: 2026-04-15
---

# Phase 2 Plan 01: Scene Schema Contracts Summary

**Scene template contracts with typed slots, explicit role relations, and structured latent-state specifications**

## Performance

- **Duration:** 10 min
- **Started:** 2026-04-15T12:50:00Z
- **Completed:** 2026-04-15T13:00:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added a dedicated `scene.py` contract layer for template declarations and sampled scenario containers.
- Introduced explicit role relation edges and latent-state specs with auditable ownership and sampling fields.
- Added focused unit coverage proving typed slots, relation wiring, and latent-state structure.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement scene, role, relation, and latent-state contracts** - `45a57bb` (feat)
2. **Task 2: Add contract tests for typed slots, relations, and latent-state structure** - `df4b85b` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/schemas/scene.py` - Scene template, role, relation, latent-state, and sampled scenario models
- `src/smdgf/schemas/__init__.py` - Public exports for the new scene contract symbols
- `tests/unit/test_scene_models.py` - Contract tests for slot typing, relation edges, and latent-state structure

## Decisions Made
- Kept template declarations and sampled scenario containers as separate models to prevent config from becoming generated state.
- Required `allowed_values` on latent-state specs so later samplers can remain deterministic and auditable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 2 can now build deterministic samplers directly against explicit `SceneTemplate` and `ScenarioSample` contracts.
- No blockers from this plan.

---
*Phase: 02-scenario-and-sampling-engine*
*Completed: 2026-04-15*
