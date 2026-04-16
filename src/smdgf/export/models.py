"""Shared export models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ExportFormatName = Literal["qa", "mcq", "open_qa"]


class ExportOption(BaseModel):
    """One MCQ option emitted by an export renderer."""

    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class ExportRecord(BaseModel):
    """One rendered dataset record derived from a canonical sample."""

    model_config = ConfigDict(extra="forbid")

    export_id: str = Field(min_length=1)
    source_sample_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    format: ExportFormatName
    split: str = Field(default="unsplit", min_length=1)
    context: Optional[str] = None
    question: str = Field(min_length=1)
    answer: Any
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportSplit(BaseModel):
    """Manifest entry for one exported split artifact."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    format: ExportFormatName
    path: str = Field(min_length=1)
    record_count: int = Field(default=0, ge=0)
