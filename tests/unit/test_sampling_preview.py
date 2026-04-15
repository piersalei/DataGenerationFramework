import json
from pathlib import Path

from typer.testing import CliRunner

from smdgf.cli.main import app


runner = CliRunner()


def fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / name


def run_preview(seed: int) -> dict[str, object]:
    result = runner.invoke(
        app,
        [
            "sampling",
            "preview",
            str(fixture_path("scene_template_valid.yaml")),
            "--seed",
            str(seed),
        ],
    )
    assert result.exit_code == 0
    return json.loads(result.stdout)


def test_preview_is_reproducible_for_same_seed() -> None:
    first = run_preview(3)
    second = run_preview(3)

    assert first == second


def test_preview_changes_for_different_seeds() -> None:
    first = run_preview(3)
    second = run_preview(11)

    assert first["sampled_slots"] != second["sampled_slots"] or (
        first["latent_state_assignments"][0]["value"]
        != second["latent_state_assignments"][0]["value"]
    )


def test_preview_output_exposes_roles_relations_and_latent_states() -> None:
    payload = run_preview(5)

    assert payload["template_id"] == "relation.support"
    assert "roles" in payload
    assert "relations" in payload
    assert "latent_state_assignments" in payload
    assert payload["relations"][0]["relation_type"] == "supports"
