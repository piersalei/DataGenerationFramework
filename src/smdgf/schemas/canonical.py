"""Canonical sample contracts independent of export formats."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Union

from pydantic import BaseModel, ConfigDict, Field


class CanonicalQuestion(BaseModel):
    """A normalized question before it is rendered into a target export format."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    target_capability: str = Field(min_length=1)


class CanonicalAnswer(BaseModel):
    """Semantic answer payload for a canonical question."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    value: Union[str, dict[str, Any]]
    rationale: Union[str, None] = None


class ProvenanceRecord(BaseModel):
    """Generation provenance for replay and audit."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(default="manual", min_length=1)
    model_id: Union[str, None] = None
    prompt_id: Union[str, None] = None
    seed: Union[int, None] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CanonicalSample(BaseModel):
    """Export-agnostic sample with latent state and semantic answers."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    scene_text: Union[str, None] = None
    scene_payload: dict[str, Any] = Field(default_factory=dict)
    role_state: dict[str, Any] = Field(default_factory=dict)
    latent_state: dict[str, Any] = Field(default_factory=dict)
    questions: list[CanonicalQuestion] = Field(default_factory=list)
    answers: list[CanonicalAnswer] = Field(default_factory=list)
    provenance: ProvenanceRecord = Field(default_factory=ProvenanceRecord)
