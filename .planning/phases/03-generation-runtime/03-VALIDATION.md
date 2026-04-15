---
phase: 3
slug: generation-runtime
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-15
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/unit/test_generation_provider.py -q` |
| **Full suite command** | `python3 -m pytest -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific unit target for the touched generation module
- **After every plan wave:** Run `python3 -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | GEN-01 | T-3-01 | Provider configs normalize local and remote backend settings behind one adapter surface | unit | `python3 -m pytest tests/unit/test_generation_provider.py -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | GEN-04 | T-3-02 | Provider response normalization preserves provider/model/usage/error metadata | unit | `python3 -m pytest tests/unit/test_generation_provider.py -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 2 | GEN-02 | T-3-03 | Prompt assembly is deterministic from task and scenario inputs | unit | `python3 -m pytest tests/unit/test_prompt_assembly.py -q` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 2 | GEN-04 | T-3-04 | Prompt metadata captures prompt fingerprint, task id, scenario id, and seed | unit | `python3 -m pytest tests/unit/test_prompt_assembly.py -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 3 | GEN-03 | T-3-05 | Runtime checkpoints completed item ids and resumes without duplicate execution | unit | `python3 -m pytest tests/unit/test_generation_runtime.py -q` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 3 | GEN-01 | T-3-06 | Batch runner applies retry policy and records failure state explicitly | unit | `python3 -m pytest tests/unit/test_generation_runtime.py -q` | ❌ W0 | ⬜ pending |
| 3-04-01 | 04 | 4 | GEN-04 | T-3-07 | Run manifests persist prompt, seed, provider, and raw response provenance | integration | `python3 -m pytest tests/unit/test_generation_manifest.py -q` | ❌ W0 | ⬜ pending |
| 3-04-02 | 04 | 4 | GEN-03 | T-3-08 | Manifest-backed reruns skip completed item ids deterministically | integration | `python3 -m pytest tests/unit/test_generation_manifest.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/smdgf/generation/__init__.py` — generation package exports
- [ ] `src/smdgf/generation/models.py` — runtime, request, result, and manifest contracts
- [ ] `src/smdgf/generation/providers.py` — provider adapter surface
- [ ] `src/smdgf/generation/prompts.py` — deterministic prompt assembly helpers
- [ ] `src/smdgf/generation/runtime.py` — batch runner, retries, checkpoints, resume
- [ ] `tests/unit/test_generation_provider.py` — provider normalization tests
- [ ] `tests/unit/test_prompt_assembly.py` — prompt determinism tests
- [ ] `tests/unit/test_generation_runtime.py` — retry/resume tests
- [ ] `tests/unit/test_generation_manifest.py` — provenance manifest tests

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
