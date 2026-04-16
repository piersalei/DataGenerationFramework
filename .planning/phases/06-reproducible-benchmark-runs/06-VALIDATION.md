---
phase: 6
slug: reproducible-benchmark-runs
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-16
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/unit/test_benchmark_manifest.py -q` |
| **Full suite command** | `python3 -m pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific benchmark unit target for the touched module
- **After every plan wave:** Run `python3 -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | REPR-01 | T-6-01 | Benchmark run manifests stitch together generation, QC, export, config, and seed references deterministically | unit | `python3 -m pytest tests/unit/test_benchmark_manifest.py -q` | ❌ W0 | ⬜ pending |
| 6-01-02 | 01 | 1 | REPR-01 | T-6-02 | Run layouts remain deterministic and DVC-friendly across benchmark artifacts | unit | `python3 -m pytest tests/unit/test_benchmark_manifest.py -q` | ❌ W0 | ⬜ pending |
| 6-02-01 | 02 | 2 | REPR-02 | T-6-03 | Run tracking stores parameters, metrics, and artifact references behind a local-first adapter | unit | `python3 -m pytest tests/unit/test_benchmark_tracker.py -q` | ❌ W0 | ⬜ pending |
| 6-02-02 | 02 | 2 | REPR-02 | T-6-04 | Tracking hooks remain optional and do not require a remote backend to compare runs | unit | `python3 -m pytest tests/unit/test_benchmark_tracker.py -q` | ❌ W0 | ⬜ pending |
| 6-03-01 | 03 | 3 | REPR-01 | T-6-05 | Baseline task packs package benchmark inputs and references explicitly | integration | `python3 -m pytest tests/unit/test_taskpack_smoke.py -q` | ❌ W0 | ⬜ pending |
| 6-03-02 | 03 | 3 | REPR-01, REPR-02 | T-6-06 | End-to-end smoke flow exercises generation/QC/export/run-tracking boundaries through one baseline task pack | integration | `python3 -m pytest tests/unit/test_taskpack_smoke.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/smdgf/benchmark/__init__.py` — benchmark package exports
- [ ] `src/smdgf/benchmark/models.py` — benchmark-run manifest and artifact-reference contracts
- [ ] `src/smdgf/benchmark/tracker.py` — local-first run tracker and optional adapter hooks
- [ ] `src/smdgf/benchmark/taskpack.py` — baseline task-pack metadata and smoke helpers
- [ ] `tests/unit/test_benchmark_manifest.py` — benchmark manifest and layout tests
- [ ] `tests/unit/test_benchmark_tracker.py` — run tracking and comparison tests
- [ ] `tests/unit/test_taskpack_smoke.py` — baseline task-pack and end-to-end smoke tests

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
