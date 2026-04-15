---
phase: 5
slug: multi-format-export
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-16
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/unit/test_export_qa.py -q` |
| **Full suite command** | `python3 -m pytest -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific export unit target for the touched module
- **After every plan wave:** Run `python3 -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | EXPO-01 | T-5-01 | Approved canonical samples render into QA records without mutating source semantics | unit | `python3 -m pytest tests/unit/test_export_qa.py -q` | ❌ W0 | ⬜ pending |
| 5-01-02 | 01 | 1 | EXPO-03 | T-5-02 | Open-QA export preserves richer answer payloads and provenance from the same canonical sample | unit | `python3 -m pytest tests/unit/test_export_qa.py -q` | ❌ W0 | ⬜ pending |
| 5-02-01 | 02 | 2 | EXPO-02 | T-5-03 | MCQ export derives one correct option and deterministic distractors from the same approved sample | unit | `python3 -m pytest tests/unit/test_export_mcq.py -q` | ❌ W0 | ⬜ pending |
| 5-02-02 | 02 | 2 | EXPO-02 | T-5-04 | Distractor strategies remain pluggable and do not collapse into duplicate correct answers | unit | `python3 -m pytest tests/unit/test_export_mcq.py -q` | ❌ W0 | ⬜ pending |
| 5-03-01 | 03 | 3 | EXPO-04 | T-5-05 | Export manifests describe formats, splits, config snapshots, and artifact paths deterministically | integration | `python3 -m pytest tests/unit/test_export_manifest.py -q` | ❌ W0 | ⬜ pending |
| 5-03-02 | 03 | 3 | EXPO-04 | T-5-06 | Export layouts preserve run-level artifact grouping and split inventory for reproducible packaging | integration | `python3 -m pytest tests/unit/test_export_manifest.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/smdgf/export/__init__.py` — export package exports
- [ ] `src/smdgf/export/models.py` — shared export record and manifest contracts
- [ ] `src/smdgf/export/qa.py` — QA and open-QA rendering helpers
- [ ] `src/smdgf/export/mcq.py` — MCQ rendering and distractor strategy hooks
- [ ] `src/smdgf/export/manifest.py` — export-run manifest and packaged layout helpers
- [ ] `tests/unit/test_export_qa.py` — QA and open-QA tests
- [ ] `tests/unit/test_export_mcq.py` — MCQ and distractor tests
- [ ] `tests/unit/test_export_manifest.py` — manifest and artifact-layout tests

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
