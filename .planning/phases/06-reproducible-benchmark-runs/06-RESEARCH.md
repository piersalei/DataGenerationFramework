# Phase 6 Research: Reproducible Benchmark Runs

## Objective

Research how to turn the framework into a reproducible internal benchmark-building system by connecting generation, QC, export, and artifact tracking into replayable runs with baseline task packs.

## Scope

Phase 6 covers:

- `REPR-01`: reproduce a dataset build from versioned config, prompt template, model identifier, and seed inputs
- `REPR-02`: record run parameters, metrics, and artifacts for later comparison across benchmark builds

## Inputs From Earlier Phases

Phase 3 established:

- generation run manifests with prompt, provider, model, seed, and response provenance

Phase 4 established:

- QC reports, review queues, and acceptance metrics tied to run ids

Phase 5 established:

- export manifests, split inventories, and packaged export layouts

Phase 6 should connect these existing artifacts instead of inventing a separate benchmark state model from scratch.

## Key Conclusions

### 1. Reproducibility should be run-centric, not file-centric

Configs alone are not enough.

A reproducible benchmark run should bind together:

- config snapshot
- code revision
- prompt template version or fingerprint
- model/provider identifiers
- generation seed inputs
- QC artifact references
- export artifact references

This must exist as one structured run contract.

### 2. Run manifests should stitch together earlier phase artifacts

Recommended approach:

- keep generation manifest as the generation-layer artifact
- keep QC report as the QC-layer artifact
- keep export manifest as the export-layer artifact
- add one benchmark-run manifest that references all three

This preserves phase boundaries while enabling replay and comparison.

### 3. Artifact layout should remain DVC-friendly and local-first

Phase 6 should not require an external orchestration service.

Recommended layout:

- one benchmark run directory
- subpaths or references to generation, QC, export, and metrics artifacts
- deterministic filenames and JSON metadata

This keeps the system CLI-friendly and internal-team friendly.

### 4. Tracking hooks should be optional and adapter-based

The user asked for reproducible experiments and comparison hooks, but not for a heavy platform dependency in v1.

Recommended abstractions:

- `RunTracker` protocol
- local JSON tracker by default
- optional MLflow-compatible adapter hook

This preserves provider-agnostic and tool-agnostic behavior while leaving room for later integration.

### 5. Baseline task packs should exercise the whole pipeline

The framework should ship at least one internal task-pack example that demonstrates:

- task definition
- scenario sampling
- generation config
- QC flow
- export flow

This pack is not just sample data; it is a reproducibility fixture and smoke-test target.

### 6. End-to-end verification should stay lightweight in v1

Phase 6 does not need to replay real remote model calls in CI.

It does need:

- fixture-backed manifests
- baseline task-pack examples
- end-to-end smoke tests using stubbed or local artifacts

This keeps the workflow testable under the current local Python environment.

## Recommended Modules

```text
src/smdgf/
  benchmark/
    __init__.py
    models.py
    tracker.py
    taskpack.py
```

## Data Model Guidance

### Benchmark-run manifest

Should include:

- benchmark run id
- config snapshot
- code revision
- generation manifest reference
- QC report reference
- export manifest reference
- model and prompt metadata
- seed inventory
- summary metrics

### Tracking entry

Should include:

- run id
- timestamps
- parameter fields
- metric fields
- artifact references
- comparison labels or tags

### Baseline task-pack metadata

Should include:

- task-pack id
- included task ids
- source fixture paths
- intended benchmark purpose
- smoke-test entrypoints

## Validation Architecture

Phase 6 validation should prove:

- a benchmark run can be reconstructed from structured manifests and config snapshots
- run tracking stores parameters, metrics, and artifact references for comparison
- a baseline task pack exists and can drive an end-to-end smoke workflow without manual intervention

Recommended tests:

- `tests/unit/test_benchmark_manifest.py`
- `tests/unit/test_benchmark_tracker.py`
- `tests/unit/test_taskpack_smoke.py`

## Risks And Watchouts

- Do not duplicate earlier phase artifacts inside one giant opaque file.
- Do not make tracking depend on a remote service in order to function locally.
- Do not ship a baseline task pack that bypasses generation, QC, or export boundaries.
- Keep artifact references explicit so runs can be compared without filesystem guessing.
- Maintain Python 3.9 compatibility in all new tests and helpers.

## Recommended Plan Split

### Plan 01

Integrate benchmark-run manifests and deterministic artifact-layout stitching across generation, QC, and export.

### Plan 02

Implement local-first run tracking plus optional adapter hooks for experiment comparison.

### Plan 03

Ship a baseline internal task pack and end-to-end smoke tests that exercise the full benchmark workflow.

## Outcome

Phase 6 should end with a reproducible benchmark-run layer that ties the whole framework together and proves one baseline task pack can travel the end-to-end path from canonical contracts to packaged dataset artifacts.
