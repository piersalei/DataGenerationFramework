from pathlib import Path

from typer.testing import CliRunner

from smdgf.cli.main import app


runner = CliRunner()


def fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / name


def test_validate_accepts_valid_task_definition() -> None:
    result = runner.invoke(
        app,
        [
            "contracts",
            "validate",
            str(fixture_path("task_definition_valid.yaml")),
            "--kind",
            "task-definition",
        ],
    )

    assert result.exit_code == 0
    assert "VALID" in result.stdout


def test_validate_rejects_invalid_task_definition() -> None:
    result = runner.invoke(
        app,
        [
            "contracts",
            "validate",
            str(fixture_path("task_definition_invalid.yaml")),
            "--kind",
            "task-definition",
        ],
    )

    assert result.exit_code != 0
    assert "validation" in result.output


def test_validate_accepts_valid_task_spec() -> None:
    result = runner.invoke(
        app,
        [
            "contracts",
            "validate",
            str(fixture_path("task_spec_valid.yaml")),
            "--kind",
            "task-spec",
        ],
    )

    assert result.exit_code == 0
    assert "VALID" in result.stdout


def test_inspect_lists_registered_tasks() -> None:
    result = runner.invoke(app, ["contracts", "inspect"])

    assert result.exit_code == 0
    assert result.stdout == ""
