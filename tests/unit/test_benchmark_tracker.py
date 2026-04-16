from __future__ import annotations

from pathlib import Path

from smdgf.benchmark import (
    ArtifactReference,
    BenchmarkCodeSnapshot,
    BenchmarkConfigSnapshot,
    BenchmarkRunManifest,
    LocalRunTracker,
    SeedInventory,
    build_benchmark_layout,
    compare_runs,
)


class _FailingAdapter:
    def record_run(self, tracked_run: object) -> None:
        raise RuntimeError("adapter offline")


def _artifact_ref(
    *,
    artifact_type: str,
    run_id: str,
    manifest_path: Path,
    artifact_paths: dict[str, str] | None = None,
) -> ArtifactReference:
    return ArtifactReference(
        artifact_type=artifact_type,
        run_id=run_id,
        manifest_path=str(manifest_path),
        artifact_paths=artifact_paths or {"manifest": str(manifest_path)},
    )


def _manifest(
    tmp_path: Path,
    *,
    run_id: str,
    benchmark_id: str = "social-mind-v1",
    tags: list[str] | None = None,
    metrics: dict[str, float] | None = None,
) -> BenchmarkRunManifest:
    layout = build_benchmark_layout(tmp_path / "benchmark-runs", run_id)
    generation_ref = _artifact_ref(
        artifact_type="generation",
        run_id=f"{run_id}-gen",
        manifest_path=tmp_path / f"{run_id}-generation.json",
    )
    qc_ref = _artifact_ref(
        artifact_type="qc",
        run_id=f"{run_id}-qc",
        manifest_path=tmp_path / f"{run_id}-qc.json",
    )
    export_ref = _artifact_ref(
        artifact_type="export",
        run_id=f"{run_id}-export",
        manifest_path=tmp_path / f"{run_id}-export.json",
        artifact_paths={
            "manifest": str(tmp_path / f"{run_id}-export.json"),
            "artifacts_dir": str(tmp_path / f"{run_id}-artifacts"),
        },
    )
    return BenchmarkRunManifest(
        run_id=run_id,
        benchmark_id=benchmark_id,
        config_snapshot=BenchmarkConfigSnapshot(
            config_path="configs/repro.yaml",
            prompt_template_version="prompt-v1",
            values={"provider": "local", "temperature": 0.0},
        ),
        code_snapshot=BenchmarkCodeSnapshot(revision="abc1234"),
        seed_inventory=SeedInventory(primary_seed=7),
        generation_manifest=generation_ref,
        qc_report=qc_ref,
        export_manifest=export_ref,
        artifact_refs=[generation_ref, qc_ref, export_ref],
        layout=layout,
        tags=tags or ["fixture"],
        metrics=metrics or {"accepted_rate": 0.75},
    )


def test_local_tracker_records_params_metrics_and_artifacts(tmp_path: Path) -> None:
    tracker = LocalRunTracker(tmp_path / "tracking")
    manifest = _manifest(
        tmp_path,
        run_id="bench-run-001",
        metrics={"accepted_rate": 0.8, "review_queue": 2.0},
    )

    tracked_run = tracker.track_run(
        manifest,
        params={"provider": "local", "seed": 7},
        tags={"stage": "baseline"},
    )

    persisted = tracker.get_run("bench-run-001")

    assert tracked_run == persisted
    assert persisted.params == {"provider": "local", "seed": 7}
    assert persisted.metrics == {"accepted_rate": 0.8, "review_queue": 2.0}
    assert persisted.tags == {"stage": "baseline", "labels": "fixture"}
    assert len(persisted.artifact_refs) == 3
    assert persisted.artifact_refs[2].artifact_paths["artifacts_dir"].endswith(
        "bench-run-001-artifacts"
    )


def test_compare_runs_surfaces_metric_deltas(tmp_path: Path) -> None:
    tracker = LocalRunTracker(tmp_path / "tracking")
    baseline = tracker.track_run(
        _manifest(
            tmp_path,
            run_id="bench-run-010",
            tags=["baseline"],
            metrics={"accepted_rate": 0.7, "review_queue": 3.0},
        ),
        tags={"stage": "baseline"},
    )
    candidate = tracker.track_run(
        _manifest(
            tmp_path,
            run_id="bench-run-011",
            tags=["candidate"],
            metrics={"accepted_rate": 0.9, "review_queue": 1.0},
        ),
        tags={"stage": "candidate"},
    )

    comparison = compare_runs(baseline, candidate)

    assert comparison.baseline_run_id == "bench-run-010"
    assert comparison.candidate_run_id == "bench-run-011"
    assert comparison.metric_deltas == {
        "accepted_rate": 0.2,
        "review_queue": -2.0,
    }
    assert comparison.changed_tags == {
        "labels": ("baseline", "candidate"),
        "stage": ("baseline", "candidate"),
    }
    assert comparison.artifact_ref_delta == 0


def test_tracker_round_trip_preserves_tags(tmp_path: Path) -> None:
    tracker = LocalRunTracker(tmp_path / "tracking")
    manifest = _manifest(
        tmp_path,
        run_id="bench-run-020",
        tags=["nightly", "smoke"],
    )

    tracker.track_run(
        manifest,
        tags={"owner": "research", "priority": "high"},
    )

    loaded = tracker.list_runs()[0]

    assert loaded.run_id == "bench-run-020"
    assert loaded.tags == {
        "owner": "research",
        "priority": "high",
        "labels": "nightly,smoke",
    }


def test_tracker_records_adapter_errors_without_failing_local_persistence(
    tmp_path: Path,
) -> None:
    tracker = LocalRunTracker(
        tmp_path / "tracking",
        adapters=[_FailingAdapter()],
    )
    manifest = _manifest(tmp_path, run_id="bench-run-030")

    tracked_run = tracker.track_run(manifest)
    persisted = tracker.get_run("bench-run-030")

    assert tracked_run.adapter_metadata["adapter_count"] == 1
    assert tracked_run.adapter_metadata["adapter_errors"] == [
        {"adapter": "_FailingAdapter", "error": "adapter offline"}
    ]
    assert persisted.adapter_metadata == tracked_run.adapter_metadata


def test_tracker_rejects_unsafe_run_id(tmp_path: Path) -> None:
    tracker = LocalRunTracker(tmp_path / "tracking")
    manifest = _manifest(tmp_path, run_id="bench-run-031").model_copy(
        update={"run_id": "nested/run"}
    )

    try:
        tracker.track_run(manifest)
    except ValueError as exc:
        assert "run_id" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("unsafe run_id should be rejected")
