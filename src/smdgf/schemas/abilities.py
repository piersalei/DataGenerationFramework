"""Ability taxonomy contracts for social-mind benchmark tasks."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AbilityCategory(str, Enum):
    """Top-level social-mind ability categories supported by the framework."""

    EMOTION = "emotion"
    DESIRE = "desire"
    INTENTION = "intention"
    BELIEF = "belief"
    KNOWLEDGE = "knowledge"
    SOCIAL_RELATION = "social_relation"
    NON_LITERAL = "non_literal"
    SOCIAL_DECISION = "social_decision"
    IMPLICIT_STANCE = "implicit_stance"


class AbilityDescriptor(BaseModel):
    """Human-readable metadata for an ability category or sub-capability."""

    model_config = ConfigDict(extra="forbid")

    category: AbilityCategory
    name: str = Field(min_length=1)
    description: str = ""
    tags: list[str] = Field(default_factory=list)
