import pytest

from smdgf.schemas import (
    LatentStateSpec,
    RelationSpec,
    RoleSpec,
    SceneTemplate,
    SlotSpec,
)


def build_scene_template() -> SceneTemplate:
    return SceneTemplate(
        template_id="belief.false-belief",
        task_id="belief.false_location",
        scene_blueprint="{observer} sees {actor} place the snack in the cupboard.",
        slot_specs=[
            SlotSpec(slot_id="observer", value_type="person_name"),
            SlotSpec(slot_id="actor", value_type="person_name"),
            SlotSpec(
                slot_id="container",
                value_type="object_location",
                allowed_values=["cupboard", "drawer"],
            ),
        ],
        roles=[
            RoleSpec(
                role_id="actor",
                role_type="agent",
                display_name_source="slot:actor",
            ),
            RoleSpec(
                role_id="observer",
                role_type="agent",
                display_name_source="slot:observer",
            ),
        ],
        relations=[
            RelationSpec(
                relation_id="rel-1",
                source_role="observer",
                relation_type="observes",
                target_role="actor",
            )
        ],
        latent_state_specs=[
            LatentStateSpec(
                state_id="belief-location",
                owner_role="observer",
                state_type="belief",
                allowed_values=["cupboard", "drawer"],
                sampling_strategy="choice",
            )
        ],
        constraints=[],
    )


def test_scene_template_requires_typed_slots() -> None:
    template = build_scene_template()

    assert template.slot_specs[0].slot_id == "observer"
    assert template.slot_specs[0].value_type == "person_name"

    with pytest.raises(ValueError, match="slot_specs"):
        SceneTemplate(
            template_id="empty",
            task_id="belief.false_location",
            scene_blueprint="No slots.",
            slot_specs=[],
            roles=[],
            relations=[],
            latent_state_specs=[],
            constraints=[],
        )


def test_scene_template_supports_role_relations() -> None:
    template = build_scene_template()

    relation = template.relations[0]
    assert relation.source_role == "observer"
    assert relation.relation_type == "observes"
    assert relation.target_role == "actor"


def test_latent_state_spec_is_structured() -> None:
    template = build_scene_template()

    latent_state = template.latent_state_specs[0]
    assert latent_state.owner_role == "observer"
    assert latent_state.state_type == "belief"
    assert latent_state.sampling_strategy == "choice"
    assert latent_state.allowed_values == ["cupboard", "drawer"]
