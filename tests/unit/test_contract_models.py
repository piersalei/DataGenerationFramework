import pytest
from pydantic import ValidationError

from smdgf.registry import TaskRegistry
from smdgf.schemas import (
    AbilityCategory,
    AnswerMode,
    CanonicalSample,
    ExportFormat,
    QualityExpectationSpec,
    QuestionPatternSpec,
    SceneTemplateSpec,
    TaskDefinition,
    TaskSpecification,
)


def make_task(task_id: str = "emotion.typical") -> TaskDefinition:
    return TaskDefinition(
        task_id=task_id,
        name="Typical emotion inference",
        description="Assess emotion inference from a social scene.",
        ability_category=AbilityCategory.EMOTION,
        sub_capabilities=["contextual_emotion"],
        latent_variables=[{"name": "protagonist_emotion", "value_type": "string"}],
        answer_mode=AnswerMode.SINGLE_CHOICE,
        supported_exports=[ExportFormat.MCQ, ExportFormat.QA, ExportFormat.OPEN_QA],
    )


def test_task_definition_validation() -> None:
    task = make_task()
    assert task.task_id == "emotion.typical"
    assert task.ability_category is AbilityCategory.EMOTION

    with pytest.raises(ValidationError):
        TaskDefinition(
            task_id="invalid id",
            name="Invalid",
            description="Invalid task.",
            ability_category=AbilityCategory.EMOTION,
            answer_mode=AnswerMode.SINGLE_CHOICE,
            supported_exports=[],
        )


def test_task_specification_supports_qc_expectations() -> None:
    spec = TaskSpecification(
        task_id="emotion.typical",
        scene_templates=[
            SceneTemplateSpec(
                template_id="scene-1",
                narrative_template="{person} received unexpected help.",
                slots={"person": "human name"},
                role_constraints=["person has a goal"],
                latent_state_requirements=["emotion_after_event"],
            )
        ],
        question_patterns=[
            QuestionPatternSpec(
                question_id="q1",
                prompt_template="How does {person} feel?",
                target_capability="emotion",
                answer_mode=AnswerMode.SINGLE_CHOICE,
                options_count=4,
            )
        ],
        quality_expectations=[
            QualityExpectationSpec(
                expectation_id="no-leakage",
                description="Question must not leak the answer.",
                rule_type="leakage",
            )
        ],
    )

    assert spec.quality_expectations[0].rule_type == "leakage"
    assert spec.scene_templates[0].latent_state_requirements == ["emotion_after_event"]


def test_canonical_sample_is_export_agnostic() -> None:
    sample = CanonicalSample(
        sample_id="sample-1",
        task_id="emotion.typical",
        scene_text="Mina was helped by her teammate before a presentation.",
        role_state={"Mina": {"role": "speaker"}},
        latent_state={"Mina": {"emotion": "grateful"}},
    )

    dumped = sample.model_dump()
    assert "options" not in dumped
    assert "distractors" not in dumped
    assert sample.latent_state["Mina"]["emotion"] == "grateful"


def test_registry_rejects_duplicate_task_id() -> None:
    registry = TaskRegistry()
    registry.register(make_task("belief.false_location"))

    with pytest.raises(ValueError, match="duplicate task_id"):
        registry.register(make_task("belief.false_location"))

    assert registry.get("belief.false_location").name == "Typical emotion inference"
