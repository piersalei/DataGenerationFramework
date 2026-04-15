---
phase: 02-scenario-and-sampling-engine
plan: 02
subsystem: sampling
tags: [determinism, seeded-sampling, rng, scenario-instantiation]
requires:
  - phase: 02-01
    provides: "SceneTemplate and ScenarioSample contracts for sampler input/output"
provides:
  - "Seeded sampling context with stable child RNG derivation"
  - "Deterministic scenario instantiation over slots, roles, relations, and latent states"
  - "Unit coverage for reproducibility and latent-state assignments"
affects: [preview-cli, generation-runtime, qc]
tech-stack:
  added: []
  patterns: [centralized seeded context, stable label-derived child RNG]
key-files:
  created:
    - src/smdgf/samplers/__init__.py
    - src/smdgf/samplers/context.py
    - src/smdgf/samplers/scenario.py
    - tests/unit/test_sampling_engine.py
  modified: []
key-decisions:
  - "Centralized all stochastic behavior in SamplingContext so reproducibility does not depend on ad hoc random calls."
  - "Derived child seeds from sha256(seed:label) instead of Python hash values to avoid interpreter-level randomization drift."
patterns-established:
  - "Samplers iterate slot specs in sorted key order before making RNG decisions."
  - "Scenario samples expose latent_state_assignments and relation edges as first-class structured outputs."
requirements-completed: [SCEN-03, SCEN-04]
duration: 9 min
completed: 2026-04-15
---

# Phase 2 Plan 02: Deterministic Sampling Summary

**Seeded scenario sampling with stable child RNG derivation and explicit latent-state assignments**

## Performance

- **Duration:** 9 min
- **Started:** 2026-04-15T13:01:00Z
- **Completed:** 2026-04-15T13:10:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added a reusable `SamplingContext` with deterministic `choose`, `shuffle_copy`, and `child` helpers.
- Implemented `sample_scenario` to instantiate slots, roles, relations, and latent states into `ScenarioSample`.
- Added tests proving same-seed reproducibility, different-seed variation, and explicit latent-state preservation.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement seeded sampling context and deterministic helper surface** - `20b749f` (feat)
2. **Task 2: Implement scenario sampler and deterministic sampling tests** - `6f9e705` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/samplers/context.py` - Seeded sampling context with stable child seed derivation
- `src/smdgf/samplers/scenario.py` - Deterministic template instantiation into `ScenarioSample`
- `src/smdgf/samplers/__init__.py` - Sampler exports
- `tests/unit/test_sampling_engine.py` - Reproducibility and latent-state assignment tests

## Decisions Made
- Used a label-derived child context per slot/state to keep sampling deterministic while isolating RNG decisions by concern.
- Kept sampled roles and relations as direct structural mirrors of the template so later exporters can consume explicit world state.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Wave 3 can now expose scenario previews through the CLI without touching provider execution code.
- No blockers from this plan.

---
*Phase: 02-scenario-and-sampling-engine*
*Completed: 2026-04-15*
