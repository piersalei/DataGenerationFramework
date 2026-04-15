---
phase: 2
slug: scenario-and-sampling-engine
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/unit/test_scene_models.py -q` |
| **Full suite command** | `python3 -m pytest -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific unit target for the touched scene or sampling modules
- **After every plan wave:** Run `python3 -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | SCEN-01 | T-2-01 | Scene templates enforce typed slots and explicit constraints | unit | `python3 -m pytest tests/unit/test_scene_models.py -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | SCEN-02 | T-2-02 | Role and relation structures are explicit and serializable | unit | `python3 -m pytest tests/unit/test_scene_models.py -q` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | SCEN-03 | T-2-02 | Latent-state specs are modeled as structured fields, not prompt-only prose | unit | `python3 -m pytest tests/unit/test_scene_models.py -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 2 | SCEN-04 | T-2-03 | Seeded sampling context yields deterministic slot and role assignments | unit | `python3 -m pytest tests/unit/test_sampling_engine.py -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 2 | SCEN-03 | T-2-04 | Latent-state assignments stay reproducible and explicit | unit | `python3 -m pytest tests/unit/test_sampling_engine.py -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 3 | SCEN-01 | T-2-05 | Preview output exposes sampled scene structure without provider execution | integration | `python3 -m pytest tests/unit/test_sampling_preview.py -q` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 3 | SCEN-04 | T-2-06 | Same seed produces identical preview output across runs | integration | `python3 -m pytest tests/unit/test_sampling_preview.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/smdgf/schemas/scene.py` — scene, role, relation, and latent-state models
- [ ] `src/smdgf/samplers/__init__.py` — sampler package marker
- [ ] `src/smdgf/samplers/context.py` — seeded sampling context
- [ ] `src/smdgf/samplers/scenario.py` — deterministic scenario sampler
- [ ] `tests/unit/test_scene_models.py` — scene-model contract tests
- [ ] `tests/unit/test_sampling_engine.py` — deterministic sampling tests
- [ ] `tests/unit/test_sampling_preview.py` — preview and reproducibility tests

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
