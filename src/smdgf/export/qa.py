"""QA and open-QA exporters."""

from __future__ import annotations

from typing import Iterable, Optional

from smdgf.export.models import ExportRecord
from smdgf.schemas.canonical import CanonicalAnswer, CanonicalQuestion, CanonicalSample


def _answer_map(sample: CanonicalSample) -> dict[str, CanonicalAnswer]:
    return {answer.question_id: answer for answer in sample.answers}


def _provenance(sample: CanonicalSample, extra: Optional[dict] = None) -> dict:
    provenance = sample.provenance.model_dump(mode="json")
    if extra:
        provenance.update(extra)
    return provenance


def _record_id(sample: CanonicalSample, question: CanonicalQuestion, fmt: str) -> str:
    return f"{sample.sample_id}:{question.question_id}:{fmt}"


def export_sample_to_qa(
    sample: CanonicalSample,
    *,
    split: str = "unsplit",
    provenance: Optional[dict] = None,
) -> list[ExportRecord]:
    """Render a canonical sample into concise QA records."""

    answers = _answer_map(sample)
    records = []
    for question in sample.questions:
        answer = answers.get(question.question_id)
        if answer is None:
            continue
        records.append(
            ExportRecord(
                export_id=_record_id(sample, question, "qa"),
                source_sample_id=sample.sample_id,
                task_id=sample.task_id,
                format="qa",
                split=split,
                context=sample.scene_text,
                question=question.text,
                answer=answer.value,
                payload={
                    "question_id": question.question_id,
                    "target_capability": question.target_capability,
                },
                provenance=_provenance(sample, provenance),
            )
        )
    return records


def export_sample_to_open_qa(
    sample: CanonicalSample,
    *,
    split: str = "unsplit",
    provenance: Optional[dict] = None,
) -> list[ExportRecord]:
    """Render a canonical sample into open-ended QA records."""

    answers = _answer_map(sample)
    records = []
    for question in sample.questions:
        answer = answers.get(question.question_id)
        if answer is None:
            continue
        records.append(
            ExportRecord(
                export_id=_record_id(sample, question, "open_qa"),
                source_sample_id=sample.sample_id,
                task_id=sample.task_id,
                format="open_qa",
                split=split,
                context=sample.scene_text,
                question=question.text,
                answer=answer.value,
                payload={
                    "question_id": question.question_id,
                    "target_capability": question.target_capability,
                    "rationale": answer.rationale,
                    "answer_payload": answer.model_dump(mode="json"),
                },
                provenance=_provenance(sample, provenance),
            )
        )
    return records


def export_many_to_qa(
    samples: Iterable[CanonicalSample],
    *,
    split: str = "unsplit",
) -> list[ExportRecord]:
    """Render multiple canonical samples into QA records."""

    records = []
    for sample in samples:
        records.extend(export_sample_to_qa(sample, split=split))
    return records
