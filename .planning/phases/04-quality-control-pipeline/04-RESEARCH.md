# Phase 4 Research: Quality Control Pipeline

## Objective

Research how to turn quality control into a first-class pipeline stage for canonical samples so the framework can validate structure, apply deterministic rules, support optional score-based judging, detect duplicates, and emit audit-ready review artifacts before export.

## Scope

Phase 4 covers:

- `QUAL-01`: schema validation for every candidate sample before export
- `QUAL-02`: deterministic QC rules for structural errors, leakage, and latent inconsistency
- `QUAL-03`: configurable score-based or judge-based filtering extension points
- `QUAL-04`: duplicate and near-duplicate detection for accepted samples
- `QUAL-05`: auditable rejection reasons and QC artifacts
- `QUAL-06`: human review and arbitration workflow for flagged samples

## Inputs From Earlier Phases

Phase 1 established:

- strict canonical sample contracts
- task definition and task specification models
- export-independent sample semantics

Phase 2 established:

- scenario templates and deterministic latent-state sampling
- explicit roles, relations, and hidden-state representations

Phase 3 established:

- provider-agnostic generation runtime
- prompt and response provenance manifests
- resumable execution artifacts that Phase 4 can inspect directly

Phase 4 should consume canonical samples plus runtime provenance instead of evaluating raw provider payloads in isolation.

## Key Conclusions

### 1. QC should operate on one normalized candidate record

The quality layer should not reimplement parsing logic from generation providers.

Recommended approach:

- define a QC-facing candidate model that wraps a canonical sample
- attach generation provenance, prompt metadata, and intermediate QC annotations
- keep QC decisions stable even if provider backends change later

This preserves the canonical boundary and keeps rule logic provider-agnostic.

### 2. Deterministic QC rules should be separate from subjective judging

Do not mix hard validation failures with soft quality assessments.

Recommended split:

- schema and contract validation
- deterministic rules for leakage, missing fields, malformed answers, latent inconsistency
- optional judge or score modules for plausibility, explanation quality, or ambiguity

Hard failures should always be reproducible without another model call.

### 3. Judge-based QC needs extension points, not a baked-in policy

The framework should support:

- threshold-based scalar scorers
- rubric-based judge outputs
- model-backed or local judge implementations

Recommended abstractions:

- `QualityJudge` protocol
- normalized judge request and result models
- configurable thresholds and aggregation policy

This lets the team evolve QC criteria without rewriting the pipeline core.

### 4. Duplicate detection needs both exact and near-duplicate passes

Exact duplicate checks should cover stable fingerprints for:

- canonical question text
- answer contract
- scenario identity
- latent-state signature

Near-duplicate checks should cover:

- lexical similarity between rendered prompts or answers
- template-family repetition
- repeated latent reasoning patterns

For v1, lightweight text normalization plus token or n-gram similarity is enough. Avoid bringing in heavy retrieval infrastructure unless tests prove it is necessary.

### 5. QC outcomes must be audit artifacts, not transient console logs

Researchers need post-run inspection for:

- why a sample was rejected
- which rules or judges fired
- which samples require human review
- final acceptance and rejection counts

Recommended artifacts:

- rejection manifest
- review queue file
- acceptance metrics summary
- per-run QC report linked to generation manifest ids

Phase 6 reproducibility depends on these artifacts being structured and deterministic.

### 6. Human review should be modeled explicitly

Flagged samples should not be silently accepted or discarded.

Recommended review path:

- automatic QC marks `accept`, `reject`, or `review`
- flagged records enter a review queue with evidence
- reviewer records `keep`, `revise`, or `discard`
- arbitration preserves reviewer id, timestamp, rationale, and final disposition

The v1 implementation can stay CLI and file based. A web annotation tool is out of scope.

## Recommended Modules

```text
src/smdgf/
  qc/
    __init__.py
    models.py
    rules.py
    judges.py
    dedup.py
    reports.py
```

## Data Model Guidance

### QC candidate surface

Should include:

- candidate id
- canonical sample
- task id and capability metadata
- scenario id or seed linkage
- prompt fingerprint and generation provenance
- QC annotations and statuses

### Deterministic rule output

Should include:

- rule id
- severity
- decision
- human-readable reason
- structured evidence payload

### Judge output

Should include:

- judge id
- score or verdict
- threshold config
- explanation text
- provenance for the judging model when applicable

### QC report surface

Should include:

- run id
- counts by decision and rule
- duplicate cluster summary
- review queue inventory
- acceptance rate and rejection breakdown

## Validation Architecture

Phase 4 validation should prove:

- structural validation rejects malformed canonical samples deterministically
- deterministic rules catch leakage and latent inconsistency without model calls
- score-based judging plugs into the pipeline without coupling to one provider
- duplicate and near-duplicate checks identify repeated accepted samples
- reports and review queues preserve auditable reasons and acceptance metrics

Recommended tests:

- `tests/unit/test_qc_rules.py`
- `tests/unit/test_qc_judges.py`
- `tests/unit/test_qc_dedup.py`
- `tests/unit/test_qc_reports.py`

## Risks And Watchouts

- Do not let QC read unstable raw provider payloads instead of normalized candidate records.
- Do not encode reviewer-only decisions as automatic rejections.
- Do not rely on a single judge score as the only QC mechanism.
- Do not make duplicate detection depend on non-deterministic embeddings in v1.
- Keep rejection reasons structured enough that later benchmark reports can aggregate them.

## Recommended Plan Split

### Plan 01

Implement QC models, schema validation, and deterministic rule engine.

### Plan 02

Implement judge and score-based QC extension points with normalized outputs.

### Plan 03

Implement exact and near-duplicate detection for accepted samples.

### Plan 04

Implement QC reports, rejection manifests, review queues, and acceptance metrics.

## Outcome

Phase 4 should end with a reproducible QC pipeline that evaluates canonical candidates, preserves audit trails, and cleanly hands approved samples to downstream exporters.
