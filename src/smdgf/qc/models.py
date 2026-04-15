"""Quality control models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from smdgf.generation.models import GenerationResult
from smdgf.schemas.canonical import CanonicalSample

DecisionLabel = Literal["accept", "reject", "review"]
FindingSeverity = Literal["info", "warning", "error", "critical"]
FindingSource = Literal["rule", "judge", "dedup", "review"]
ReviewOutcome = Literal["keep", "revise", "discard"]
JudgeVerdict = Literal["accept", "review", "reject"]


class QualityFinding(BaseModel):
    """Structured QC finding with auditable evidence."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    source_type: FindingSource = "rule"
    source_id: str = Field(min_length=1)
    severity: FindingSeverity = "error"
    message: str = Field(min_length=1)
    decision_hint: Optional[DecisionLabel] = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    """Normalized output of a deterministic QC rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    passed: bool = True
    findings: list[QualityFinding] = Field(default_factory=list)


class JudgeResult(BaseModel):
    """Normalized output from a soft QC judge or scorer."""

    model_config = ConfigDict(extra="forbid")

    judge_id: str = Field(min_length=1)
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verdict: Optional[JudgeVerdict] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    explanation: Optional[str] = None
    findings: list[QualityFinding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewDisposition(BaseModel):
    """Final human review outcome for a flagged candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    outcome: ReviewOutcome
    reviewer_id: Optional[str] = None
    rationale: Optional[str] = None
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DuplicateCluster(BaseModel):
    """Cluster of duplicate or near-duplicate candidates."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(min_length=1)
    cluster_type: Literal["exact", "near"] = "exact"
    member_ids: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    representative_id: Optional[str] = None


class QualityCandidate(BaseModel):
    """QC-facing wrapper around one canonical sample candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    canonical_sample: CanonicalSample
    generation_result: Optional[GenerationResult] = None
    generation_run_id: Optional[str] = None
    scenario_sample_id: Optional[str] = None
    prompt_fingerprint: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    labels: list[str] = Field(default_factory=list)


class QualityDecision(BaseModel):
    """QC decision with supporting findings and review state."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1)
    status: DecisionLabel
    findings: list[QualityFinding] = Field(default_factory=list)
    applied_rules: list[str] = Field(default_factory=list)
    judge_scores: dict[str, float] = Field(default_factory=dict)
    duplicate_cluster_ids: list[str] = Field(default_factory=list)
    review_required: bool = False
    final_disposition: Optional[ReviewDisposition] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
