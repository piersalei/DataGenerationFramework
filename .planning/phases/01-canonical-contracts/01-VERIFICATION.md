---
phase: 01-canonical-contracts
verified: 2026-04-15T11:20:00Z
status: passed
score: 11/11 must-haves verified
---

# Phase 1: Canonical Contracts Verification Report

**Phase Goal:** Define the stable contracts that every later phase will depend on: task schemas, structured task specifications, ability metadata, and one canonical sample representation.
**Verified:** 2026-04-15T11:20:00Z
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Project installs as a Python package with pinned contract-layer dependencies. | ✓ VERIFIED | `pyproject.toml` defines project metadata, dependency pins, setuptools src-layout, and `smdgf` script entrypoint. |
| 2 | The `src/smdgf` package and its contract-related subpackages can be imported by tests. | ✓ VERIFIED | `tests/unit/test_contract_scaffold.py` passes and imports `smdgf` plus `smdgf.cli.main`. |
| 3 | Wave 1 test scaffolding exists so later contract and CLI plans can add real assertions without reworking infrastructure. | ✓ VERIFIED | `tests/conftest.py` plus scaffold and model/CLI test files exist and run successfully. |
| 4 | Researchers can define valid task contracts with constrained ability metadata. | ✓ VERIFIED | `TaskDefinition` and `AbilityCategory` are implemented with validation and tested in `test_task_definition_validation`. |
| 5 | Structured task specifications can describe scene rules, question patterns, and QC expectations. | ✓ VERIFIED | `TaskSpecification`, `SceneTemplateSpec`, `QuestionPatternSpec`, and `QualityExpectationSpec` are implemented and exercised in tests. |
| 6 | Canonical samples exist as export-agnostic representations independent from MCQ, QA, or open QA renderers. | ✓ VERIFIED | `CanonicalSample` stores semantic scene, latent state, questions, and answers without distractor/options fields; tested by `test_canonical_sample_is_export_agnostic`. |
| 7 | A task registry can register, list, fetch, and reject duplicate task identifiers. | ✓ VERIFIED | `TaskRegistry` implements `register/get/list/clear` and duplicate rejection is tested. |
| 8 | Researchers can inspect registered contracts from the CLI. | ✓ VERIFIED | `contracts inspect` command exists and returns deterministic output on an empty registry. |
| 9 | Researchers can validate task definition files from the CLI. | ✓ VERIFIED | `test_validate_accepts_valid_task_definition` and invalid-case test both pass. |
| 10 | Researchers can validate task specification files from the CLI. | ✓ VERIFIED | `test_validate_accepts_valid_task_spec` passes using YAML fixture input. |
| 11 | Invalid contract files fail with non-zero exit code and actionable validation output. | ✓ VERIFIED | CLI returns non-zero exit and emits `validation failed:` output for invalid fixtures. |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Python project metadata and dependency pins | ✓ EXISTS + SUBSTANTIVE | Contains project section, dependency ranges, pytest config, and `smdgf` script |
| `src/smdgf/schemas/task.py` | TaskDefinition contract model | ✓ EXISTS + SUBSTANTIVE | Defines `TaskDefinition`, `AnswerMode`, `ExportFormat`, and validators |
| `src/smdgf/schemas/spec.py` | Structured task specification models | ✓ EXISTS + SUBSTANTIVE | Defines scene, question, and QC specification models |
| `src/smdgf/schemas/canonical.py` | Canonical sample model | ✓ EXISTS + SUBSTANTIVE | Defines canonical sample, question, answer, and provenance contracts |
| `src/smdgf/registry.py` | Duplicate-safe registry | ✓ EXISTS + SUBSTANTIVE | Implements register/get/list/clear with duplicate guard |
| `src/smdgf/cli/contracts.py` | CLI contract inspect and validate commands | ✓ EXISTS + SUBSTANTIVE | Safe YAML/JSON parsing with deterministic success/failure behavior |
| `tests/unit/test_contract_scaffold.py` | Scaffold smoke tests | ✓ EXISTS + SUBSTANTIVE | 2 scaffold import tests |
| `tests/unit/test_contract_models.py` | Contract model tests | ✓ EXISTS + SUBSTANTIVE | 4 model and registry tests |
| `tests/unit/test_cli_contracts.py` | CLI contract tests | ✓ EXISTS + SUBSTANTIVE | 4 CLI validation/inspect tests |

**Artifacts:** 9/9 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `pyproject.toml` | `src/smdgf` | setuptools src-layout | ✓ WIRED | `package-dir = {"" = "src"}` and package discovery under `src` |
| `tests/unit/test_contract_scaffold.py` | `src/smdgf/cli/main.py` | import smoke test | ✓ WIRED | `test_cli_entrypoint_module_exists` imports `smdgf.cli.main` |
| `src/smdgf/registry.py` | `src/smdgf/schemas/task.py` | registry stores `TaskDefinition` | ✓ WIRED | Registry imports and types against `TaskDefinition` |
| `src/smdgf/cli/contracts.py` | `src/smdgf/schemas/task.py` | `contracts validate --kind task-definition` | ✓ WIRED | CLI instantiates `TaskDefinition.model_validate(...)` |
| `src/smdgf/cli/contracts.py` | `src/smdgf/schemas/spec.py` | `contracts validate --kind task-spec` | ✓ WIRED | CLI instantiates `TaskSpecification.model_validate(...)` |

**Wiring:** 5/5 connections verified

## Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| `TASK-01`: Researcher can define a task schema with task id, target social-mind ability, required latent variables, and answer contract. | ✓ SATISFIED | - |
| `TASK-02`: Researcher can register task metadata for intention, belief, relation, emotion, motivation, social decision, or implicit stance categories. | ✓ SATISFIED | - |
| `TASK-03`: Framework stores one canonical sample representation that is independent of final export format. | ✓ SATISFIED | - |
| `TASK-04`: Researcher can author structured task specification artifacts that capture scene rules, question patterns, and quality expectations before batch expansion. | ✓ SATISFIED | - |

**Coverage:** 4/4 requirements satisfied

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/smdgf/cli/main.py` | - | Minimal CLI root only, no additional command groups yet | ℹ️ Info | Acceptable for Phase 1; later phases can extend it |

**Anti-patterns:** 1 found (0 blockers, 0 warnings)

## Human Verification Required

None — all verifiable items checked programmatically.

## Gaps Summary

**No gaps found.** Phase goal achieved. Ready to proceed.

## Verification Metadata

**Verification approach:** Goal-backward (derived from plan must-haves and phase goal)  
**Must-haves source:** PLAN.md frontmatter  
**Automated checks:** 10 passed, 0 failed  
**Human checks required:** 0  
**Total verification time:** 4 min

---
*Verified: 2026-04-15T11:20:00Z*
*Verifier: the agent (inline execution)*
