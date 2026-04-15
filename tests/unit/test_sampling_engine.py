from smdgf.samplers import SamplingContext, sample_scenario
from smdgf.schemas import (
    LatentStateSpec,
    RelationSpec,
    RoleSpec,
    SceneTemplate,
    SlotSpec,
)


def build_scene_template() -> SceneTemplate:
    return SceneTemplate(
        template_id="emotion.support",
        task_id="emotion.typical",
        scene_blueprint="{helper} comforts {target} in the {location}.",
        slot_specs=[
            SlotSpec(slot_id="helper", value_type="person_name"),
            SlotSpec(slot_id="target", value_type="person_name"),
            SlotSpec(
                slot_id="location",
                value_type="location",
                allowed_values=["office", "classroom", "garden"],
            ),
        ],
        roles=[
            RoleSpec(
                role_id="helper",
                role_type="agent",
                display_name_source="slot:helper",
            ),
            RoleSpec(
                role_id="target",
                role_type="agent",
                display_name_source="slot:target",
            ),
        ],
        relations=[
            RelationSpec(
                relation_id="support-edge",
                source_role="helper",
                relation_type="supports",
                target_role="target",
            )
        ],
        latent_state_specs=[
            LatentStateSpec(
                state_id="target-emotion",
                owner_role="target",
                state_type="emotion",
                allowed_values=["relieved", "grateful", "calm"],
                sampling_strategy="choice",
            )
        ],
        constraints=[],
    )


def test_sampling_is_deterministic_for_same_seed() -> None:
    template = build_scene_template()

    first = sample_scenario(template, SamplingContext(seed=7))
    second = sample_scenario(template, SamplingContext(seed=7))

    assert first.model_dump() == second.model_dump()


def test_sampling_varies_for_different_seeds() -> None:
    template = build_scene_template()

    first = sample_scenario(template, SamplingContext(seed=7))
    second = sample_scenario(template, SamplingContext(seed=8))

    assert first.sampled_slots != second.sampled_slots or (
        first.latent_state_assignments[0].value
        != second.latent_state_assignments[0].value
    )


def test_sampling_preserves_latent_state_assignments() -> None:
    template = build_scene_template()
    sample = sample_scenario(template, SamplingContext(seed=13))

    assignment = sample.latent_state_assignments[0]
    assert assignment.owner_role == "target"
    assert assignment.state_type == "emotion"
    assert assignment.sampling_strategy == "choice"
    assert assignment.value in {"relieved", "grateful", "calm"}
    assert sample.relations[0].relation_type == "supports"
