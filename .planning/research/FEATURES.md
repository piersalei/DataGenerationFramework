# Feature Research

## Summary

For this project, "table stakes" are the capabilities a serious benchmark-generation framework must have to support controlled social-mind data creation. Differentiators are features that make the framework more credible or efficient but are not strictly required for v1. Anti-features are tempting expansions that would dilute the first release.

## Table Stakes

### Task Definition

| Feature | Why It Matters | Complexity | Dependencies |
|---------|----------------|------------|--------------|
| Task schema registry | Every capability family needs explicit contracts and metadata | Medium | Typed schema layer |
| Canonical sample representation | Multi-format export depends on one latent source of truth | High | Task schema registry |
| Capability tags and metadata | Needed to organize social-mind abilities and benchmark slices | Low | Task schema registry |

### Scenario Modeling

| Feature | Why It Matters | Complexity | Dependencies |
|---------|----------------|------------|--------------|
| Scene templates with slots and constraints | Controls scenario diversity without full manual writing | Medium | Schema layer |
| Role graph and world-state modeling | Social-mind tasks depend on role relations and latent states | High | Schema layer |
| Sampling policies with seeds | Required for reproducibility and balanced coverage | Medium | Config system |
| Structured task specification artifacts | CogToM uses explicit task requirement specifications before large-scale expansion | Medium | Task schema registry |

### Generation Runtime

| Feature | Why It Matters | Complexity | Dependencies |
|---------|----------------|------------|--------------|
| Local and remote LLM adapters | Required by project constraints | Medium | Provider abstraction |
| Batched generation jobs | Dataset construction needs throughput and resumability | Medium | Tracking + storage |
| Prompt/render pipeline | Templates must become prompts deterministically | Medium | Scene templates |

### Quality Control

| Feature | Why It Matters | Complexity | Dependencies |
|---------|----------------|------------|--------------|
| Schema validation on outputs | Prevent malformed records | Low | Typed schema layer |
| Rule-based QC filters | Catch structural and logic failures early | Medium | Canonical sample |
| Deduplication and near-deduplication | Prevent benchmark contamination and low diversity | Medium | Data pipeline |
| Audit trail for rejected samples | Required to debug dataset quality decisions | Medium | Tracking |
| Human review and arbitration workflow | CogToM quality is maintained through multi-round review, not automatic filtering alone | High | Tracking + QC |

### Export And Packaging

| Feature | Why It Matters | Complexity | Dependencies |
|---------|----------------|------------|--------------|
| QA export | Core supervised format | Low | Canonical sample |
| Multiple-choice export | Required by user request | Medium | Canonical sample + distractor policy |
| Open-ended QA export | Required by user request | Low | Canonical sample |
| Dataset metadata and manifests | Needed for reproducible release | Medium | Tracking |

## Differentiators

| Feature | Why It Helps | Complexity |
|---------|--------------|------------|
| Model-based judge ensemble for QC | Improves filtering robustness beyond hand-written rules | High |
| Coverage diagnostics by ability/state/template | Makes benchmark balance measurable | Medium |
| Human review queue generation | Helps create curator-in-the-loop workflows later | Medium |
| Automatic distractor construction strategies for MCQ | Improves multiple-choice quality | High |
| Benchmark card generation | Speeds internal reporting and later publication | Low |

## Anti-Features

| Feature | Why Not In v1 |
|---------|---------------|
| Full web app and annotation platform | Pulls effort away from the core pipeline and internal CLI workflow |
| Training/fine-tuning orchestration | Separate concern from data generation |
| Multimodal data support from day one | Adds too much surface area before text pipeline quality is proven |
| Public leaderboard hosting | Not needed for internal benchmark incubation |
| Agentic orchestration framework as the main abstraction | Risks obscuring explicit dataset semantics and reproducibility |

## Build Implications

- Start with contracts and canonical data models before generation logic.
- Keep export logic downstream of canonical sample creation.
- Treat QC as a pipeline phase with separate artifacts and metrics.
- Model CogToM's "task specification -> expansion -> review -> annotation -> arbitration -> de-duplication" pattern as first-class framework stages.
- Make each task family pluggable so new social-mind abilities extend configs and schemas, not hardcoded scripts.
