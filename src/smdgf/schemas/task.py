"""Task definition contracts."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from smdgf.schemas.abilities import AbilityCategory


class AnswerMode(str, Enum):
    """Canonical answer modes before export-specific rendering."""

    SINGLE_CHOICE = "single_choice"
    FREE_TEXT = "free_text"
    STRUCTURED = "structured"


class ExportFormat(str, Enum):
    """Output formats that can be rendered from canonical samples."""

    QA = "qa"
    MCQ = "mcq"
    OPEN_QA = "open_qa"


class LatentVariable(BaseModel):
    """A mental-state or scenario variable required by a task."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = ""
    value_type: str = Field(default="string", min_length=1)
    required: bool = True


class TaskDefinition(BaseModel):
    """Defines what a task assesses and which canonical outputs it supports."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_.-]+$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    ability_category: AbilityCategory
    sub_capabilities: list[str] = Field(default_factory=list)
    latent_variables: list[LatentVariable] = Field(default_factory=list)
    answer_mode: AnswerMode
    supported_exports: list[ExportFormat] = Field(default_factory=list)

    @field_validator("supported_exports")
    @classmethod
    def require_supported_exports(
        cls, supported_exports: list[ExportFormat]
    ) -> list[ExportFormat]:
        if not supported_exports:
            raise ValueError("supported_exports must contain at least one format")
        return supported_exports
