"""QC reports, rejection manifests, and review queues."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field

from smdgf.qc.models import (
    AcceptanceMetrics,
    DuplicateCluster,
    QualityDecision,
    ReviewDisposition,
    ReviewQueueEntry as BaseReviewQueueEntry,
)


class RejectionManifestEntry(BaseModel):
    """One rejected candidate and the reasons supporting rejection."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    reasons: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class ReviewQueueEntry(BaseReviewQueueEntry):
    """Local alias so report helpers expose review-queue records directly."""


class QualityControlReport(BaseModel):
    """Structured QC report for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    metrics: AcceptanceMetrics = Field(default_factory=AcceptanceMetrics)
    rejection_manifest: list[RejectionManifestEntry] = Field(default_factory=list)
    review_queue: list[ReviewQueueEntry] = Field(default_factory=list)
    duplicate_clusters: list[DuplicateCluster] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def write_json(self, path: Path) -> None:
        """Persist the report as deterministic JSON."""

        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def read_json(cls, path: Path) -> "QualityControlReport":
        """Load a serialized report without code execution."""

        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))


def summarize_metrics(decisions: Iterable[QualityDecision]) -> AcceptanceMetrics:
    """Summarize acceptance, rejection, and review counts for one QC run."""

    decision_list = list(decisions)
    metrics = AcceptanceMetrics(total_candidates=len(decision_list))

    for decision in decision_list:
        if decision.status == "accept":
            metrics.accepted += 1
        elif decision.status == "reject":
            metrics.rejected += 1
            for finding in decision.findings:
                metrics.rejection_reasons[finding.source_id] = (
                    metrics.rejection_reasons.get(finding.source_id, 0) + 1
                )
        else:
            metrics.review += 1

    if metrics.total_candidates:
        metrics.acceptance_rate = metrics.accepted / metrics.total_candidates
    return metrics


def build_rejection_manifest(decisions: Iterable[QualityDecision]) -> list[RejectionManifestEntry]:
    """Build rejection manifest entries for rejected decisions only."""

    entries = []
    for decision in decisions:
        if decision.status != "reject":
            continue
        entries.append(
            RejectionManifestEntry(
                candidate_id=decision.candidate_id,
                reasons=[finding.message for finding in decision.findings],
                source_ids=sorted({finding.source_id for finding in decision.findings}),
            )
        )
    return entries


def build_review_queue(decisions: Iterable[QualityDecision]) -> list[ReviewQueueEntry]:
    """Build review queue entries for flagged or human-reviewed decisions."""

    queue = []
    for decision in decisions:
        if decision.status != "review" and decision.final_disposition is None:
            continue
        status = "resolved" if decision.final_disposition is not None else "pending"
        queue.append(
            ReviewQueueEntry(
                candidate_id=decision.candidate_id,
                status=status,
                findings=decision.findings,
                recommended_action="review",
                final_disposition=decision.final_disposition,
            )
        )
    return queue


def build_qc_report(
    run_id: str,
    decisions: Iterable[QualityDecision],
    *,
    duplicate_clusters: Optional[Iterable[DuplicateCluster]] = None,
    metadata: Optional[dict] = None,
) -> QualityControlReport:
    """Assemble one complete QC report from QC decisions and dedup clusters."""

    decision_list = list(decisions)
    return QualityControlReport(
        run_id=run_id,
        metrics=summarize_metrics(decision_list),
        rejection_manifest=build_rejection_manifest(decision_list),
        review_queue=build_review_queue(decision_list),
        duplicate_clusters=list(duplicate_clusters or []),
        metadata=metadata or {},
    )


def apply_review_disposition(
    decision: QualityDecision,
    disposition: ReviewDisposition,
) -> QualityDecision:
    """Attach a final human-review outcome to a QC decision."""

    decision.final_disposition = disposition
    decision.review_required = False
    return decision
