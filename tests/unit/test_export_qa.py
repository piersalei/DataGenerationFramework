from copy import deepcopy

from smdgf.export.qa import export_sample_to_open_qa, export_sample_to_qa
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample


def make_sample() -> CanonicalSample:
    return CanonicalSample(
        sample_id="sample-export-1",
        task_id="emotion.typical",
        scene_text="Mina receives unexpected help before a presentation.",
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text="How does Mina feel?",
                target_capability="emotion",
            )
        ],
        answers=[
            CanonicalAnswer(
                question_id="q1",
                value="grateful",
                rationale="The help reduces pressure before the presentation.",
            )
        ],
    )


def test_export_sample_to_qa_preserves_source_ids() -> None:
    sample = make_sample()

    records = export_sample_to_qa(sample, split="train")

    assert len(records) == 1
    record = records[0]
    assert record.source_sample_id == "sample-export-1"
    assert record.task_id == "emotion.typical"
    assert record.format == "qa"
    assert record.split == "train"
    assert record.answer == "grateful"


def test_export_sample_to_open_qa_preserves_rationale() -> None:
    sample = make_sample()

    records = export_sample_to_open_qa(sample)

    assert records[0].format == "open_qa"
    assert records[0].payload["rationale"] == "The help reduces pressure before the presentation."
    assert records[0].payload["answer_payload"]["value"] == "grateful"


def test_exporters_do_not_mutate_canonical_sample() -> None:
    sample = make_sample()
    before = deepcopy(sample.model_dump(mode="json"))

    export_sample_to_qa(sample)
    export_sample_to_open_qa(sample)

    assert sample.model_dump(mode="json") == before
