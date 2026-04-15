"""Deterministic prompt assembly for generation runtime."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Tuple

from smdgf.schemas.scene import ScenarioSample
from smdgf.schemas.spec import QuestionPatternSpec, TaskSpecification
from smdgf.schemas.task import TaskDefinition


def _ordered_role_lines(scenario_sample: ScenarioSample) -> list[str]:
    lines = []
    for role in sorted(scenario_sample.roles, key=lambda item: item.role_id):
        lines.append(
            f"- {role.role_id}: {role.display_name} ({role.role_type}) attributes={json.dumps(role.attributes, sort_keys=True)}"
        )
    return lines


def _ordered_relation_lines(scenario_sample: ScenarioSample) -> list[str]:
    lines = []
    for relation in sorted(
        scenario_sample.relations,
        key=lambda item: (item.source_role, item.relation_type, item.target_role),
    ):
        lines.append(
            f"- {relation.source_role} --{relation.relation_type}--> {relation.target_role}"
        )
    return lines


def _ordered_latent_state_lines(scenario_sample: ScenarioSample) -> list[str]:
    lines = []
    for state in sorted(
        scenario_sample.latent_state_assignments,
        key=lambda item: (item.owner_role, item.state_id),
    ):
        lines.append(
            f"- {state.owner_role}.{state.state_id} ({state.state_type}) = {state.value}"
        )
    return lines


def _ordered_question_lines(task_specification: TaskSpecification) -> list[str]:
    lines = []
    for question in sorted(
        task_specification.question_patterns, key=lambda item: item.question_id
    ):
        question = question  # type: QuestionPatternSpec
        lines.append(
            f"- {question.question_id}: capability={question.target_capability} mode={question.answer_mode.value} template={question.prompt_template}"
        )
    return lines


def build_generation_prompt(
    task_definition: TaskDefinition,
    task_specification: TaskSpecification,
    scenario_sample: ScenarioSample,
    seed: int,
) -> Tuple[str, Dict[str, Any]]:
    """Build deterministic prompt text and replay metadata."""

    prompt_sections = [
        f"Task ID: {task_definition.task_id}",
        f"Task Name: {task_definition.name}",
        f"Ability Category: {task_definition.ability_category.value}",
        f"Description: {task_definition.description}",
        f"Scenario Sample ID: {scenario_sample.sample_id}",
        f"Scenario Blueprint: {scenario_sample.scene_blueprint}",
        "Sampled Slots:",
        json.dumps(scenario_sample.sampled_slots, sort_keys=True, ensure_ascii=True),
        "Roles:",
        "\n".join(_ordered_role_lines(scenario_sample)),
        "Relations:",
        "\n".join(_ordered_relation_lines(scenario_sample)),
        "Latent States:",
        "\n".join(_ordered_latent_state_lines(scenario_sample)),
        "Question Patterns:",
        "\n".join(_ordered_question_lines(task_specification)),
        "Produce a candidate response that matches the task specification and preserves the latent state logic.",
    ]
    prompt_text = "\n\n".join(prompt_sections)

    fingerprint_payload = {
        "task_id": task_definition.task_id,
        "scenario_sample_id": scenario_sample.sample_id,
        "seed": seed,
        "prompt_text": prompt_text,
    }
    prompt_fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    metadata: Dict[str, Any] = {
        "task_id": task_definition.task_id,
        "scenario_sample_id": scenario_sample.sample_id,
        "seed": seed,
        "prompt_fingerprint": prompt_fingerprint,
        "question_ids": [
            question.question_id
            for question in sorted(
                task_specification.question_patterns,
                key=lambda item: item.question_id,
            )
        ],
    }
    return prompt_text, metadata
