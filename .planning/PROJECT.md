# Social Mind Data Generation Framework

## What This Is

This project is a Python framework for generating benchmark datasets for social-mind large models inside a research team. It is explicitly inspired by the CogToM paper, "CogToM: A Comprehensive Theory of Mind Benchmark inspired by Human Cognition for Large Language Models" (arXiv:2601.15628v1, January 22, 2026), especially its task-centered benchmark design and staged dataset construction process.

CogToM itself standardizes psychological Theory-of-Mind paradigms into scene-based multiple-choice tasks and builds data through a multi-stage pipeline with human supervision. This project generalizes that idea into a reusable framework: define tasks, instantiate scenario templates, sample roles and mental states, generate candidate samples with LLMs, run strict quality control, and then export multiple supervised formats from the same canonical sample.

The framework is not just a dataset dump script. It is intended to become the team's reusable data construction backbone for proposing new social-mind benchmarks with lower manual effort and stronger reproducibility.

## Core Value

Produce high-quality, reproducible social-mind benchmark data with minimal manual authoring while preserving one canonical sample that can be exported into multiple task formats.

## Requirements

### Validated

- [x] Canonical-sample-first pipeline foundation validated through Phases 1-6.
- [x] Local and remote generation, QC, export, and reproducible benchmark packaging validated in code and tests.
- [x] Reproducible benchmark runs with local-first tracking and a baseline end-to-end task pack validated in Phase 6.

### Active

- [ ] Build a configurable pipeline for task definition, scene templating, role/state sampling, generation, and filtering.
- [ ] Support the full target ability space: intention inference, belief tracking, multi-role relation understanding, emotion and motivation reasoning, social decision making, and implicit stance or strategy understanding.
- [ ] Preserve one canonical latent sample representation that can be rendered into QA, multiple-choice, and open-ended QA formats.
- [ ] Run against both local and remote LLM providers under a unified execution interface.
- [ ] Extend the validated backbone with additional task families, richer review workflows, and future release/reporting features.

### Out of Scope

- Full model training and fine-tuning pipeline - this project focuses on data generation and packaging, not training infrastructure.
- Public benchmark website or leaderboard - internal team workflow comes first and external presentation can be added later.
- Rich frontend product surface - CLI and config-driven operation are sufficient for v1.
- Multimodal data generation - v1 focuses on text-first social-mind dataset construction.

## Context

The team needs a new benchmark for social-mind capabilities and cannot afford a mainly manual data authoring workflow. Existing benchmark construction effort is too labor-intensive, hard to scale across many mental-capability categories, and too fragile when requirements change.

The desired workflow is explicitly inspired by CogToM's benchmark construction process described in Section 3.2 of the paper: task collection and adaptation, structured task specification, LLM-based expansion, intermediate review, human annotation and arbitration, and final de-duplication and release preparation. Our framework keeps that staged discipline but generalizes beyond CogToM's native scene-based multiple-choice target into a canonical-sample-first system that can also export QA and open-ended QA.

Primary users are internal researchers and benchmark builders, not end users. The framework therefore needs strong composition, traceability, and reproducibility more than product polish.

## Constraints

- **Tech stack**: Python-first implementation - the team wants the framework to live in a standard research Python workflow.
- **Model access**: Must support both local and remote LLMs - experiments cannot be tied to a single provider or deployment style.
- **Reproducibility**: Builds must be replayable - benchmark claims need config, seed, prompt, and run provenance.
- **Format strategy**: One canonical sample, multiple exports - CogToM's primary benchmark format is scene-based multiple-choice, but this framework must preserve the same underlying semantics while exporting MCQ, QA, and open-ended QA.
- **Quality priority**: Filtering and quality control are more important than raw generation throughput - benchmark credibility depends on it.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use a pipeline-first framework architecture instead of one-off dataset scripts | The team needs a reusable benchmark construction backbone, not a single benchmark artifact | pending |
| Use a canonical intermediate sample representation before export | QA, MCQ, and open QA should stay semantically aligned and derive from the same latent sample | pending |
| Make quality control a mandatory pipeline stage | The user identified filtering and quality as the highest v1 priority | pending |
| Treat human review and arbitration as explicit pipeline concepts | CogToM's construction quality relies on repeated human supervision, review, and de-duplication rather than single-pass generation | pending |
| Start with Python CLI and config-driven workflows | Internal research usage does not require a frontend-first implementation | pending |
| Support local and remote LLM backends behind one adapter layer | Benchmark generation must remain deployment-agnostic | pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-16 after Phase 6 completion*
