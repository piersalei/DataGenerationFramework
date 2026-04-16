from pathlib import Path

from smdgf.export.manifest import ExportRunManifest, build_export_layout, write_export_manifest
from smdgf.export.models import ExportRecord


def make_records():
    return [
        ExportRecord(
            export_id="sample-1:q1:qa",
            source_sample_id="sample-1",
            task_id="emotion.typical",
            format="qa",
            split="train",
            context="scene",
            question="How does Mina feel?",
            answer="grateful",
        ),
        ExportRecord(
            export_id="sample-1:q1:mcq",
            source_sample_id="sample-1",
            task_id="emotion.typical",
            format="mcq",
            split="train",
            context="scene",
            question="How does Mina feel?",
            answer="grateful",
        ),
    ]


def test_export_manifest_records_formats_splits_and_paths(tmp_path: Path) -> None:
    manifest = write_export_manifest(
        tmp_path,
        "run-export-1",
        make_records(),
        config_snapshot={"seed": 7},
        source_qc_run_id="qc-run-1",
    )

    assert manifest.run_id == "run-export-1"
    assert manifest.formats == ["mcq", "qa"]
    assert manifest.splits[0].record_count >= 1
    assert manifest.source_qc_run_id == "qc-run-1"
    assert manifest.artifact_paths["manifest"].endswith("manifest.json")


def test_export_layout_groups_artifacts_by_run_id(tmp_path: Path) -> None:
    layout = build_export_layout(tmp_path, "run-export-2")

    assert layout["run_dir"] == tmp_path / "run-export-2"
    assert layout["artifacts_dir"] == tmp_path / "run-export-2" / "artifacts"


def test_manifest_round_trip_preserves_config_snapshot(tmp_path: Path) -> None:
    manifest = write_export_manifest(
        tmp_path,
        "run-export-3",
        make_records(),
        config_snapshot={"seed": 11, "split_policy": "default"},
    )
    loaded = ExportRunManifest.read_json(Path(manifest.artifact_paths["manifest"]))

    assert loaded.run_id == "run-export-3"
    assert loaded.config_snapshot["seed"] == 11
    assert loaded.config_snapshot["split_policy"] == "default"
