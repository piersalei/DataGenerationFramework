# Requirements: Social Mind Data Generation Framework

**Defined:** 2026-04-15
**Core Value:** Produce high-quality, reproducible social-mind benchmark data with minimal manual authoring while preserving one canonical sample that can be exported into multiple task formats.

## v1 Requirements

### Task Contracts

- [x] **TASK-01**: Researcher can define a task schema with task id, target social-mind ability, required latent variables, and answer contract.
- [x] **TASK-02**: Researcher can register task metadata for intention, belief, relation, emotion, motivation, social decision, or implicit stance categories.
- [x] **TASK-03**: Framework stores one canonical sample representation that is independent of final export format.
- [x] **TASK-04**: Researcher can author structured task specification artifacts that capture scene rules, question patterns, and quality expectations before batch expansion.

### Scenario Modeling

- [x] **SCEN-01**: Researcher can define scene templates with typed slots and constraints.
- [x] **SCEN-02**: Researcher can define multiple roles and their relations inside one scenario.
- [x] **SCEN-03**: Researcher can define latent mental-state fields such as beliefs, intentions, emotions, or motivations as explicit sampled variables.
- [x] **SCEN-04**: Researcher can generate deterministic scenario samples from configs and random seeds.

### Generation Runtime

- [x] **GEN-01**: Researcher can run batch sample generation through a unified interface for local and remote LLM backends.
- [x] **GEN-02**: Researcher can configure prompt rendering from task schema plus sampled scenario state.
- [x] **GEN-03**: Framework can resume interrupted generation jobs without silently duplicating accepted samples.
- [x] **GEN-04**: Framework records request and response provenance for every generated candidate sample.

### Quality Control

- [x] **QUAL-01**: Framework validates every candidate sample against schema constraints before export.
- [x] **QUAL-02**: Framework applies rule-based quality filters for structural errors, answer leakage, and invalid latent-state consistency.
- [x] **QUAL-03**: Framework supports configurable score-based or judge-based filtering in addition to deterministic rules.
- [x] **QUAL-04**: Framework detects duplicate and near-duplicate accepted samples.
- [x] **QUAL-05**: Framework emits rejection reasons and QC artifacts that researchers can audit after a run.
- [x] **QUAL-06**: Framework supports human review, disagreement arbitration, and final keep-revise-discard decisions for flagged samples.

### Export

- [x] **EXPO-01**: Researcher can export approved canonical samples as QA records.
- [x] **EXPO-02**: Researcher can export approved canonical samples as multiple-choice records from the same underlying sample.
- [x] **EXPO-03**: Researcher can export approved canonical samples as open-ended QA records from the same underlying sample.
- [x] **EXPO-04**: Framework writes dataset manifests that describe splits, configs, seeds, and artifact locations for each export run.

### Reproducibility And Operations

- [ ] **REPR-01**: Researcher can reproduce a dataset build from versioned config, prompt template, model identifier, and seed inputs.
- [ ] **REPR-02**: Framework records run parameters, metrics, and artifacts for later comparison across benchmark builds.

## v2 Requirements

### Review And Expansion

- **REVW-01**: Researcher can generate human-review queues from QC borderline cases.
- **REVW-02**: Framework supports multilingual dataset variants from the same latent sample.
- **REVW-03**: Framework supports benchmark reporting cards and release packaging for external publication.
- **REVW-04**: Framework supports multimodal social-mind task variants.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Model training and fine-tuning pipeline | Separate concern from benchmark data generation |
| Public leaderboard service | Internal benchmark incubation is the current goal |
| Full annotation web platform | CLI and config workflow are enough for v1 |
| Multimodal data generation | Too much scope before text-first pipeline quality is proven |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TASK-01 | Phase 1 | Complete |
| TASK-02 | Phase 1 | Complete |
| TASK-03 | Phase 1 | Complete |
| TASK-04 | Phase 1 | Complete |
| SCEN-01 | Phase 2 | Complete |
| SCEN-02 | Phase 2 | Complete |
| SCEN-03 | Phase 2 | Complete |
| SCEN-04 | Phase 2 | Complete |
| GEN-01 | Phase 3 | Complete |
| GEN-02 | Phase 3 | Complete |
| GEN-03 | Phase 3 | Complete |
| GEN-04 | Phase 3 | Complete |
| QUAL-01 | Phase 4 | Complete |
| QUAL-02 | Phase 4 | Complete |
| QUAL-03 | Phase 4 | Complete |
| QUAL-04 | Phase 4 | Complete |
| QUAL-05 | Phase 4 | Complete |
| QUAL-06 | Phase 4 | Complete |
| EXPO-01 | Phase 5 | Complete |
| EXPO-02 | Phase 5 | Complete |
| EXPO-03 | Phase 5 | Complete |
| EXPO-04 | Phase 5 | Complete |
| REPR-01 | Phase 6 | Pending |
| REPR-02 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-16 after Phase 5 completion*
