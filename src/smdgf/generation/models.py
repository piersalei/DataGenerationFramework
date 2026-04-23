"""Generation runtime models."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from smdgf.schemas.scene import ScenarioSample


class ProviderConfig(BaseModel):
    """Normalized provider configuration for local or remote backends."""

    model_config = ConfigDict(extra="forbid")

    provider_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    timeout_seconds: float = Field(default=60.0, gt=0)
    mode: Literal["remote", "local"] = "remote"
    extra_options: dict[str, Any] = Field(default_factory=dict)


class GenerationRequest(BaseModel):
    """Framework-owned request model before provider execution."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    scenario_sample: Optional[ScenarioSample] = Field(default=None)
    prompt_text: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    seed: int
    prompt_metadata: dict[str, Any] = Field(default_factory=dict)


class GenerationUsage(BaseModel):
    """Normalized token usage payload."""

    model_config = ConfigDict(extra="forbid")

    prompt_tokens: Optional[int] = Field(default=None, ge=0)
    completion_tokens: Optional[int] = Field(default=None, ge=0)
    total_tokens: Optional[int] = Field(default=None, ge=0)


class GenerationError(BaseModel):
    """Normalized generation error metadata."""

    model_config = ConfigDict(extra="forbid")

    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retriable: bool = False
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class GenerationResult(BaseModel):
    """Normalized provider response."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    prompt_text: str = Field(min_length=1)
    prompt_fingerprint: Optional[str] = None
    response_text: Optional[str] = None
    finish_reason: Optional[str] = None
    status: Literal["completed", "failed"] = "completed"
    seed: Optional[int] = None
    usage: GenerationUsage = Field(default_factory=GenerationUsage)
    error: Optional[GenerationError] = None
    raw_response: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("response_text")
    @classmethod
    def require_response_when_completed(
        cls, response_text: Optional[str], info: Any
    ) -> Optional[str]:
        status = info.data.get("status")
        if status == "completed" and not response_text:
            raise ValueError("response_text is required when status is completed")
        return response_text


class GenerationRunItem(BaseModel):
    """One request tracked inside a generation run."""

    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    scenario_sample_id: str = Field(min_length=1)
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    attempts: int = Field(default=0, ge=0)
    prompt_fingerprint: Optional[str] = None
    seed: Optional[int] = None
    result: Optional[GenerationResult] = None
    error: Optional[GenerationError] = None


class GenerationRunManifest(BaseModel):
    """Structured generation run artifact used for replay and resume."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    provider: ProviderConfig
    prompt_template_version: str = Field(default="v1", min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    items: list[GenerationRunItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def write_json(self, path: Path) -> None:
        """Write a deterministic JSON manifest artifact."""

        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def read_json(cls, path: Path) -> "GenerationRunManifest":
        """Read a manifest artifact without executing custom code."""

        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))
