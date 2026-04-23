"""Smoke: yaml assemble-prompt loads fixtures and produces non-empty prompt_text."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from smdgf.cli.main import app

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_yaml_assemble_prompt_fixture_outputs_stable_prefix() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "yaml",
            "assemble-prompt",
            "--task-definition",
            str(FIXTURE_ROOT / "task_definition_valid.yaml"),
            "--task-specification",
            str(FIXTURE_ROOT / "task_spec_valid.yaml"),
            "--scene-template",
            str(FIXTURE_ROOT / "scene_template_valid.yaml"),
            "--seed",
            "7",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Task ID:" in result.stdout
    assert "Scenario Sample ID:" in result.stdout


def test_yaml_assemble_prompt_writes_output_file(tmp_path: Path) -> None:
    out = tmp_path / "p.txt"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "yaml",
            "assemble-prompt",
            "--task-definition",
            str(FIXTURE_ROOT / "task_definition_valid.yaml"),
            "--task-specification",
            str(FIXTURE_ROOT / "task_spec_valid.yaml"),
            "--scene-template",
            str(FIXTURE_ROOT / "scene_template_valid.yaml"),
            "--seed",
            "7",
            "-o",
            str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert len(text) > 50
