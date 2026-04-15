from smdgf.generation.prompts import build_generation_prompt
from smdgf.schemas import (
    AbilityCategory,
    AnswerMode,
    ExportFormat,
    LatentStateAssignment,
    QuestionPatternSpec,
    SampledRelation,
    SampledRole,
    ScenarioSample,
    TaskDefinition,
    TaskSpecification,
)


def make_task_definition() -> TaskDefinition:
    return TaskDefinition(
        task_id="belief.false_location",
        name="False belief location",
        description="Assess whether the model tracks outdated beliefs.",
        ability_category=AbilityCategory.BELIEF,
        answer_mode=AnswerMode.FREE_TEXT,
        supported_exports=[ExportFormat.QA],
    )


def make_task_specification() -> TaskSpecification:
    return TaskSpecification(
        task_id="belief.false_location",
        question_patterns=[
            QuestionPatternSpec(
                question_id="q-belief",
                prompt_template="Where will {observer} look for the object first?",
                target_capability="belief_tracking",
                answer_mode=AnswerMode.FREE_TEXT,
            )
        ],
    )


def make_scenario_sample() -> ScenarioSample:
    return ScenarioSample(
        sample_id="sample-belief-1",
        template_id="template-belief-1",
        task_id="belief.false_location",
        scene_blueprint="{observer} sees {actor} move the toy.",
        sampled_slots={"observer": "Mina", "actor": "Jun", "location": "drawer"},
        roles=[
            SampledRole(role_id="observer", role_type="agent", display_name="Mina"),
            SampledRole(role_id="actor", role_type="agent", display_name="Jun"),
        ],
        relations=[
            SampledRelation(
                relation_id="r1",
                source_role="observer",
                relation_type="observes",
                target_role="actor",
            )
        ],
        latent_state_assignments=[
            LatentStateAssignment(
                state_id="belief-location",
                owner_role="observer",
                state_type="belief",
                value="drawer",
                sampling_strategy="choice",
            )
        ],
        provenance={"seed": 17},
    )


def test_prompt_assembly_is_deterministic() -> None:
    prompt_a, metadata_a = build_generation_prompt(
        make_task_definition(), make_task_specification(), make_scenario_sample(), 17
    )
    prompt_b, metadata_b = build_generation_prompt(
        make_task_definition(), make_task_specification(), make_scenario_sample(), 17
    )

    assert prompt_a == prompt_b
    assert metadata_a == metadata_b


def test_prompt_metadata_contains_task_scenario_and_seed_context() -> None:
    _, metadata = build_generation_prompt(
        make_task_definition(), make_task_specification(), make_scenario_sample(), 17
    )

    assert metadata["task_id"] == "belief.false_location"
    assert metadata["scenario_sample_id"] == "sample-belief-1"
    assert metadata["seed"] == 17
    assert metadata["question_ids"] == ["q-belief"]
    assert len(metadata["prompt_fingerprint"]) == 64


def test_prompt_includes_roles_relations_and_latent_state_context() -> None:
    prompt, _ = build_generation_prompt(
        make_task_definition(), make_task_specification(), make_scenario_sample(), 17
    )

    assert "Roles:" in prompt
    assert "Relations:" in prompt
    assert "Latent States:" in prompt
    assert "observer --observes--> actor" in prompt
    assert "observer.belief-location (belief) = drawer" in prompt
