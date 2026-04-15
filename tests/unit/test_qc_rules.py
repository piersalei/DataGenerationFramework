import pytest
from pydantic import ValidationError
from typing import Optional

from smdgf.qc import QualityCandidate, RuleEngine
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample


def make_candidate(
    *,
    question_text: str = "How does Mina feel?",
    answer_value: str = "grateful",
    latent_state: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> QualityCandidate:
    sample = CanonicalSample(
        sample_id="sample-1",
        task_id="emotion.typical",
        scene_text="Mina receives unexpected help before speaking.",
        latent_state=latent_state or {"Mina": {"emotion": "grateful"}},
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text=question_text,
                target_capability="emotion",
            )
        ],
        answers=[CanonicalAnswer(question_id="q1", value=answer_value)],
    )
    return QualityCandidate(
        candidate_id="candidate-1",
        canonical_sample=sample,
        metadata=metadata or {},
    )


def test_quality_candidate_validation_rejects_missing_fields() -> None:
    with pytest.raises(ValidationError):
        QualityCandidate(candidate_id="candidate-1")


def test_rule_engine_rejects_answer_leakage() -> None:
    candidate = make_candidate(question_text="Is Mina grateful after the help?")

    decision = RuleEngine().evaluate(candidate)

    assert decision.status == "reject"
    assert any(finding.source_id == "answer-leakage" for finding in decision.findings)


def test_rule_engine_rejects_latent_inconsistency() -> None:
    candidate = make_candidate(
        latent_state={"Mina": {"emotion": "embarrassed"}},
        metadata={"latent_expectations": {"Mina.emotion": "grateful"}},
    )

    decision = RuleEngine().evaluate(candidate)

    assert decision.status == "reject"
    assert any(finding.source_id == "latent-consistency" for finding in decision.findings)


def test_rule_engine_rejects_answers_for_unknown_question_ids() -> None:
    sample = CanonicalSample(
        sample_id="sample-2",
        task_id="emotion.typical",
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text="How does Mina feel?",
                target_capability="emotion",
            )
        ],
        answers=[CanonicalAnswer(question_id="q2", value="grateful")],
    )
    candidate = QualityCandidate(candidate_id="candidate-2", canonical_sample=sample)

    decision = RuleEngine().evaluate(candidate)

    assert decision.status == "reject"
    assert any(finding.source_id == "structure" for finding in decision.findings)
