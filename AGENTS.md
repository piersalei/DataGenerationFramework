<!-- GSD:project-start source:PROJECT.md -->
## Project

**Social Mind Data Generation Framework**

This project is a Python framework for generating benchmark datasets for social-mind large models inside a research team. It follows a CogToM-style pipeline mindset: define tasks, instantiate scenario templates, sample roles and mental states, generate candidate samples with LLMs, then apply strict quality control before exporting multiple supervised formats from the same canonical sample.

The framework is not just a dataset dump script. It is intended to become the team's reusable data construction backbone for proposing new social-mind benchmarks with lower manual effort and stronger reproducibility.

**Core Value:** Produce high-quality, reproducible social-mind benchmark data with minimal manual authoring while preserving one canonical sample that can be exported into multiple task formats.

### Constraints

- **Tech stack**: Python-first implementation - the team wants the framework to live in a standard research Python workflow.
- **Model access**: Must support both local and remote LLMs - experiments cannot be tied to a single provider or deployment style.
- **Reproducibility**: Builds must be replayable - benchmark claims need config, seed, prompt, and run provenance.
- **Format strategy**: One canonical sample, multiple exports - downstream tasks should not fork the generation logic per format.
- **Quality priority**: Filtering and quality control are more important than raw generation throughput - benchmark credibility depends on it.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommendation
## Recommended Stack
| Layer | Choice | Why | Confidence |
|-------|--------|-----|------------|
| Runtime | Python 3.11 | Mature async support, broad LLM/data ecosystem, pragmatic research-team default | High |
| CLI | Typer 0.24.x | Fast CLI construction with strong typing and good UX for internal tools | High |
| Schema and validation | Pydantic 2.12.x | Strong model and validator support for task schemas, canonical samples, and export contracts | High |
| Config composition | Hydra 1.3 | Hierarchical config composition and multirun fit dataset sweeps and benchmark ablations | High |
| Templating | Jinja2 3.x | Mature structured templating for scenes, prompts, and export renderers | High |
| LLM abstraction | LiteLLM 1.82.x | One SDK for local and remote LLM providers with retries and routing support | High |
| Tabular processing | Polars 1.39.x | Fast lazy data pipeline for filtering, deduplication, joins, and export builds | High |
| Dataset packaging | Hugging Face Datasets 4.8.x | Useful typed dataset metadata and standard export surface for benchmark release | Medium |
| Data and pipeline reproducibility | DVC | Versioned artifacts and file-based pipelines for reproducible dataset builds | High |
| Run metadata | MLflow 3.x | Track run params, metrics, artifacts, and dataset-build comparisons | Medium |
| Testing | Pytest 8.x | Standard Python testing baseline for schema, sampler, and exporter correctness | High |
| Lint/format | Ruff | Fast lint and format path for a Python research codebase | High |
## Why This Fits The Project
### Typed contracts first
### Config-driven generation
### Provider-agnostic generation
### Filtering is a first-class workload
### Reproducible benchmark claims
## Suggested Project Layout
## What Not To Use First
- LangChain-style framework-heavy orchestration as the project core - too much abstraction for a pipeline that needs explicit dataset semantics.
- Notebook-only workflow - too weak for reproducibility and code review.
- Provider-specific SDKs in business logic - they fight the local/remote compatibility requirement.
- Pandas as the primary filtering engine - workable, but less attractive than Polars for larger reproducible pipelines.
## Notes On Versions
- Pydantic docs currently expose v2.12.5.
- Hydra docs currently mark 1.3 as stable.
- LiteLLM PyPI currently shows 1.82.1.
- Polars PyPI currently shows 1.39.x releases in March 2026.
- Datasets PyPI currently shows 4.8.4.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
