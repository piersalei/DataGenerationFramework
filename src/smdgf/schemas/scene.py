"""Scene template and sampled scenario contracts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SlotSpec(BaseModel):
    """Typed slot definition used by a scene template."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    value_type: str = Field(min_length=1)
    description: str = ""
    allowed_values: list[str] = Field(default_factory=list)
    required: bool = True


class RoleSpec(BaseModel):
    """Role declaration inside a reusable scene template."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    role_type: str = Field(min_length=1)
    display_name_source: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    required: bool = True


class RelationSpec(BaseModel):
    """Explicit relation edge between two roles."""

    model_config = ConfigDict(extra="forbid")

    relation_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    source_role: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    target_role: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class LatentStateSpec(BaseModel):
    """Definition of a latent mental-state variable to sample."""

    model_config = ConfigDict(extra="forbid")

    state_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    owner_role: str = Field(min_length=1)
    state_type: str = Field(min_length=1)
    allowed_values: list[str] = Field(default_factory=list)
    sampling_strategy: str = Field(default="choice", min_length=1)
    required: bool = True
    description: str = ""

    @field_validator("allowed_values")
    @classmethod
    def require_allowed_values(cls, allowed_values: list[str]) -> list[str]:
        if not allowed_values:
            raise ValueError("allowed_values must contain at least one value")
        return allowed_values


class SceneConstraint(BaseModel):
    """Declarative scene-level constraint."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    constraint_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class SceneTemplate(BaseModel):
    """Reusable template describing a scenario before sampling."""

    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    task_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    scene_blueprint: str = Field(min_length=1)
    slot_specs: list[SlotSpec] = Field(default_factory=list)
    roles: list[RoleSpec] = Field(default_factory=list)
    relations: list[RelationSpec] = Field(default_factory=list)
    latent_state_specs: list[LatentStateSpec] = Field(default_factory=list)
    constraints: list[SceneConstraint] = Field(default_factory=list)

    @field_validator("slot_specs")
    @classmethod
    def require_typed_slots(cls, slot_specs: list[SlotSpec]) -> list[SlotSpec]:
        if not slot_specs:
            raise ValueError("slot_specs must contain at least one slot")
        return slot_specs

    @model_validator(mode="after")
    def validate_references(self) -> "SceneTemplate":
        """Ensure role and slot references are internally consistent."""

        role_ids = {role.role_id for role in self.roles}
        slot_ids = {slot.slot_id for slot in self.slot_specs}

        for role in self.roles:
            if role.display_name_source.startswith("slot:"):
                slot_id = role.display_name_source.split(":", 1)[1]
                if slot_id not in slot_ids:
                    raise ValueError(
                        f"display_name_source references unknown slot: {slot_id}"
                    )

        for relation in self.relations:
            if relation.source_role not in role_ids:
                raise ValueError(
                    f"relation source_role references unknown role: {relation.source_role}"
                )
            if relation.target_role not in role_ids:
                raise ValueError(
                    f"relation target_role references unknown role: {relation.target_role}"
                )

        for latent_state in self.latent_state_specs:
            if latent_state.owner_role not in role_ids:
                raise ValueError(
                    f"latent_state owner_role references unknown role: {latent_state.owner_role}"
                )

        return self


class SampledRole(BaseModel):
    """Concrete role instance sampled from a role specification."""

    model_config = ConfigDict(extra="forbid")

    role_id: str = Field(min_length=1)
    role_type: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class SampledRelation(BaseModel):
    """Concrete relation edge between sampled roles."""

    model_config = ConfigDict(extra="forbid")

    relation_id: str = Field(min_length=1)
    source_role: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    target_role: str = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)


class LatentStateAssignment(BaseModel):
    """Concrete latent-state value assigned during sampling."""

    model_config = ConfigDict(extra="forbid")

    state_id: str = Field(min_length=1)
    owner_role: str = Field(min_length=1)
    state_type: str = Field(min_length=1)
    value: str = Field(min_length=1)
    sampling_strategy: str = Field(min_length=1)


class ScenarioSample(BaseModel):
    """Sampled scenario container with explicit roles, relations, and latent states."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    scene_blueprint: str = Field(min_length=1)
    sampled_slots: dict[str, str] = Field(default_factory=dict)
    roles: list[SampledRole] = Field(default_factory=list)
    relations: list[SampledRelation] = Field(default_factory=list)
    latent_state_assignments: list[LatentStateAssignment] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
