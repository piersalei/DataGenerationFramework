"""Structured task specification contracts."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from smdgf.schemas.task import AnswerMode


class SceneTemplateSpec(BaseModel):
    """Rules for constructing a family of social scenes."""

    model_config = ConfigDict(extra="forbid")

    template_id: str = Field(min_length=1)
    narrative_template: str = Field(min_length=1)
    slots: dict[str, str] = Field(default_factory=dict)
    role_constraints: list[str] = Field(default_factory=list)
    latent_state_requirements: list[str] = Field(default_factory=list)


class QuestionPatternSpec(BaseModel):
    """Question pattern applied to generated scenes."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    prompt_template: str = Field(min_length=1)
    target_capability: str = Field(min_length=1)
    answer_mode: AnswerMode
    options_count: Optional[int] = Field(default=None, ge=2)
    answer_key_required: bool = True


class QualityExpectationSpec(BaseModel):
    """A quality expectation checked before accepting generated data."""

    model_config = ConfigDict(extra="forbid")

    expectation_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Literal["error", "warning"] = "error"
    rule_type: Literal["schema", "logic", "leakage", "diversity", "human_review"]


class TaskSpecification(BaseModel):
    """Structured construction requirements for a task before batch expansion."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    scene_templates: list[SceneTemplateSpec] = Field(default_factory=list)
    question_patterns: list[QuestionPatternSpec] = Field(default_factory=list)
    quality_expectations: list[QualityExpectationSpec] = Field(default_factory=list)
