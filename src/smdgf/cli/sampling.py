"""CLI commands for deterministic scenario sampling previews."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import ValidationError

from smdgf.samplers import SamplingContext, sample_scenario
from smdgf.schemas import SceneTemplate


app = typer.Typer(no_args_is_help=True)


def _load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        loaded = json.loads(raw)
    else:
        loaded = yaml.safe_load(raw)
    if not isinstance(loaded, dict):
        raise typer.BadParameter("scene template file must contain a mapping/object")
    return loaded


@app.command()
def preview(path: Path, seed: int = typer.Option(..., "--seed")) -> None:
    """Preview a deterministic sampled scenario from a template file."""

    try:
        template = SceneTemplate.model_validate(_load_mapping(path))
        sample = sample_scenario(template, SamplingContext(seed=seed))
    except (
        OSError,
        json.JSONDecodeError,
        yaml.YAMLError,
        ValidationError,
        typer.BadParameter,
    ) as exc:
        typer.echo(f"preview failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(json.dumps(sample.model_dump(), indent=2, sort_keys=True))
