from pathlib import Path

from smdgf.qc.models import QualityDecision, QualityFinding, ReviewDisposition
from smdgf.qc.reports import (
    QualityControlReport,
    apply_review_disposition,
    build_qc_report,
    build_rejection_manifest,
)


def make_findings(source_id: str, message: str):
    return [
        QualityFinding(
            finding_id=f"{source_id}:1",
            source_type="rule",
            source_id=source_id,
            severity="error",
            message=message,
            decision_hint="reject",
        )
    ]


def test_qc_report_summarizes_acceptance_and_rejection_metrics(tmp_path: Path) -> None:
    decisions = [
        QualityDecision(candidate_id="c1", status="accept"),
        QualityDecision(candidate_id="c2", status="reject", findings=make_findings("answer-leakage", "leak")),
        QualityDecision(candidate_id="c3", status="review", review_required=True),
    ]

    report = build_qc_report("run-1", decisions)
    path = tmp_path / "qc-report.json"
    report.write_json(path)
    loaded = QualityControlReport.read_json(path)

    assert loaded.metrics.total_candidates == 3
    assert loaded.metrics.accepted == 1
    assert loaded.metrics.rejected == 1
    assert loaded.metrics.review == 1
    assert loaded.metrics.rejection_reasons["answer-leakage"] == 1


def test_rejection_manifest_preserves_rule_reasons_and_candidate_ids() -> None:
    decisions = [
        QualityDecision(
            candidate_id="c2",
            status="reject",
            findings=make_findings("latent-consistency", "latent conflict"),
        )
    ]

    manifest = build_rejection_manifest(decisions)

    assert manifest[0].candidate_id == "c2"
    assert manifest[0].reasons == ["latent conflict"]
    assert manifest[0].source_ids == ["latent-consistency"]


def test_review_queue_preserves_keep_revise_discard_outcomes() -> None:
    review_decision = QualityDecision(candidate_id="c3", status="review", review_required=True)
    final = apply_review_disposition(
        review_decision,
        ReviewDisposition(candidate_id="c3", outcome="keep", reviewer_id="reviewer-1"),
    )
    report = build_qc_report("run-2", [final])

    assert report.review_queue[0].candidate_id == "c3"
    assert report.review_queue[0].status == "resolved"
    assert report.review_queue[0].final_disposition is not None
    assert report.review_queue[0].final_disposition.outcome == "keep"
