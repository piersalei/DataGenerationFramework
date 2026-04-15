"""Scenario template instantiation helpers."""

from __future__ import annotations

from smdgf.samplers.context import SamplingContext
from smdgf.schemas.scene import (
    LatentStateAssignment,
    LatentStateSpec,
    RelationSpec,
    RoleSpec,
    SampledRelation,
    SampledRole,
    ScenarioSample,
    SceneTemplate,
    SlotSpec,
)


DEFAULT_SLOT_VALUES = {
    "person_name": ["Mina", "Jun", "Ava", "Leo", "Nora", "Kai"],
    "object_location": ["cupboard", "drawer", "shelf", "desk"],
    "location": ["classroom", "kitchen", "garden", "office"],
    "emotion": ["happy", "worried", "relieved", "frustrated"],
}


def _slot_candidates(slot_spec: SlotSpec) -> list[str]:
    if slot_spec.allowed_values:
        return list(slot_spec.allowed_values)
    return list(DEFAULT_SLOT_VALUES.get(slot_spec.value_type, [slot_spec.slot_id]))


def _resolve_display_name(role_spec: RoleSpec, sampled_slots: dict[str, str]) -> str:
    source = role_spec.display_name_source
    if source.startswith("slot:"):
        slot_id = source.split(":", 1)[1]
        return sampled_slots.get(slot_id, slot_id)
    return source


def _sample_roles(
    template: SceneTemplate, sampled_slots: dict[str, str]
) -> list[SampledRole]:
    roles: list[SampledRole] = []
    for role_spec in template.roles:
        roles.append(
            SampledRole(
                role_id=role_spec.role_id,
                role_type=role_spec.role_type,
                display_name=_resolve_display_name(role_spec, sampled_slots),
                attributes=dict(role_spec.attributes),
            )
        )
    return roles


def _sample_relations(relation_specs: list[RelationSpec]) -> list[SampledRelation]:
    relations: list[SampledRelation] = []
    for relation_spec in relation_specs:
        relations.append(
            SampledRelation(
                relation_id=relation_spec.relation_id,
                source_role=relation_spec.source_role,
                relation_type=relation_spec.relation_type,
                target_role=relation_spec.target_role,
                attributes=dict(relation_spec.attributes),
            )
        )
    return relations


def _sample_latent_states(
    latent_state_specs: list[LatentStateSpec], context: SamplingContext
) -> list[LatentStateAssignment]:
    assignments: list[LatentStateAssignment] = []
    for latent_state_spec in latent_state_specs:
        state_context = context.child(latent_state_spec.state_id)
        assignments.append(
            LatentStateAssignment(
                state_id=latent_state_spec.state_id,
                owner_role=latent_state_spec.owner_role,
                state_type=latent_state_spec.state_type,
                value=state_context.choose(list(latent_state_spec.allowed_values)),
                sampling_strategy=latent_state_spec.sampling_strategy,
            )
        )
    return assignments


def sample_scenario(template: SceneTemplate, context: SamplingContext) -> ScenarioSample:
    """Instantiate a scene template into a deterministic scenario sample."""

    sampled_slots: dict[str, str] = {}
    for slot_spec in sorted(template.slot_specs, key=lambda item: item.slot_id):
        slot_context = context.child("slot:" + slot_spec.slot_id)
        sampled_slots[slot_spec.slot_id] = slot_context.choose(_slot_candidates(slot_spec))

    return ScenarioSample(
        sample_id=f"{template.template_id}:{context.seed}",
        template_id=template.template_id,
        task_id=template.task_id,
        scene_blueprint=template.scene_blueprint,
        sampled_slots=sampled_slots,
        roles=_sample_roles(template, sampled_slots),
        relations=_sample_relations(template.relations),
        latent_state_assignments=_sample_latent_states(
            template.latent_state_specs, context
        ),
        provenance={"seed": context.seed, "sampling_metadata": dict(context.metadata)},
    )
