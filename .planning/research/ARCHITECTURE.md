# Architecture Research

## Recommended Architecture

Build the framework as a layered batch pipeline with a stable canonical sample contract in the middle.

## Major Components

### 1. Task Registry

Owns task schemas, capability metadata, answer-space rules, and export affordances.

### 2. Scenario Template Engine

Owns scene templates, role definitions, latent-state declarations, and template rendering helpers.

### 3. Sampling Engine

Owns seeded sampling of scenarios, roles, hidden states, and control distributions.

### 4. Generation Runtime

Owns prompt assembly, provider selection, batching, retries, and resumable generation jobs.

### 5. Review And Annotation Layer

Owns intermediate review queues, human annotation inputs, arbitration records, and de-duplication decisions.

### 6. Canonical Sample Store

Owns the normalized latent sample representation, provenance, and intermediate artifacts before export.

### 7. Quality Pipeline

Owns structural validation, rule-based checks, score-based filtering, deduplication, and rejection reports.

### 8. Export Layer

Owns renderers that convert canonical samples into QA, MCQ, and open-ended QA outputs.

### 9. Tracking And Reproducibility Layer

Owns configs, seeds, run metadata, metrics, artifacts, and dataset manifests.

## Data Flow

1. Researcher selects a task family and config profile.
2. Task registry resolves the expected canonical sample contract.
3. Scenario templates are instantiated with role and world-state variables.
4. Sampling engine materializes concrete latent worlds with reproducible seeds.
5. Generation runtime renders prompts and calls the chosen LLM backend.
6. Review and annotation layer supports intermediate inspection, human labeling, arbitration, and hard case handling.
7. Candidate outputs are normalized into canonical samples with provenance.
8. Quality pipeline validates, scores, filters, and deduplicates canonical samples.
9. Export layer renders approved samples into one or more output formats.
10. Tracking layer persists configs, seeds, prompts, metrics, and manifests.

## Component Boundaries

- Task registry should not know provider details.
- Template engine should not embed filtering logic.
- Sampling engine should produce latent variables, not exported task text.
- Generation runtime should not decide benchmark validity beyond low-level execution failures.
- Review workflow should be separable from automatic QC so human arbitration remains inspectable.
- Quality pipeline should operate on canonical samples, not raw provider payloads.
- Exporters should be pure downstream transforms from canonical samples.

## Suggested Build Order

1. Canonical schema contracts and task registry
2. Template and latent-state modeling
3. Sampling engine with reproducible seeds
4. Generation runtime and provider adapters
5. Review and annotation workflow primitives
6. Quality pipeline
7. Exporters and manifests
8. Built-in baseline task packs and reporting

## Why This Matters For Roadmapping

This architecture implies the roadmap should progress from contracts to scenario control, then provider execution, then QC, and only then exporter polish and benchmark packaging. If export logic is built before the canonical sample layer is stable, semantic drift across QA, MCQ, and open QA becomes likely.
