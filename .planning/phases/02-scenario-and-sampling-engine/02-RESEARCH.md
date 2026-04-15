# Phase 2 Research: Scenario And Sampling Engine

## Objective

Research how to implement Phase 2 so the framework can define scene templates, encode role relations and latent states, and sample deterministic scenario instances from seeds without contaminating the canonical sample contract.

## Scope

Phase 2 covers:

- `SCEN-01`: scene templates with typed slots and constraints
- `SCEN-02`: multiple roles and relations inside one scenario
- `SCEN-03`: explicit latent mental-state fields
- `SCEN-04`: deterministic seeded sampling from configs

## Inputs From Phase 1

Phase 1 established:

- strict Pydantic contract models
- an export-agnostic `CanonicalSample`
- a task registry and contract-validation CLI

Phase 2 should extend those foundations rather than bypass them. Scenario and sampling models should feed the canonical sample, not replace it.

## Key Conclusions

### 1. Split template contracts from sampled scenario instances

Keep a hard boundary between:

- reusable template declarations
- sampled role instances and latent states
- final canonical sample payload

Recommended model layers:

- `SceneTemplate`
- `RoleSpec`
- `RelationSpec`
- `LatentStateSpec`
- `ScenarioSample`

This prevents template config from being mistaken for generated data.

### 2. Role relations need graph-friendly structure, not flat metadata

Social-mind tasks frequently depend on:

- who knows what
- who intends what
- who is related to whom
- who observes which event

Use explicit relation edges, for example:

- `source_role`
- `relation_type`
- `target_role`
- optional attributes

This will scale better into higher-order belief and multi-party tasks than a flat per-role dict alone.

### 3. Latent states should be sampled as structured values

Do not keep mental states as prompt prose only. Phase 2 should define and sample explicit latent states such as:

- belief contents
- intention goals
- desire preferences
- emotional reactions
- knowledge access

Recommended split:

- `LatentStateSpec` describes required state slots and allowed value sources
- `LatentStateAssignment` records the sampled result per role

### 4. Determinism should be centralized

Use one seeded sampling surface, not ad hoc `random.choice()` calls spread across modules.

Recommended implementation:

- a `SamplingContext` with seed and RNG object
- sampler methods that receive `SamplingContext`
- deterministic ordering when iterating slots, roles, and constraints

This makes replay and debugging much easier.

### 5. Constraint evaluation should remain lightweight in v1

Phase 2 does not need a full rule engine. It does need simple, explicit constraints such as:

- required roles
- allowed slot values
- relation requirements
- latent-state prerequisites

Implement constraints as data plus validation helpers. Avoid premature DSL complexity.

## Recommended Modules

```text
src/smdgf/
  samplers/
    __init__.py
    context.py
    scenario.py
  schemas/
    scene.py
```

### `scene.py`

Should define:

- `RoleSpec`
- `RelationSpec`
- `LatentStateSpec`
- `SceneTemplate`
- `ScenarioSample`

### `samplers/context.py`

Should define:

- `SamplingContext`
- seeded RNG construction
- helper methods for deterministic picks

### `samplers/scenario.py`

Should define:

- scene-template instantiation
- role materialization
- latent-state assignment
- reproducible sample preview output

## Data Model Guidance

### Scene template

Needs:

- `template_id`
- `task_id`
- `scene_blueprint`
- slot definitions
- role specifications
- relation specifications
- latent-state specifications
- template-level constraints

### Scenario sample

Needs:

- `sample_id`
- `template_id`
- rendered scene text or structured scene payload
- sampled slots
- sampled roles
- sampled relations
- latent-state assignments
- provenance including seed

### Role specifications

Recommended fields:

- `role_id`
- `display_name_source`
- `role_type`
- `attributes`
- `required`

### Latent-state specifications

Recommended fields:

- `state_id`
- `owner_role`
- `state_type`
- `allowed_values`
- `sampling_strategy`
- `required`

## Validation Architecture

Phase 2 validation should prove:

- invalid templates fail fast
- role relation structure is explicit and serializable
- latent-state assignments remain structured
- same seed + same template + same config produce identical outputs
- different seeds can produce different slot/state assignments

Recommended tests:

- `tests/unit/test_scene_models.py`
- `tests/unit/test_sampling_engine.py`
- `tests/unit/test_sampling_preview.py`

## Risks And Watchouts

- Do not let rendered prompt text become the source of truth for latent states.
- Do not sample from unordered sets or dict iteration paths if reproducibility matters.
- Do not hardcode one benchmark's task assumptions into the generic scene engine.
- Keep scene rendering helpers separate from provider-calling logic, which belongs to Phase 3.

## Recommended Plan Split

### Plan 01

Implement scene template, role, relation, and latent-state schema contracts.

### Plan 02

Implement seeded sampling context plus deterministic scenario and latent-state samplers.

### Plan 03

Implement preview utilities and tests that prove reproducibility and structure.

## Outcome

Phase 2 should end with a reusable scenario engine that emits deterministic, inspectable scenario samples ready to feed Phase 3 generation runtime.
