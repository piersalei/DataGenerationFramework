"""Export manifests and artifact-layout helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field

from smdgf.export.models import ExportRecord, ExportSplit


class ExportRunManifest(BaseModel):
    """Structured manifest for one export run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    formats: list[str] = Field(default_factory=list)
    splits: list[ExportSplit] = Field(default_factory=list)
    config_snapshot: dict = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)
    source_qc_run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def write_json(self, path: Path) -> None:
        """Write a deterministic manifest to disk."""

        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def read_json(cls, path: Path) -> "ExportRunManifest":
        """Read a previously written export manifest."""

        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))


def build_export_layout(base_dir: Path, run_id: str) -> dict[str, Path]:
    """Return deterministic filesystem paths for one export run."""

    run_dir = base_dir / run_id
    return {
        "run_dir": run_dir,
        "manifest": run_dir / "manifest.json",
        "artifacts_dir": run_dir / "artifacts",
    }


def summarize_splits(records: Iterable[ExportRecord], layout: dict[str, Path]) -> list[ExportSplit]:
    """Build split inventory entries from rendered export records."""

    buckets = {}
    for record in records:
        key = (record.split, record.format)
        buckets.setdefault(key, 0)
        buckets[key] += 1

    splits = []
    artifacts_dir = layout["artifacts_dir"]
    for (split_name, fmt), count in sorted(buckets.items()):
        splits.append(
            ExportSplit(
                name=split_name,
                format=fmt,
                path=str(artifacts_dir / f"{fmt}-{split_name}.jsonl"),
                record_count=count,
            )
        )
    return splits


def write_export_manifest(
    base_dir: Path,
    run_id: str,
    records: Iterable[ExportRecord],
    *,
    config_snapshot: Optional[dict] = None,
    source_qc_run_id: Optional[str] = None,
) -> ExportRunManifest:
    """Create and persist a manifest for one export run."""

    records_list = list(records)
    layout = build_export_layout(base_dir, run_id)
    layout["run_dir"].mkdir(parents=True, exist_ok=True)
    layout["artifacts_dir"].mkdir(parents=True, exist_ok=True)

    manifest = ExportRunManifest(
        run_id=run_id,
        formats=sorted({record.format for record in records_list}),
        splits=summarize_splits(records_list, layout),
        config_snapshot=config_snapshot or {},
        artifact_paths={key: str(path) for key, path in layout.items()},
        source_qc_run_id=source_qc_run_id,
    )
    manifest.write_json(layout["manifest"])
    return manifest
