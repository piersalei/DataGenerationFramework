import pytest

from smdgf.export.mcq import export_sample_to_mcq
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample


class StaticDistractorStrategy:
    strategy_id = "static"

    def __init__(self, options):
        self._options = list(options)

    def generate(self, sample, question, answer):
        return list(self._options)


def make_sample() -> CanonicalSample:
    return CanonicalSample(
        sample_id="sample-mcq-1",
        task_id="emotion.typical",
        scene_text="Mina receives unexpected help before a presentation.",
        questions=[
            CanonicalQuestion(
                question_id="q1",
                text="How does Mina feel?",
                target_capability="emotion",
            )
        ],
        answers=[CanonicalAnswer(question_id="q1", value="grateful")],
    )


def test_export_sample_to_mcq_keeps_unique_correct_answer() -> None:
    records = export_sample_to_mcq(
        make_sample(),
        StaticDistractorStrategy(["relieved", "embarrassed", "angry"]),
    )

    payload = records[0].payload
    option_texts = [option["text"] for option in payload["options"]]
    assert records[0].format == "mcq"
    assert payload["correct_option_id"] == "option-0"
    assert option_texts.count("grateful") == 1


def test_distractor_strategy_can_supply_deterministic_options() -> None:
    left = export_sample_to_mcq(
        make_sample(),
        StaticDistractorStrategy(["relieved", "embarrassed", "angry"]),
    )
    right = export_sample_to_mcq(
        make_sample(),
        StaticDistractorStrategy(["relieved", "embarrassed", "angry"]),
    )

    assert left[0].payload["options"] == right[0].payload["options"]


def test_mcq_export_rejects_duplicate_correct_option() -> None:
    with pytest.raises(ValueError, match="correct answer"):
        export_sample_to_mcq(
            make_sample(),
            StaticDistractorStrategy(["grateful", "embarrassed", "angry"]),
        )
