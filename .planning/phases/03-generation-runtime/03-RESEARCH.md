# Phase 3 Research: Generation Runtime

## Objective

Research how to implement the generation runtime so the framework can render prompts from canonical task and sampled scenario state, execute batches over local and remote LLM backends, resume interrupted runs, and persist request/response provenance without breaking the canonical sample boundary established in Phases 1 and 2.

## Scope

Phase 3 covers:

- `GEN-01`: unified generation interface for local and remote LLM backends
- `GEN-02`: prompt rendering from task schema plus sampled scenario state
- `GEN-03`: resumable generation jobs without silent duplicate accepted samples
- `GEN-04`: provider, model, prompt, seed, and response provenance for every candidate

## Inputs From Earlier Phases

Phase 1 established:

- strict task-definition and task-spec contracts
- a canonical export-agnostic sample model
- CLI-safe YAML/JSON validation patterns

Phase 2 established:

- scene templates, role graph, and latent-state contracts
- deterministic `ScenarioSample` generation from seeds
- preview CLI proving structured scenario state is inspectable before provider execution

Phase 3 should consume these contracts rather than invent new runtime-specific representations.

## Key Conclusions

### 1. Keep provider execution behind one normalized adapter surface

The framework needs one runtime abstraction that can drive:

- hosted APIs such as OpenAI-compatible endpoints
- local model backends exposed through OpenAI-compatible or LiteLLM-supported providers
- future provider additions without changing prompt assembly or job orchestration

Recommended split:

- `ProviderRequest`
- `ProviderResponse`
- `GenerationProvider` protocol or base class
- `LiteLLMGenerationProvider` as the default implementation

This preserves provider-agnostic orchestration while staying practical for v1.

### 2. Prompt assembly should be deterministic and artifact-backed

Prompt rendering must not be interleaved with provider calls ad hoc.

Recommended inputs:

- `TaskDefinition`
- `TaskSpecification`
- `ScenarioSample`
- generation config

Recommended outputs:

- prompt text
- structured prompt metadata
- prompt fingerprint/version id

This allows replay, auditing, and later QC/debugging when a sample fails.

### 3. Resumability needs explicit run-state manifests

Do not infer resumability from provider logs or directory contents alone.

Recommended run-state artifacts:

- `RunManifest`
- `RunItem`
- `RunCheckpoint`
- accepted candidate ids or generation item ids

The runtime should distinguish:

- pending items
- running items
- completed items
- failed items

Replays should reuse the manifest and skip already completed item ids.

### 4. Provenance must be first-class, not an afterthought

Every candidate sample should retain:

- provider id
- model id
- generation config
- prompt fingerprint or prompt text snapshot
- scenario seed
- raw response text or normalized response payload
- timestamps and error state if failed

Phase 4 quality filters and Phase 6 reproducibility both depend on this.

### 5. LiteLLM is the pragmatic v1 integration point

Inference from LiteLLM docs and ecosystem usage:

- it already normalizes many provider APIs behind one Python interface
- it supports local and remote backends through a common call surface
- it provides retry/routing patterns the framework can grow into later

For Phase 3, keep integration shallow:

- use LiteLLM for completion execution
- wrap it in the framework's own provider adapter
- do not let LiteLLM request shape leak into core contracts

### 6. Batch execution should remain simple in v1

Phase 3 does not need distributed queue infrastructure.

It does need:

- list-based batch submission
- deterministic item ids
- retry policy
- periodic checkpoint writes
- resumption from manifest/checkpoint state

Implement synchronous batch orchestration first. Concurrency can remain configurable and modest.

## Recommended Modules

```text
src/smdgf/
  generation/
    __init__.py
    prompts.py
    models.py
    providers.py
    runtime.py
```

### `models.py`

Should define:

- `ProviderConfig`
- `GenerationRequest`
- `GenerationResult`
- `GenerationRunManifest`
- `GenerationRunItem`

### `providers.py`

Should define:

- `GenerationProvider` protocol
- `LiteLLMGenerationProvider`
- provider normalization helpers

### `prompts.py`

Should define:

- prompt assembly from task + scenario
- prompt metadata or fingerprint helpers

### `runtime.py`

Should define:

- batch runner
- retry behavior
- checkpoint persistence
- resume behavior

## Data Model Guidance

### Request surface

Needs:

- `request_id`
- `task_id`
- `scenario_sample`
- prompt text
- provider config
- seed
- export target or answer mode hint where needed

### Result surface

Needs:

- `request_id`
- provider/model ids
- prompt fingerprint
- raw response text
- parsed response payload if available
- finish status
- error info
- timestamps

### Run manifest

Needs:

- `run_id`
- creation time
- config snapshot
- prompt version
- provider selection
- request inventory
- checkpoint path(s)

## Validation Architecture

Phase 3 validation should prove:

- provider adapter can normalize local and remote execution configs
- prompt rendering is deterministic from task and scenario inputs
- resumable runs skip completed item ids instead of duplicating them
- provenance artifacts include prompt, seed, provider, and response details

Recommended tests:

- `tests/unit/test_generation_provider.py`
- `tests/unit/test_prompt_assembly.py`
- `tests/unit/test_generation_runtime.py`
- `tests/unit/test_generation_cli_or_manifest.py`

## Risks And Watchouts

- Do not let provider-specific kwargs bleed into core contracts.
- Do not write run state in an append-only opaque log without structured resume metadata.
- Do not let prompt assembly read unordered dicts if prompt determinism matters.
- Do not create accepted sample ids from transient batch order; use stable ids derived from task and scenario.
- Keep runtime artifacts structured so Phase 4 can inspect failures without replaying the provider call.

## Recommended Plan Split

### Plan 01

Implement provider/runtime contracts plus LiteLLM-backed adapter stubs and tests.

### Plan 02

Implement deterministic prompt assembly from task and scenario inputs.

### Plan 03

Implement batch runtime with retry/checkpoint/resume behavior.

### Plan 04

Persist provenance-rich run manifests and fixture-backed runtime tests.

## Outcome

Phase 3 should end with a provider-agnostic generation runtime that can turn sampled scenarios into prompt-driven generation jobs, resume safely, and persist the artifacts that later QC and benchmark replay will depend on.
