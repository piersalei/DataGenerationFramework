# Stack Research

## Recommendation

Use a Python 3.11+ CLI-first stack built around typed contracts, composable configuration, unified LLM adapters, columnar data processing, and explicit experiment tracking.

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

The framework needs a canonical latent sample that survives multiple export formats without semantic drift. Pydantic models are a strong fit for task definitions, scene variables, sampled world state, candidate answers, and QC verdicts.

### Config-driven generation

The project needs reproducible benchmark builds and easy variation across capability families. Hydra maps well to nested task configs, provider configs, prompt variants, and sweepable sampling settings.

### Provider-agnostic generation

The user explicitly needs local and remote LLM compatibility. LiteLLM is the cleanest way to normalize provider calls without baking provider-specific logic into generation nodes.

### Filtering is a first-class workload

The project prioritizes filtering and QC. Polars is a better fit than pandas for large-scale sample filtering, deduplication, ranking, and pipeline-style transformations.

### Reproducible benchmark claims

This benchmark framework should not rely on ad-hoc notebooks. DVC plus MLflow provides a pragmatic split: DVC for artifact and stage reproducibility, MLflow for run metadata and comparisons.

## Suggested Project Layout

```text
src/
  smdgf/
    cli/
    config/
    schemas/
    tasks/
    templates/
    samplers/
    generators/
    quality/
    exporters/
    tracking/
configs/
  tasks/
  models/
  exports/
  quality/
data/
artifacts/
tests/
```

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

These are inputs for initial pinning, not a promise that every patch should be auto-upgraded without compatibility checks.
