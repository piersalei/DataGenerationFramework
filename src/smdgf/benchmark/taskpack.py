"""Baseline task-pack metadata and smoke helpers for benchmark runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from smdgf.benchmark.models import (
    ArtifactReference,
    BenchmarkCodeSnapshot,
    BenchmarkConfigSnapshot,
    BenchmarkRunManifest,
    SeedInventory,
    build_benchmark_layout,
)
from smdgf.benchmark.tracker import LocalRunTracker
from smdgf.export.manifest import ExportRunManifest
from smdgf.generation.models import GenerationRunItem, GenerationRunManifest, ProviderConfig
from smdgf.qc.reports import QualityControlReport


class TaskPackFixture(BaseModel):
    """One repository fixture referenced by a baseline task pack."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    fixture_kind: str = Field(min_length=1)
    path: str = Field(min_length=1)
    role: str = Field(min_length=1)


class TaskPack(BaseModel):
    """Explicit internal task-pack metadata used for local smoke runs."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    task_ids: list[str] = Field(min_length=1)
    fixtures: list[TaskPackFixture] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fixture_paths(self) -> list[str]:
        """Return deterministic fixture paths for inspection and smoke tests."""

        return [fixture.path for fixture in self.fixtures]


class TaskPackSmokeRun(BaseModel):
    """Result of one fully local smoke run through benchmark packaging."""

    model_config = ConfigDict(extra="forbid")

    task_pack: TaskPack
    generation_manifest: GenerationRunManifest
    qc_report: QualityControlReport
    export_manifest: ExportRunManifest
    benchmark_manifest: BenchmarkRunManifest
    tracking_summary: dict[str, Any] = Field(default_factory=dict)


def build_baseline_taskpack(repo_root: Path) -> TaskPack:
    """Build the default internal task pack from repository fixtures."""

    fixture_root = Path(repo_root) / "tests" / "fixtures"
    task_ids = [
        "belief-consistency-baseline",
        "social-intent-baseline",
    ]
    fixtures = [
        TaskPackFixture(
            task_id=task_ids[0],
            fixture_kind="task-definition",
            path=str(fixture_root / "task_definition_valid.yaml"),
            role="canonical task contract",
        ),
        TaskPackFixture(
            task_id=task_ids[0],
            fixture_kind="task-spec",
            path=str(fixture_root / "task_spec_valid.yaml"),
            role="structured generation and qc expectations",
        ),
        TaskPackFixture(
            task_id=task_ids[1],
            fixture_kind="scene-template",
            path=str(fixture_root / "scene_template_valid.yaml"),
            role="scenario sampling boundary fixture",
        ),
    ]
    return TaskPack(
        pack_id="baseline-social-mind-pack",
        benchmark_id="social-mind-baseline",
        title="Baseline Social Mind Smoke Pack",
        purpose=(
            "Exercise generation, qc, export, and benchmark tracking boundaries "
            "with local fixtures and deterministic metadata."
        ),
        task_ids=task_ids,
        fixtures=fixtures,
        tags=["baseline", "smoke", "local-only"],
        metadata={
            "entrypoint": "smoke_taskpack_run",
            "remote_provider_required": False,
        },
    )


def smoke_taskpack_run(
    task_pack: TaskPack,
    output_dir: Path,
    *,
    config_path: str = "configs/benchmark/baseline.yaml",
    revision: str = "workspace",
    primary_seed: int = 7,
) -> TaskPackSmokeRun:
    """Assemble a local end-to-end smoke run without remote provider calls."""

    output_root = Path(output_dir)
    generation_dir = output_root / "generation"
    qc_dir = output_root / "qc"
    export_dir = output_root / "export"
    benchmark_dir = output_root / "benchmark"
    tracking_dir = output_root / "tracking"
    for path in (generation_dir, qc_dir, export_dir, benchmark_dir, tracking_dir):
        path.mkdir(parents=True, exist_ok=True)

    generation_manifest = GenerationRunManifest(
        run_id=f"{task_pack.pack_id}-generation-smoke",
        provider=ProviderConfig(
            provider_id="local-fixture",
            model="fixture-smoke-model",
            mode="local",
            temperature=0.0,
        ),
        prompt_template_version="baseline-smoke-v1",
        items=[
            GenerationRunItem(
                request_id=f"{task_id}-request",
                task_id=task_id,
                scenario_sample_id=f"{task_id}-scenario",
                status="completed",
                attempts=1,
                prompt_fingerprint=f"{task_id}-prompt",
                seed=primary_seed + offset,
            )
            for offset, task_id in enumerate(task_pack.task_ids)
        ],
        metadata={"fixture_paths": task_pack.fixture_paths()},
    )
    generation_manifest_path = generation_dir / "manifest.json"
    generation_manifest.write_json(generation_manifest_path)

    qc_report = QualityControlReport(
        run_id=f"{task_pack.pack_id}-qc-smoke",
        metadata={
            "source_generation_run_id": generation_manifest.run_id,
            "fixture_paths": task_pack.fixture_paths(),
            "task_ids": task_pack.task_ids,
        },
    )
    qc_report.metrics.total_candidates = len(task_pack.task_ids)
    qc_report.metrics.accepted = len(task_pack.task_ids)
    qc_report.metrics.acceptance_rate = 1.0
    qc_report_path = qc_dir / "report.json"
    qc_report.write_json(qc_report_path)

    export_manifest = ExportRunManifest(
        run_id=f"{task_pack.pack_id}-export-smoke",
        formats=["qa", "mcq", "open_qa"],
        config_snapshot={
            "task_pack_id": task_pack.pack_id,
            "task_ids": task_pack.task_ids,
            "primary_seed": primary_seed,
        },
        artifact_paths={
            "manifest": str(export_dir / "manifest.json"),
            "artifacts_dir": str(export_dir / "artifacts"),
            "package_dir": str(export_dir / "package"),
        },
        source_qc_run_id=qc_report.run_id,
    )
    Path(export_manifest.artifact_paths["artifacts_dir"]).mkdir(parents=True, exist_ok=True)
    Path(export_manifest.artifact_paths["package_dir"]).mkdir(parents=True, exist_ok=True)
    export_manifest_path = export_dir / "manifest.json"
    export_manifest.write_json(export_manifest_path)

    generation_ref = ArtifactReference(
        artifact_type="generation",
        run_id=generation_manifest.run_id,
        manifest_path=str(generation_manifest_path),
        artifact_paths={"manifest": str(generation_manifest_path)},
        metadata={"task_ids": task_pack.task_ids},
    )
    qc_ref = ArtifactReference(
        artifact_type="qc",
        run_id=qc_report.run_id,
        manifest_path=str(qc_report_path),
        artifact_paths={"report": str(qc_report_path)},
        metadata={"accepted": qc_report.metrics.accepted},
    )
    export_ref = ArtifactReference(
        artifact_type="export",
        run_id=export_manifest.run_id,
        manifest_path=str(export_manifest_path),
        artifact_paths=dict(export_manifest.artifact_paths),
        metadata={"formats": export_manifest.formats},
    )

    benchmark_layout = build_benchmark_layout(
        benchmark_dir,
        f"{task_pack.pack_id}-benchmark-smoke",
    )
    Path(benchmark_layout.run_dir).mkdir(parents=True, exist_ok=True)
    Path(benchmark_layout.artifacts_dir).mkdir(parents=True, exist_ok=True)
    Path(benchmark_layout.reports_dir).mkdir(parents=True, exist_ok=True)

    benchmark_manifest = BenchmarkRunManifest(
        run_id=f"{task_pack.pack_id}-benchmark-smoke",
        benchmark_id=task_pack.benchmark_id,
        config_snapshot=BenchmarkConfigSnapshot(
            config_path=config_path,
            prompt_template_version=generation_manifest.prompt_template_version,
            values={
                "task_pack_id": task_pack.pack_id,
                "task_ids": task_pack.task_ids,
                "fixture_paths": task_pack.fixture_paths(),
            },
        ),
        code_snapshot=BenchmarkCodeSnapshot(
            revision=revision,
            source_root="src",
            metadata={"task_pack_id": task_pack.pack_id},
        ),
        seed_inventory=SeedInventory(
            primary_seed=primary_seed,
            generation_seeds=[
                item.seed for item in generation_manifest.items if item.seed is not None
            ],
            sampler_seeds={"baseline": primary_seed},
        ),
        generation_manifest=generation_ref,
        qc_report=qc_ref,
        export_manifest=export_ref,
        artifact_refs=[generation_ref, qc_ref, export_ref],
        layout=benchmark_layout,
        tags=list(task_pack.tags),
        metrics={
            "accepted_candidates": float(qc_report.metrics.accepted),
            "acceptance_rate": qc_report.metrics.acceptance_rate,
            "task_count": float(len(task_pack.task_ids)),
        },
        metadata={
            "task_pack_id": task_pack.pack_id,
            "task_ids": task_pack.task_ids,
            "fixture_paths": task_pack.fixture_paths(),
            "smoke_only": True,
        },
    )
    benchmark_manifest.write_json(Path(benchmark_layout.manifest_path))

    tracker = LocalRunTracker(tracking_dir)
    tracked_run = tracker.track_run(
        benchmark_manifest,
        params={
            "task_pack_id": task_pack.pack_id,
            "task_ids": list(task_pack.task_ids),
            "config_path": config_path,
        },
        metrics=dict(benchmark_manifest.metrics),
        tags={"kind": "smoke", "benchmark_id": task_pack.benchmark_id},
        artifact_refs=benchmark_manifest.artifact_refs,
    )

    return TaskPackSmokeRun(
        task_pack=task_pack,
        generation_manifest=generation_manifest,
        qc_report=qc_report,
        export_manifest=export_manifest,
        benchmark_manifest=benchmark_manifest,
        tracking_summary={
            "tracked_run_id": tracked_run.run_id,
            "tracked_status": tracked_run.status,
            "tracked_params": dict(tracked_run.params),
            "artifact_ref_count": len(tracked_run.artifact_refs),
            "tracked_metrics": dict(tracked_run.metrics),
            "tracked_tags": dict(tracked_run.tags),
        },
    )
