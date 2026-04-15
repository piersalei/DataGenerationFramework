---
phase: 03-generation-runtime
plan: 02
subsystem: prompts
tags: [prompting, determinism, fingerprinting, scenario-context]
requires:
  - phase: 03-01
    provides: "Generation request/result contracts that prompt assembly feeds"
provides:
  - "Deterministic prompt text from task and scenario contracts"
  - "Prompt fingerprint and replay metadata"
  - "Prompt-focused unit coverage for determinism and structural context"
affects: [runtime, manifests, qc]
tech-stack:
  added: []
  patterns: [stable prompt assembly, fingerprint from normalized prompt inputs]
key-files:
  created:
    - src/smdgf/generation/prompts.py
    - tests/unit/test_prompt_assembly.py
  modified: []
key-decisions:
  - "Returned prompt text plus metadata tuple instead of introducing a separate prompt model at this stage."
  - "Derived prompt fingerprints from normalized task/scenario/seed inputs so prompt drift is explicit and replayable."
patterns-established:
  - "Prompt assembly iterates roles, relations, latent states, and question patterns in deterministic sorted order."
  - "Prompt metadata captures task id, scenario sample id, seed, question ids, and fingerprint explicitly."
requirements-completed: [GEN-02, GEN-04]
duration: 8 min
completed: 2026-04-15
---

# Phase 3 Plan 02: Prompt Assembly Summary

**Deterministic prompt assembly from task and scenario contracts with stable replay fingerprints**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-15T13:52:00Z
- **Completed:** 2026-04-15T14:00:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added deterministic prompt assembly over task definitions, task specs, and sampled scenario state.
- Emitted prompt metadata containing task, scenario, seed, question ids, and prompt fingerprint.
- Added prompt tests covering determinism, metadata completeness, and roles/relations/latent-state inclusion.

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement deterministic prompt assembly helpers** - `b935841` (feat)
2. **Task 2: Add prompt determinism and metadata tests** - `ffda4a3` (test)

**Plan metadata:** pending in phase metadata commit

## Files Created/Modified
- `src/smdgf/generation/prompts.py` - Stable prompt assembly and fingerprint metadata
- `tests/unit/test_prompt_assembly.py` - Prompt determinism and structural-context tests

## Decisions Made
- Prompt output stays provider-agnostic and contains only task/scenario semantics plus replay metadata.
- Fingerprinting uses normalized JSON over key prompt inputs instead of relying on the rendered prompt alone.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Prompt tests initially used an invalid `TaskDefinition` fixture with no supported exports; the fixture was corrected to satisfy the existing schema contract.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Runtime execution can now build provider-ready prompts reproducibly before checkpointed batch execution.
- No blockers from this plan.

---
*Phase: 03-generation-runtime*
*Completed: 2026-04-15*
