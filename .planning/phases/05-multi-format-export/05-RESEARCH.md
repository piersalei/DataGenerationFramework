# Phase 5 Research: Multi-Format Export

## Objective

Research how to export approved canonical samples into QA, multiple-choice, and open-ended QA records without semantic drift, while preserving deterministic artifact layouts and export-run manifests.

## Scope

Phase 5 covers:

- `EXPO-01`: export approved canonical samples as QA records
- `EXPO-02`: export approved canonical samples as MCQ records from the same underlying sample
- `EXPO-03`: export approved canonical samples as open-ended QA records from the same underlying sample
- `EXPO-04`: write dataset manifests describing splits, configs, seeds, and artifact locations

## Inputs From Earlier Phases

Phase 1 established:

- canonical sample contracts that are independent from final export format
- task-definition metadata including supported export formats and answer modes

Phase 2 established:

- deterministic scenario and latent-state sampling

Phase 3 established:

- provenance-rich generation manifests and replay-safe runtime artifacts

Phase 4 established:

- QC decisions, rejection manifests, duplicate clusters, and acceptance metrics
- explicit review outcomes for borderline samples

Phase 5 should consume approved canonical samples plus QC outputs rather than reinterpreting raw generation text.

## Key Conclusions

### 1. Exporters should be pure downstream transforms from canonical samples

Do not let each exporter invent its own semantics.

Recommended rule:

- the canonical sample remains the source of truth
- exporters only render target-format records from approved canonical data
- export layers must not mutate latent semantics or approved answers

This keeps QA, MCQ, and open QA aligned.

### 2. Approved sample gating belongs at export entry

Export should accept only:

- approved QC decisions
- optionally reviewed samples whose final disposition is `keep` or `revise`

Rejected or unresolved review items should not silently enter the dataset artifacts.

### 3. QA and open QA can share a common base renderer

The base export surface can normalize:

- sample id
- task id
- scene or context text
- question text
- answer payload
- provenance and split metadata

Then:

- QA can render a concise answer field
- open QA can preserve richer rationale or free-form answer payloads

This reduces duplication and semantic drift.

### 4. MCQ export needs explicit distractor strategy hooks

MCQ is the riskiest export format because poor distractors weaken the benchmark.

Recommended abstractions:

- `DistractorStrategy` protocol
- deterministic distractor generation from canonical answer space or task metadata
- validation that the correct option remains unique and semantically correct

For v1, keep distractor generation simple and configurable. Avoid model-generated distractors unless the strategy is explicitly pluggable.

### 5. Export manifests should describe both content and layout

Phase 5 manifests should retain:

- export run id
- source QC report or accepted sample inventory
- target format(s)
- split definitions
- config snapshot
- seeds used for any stochastic exporter behavior
- output file paths

Phase 6 reproducibility will depend on this.

### 6. Export layout should be DVC-friendly and batch-safe

Recommended layout:

- one run directory per export execution
- deterministic filenames by format and split
- one manifest file at the run root

Keep artifacts line-oriented JSON where practical. That simplifies inspection and diffing.

## Recommended Modules

```text
src/smdgf/
  export/
    __init__.py
    models.py
    qa.py
    mcq.py
    manifest.py
```

## Data Model Guidance

### Shared export record fields

Should include:

- export id
- source sample id
- task id
- format
- split
- context text
- question text
- answer payload
- provenance metadata

### MCQ-specific fields

Should include:

- options
- correct option index or key
- distractor provenance or strategy id

### Export manifest fields

Should include:

- run id
- created time
- source QC artifact reference
- formats rendered
- split inventory
- output paths
- config snapshot

## Validation Architecture

Phase 5 validation should prove:

- the same canonical sample can render to QA and open QA without semantic drift
- MCQ rendering keeps one unambiguous correct answer while exposing distractor strategy hooks
- export manifests describe run outputs, splits, configs, and artifact paths deterministically

Recommended tests:

- `tests/unit/test_export_qa.py`
- `tests/unit/test_export_mcq.py`
- `tests/unit/test_export_manifest.py`

## Risks And Watchouts

- Do not let exporter-specific structures leak back into canonical contracts.
- Do not permit unresolved review samples into exports by default.
- Do not create MCQ distractors that duplicate or paraphrase the correct answer too closely.
- Do not make export manifests optional; later reproducibility depends on them.
- Keep Python 3.9 compatibility in any new helper APIs and tests.

## Recommended Plan Split

### Plan 01

Implement shared export models plus canonical-to-QA and canonical-to-open-QA exporters.

### Plan 02

Implement canonical-to-MCQ exporter with deterministic distractor strategy hooks and validation.

### Plan 03

Implement export manifests, run layouts, and packaged artifact helpers.

## Outcome

Phase 5 should end with deterministic exporters that render one approved canonical sample into multiple benchmark formats while preserving auditable manifests and split metadata.
