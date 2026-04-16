from __future__ import annotations

from pathlib import Path

from smdgf.benchmark.taskpack import build_baseline_taskpack, smoke_taskpack_run
from smdgf.export.manifest import ExportRunManifest


def test_baseline_taskpack_smoke_produces_benchmark_run_refs(
    repo_root: Path, tmp_path: Path
) -> None:
    task_pack = build_baseline_taskpack(repo_root)

    smoke_run = smoke_taskpack_run(task_pack, tmp_path)
    export_manifest = ExportRunManifest.read_json(
        Path(smoke_run.export_manifest.artifact_paths["manifest"])
    )

    assert smoke_run.benchmark_manifest.generation_manifest.run_id.endswith(
        "generation-smoke"
    )
    assert smoke_run.benchmark_manifest.qc_report.manifest_path.endswith("report.json")
    assert smoke_run.benchmark_manifest.export_manifest.artifact_paths == (
        export_manifest.artifact_paths
    )
    assert smoke_run.benchmark_manifest.export_manifest.artifact_paths[
        "artifacts_dir"
    ].endswith("artifacts")
    assert smoke_run.benchmark_manifest.metadata["fixture_paths"] == (
        task_pack.fixture_paths()
    )


def test_baseline_taskpack_lists_task_ids_and_fixture_paths(
    repo_root: Path,
) -> None:
    task_pack = build_baseline_taskpack(repo_root)

    assert task_pack.task_ids == [
        "belief-consistency-baseline",
        "social-intent-baseline",
    ]
    assert len(task_pack.fixtures) == 3
    assert task_pack.fixture_paths() == [
        str(repo_root / "tests" / "fixtures" / "task_definition_valid.yaml"),
        str(repo_root / "tests" / "fixtures" / "task_spec_valid.yaml"),
        str(repo_root / "tests" / "fixtures" / "scene_template_valid.yaml"),
    ]
    for fixture_path in task_pack.fixture_paths():
        assert Path(fixture_path).exists()


def test_smoke_taskpack_run_records_tracking_summary(
    repo_root: Path, tmp_path: Path
) -> None:
    task_pack = build_baseline_taskpack(repo_root)

    smoke_run = smoke_taskpack_run(
        task_pack,
        tmp_path,
        config_path="configs/benchmark/local-smoke.yaml",
        revision="test-revision",
        primary_seed=13,
    )

    assert smoke_run.tracking_summary["tracked_run_id"] == smoke_run.benchmark_manifest.run_id
    assert smoke_run.tracking_summary["tracked_status"] == "completed"
    assert smoke_run.tracking_summary["artifact_ref_count"] == 3
    assert smoke_run.tracking_summary["tracked_metrics"] == {
        "accepted_candidates": 2.0,
        "acceptance_rate": 1.0,
        "task_count": 2.0,
    }
    assert smoke_run.tracking_summary["tracked_tags"] == {
        "kind": "smoke",
        "benchmark_id": "social-mind-baseline",
        "labels": "baseline,smoke,local-only",
    }
    assert smoke_run.benchmark_manifest.config_snapshot.config_path == (
        "configs/benchmark/local-smoke.yaml"
    )
    assert smoke_run.benchmark_manifest.code_snapshot.revision == "test-revision"
    assert smoke_run.benchmark_manifest.seed_inventory.generation_seeds == [13, 14]
