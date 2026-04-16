"""MCQ exporter and distractor strategy hooks."""

from __future__ import annotations

from typing import Protocol, Sequence

from smdgf.export.models import ExportOption, ExportRecord
from smdgf.schemas.canonical import CanonicalAnswer, CanonicalQuestion, CanonicalSample


class DistractorStrategy(Protocol):
    """Protocol for deterministic distractor generation."""

    strategy_id: str

    def generate(
        self,
        sample: CanonicalSample,
        question: CanonicalQuestion,
        answer: CanonicalAnswer,
    ) -> Sequence[str]:
        """Return distractor option texts for one question."""


def _answer_text(answer: CanonicalAnswer) -> str:
    if isinstance(answer.value, dict):
        return " ".join(str(answer.value[key]) for key in sorted(answer.value))
    return str(answer.value)


def export_sample_to_mcq(
    sample: CanonicalSample,
    distractor_strategy: DistractorStrategy,
    *,
    split: str = "unsplit",
) -> list[ExportRecord]:
    """Render a canonical sample into MCQ records."""

    answers = {answer.question_id: answer for answer in sample.answers}
    records = []

    for question in sample.questions:
        answer = answers.get(question.question_id)
        if answer is None:
            continue

        correct_text = _answer_text(answer)
        distractors = list(distractor_strategy.generate(sample, question, answer))
        if correct_text in distractors:
            raise ValueError("distractor set contains the correct answer")
        if len(set(distractors)) != len(distractors):
            raise ValueError("distractor set contains duplicate options")

        options = [correct_text] + distractors
        option_models = [
            ExportOption(option_id=f"option-{index}", text=text)
            for index, text in enumerate(options)
        ]
        records.append(
            ExportRecord(
                export_id=f"{sample.sample_id}:{question.question_id}:mcq",
                source_sample_id=sample.sample_id,
                task_id=sample.task_id,
                format="mcq",
                split=split,
                context=sample.scene_text,
                question=question.text,
                answer=correct_text,
                payload={
                    "question_id": question.question_id,
                    "options": [option.model_dump(mode="json") for option in option_models],
                    "correct_option_id": option_models[0].option_id,
                    "distractor_strategy_id": distractor_strategy.strategy_id,
                },
                provenance=sample.provenance.model_dump(mode="json"),
            )
        )

    return records
