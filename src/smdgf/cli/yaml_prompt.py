"""CLI: YAML 契约 → prompt_text（仅拼接与采样，不调模型、不质控、不导出）."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import ValidationError

from smdgf.generation.prompts import build_generation_prompt
from smdgf.samplers import SamplingContext, sample_scenario
from smdgf.schemas.scene import SceneTemplate
from smdgf.schemas.spec import TaskSpecification
from smdgf.schemas.task import TaskDefinition

app = typer.Typer(help="从 YAML 契约组装 prompt_text（到此为止，不接入生成流水线）。")


def _load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(raw)
    if not isinstance(loaded, dict):
        raise typer.BadParameter(f"YAML 必须是 mapping: {path}")
    return loaded


@app.command("assemble-prompt")
def assemble_prompt(
    task_definition: Path = typer.Option(
        ..., "--task-definition", help="task_definition.yaml 路径"
    ),
    task_specification: Path = typer.Option(
        ..., "--task-specification", help="task_specification.yaml 路径"
    ),
    scene_template: Path = typer.Option(
        ..., "--scene-template", help="scene_template.yaml 路径"
    ),
    seed: int = typer.Option(42, "--seed", "-s", help="场景采样种子"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="写入 prompt 文本；默认打印到 stdout"
    ),
) -> None:
    """加载三份 YAML，采样场景，输出 build_generation_prompt 的 prompt_text。"""
    try:
        td = TaskDefinition.model_validate(_load_mapping(task_definition))
        ts = TaskSpecification.model_validate(_load_mapping(task_specification))
        st = SceneTemplate.model_validate(_load_mapping(scene_template))
    except (OSError, yaml.YAMLError, ValidationError, typer.BadParameter) as exc:
        typer.secho(f"加载或校验失败: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc

    if td.task_id != ts.task_id:
        typer.secho(
            f"task_id 不一致: task_definition={td.task_id!r} "
            f"vs task_specification={ts.task_id!r}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    if st.task_id != td.task_id:
        typer.secho(
            f"task_id 不一致: scene_template={st.task_id!r} "
            f"vs task_definition={td.task_id!r}",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    try:
        scenario = sample_scenario(st, SamplingContext(seed=seed))
    except Exception as exc:
        typer.secho(f"场景采样失败: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from exc

    prompt_text, _metadata = build_generation_prompt(td, ts, scenario, seed)

    if output is None:
        typer.echo(prompt_text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(prompt_text, encoding="utf-8")
        typer.secho(f"已写入 {output}", fg=typer.colors.GREEN)
