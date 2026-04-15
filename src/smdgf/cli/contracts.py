"""CLI commands for inspecting and validating contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import typer
import yaml
from pydantic import ValidationError

from smdgf.registry import TaskRegistry
from smdgf.schemas.task import TaskDefinition
from smdgf.schemas.spec import TaskSpecification


app = typer.Typer(no_args_is_help=True)


def _load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        loaded = json.loads(raw)
    else:
        loaded = yaml.safe_load(raw)
    if not isinstance(loaded, dict):
        raise typer.BadParameter("contract file must contain a mapping/object")
    return loaded


@app.command()
def inspect() -> None:
    """Print registered task ids and names in deterministic order."""

    registry = TaskRegistry()
    for task in registry.list():
        typer.echo(f"{task.task_id}\t{task.name}")


@app.command()
def validate(
    path: Path,
    kind: Literal["task-definition", "task-spec"] = typer.Option(
        ..., "--kind", help="Contract kind to validate."
    ),
) -> None:
    """Validate a task-definition or task-spec file without executing it."""

    try:
        payload = _load_mapping(path)
        if kind == "task-definition":
            TaskDefinition.model_validate(payload)
        else:
            TaskSpecification.model_validate(payload)
    except (OSError, json.JSONDecodeError, yaml.YAMLError, ValidationError, typer.BadParameter) as exc:
        typer.echo(f"validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("VALID")
