from smdgf.qc.judges import ThresholdJudge, aggregate_judge_results, apply_thresholds
from smdgf.qc.models import JudgeResult, QualityFinding
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample
from smdgf.qc import QualityCandidate


def make_candidate() -> QualityCandidate:
    sample = CanonicalSample(
        sample_id="sample-judge-1",
        task_id="emotion.typical",
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text="How does Mina feel after receiving help?",
                target_capability="emotion",
            )
        ],
        answers=[CanonicalAnswer(question_id="q1", value="grateful")],
    )
    return QualityCandidate(candidate_id="candidate-judge-1", canonical_sample=sample)


def test_score_based_judge_result_normalizes_provenance() -> None:
    judge = ThresholdJudge(
        "clarity",
        lambda _: 0.92,
        confidence=0.88,
        explanation="clear reasoning chain",
        metadata={"provider": "stub-judge"},
    )

    result = judge.evaluate(make_candidate())

    assert result.judge_id == "clarity"
    assert result.score == 0.92
    assert result.confidence == 0.88
    assert result.metadata["provider"] == "stub-judge"


def test_threshold_judge_marks_borderline_sample_for_review() -> None:
    judge = ThresholdJudge("ambiguity", lambda _: 0.63, explanation="borderline ambiguity")
    result = judge.evaluate(make_candidate())

    status = apply_thresholds(result, accept_at=0.8, review_at=0.5)

    assert status == "review"


def test_judge_aggregation_can_reject_low_confidence_candidate() -> None:
    candidate = make_candidate()
    low_score = JudgeResult(
        judge_id="faithfulness",
        score=0.22,
        confidence=0.91,
        explanation="candidate conflicts with rubric",
        findings=[
            QualityFinding(
                finding_id="faithfulness:conflict",
                source_type="judge",
                source_id="faithfulness",
                severity="error",
                message="rubric conflict",
                decision_hint="reject",
            )
        ],
    )

    decision = aggregate_judge_results(candidate, [low_score], accept_at=0.8, review_at=0.5)

    assert decision.status == "reject"
    assert decision.judge_scores["faithfulness"] == 0.22
    assert any(finding.source_id == "faithfulness" for finding in decision.findings)
