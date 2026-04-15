# Phase 1 Research: Canonical Contracts

## Objective

Research how to implement Phase 1 so the project gets a durable contract layer for all later scenario, generation, QC, and export work.

## Scope

Phase 1 covers:

- `TASK-01`: task schema definition
- `TASK-02`: ability metadata registration
- `TASK-03`: canonical sample representation
- `TASK-04`: structured task specification artifacts

## Key Conclusions

### 1. Contract-first layout should be explicit and small

The repo should start with a minimal but opinionated package structure:

```text
src/smdgf/
  __init__.py
  cli/
    __init__.py
    main.py
  schemas/
    __init__.py
    abilities.py
    task.py
    canonical.py
    spec.py
  registry.py
```

This is enough to make task contracts, canonical samples, and CLI validation real without prematurely building sampling or provider layers.

### 2. Pydantic models should be the contract boundary

Pydantic v2 is the right fit for:

- task identifiers and metadata
- ability and sub-ability enums
- structured task specifications
- canonical samples and answer payloads
- schema validation errors surfaced through the CLI

The critical rule is to keep export-specific fields out of the canonical sample model. MCQ, QA, and open QA renderers should be downstream transforms in later phases.

### 3. Ability taxonomy needs two levels now

The current project requirements and CogToM-inspired benchmark direction imply:

- top-level ability categories
- optional sub-abilities or capability tags

Phase 1 should not hardcode the full final benchmark ontology, but it should support:

- `emotion`
- `desire`
- `intention`
- `belief`
- `knowledge`
- `social_relation`
- `non_literal`
- `social_decision`
- `implicit_stance`

Use enums for constrained top-level categories and free-form tag arrays for extensibility.

### 4. Structured task specification should be distinct from canonical samples

CogToM-like construction uses explicit task requirements before batch expansion. The framework should reflect that by separating:

- `TaskDefinition`: what a task is and what it assesses
- `TaskSpecification`: how scenes, question patterns, and QC rules should be constructed
- `CanonicalSample`: one generated latent sample instance

This separation prevents prompt-generation settings from polluting the benchmark data contract.

### 5. Registry should be code-first now, file-backed later

For Phase 1 the registry should support:

- registering a task definition object
- fetching a task by `task_id`
- listing registered tasks
- validating duplicate `task_id` rejection

This can be implemented as an in-memory registry plus simple file-based spec loading hooks. Full plugin/discovery systems can wait.

## Recommended Models

### Ability metadata

- `AbilityCategory`
- `AbilityDescriptor`

`AbilityDescriptor` should include category, display name, description, and tags.

### Task definition

- `TaskDefinition`

Required fields:

- `task_id`
- `name`
- `description`
- `ability_category`
- `sub_capabilities`
- `latent_variables`
- `answer_mode`
- `supported_exports`

### Structured task specification

- `TaskSpecification`
- `SceneTemplateSpec`
- `QuestionPatternSpec`
- `QualityExpectationSpec`

These should capture:

- scene construction rules
- role constraints
- latent-state requirements
- question layout expectations
- QC expectations before expansion

### Canonical sample

- `CanonicalSample`
- `CanonicalAnswer`
- `CanonicalQuestion`
- `ProvenanceRecord`

Canonical sample fields should include:

- sample id
- task id
- scene text or structured scene payload
- role state snapshot
- latent state snapshot
- canonical answer semantics
- provenance metadata

## Validation Architecture

Phase 1 should establish validation as soon as contracts exist.

### Automated checks

- `python -m pytest tests/unit/test_contract_scaffold.py -q`
- `python -m pytest tests/unit/test_contract_models.py -q`
- `python -m pytest tests/unit/test_cli_contracts.py -q`
- `python -m pytest -q`

### What validation must prove

- invalid task definitions fail with useful schema errors
- duplicate registry entries are rejected
- canonical sample model is export-agnostic
- CLI contract validation returns exit code `0` on valid specs and non-zero on invalid specs

### Sampling continuity

Every plan in this phase should end with automated verification. There should be no manual-only tasks in Phase 1.

## Risks And Watchouts

- Do not leak MCQ-specific distractor logic into `CanonicalSample`.
- Do not encode the entire future ontology as enums if the taxonomy is still evolving.
- Do not mix CLI parsing logic into core schema modules.
- Keep file paths and public import surfaces stable now so later phases can build on them.

## Recommended Plan Split

### Plan 01

Create Python package scaffold, dependency pins, and test harness.

### Plan 02

Implement core contract models and task registry.

### Plan 03

Implement CLI contract inspection and validation commands.

## Outcome

Phase 1 should end with a usable contract layer, not just placeholder files. Later phases must be able to import these models as the source of truth.
