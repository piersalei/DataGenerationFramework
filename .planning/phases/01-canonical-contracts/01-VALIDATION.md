---
phase: 1
slug: canonical-contracts
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/unit/test_contract_scaffold.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit/test_contract_scaffold.py -q` or the task-specific unit target
- **After every plan wave:** Run `python -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | TASK-01 | T-1-01 | Dependency and toolchain definitions are pinned and inspectable | unit | `python -m pytest tests/unit/test_contract_scaffold.py -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | TASK-04 | T-1-02 | Package scaffold exposes deterministic import roots | unit | `python -m pytest tests/unit/test_contract_scaffold.py -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 2 | TASK-01 | T-1-03 | Invalid task definitions fail validation with explicit errors | unit | `python -m pytest tests/unit/test_contract_models.py -q` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 2 | TASK-02 | T-1-04 | Ability metadata is constrained and serializable | unit | `python -m pytest tests/unit/test_contract_models.py -q` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | TASK-03 | T-1-05 | Canonical samples stay export-agnostic and reproducible | unit | `python -m pytest tests/unit/test_contract_models.py -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 3 | TASK-04 | T-1-06 | CLI validates structured task specifications without code execution | integration | `python -m pytest tests/unit/test_cli_contracts.py -q` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 3 | TASK-01 | T-1-07 | CLI inspect output matches registered contracts | integration | `python -m pytest tests/unit/test_cli_contracts.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — add pytest, pydantic, typer, hydra-core, ruff, and editable package config
- [ ] `tests/conftest.py` — shared fixtures for contract and CLI tests
- [ ] `tests/unit/test_contract_scaffold.py` — scaffold and import smoke checks
- [ ] `tests/unit/test_contract_models.py` — schema and registry checks
- [ ] `tests/unit/test_cli_contracts.py` — CLI validation and inspect checks

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
