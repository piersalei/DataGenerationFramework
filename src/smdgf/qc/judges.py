"""Judge and score-based QC extension points."""

from __future__ import annotations

from typing import Iterable, Optional, Protocol

from smdgf.qc.models import (
    JudgeResult as BaseJudgeResult,
    QualityCandidate,
    QualityDecision,
    QualityFinding,
)


class JudgeResult(BaseJudgeResult):
    """Local alias so judge modules expose the normalized result model directly."""


class QualityJudge(Protocol):
    """Protocol implemented by score or verdict-based QC judges."""

    judge_id: str

    def evaluate(self, candidate: QualityCandidate) -> JudgeResult:
        """Evaluate a candidate and return a normalized judge result."""


def apply_thresholds(
    judge_result: JudgeResult,
    *,
    accept_at: float = 0.8,
    review_at: float = 0.5,
) -> str:
    """Convert a judge score or verdict into a deterministic routing label."""

    if judge_result.verdict is not None:
        return judge_result.verdict

    score = judge_result.score
    if score is None:
        return "review"
    if score >= accept_at:
        return "accept"
    if score >= review_at:
        return "review"
    return "reject"


def judge_result_to_finding(judge_result: JudgeResult, status: str) -> QualityFinding:
    """Normalize one judge result into a structured QC finding."""

    severity = "warning" if status == "review" else "error"
    if status == "accept":
        severity = "info"

    return QualityFinding(
        finding_id=f"{judge_result.judge_id}:{status}",
        source_type="judge",
        source_id=judge_result.judge_id,
        severity=severity,
        message=judge_result.explanation or f"judge routed candidate to {status}",
        decision_hint=status,
        evidence={
            "score": judge_result.score,
            "verdict": judge_result.verdict,
            "confidence": judge_result.confidence,
            **judge_result.metadata,
        },
    )


def aggregate_judge_results(
    candidate: QualityCandidate,
    judge_results: Iterable[JudgeResult],
    *,
    accept_at: float = 0.8,
    review_at: float = 0.5,
) -> QualityDecision:
    """Aggregate multiple judge results into one normalized QC decision."""

    results = list(judge_results)
    findings = []
    judge_scores = {}
    status = "accept"

    for result in results:
        routed = apply_thresholds(result, accept_at=accept_at, review_at=review_at)
        if result.score is not None:
            judge_scores[result.judge_id] = result.score
        findings.extend(result.findings)
        findings.append(judge_result_to_finding(result, routed))
        if routed == "reject":
            status = "reject"
        elif routed == "review" and status != "reject":
            status = "review"

    return QualityDecision(
        candidate_id=candidate.candidate_id,
        status=status,
        findings=findings,
        judge_scores=judge_scores,
        review_required=status == "review",
        metadata={
            "judge_ids": [result.judge_id for result in results],
            "accept_at": accept_at,
            "review_at": review_at,
        },
    )


class ThresholdJudge:
    """Simple score-based judge backed by a deterministic callback."""

    def __init__(
        self,
        judge_id: str,
        scorer,
        *,
        confidence: Optional[float] = None,
        explanation: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        self.judge_id = judge_id
        self._scorer = scorer
        self._confidence = confidence
        self._explanation = explanation
        self._metadata = metadata or {}

    def evaluate(self, candidate: QualityCandidate) -> JudgeResult:
        """Run the deterministic scorer for one candidate."""

        score = float(self._scorer(candidate))
        return JudgeResult(
            judge_id=self.judge_id,
            score=score,
            confidence=self._confidence,
            explanation=self._explanation,
            metadata=dict(self._metadata),
        )
