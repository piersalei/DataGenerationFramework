---
phase: 02-scenario-and-sampling-engine
plan: 03
subsystem: cli
tags: [typer, yaml, json, preview, reproducibility]
requires:
  - phase: 02-02
    provides: "Deterministic scenario sampling primitives and ScenarioSample output"
provides:
  - "CLI preview command for deterministic scenario sampling"
  - "Fixture-backed scene template loading path"
  - "Preview reproducibility and structural output tests"
affects: [researcher-workflow, generation-runtime, qc]
tech-stack:
  added: []
  patterns: [safe yaml-json template loading, deterministic json preview output]
key-files:
  created:
    - src/smdgf/cli/sampling.py
    - tests/fixtures/scene_template_valid.yaml
    - tests/unit/test_sampling_preview.py
  modified:
    - src/smdgf/cli/main.py
key-decisions:
  - "Preview output is emitted as sorted JSON from strict SceneTemplate parsing so sampled world state can be diffed across seeds."
  - "The preview path reuses the same safe mapping-only loading pattern as contract validation, with no template execution."
patterns-established:
  - "CLI subcommands remain grouped by workflow surface, with fixture-backed Typer CliRunner tests."
  - "Scenario preview exposes sampled slots, roles, relations, and latent_state_assignments explicitly."
requirements-completed: [SCEN-01, SCEN-04]
duration: 8 min
completed: 2026-04-15
---

# Phase 2 Plan 03: Sampling Preview Summary

**Deterministic CLI preview for sampled social scenarios with fixture-backed reproducibility tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T13:11:00Z
- **Completed:** 2026-04-15T13:19:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added a `sampling preview` CLI that loads scene templates from YAML or JSON and prints deterministic sampled output.
- Created a realistic multi-role fixture template with relation edges and latent-state specs.
- Added preview tests proving same-seed reproducibility, different-seed variation, and explicit roles/relations/state exposure.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add sampling preview CLI and fixture-backed loading path** - `f4a1f66` (feat)
2. **Task 2: Add preview reproducibility tests and explicit output checks** - `b448298` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/cli/sampling.py` - Deterministic preview command over scene template files
- `src/smdgf/cli/main.py` - CLI registration for the `sampling` sub-app
- `tests/fixtures/scene_template_valid.yaml` - Realistic scene template fixture for preview tests
- `tests/unit/test_sampling_preview.py` - Fixture-backed preview reproducibility tests

## Decisions Made
- Kept preview output focused on sampled structural state rather than rendered prompt text so later phases can reuse it directly.
- Used sorted JSON output to make seed-to-seed diffs straightforward for researchers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 now ends with an inspectable deterministic preview path for scene sampling.
- No blockers from this plan.

---
*Phase: 02-scenario-and-sampling-engine*
*Completed: 2026-04-15*
