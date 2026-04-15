# Roadmap: Social Mind Data Generation Framework

## Overview

The project will start by establishing stable canonical contracts, then move upward through scenario control and generation execution, and only then lock in quality control, export, and reproducible benchmark packaging. This ordering keeps the framework aligned with the user's intended CogToM-style pipeline and prevents format-specific logic from distorting the core sample semantics.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Canonical Contracts** - Establish task schemas, structured task specifications, capability metadata, and the canonical sample model. (completed 2026-04-15)
- [ ] **Phase 2: Scenario And Sampling Engine** - Build template, role, latent-state, and seeded sampling foundations.
- [ ] **Phase 3: Generation Runtime** - Add provider-agnostic batch generation and run provenance.
- [ ] **Phase 4: Quality Control Pipeline** - Implement deterministic and score-based filtering plus audit artifacts.
- [ ] **Phase 5: Multi-Format Export** - Render approved canonical samples into QA, MCQ, and open QA outputs.
- [ ] **Phase 6: Reproducible Benchmark Runs** - Package run manifests, tracking, and baseline task packs for internal benchmark building.

## Phase Details

### Phase 1: Canonical Contracts
**Goal**: Define the stable contracts that every later phase will depend on: task schemas, structured task specifications, ability metadata, and one canonical sample representation.
**Depends on**: Nothing (first phase)
**Requirements**: TASK-01, TASK-02, TASK-03, TASK-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Researcher can define a task contract and validate it before generation.
  2. Canonical sample schema exists and is independent from QA, MCQ, and open QA exporters.
  3. Capability metadata can distinguish major social-mind ability families in config and code.
  4. Structured task specifications can define scene rules, question patterns, and QC expectations before batch expansion.
**Plans**: 3 plans

Plans:
- [x] 01-01: Create project package structure, typed schema modules, and config scaffolding.
- [x] 01-02: Implement task registry, task specification models, and canonical sample models with validation tests.
- [x] 01-03: Add CLI entry points for schema inspection and contract validation.

### Phase 2: Scenario And Sampling Engine
**Goal**: Build explicit scenario templates, role relations, latent-state modeling, and deterministic sampling from seeded configs.
**Depends on**: Phase 1
**Requirements**: SCEN-01, SCEN-02, SCEN-03, SCEN-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Researcher can define scene templates with typed slots and constraints.
  2. Sampled scenarios include explicit role relations and latent mental-state variables.
  3. Re-running the same sampling config with the same seed reproduces the same sampled latent scenarios.
**Plans**: 3 plans

Plans:
- [x] 02-01: Implement template model, renderer helpers, and role graph abstractions.
- [x] 02-02: Implement latent-state samplers and deterministic seeded sampling policies.
- [x] 02-03: Add sample preview and fixture-based tests for scenario generation.

### Phase 3: Generation Runtime
**Goal**: Execute batch generation jobs over local and remote providers with prompt rendering, resumability, and provenance capture.
**Depends on**: Phase 2
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Researcher can run generation jobs against both local and remote LLM providers through one interface.
  2. Prompt rendering uses task contracts plus sampled scenario state deterministically.
  3. Interrupted generation runs can resume without corrupting accepted sample ids or provenance.
  4. Every candidate sample stores provider, model, prompt, seed, and response provenance.
**Plans**: 4 plans

Plans:
- [ ] 03-01: Implement provider adapter interface and LiteLLM-backed execution layer.
- [ ] 03-02: Implement prompt assembly from canonical task and scenario inputs.
- [ ] 03-03: Implement batched job runner with retries and resumable checkpoints.
- [ ] 03-04: Persist provenance artifacts and generation logs.

### Phase 4: Quality Control Pipeline
**Goal**: Turn filtering and review into first-class stages with schema validation, deterministic rules, score-based filtering, deduplication, rejection audits, and human arbitration hooks.
**Depends on**: Phase 3
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Every candidate sample is validated structurally before it can be exported.
  2. QC rules can reject answer leakage, latent inconsistency, and malformed records.
  3. Duplicate and near-duplicate accepted samples are detected and handled.
  4. Rejected samples produce auditable reasons and QC artifacts.
  5. Flagged samples can enter a human review and arbitration path with explicit keep-revise-discard outcomes.
**Plans**: 4 plans

Plans:
- [ ] 04-01: Implement schema validation and deterministic QC rule engine.
- [ ] 04-02: Implement judge or score-based QC extension points.
- [ ] 04-03: Implement duplicate and near-duplicate detection pipeline.
- [ ] 04-04: Emit QC reports, rejection manifests, review queues, and acceptance metrics.

### Phase 5: Multi-Format Export
**Goal**: Export approved canonical samples into QA, multiple-choice, and open-ended QA records without semantic drift.
**Depends on**: Phase 4
**Requirements**: EXPO-01, EXPO-02, EXPO-03, EXPO-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. The same approved canonical sample can be rendered into QA, MCQ, and open QA outputs.
  2. MCQ export defines distractors without breaking the underlying latent answer semantics.
  3. Export runs produce manifests describing splits, configs, seeds, and artifact locations.
**Plans**: 3 plans

Plans:
- [ ] 05-01: Implement canonical-to-QA and canonical-to-open-QA exporters.
- [ ] 05-02: Implement canonical-to-MCQ exporter and distractor strategy hooks.
- [ ] 05-03: Implement dataset manifests and packaged export layouts.

### Phase 6: Reproducible Benchmark Runs
**Goal**: Make the whole framework usable for internal benchmark construction through tracked runs, reproducible manifests, and built-in baseline task packs.
**Depends on**: Phase 5
**Requirements**: REPR-01, REPR-02
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. A dataset build can be replayed from config, prompt template version, model id, and seed inputs.
  2. Researchers can compare benchmark runs using stored params, metrics, and artifacts.
  3. The repo includes at least one baseline social-mind task pack that exercises the full pipeline end to end.
**Plans**: 3 plans

Plans:
- [ ] 06-01: Integrate run manifests, DVC-friendly artifact layout, and experiment metadata capture.
- [ ] 06-02: Add MLflow or equivalent run tracking and comparison hooks.
- [ ] 06-03: Ship baseline internal task pack examples and end-to-end smoke tests.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Canonical Contracts | 3/3 | Complete    | 2026-04-15 |
| 2. Scenario And Sampling Engine | 0/3 | Not started | - |
| 3. Generation Runtime | 0/4 | Not started | - |
| 4. Quality Control Pipeline | 0/4 | Not started | - |
| 5. Multi-Format Export | 0/3 | Not started | - |
| 6. Reproducible Benchmark Runs | 0/3 | Not started | - |
