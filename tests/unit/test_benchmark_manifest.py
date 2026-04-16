from __future__ import annotations

from pathlib import Path

from smdgf.benchmark import (
    ArtifactReference,
    BenchmarkCodeSnapshot,
    BenchmarkConfigSnapshot,
    BenchmarkRunManifest,
    SeedInventory,
    build_benchmark_layout,
)


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


def test_benchmark_manifest_stitches_generation_qc_and_export_refs(tmp_path: Path) -> None:
    layout = build_benchmark_layout(tmp_path, "bench-run-001")

    generation_ref = _artifact_ref(
        artifact_type="generation",
        run_id="gen-run-001",
        manifest_path=tmp_path / "generation" / "manifest.json",
        artifact_paths={"manifest": str(tmp_path / "generation" / "manifest.json")},
    )
    qc_ref = _artifact_ref(
        artifact_type="qc",
        run_id="qc-run-001",
        manifest_path=tmp_path / "qc" / "report.json",
        artifact_paths={"report": str(tmp_path / "qc" / "report.json")},
    )
    export_ref = _artifact_ref(
        artifact_type="export",
        run_id="exp-run-001",
        manifest_path=tmp_path / "export" / "manifest.json",
        artifact_paths={
            "manifest": str(tmp_path / "export" / "manifest.json"),
            "artifacts_dir": str(tmp_path / "export" / "artifacts"),
        },
    )

    manifest = BenchmarkRunManifest(
        run_id="bench-run-001",
        benchmark_id="social-mind-v1",
        config_snapshot=BenchmarkConfigSnapshot(
            config_path="configs/benchmark.yaml",
            prompt_template_version="prompt-v3",
            values={"provider": "local", "model": "stub-1"},
        ),
        code_snapshot=BenchmarkCodeSnapshot(
            revision="abc1234",
            source_root="src",
        ),
        seed_inventory=SeedInventory(
            primary_seed=7,
            generation_seeds=[7, 11],
            sampler_seeds={"scenario": 17},
        ),
        generation_manifest=generation_ref,
        qc_report=qc_ref,
        export_manifest=export_ref,
        artifact_refs=[generation_ref, qc_ref, export_ref],
        layout=layout,
        tags=["fixture"],
        metrics={"accepted": 1.0},
    )

    assert manifest.generation_manifest.run_id == "gen-run-001"
    assert manifest.qc_report.manifest_path.endswith("report.json")
    assert manifest.export_manifest.artifact_paths["artifacts_dir"].endswith("artifacts")
    assert [ref.artifact_type for ref in manifest.artifact_refs] == [
        "generation",
        "qc",
        "export",
    ]


def test_benchmark_layout_is_deterministic_by_run_id(tmp_path: Path) -> None:
    first = build_benchmark_layout(tmp_path, "bench-run-002")
    second = build_benchmark_layout(tmp_path, "bench-run-002")
    third = build_benchmark_layout(tmp_path, "bench-run-003")

    assert first == second
    assert first.run_dir.endswith("bench-run-002")
    assert first.manifest_path.endswith("bench-run-002/manifest.json")
    assert first != third


def test_benchmark_layout_rejects_unsafe_run_id(tmp_path: Path) -> None:
    try:
        build_benchmark_layout(tmp_path, "../escape")
    except ValueError as exc:
        assert "run_id" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("unsafe run_id should be rejected")

    try:
        build_benchmark_layout(tmp_path, "..")
    except ValueError as exc:
        assert "run_id" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("parent-directory run_id should be rejected")


def test_benchmark_manifest_round_trip_preserves_config_snapshot(tmp_path: Path) -> None:
    layout = build_benchmark_layout(tmp_path, "bench-run-004")
    run_dir = Path(layout.run_dir)
    run_dir.mkdir(parents=True)
    Path(layout.artifacts_dir).mkdir()
    Path(layout.reports_dir).mkdir()

    generation_ref = _artifact_ref(
        artifact_type="generation",
        run_id="gen-run-004",
        manifest_path=tmp_path / "generation-manifest.json",
    )
    qc_ref = _artifact_ref(
        artifact_type="qc",
        run_id="qc-run-004",
        manifest_path=tmp_path / "qc-report.json",
    )
    export_ref = _artifact_ref(
        artifact_type="export",
        run_id="exp-run-004",
        manifest_path=tmp_path / "export-manifest.json",
        artifact_paths={"artifact_paths": str(tmp_path / "export-artifacts")},
    )

    manifest = BenchmarkRunManifest(
        run_id="bench-run-004",
        benchmark_id="social-mind-v1",
        config_snapshot=BenchmarkConfigSnapshot(
            config_path="configs/repro.yaml",
            prompt_template_version="prompt-v4",
            values={"seed": 19, "temperature": 0.0},
        ),
        code_snapshot=BenchmarkCodeSnapshot(revision="def5678"),
        seed_inventory=SeedInventory(primary_seed=19),
        generation_manifest=generation_ref,
        qc_report=qc_ref,
        export_manifest=export_ref,
        artifact_refs=[generation_ref, qc_ref, export_ref],
        layout=layout,
    )

    manifest_path = Path(layout.manifest_path)
    manifest.write_json(manifest_path)
    round_tripped = BenchmarkRunManifest.read_json(manifest_path)

    assert round_tripped.config_snapshot == manifest.config_snapshot
    assert round_tripped.layout == manifest.layout
    assert round_tripped.export_manifest.run_id == "exp-run-004"
