# Research Summary

## Key Findings

**Stack**

Use a Python 3.11+ stack centered on Pydantic, Hydra, LiteLLM, Polars, Hugging Face Datasets, DVC, and MLflow. This best matches the project's need for typed contracts, config-driven sweeps, provider-agnostic generation, and reproducible dataset builds.

**Table Stakes**

The framework must have explicit task schemas, structured task specifications, scene and latent-state sampling, local and remote generation adapters, mandatory quality filtering, human-review hooks, and multi-format export from one source sample.

**Watch Out For**

The biggest structural risks are skipping the canonical sample contract, letting mental states remain only implicit prompt text, and treating QC plus human review as thin post-processing instead of full pipeline stages.

## Recommended v1 Emphasis

1. Schema and contract stability
2. Reproducible sampling and generation runs
3. Strong QC, review, and auditability
4. Multi-format export from canonical samples

## Architectural Direction

The system should be built as a layered pipeline:

task registry -> template engine -> sampling engine -> generation runtime -> canonical sample store -> quality pipeline -> exporters -> tracking

This ordering should also drive the roadmap.
