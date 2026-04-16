"""Benchmark-run manifests and deterministic artifact layout helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ArtifactReference(BaseModel):
    """Reference a manifest and its artifact paths without embedding payloads."""

    model_config = ConfigDict(extra="forbid")

    artifact_type: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkConfigSnapshot(BaseModel):
    """Structured config snapshot used to replay a benchmark run."""

    model_config = ConfigDict(extra="forbid")

    config_path: Optional[str] = None
    prompt_template_version: Optional[str] = None
    values: dict[str, Any] = Field(default_factory=dict)


class BenchmarkCodeSnapshot(BaseModel):
    """Minimal code provenance needed to reconstruct one run."""

    model_config = ConfigDict(extra="forbid")

    revision: str = Field(min_length=1)
    dirty: bool = False
    source_root: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SeedInventory(BaseModel):
    """Track all seed inputs that shaped a benchmark run."""

    model_config = ConfigDict(extra="forbid")

    primary_seed: int
    generation_seeds: list[int] = Field(default_factory=list)
    sampler_seeds: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkLayout(BaseModel):
    """Deterministic benchmark-run layout for local artifact tracking."""

    model_config = ConfigDict(extra="forbid")

    run_dir: str = Field(min_length=1)
    manifest_path: str = Field(min_length=1)
    artifacts_dir: str = Field(min_length=1)
    reports_dir: str = Field(min_length=1)


class BenchmarkRunManifest(BaseModel):
    """Top-level benchmark run contract stitching prior phase artifacts together."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    config_snapshot: BenchmarkConfigSnapshot = Field(
        default_factory=BenchmarkConfigSnapshot
    )
    code_snapshot: BenchmarkCodeSnapshot
    seed_inventory: SeedInventory
    generation_manifest: ArtifactReference
    qc_report: ArtifactReference
    export_manifest: ArtifactReference
    artifact_refs: list[ArtifactReference] = Field(default_factory=list)
    layout: BenchmarkLayout
    tags: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def write_json(self, path: Path) -> None:
        """Persist a deterministic benchmark manifest to disk."""

        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def read_json(cls, path: Path) -> "BenchmarkRunManifest":
        """Load a previously written benchmark manifest."""

        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))


def build_benchmark_layout(base_dir: Path, run_id: str) -> BenchmarkLayout:
    """Return deterministic filesystem paths for one benchmark run."""

    run_dir = base_dir / run_id
    return BenchmarkLayout(
        run_dir=str(run_dir),
        manifest_path=str(run_dir / "manifest.json"),
        artifacts_dir=str(run_dir / "artifacts"),
        reports_dir=str(run_dir / "reports"),
    )
