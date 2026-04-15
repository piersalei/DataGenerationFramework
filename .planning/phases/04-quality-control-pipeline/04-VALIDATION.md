---
phase: 4
slug: quality-control-pipeline
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python3 -m pytest tests/unit/test_qc_rules.py -q` |
| **Full suite command** | `python3 -m pytest -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific QC unit target for the touched module
- **After every plan wave:** Run `python3 -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | QUAL-01 | T-4-01 | Candidate QC validation rejects malformed canonical samples before export | unit | `python3 -m pytest tests/unit/test_qc_rules.py -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | QUAL-02 | T-4-02 | Deterministic QC rules reject leakage and latent inconsistency with structured reasons | unit | `python3 -m pytest tests/unit/test_qc_rules.py -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 2 | QUAL-03 | T-4-03 | Judge interfaces normalize score or verdict outputs behind one extension surface | unit | `python3 -m pytest tests/unit/test_qc_judges.py -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 2 | QUAL-03 | T-4-04 | Judge thresholds and aggregation preserve reproducible accept, reject, and review decisions | unit | `python3 -m pytest tests/unit/test_qc_judges.py -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 3 | QUAL-04 | T-4-05 | Exact duplicate detection uses stable fingerprints over accepted canonical samples | unit | `python3 -m pytest tests/unit/test_qc_dedup.py -q` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 3 | QUAL-04 | T-4-06 | Near-duplicate detection groups lexically similar accepted samples deterministically | unit | `python3 -m pytest tests/unit/test_qc_dedup.py -q` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 4 | QUAL-05 | T-4-07 | QC reports and rejection manifests preserve auditable reasons and run-linked metrics | integration | `python3 -m pytest tests/unit/test_qc_reports.py -q` | ❌ W0 | ⬜ pending |
| 4-04-02 | 04 | 4 | QUAL-06 | T-4-08 | Review queues and arbitration records preserve keep, revise, discard outcomes explicitly | integration | `python3 -m pytest tests/unit/test_qc_reports.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/smdgf/qc/__init__.py` — QC package exports
- [ ] `src/smdgf/qc/models.py` — QC candidate, finding, decision, and review contracts
- [ ] `src/smdgf/qc/rules.py` — schema validation and deterministic QC rule engine
- [ ] `src/smdgf/qc/judges.py` — score and judge extension points
- [ ] `src/smdgf/qc/dedup.py` — exact and near-duplicate detection helpers
- [ ] `src/smdgf/qc/reports.py` — rejection manifests, review queues, and acceptance metrics
- [ ] `tests/unit/test_qc_rules.py` — schema and deterministic QC tests
- [ ] `tests/unit/test_qc_judges.py` — judge adapter and threshold tests
- [ ] `tests/unit/test_qc_dedup.py` — duplicate and near-duplicate tests
- [ ] `tests/unit/test_qc_reports.py` — reporting and review queue tests

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
