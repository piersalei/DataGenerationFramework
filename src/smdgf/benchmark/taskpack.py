"""Baseline task-pack metadata and smoke helpers for benchmark runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from smdgf.benchmark.models import (
    ArtifactReference,
    BenchmarkCodeSnapshot,
    BenchmarkConfigSnapshot,
    BenchmarkRunManifest,
    SeedInventory,
    build_benchmark_layout,
)
from smdgf.benchmark.tracker import LocalRunTracker
from smdgf.export.manifest import ExportRunManifest, write_export_manifest
from smdgf.export.mcq import export_sample_to_mcq
from smdgf.export.models import ExportRecord
from smdgf.export.qa import export_sample_to_open_qa, export_sample_to_qa
from smdgf.generation import GenerationRequest, GenerationResult, GenerationRuntime
from smdgf.generation.models import GenerationRunManifest, GenerationUsage, ProviderConfig
from smdgf.generation.prompts import build_generation_prompt
from smdgf.qc import QualityCandidate, RuleEngine
from smdgf.qc.reports import QualityControlReport, build_qc_report
from smdgf.schemas import (
    AbilityCategory,
    AnswerMode,
    CanonicalAnswer,
    CanonicalQuestion,
    CanonicalSample,
    ExportFormat,
    LatentStateAssignment,
    ProvenanceRecord,
    QualityExpectationSpec,
    QuestionPatternSpec,
    SampledRelation,
    SampledRole,
    ScenarioSample,
    SceneTemplateSpec,
    TaskDefinition,
    TaskSpecification,
)


@dataclass(frozen=True)
class _SmokeBlueprint:
    task_id: str
    ability_category: AbilityCategory
    target_capability: str
    scene_text: str
    scene_blueprint: str
    sampled_slots: dict[str, str]
    roles: list[SampledRole]
    relations: list[SampledRelation]
    latent_state_assignments: list[LatentStateAssignment]
    latent_state: dict[str, Any]
    question_text: str
    answer_value: str
    rationale: str
    distractors: list[str]


class _StaticDistractorStrategy:
    strategy_id = "baseline-static"

    def __init__(self, distractors: list[str]) -> None:
        self._distractors = list(distractors)

    def generate(
        self,
        sample: CanonicalSample,
        question: CanonicalQuestion,
        answer: CanonicalAnswer,
    ) -> list[str]:
        return list(self._distractors)


class _LocalFixtureGenerationProvider:
    """Deterministic local provider used to exercise the real generation runtime."""

    def __init__(self, payloads: dict[str, dict[str, Any]]) -> None:
        self._payloads = payloads

    def generate(
        self,
        request: GenerationRequest,
        config: ProviderConfig,
    ) -> GenerationResult:
        payload = self._payloads[request.task_id]
        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=config.model,
            prompt_text=request.prompt_text,
            prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
            response_text=json.dumps(payload, sort_keys=True),
            status="completed",
            seed=request.seed,
            usage=GenerationUsage(prompt_tokens=32, completion_tokens=12, total_tokens=44),
            raw_response={"payload": payload},
        )


class TaskPackFixture(BaseModel):
    """One repository fixture referenced by a baseline task pack."""

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1)
    fixture_kind: str = Field(min_length=1)
    path: str = Field(min_length=1)
    role: str = Field(min_length=1)


class TaskPack(BaseModel):
    """Explicit internal task-pack metadata used for local smoke runs."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str = Field(min_length=1)
    benchmark_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    task_ids: list[str] = Field(min_length=1)
    fixtures: list[TaskPackFixture] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def fixture_paths(self) -> list[str]:
        """Return deterministic fixture paths for inspection and smoke tests."""

        return [fixture.path for fixture in self.fixtures]


class TaskPackSmokeRun(BaseModel):
    """Result of one fully local smoke run through benchmark packaging."""

    model_config = ConfigDict(extra="forbid")

    task_pack: TaskPack
    generation_manifest: GenerationRunManifest
    qc_report: QualityControlReport
    export_manifest: ExportRunManifest
    benchmark_manifest: BenchmarkRunManifest
    tracking_summary: dict[str, Any] = Field(default_factory=dict)


def build_baseline_taskpack(repo_root: Path) -> TaskPack:
    """Build the default internal task pack from repository fixtures."""

    fixture_root = Path(repo_root) / "tests" / "fixtures"
    task_ids = [
        "belief-consistency-baseline",
        "social-intent-baseline",
    ]
    fixtures = [
        TaskPackFixture(
            task_id=task_ids[0],
            fixture_kind="task-definition",
            path=str(fixture_root / "task_definition_valid.yaml"),
            role="canonical task contract",
        ),
        TaskPackFixture(
            task_id=task_ids[0],
            fixture_kind="task-spec",
            path=str(fixture_root / "task_spec_valid.yaml"),
            role="structured generation and qc expectations",
        ),
        TaskPackFixture(
            task_id=task_ids[1],
            fixture_kind="scene-template",
            path=str(fixture_root / "scene_template_valid.yaml"),
            role="scenario sampling boundary fixture",
        ),
    ]
    return TaskPack(
        pack_id="baseline-social-mind-pack",
        benchmark_id="social-mind-baseline",
        title="Baseline Social Mind Smoke Pack",
        purpose=(
            "Exercise generation, qc, export, and benchmark tracking boundaries "
            "with local fixtures and deterministic metadata."
        ),
        task_ids=task_ids,
        fixtures=fixtures,
        tags=["baseline", "smoke", "local-only"],
        metadata={
            "entrypoint": "smoke_taskpack_run",
            "remote_provider_required": False,
        },
    )


def _smoke_blueprints() -> list[_SmokeBlueprint]:
    return [
        _SmokeBlueprint(
            task_id="belief-consistency-baseline",
            ability_category=AbilityCategory.BELIEF,
            target_capability="belief",
            scene_text=(
                "Mina watches Jun move the notebook into the drawer before leaving the room."
            ),
            scene_blueprint="{observer} watches {actor} move the {object} into the {location}.",
            sampled_slots={
                "observer": "Mina",
                "actor": "Jun",
                "object": "notebook",
                "location": "drawer",
            },
            roles=[
                SampledRole(role_id="observer", role_type="agent", display_name="Mina"),
                SampledRole(role_id="actor", role_type="agent", display_name="Jun"),
            ],
            relations=[
                SampledRelation(
                    relation_id="belief-observes",
                    source_role="observer",
                    relation_type="observes",
                    target_role="actor",
                )
            ],
            latent_state_assignments=[
                LatentStateAssignment(
                    state_id="belief-location",
                    owner_role="observer",
                    state_type="belief",
                    value="drawer",
                    sampling_strategy="choice",
                )
            ],
            latent_state={"Mina": {"belief_location": "drawer"}},
            question_text="Where does Mina think the notebook is now?",
            answer_value="drawer",
            rationale="Mina observed Jun place the notebook in the drawer.",
            distractors=["desk", "backpack", "shelf"],
        ),
        _SmokeBlueprint(
            task_id="social-intent-baseline",
            ability_category=AbilityCategory.INTENTION,
            target_capability="intention",
            scene_text=(
                "Jun quietly reviews Mina's slides so he can help her prepare before the meeting."
            ),
            scene_blueprint="{helper} reviews {target}'s slides before the meeting.",
            sampled_slots={
                "helper": "Jun",
                "target": "Mina",
                "artifact": "slides",
            },
            roles=[
                SampledRole(role_id="helper", role_type="agent", display_name="Jun"),
                SampledRole(role_id="target", role_type="agent", display_name="Mina"),
            ],
            relations=[
                SampledRelation(
                    relation_id="intent-supports",
                    source_role="helper",
                    relation_type="supports",
                    target_role="target",
                )
            ],
            latent_state_assignments=[
                LatentStateAssignment(
                    state_id="help-intent",
                    owner_role="helper",
                    state_type="intention",
                    value="help Mina prepare",
                    sampling_strategy="choice",
                )
            ],
            latent_state={"Jun": {"intent": "help Mina prepare"}},
            question_text="What is Jun trying to do for Mina?",
            answer_value="help Mina prepare",
            rationale="Jun is reviewing Mina's slides to support her preparation.",
            distractors=["embarrass Mina", "ignore the meeting", "leave early"],
        ),
    ]


def _build_task_definition(blueprint: _SmokeBlueprint) -> TaskDefinition:
    return TaskDefinition(
        task_id=blueprint.task_id,
        name=blueprint.task_id.replace("-", " ").title(),
        description=blueprint.scene_text,
        ability_category=blueprint.ability_category,
        sub_capabilities=[blueprint.target_capability],
        latent_variables=[],
        answer_mode=AnswerMode.FREE_TEXT,
        supported_exports=[
            ExportFormat.QA,
            ExportFormat.MCQ,
            ExportFormat.OPEN_QA,
        ],
    )


def _build_task_specification(blueprint: _SmokeBlueprint) -> TaskSpecification:
    return TaskSpecification(
        task_id=blueprint.task_id,
        scene_templates=[
            SceneTemplateSpec(
                template_id=f"{blueprint.task_id}-template",
                narrative_template=blueprint.scene_blueprint,
                slots={key: "string" for key in blueprint.sampled_slots},
                role_constraints=[role.role_id for role in blueprint.roles],
                latent_state_requirements=[
                    assignment.state_id
                    for assignment in blueprint.latent_state_assignments
                ],
            )
        ],
        question_patterns=[
            QuestionPatternSpec(
                question_id=f"{blueprint.task_id}-q1",
                prompt_template=blueprint.question_text,
                target_capability=blueprint.target_capability,
                answer_mode=AnswerMode.FREE_TEXT,
            )
        ],
        quality_expectations=[
            QualityExpectationSpec(
                expectation_id=f"{blueprint.task_id}-qc",
                description="Smoke candidate should preserve latent-state consistency.",
                rule_type="logic",
            )
        ],
    )


def _build_scenario_sample(
    blueprint: _SmokeBlueprint,
    *,
    primary_seed: int,
    offset: int,
) -> ScenarioSample:
    return ScenarioSample(
        sample_id=f"{blueprint.task_id}-scenario",
        template_id=f"{blueprint.task_id}-template",
        task_id=blueprint.task_id,
        scene_blueprint=blueprint.scene_blueprint,
        sampled_slots=dict(blueprint.sampled_slots),
        roles=list(blueprint.roles),
        relations=list(blueprint.relations),
        latent_state_assignments=list(blueprint.latent_state_assignments),
        provenance={"seed": primary_seed + offset},
    )


def _canonical_sample_from_result(
    blueprint: _SmokeBlueprint,
    result: GenerationResult,
    scenario_sample: ScenarioSample,
) -> CanonicalSample:
    payload = json.loads(result.response_text or "{}")
    question_id = f"{blueprint.task_id}-q1"
    return CanonicalSample(
        sample_id=f"{blueprint.task_id}-sample",
        task_id=blueprint.task_id,
        scene_text=payload["scene_text"],
        scene_payload={"sampled_slots": dict(scenario_sample.sampled_slots)},
        role_state={
            role.role_id: {
                "display_name": role.display_name,
                "role_type": role.role_type,
            }
            for role in scenario_sample.roles
        },
        latent_state=payload["latent_state"],
        questions=[
            CanonicalQuestion(
                question_id=question_id,
                text=payload["question_text"],
                target_capability=blueprint.target_capability,
            )
        ],
        answers=[
            CanonicalAnswer(
                question_id=question_id,
                value=payload["answer"],
                rationale=payload["rationale"],
            )
        ],
        provenance=ProvenanceRecord(
            source="local-fixture-runtime",
            model_id=result.model_id,
            prompt_id=result.prompt_fingerprint,
            seed=result.seed,
        ),
    )


def _write_export_records(records: list[ExportRecord], manifest: ExportRunManifest) -> None:
    split_paths = {
        (split.name, split.format): Path(split.path) for split in manifest.splits
    }
    for path in split_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    for record in records:
        path = split_paths[(record.split, record.format)]
        with path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json())
            handle.write("\n")


def smoke_taskpack_run(
    task_pack: TaskPack,
    output_dir: Path,
    *,
    config_path: str = "configs/benchmark/baseline.yaml",
    revision: str = "workspace",
    primary_seed: int = 7,
) -> TaskPackSmokeRun:
    """Assemble a local end-to-end smoke run without remote provider calls."""

    output_root = Path(output_dir)
    generation_dir = output_root / "generation"
    qc_dir = output_root / "qc"
    export_dir = output_root / "export"
    benchmark_dir = output_root / "benchmark"
    tracking_dir = output_root / "tracking"
    for path in (generation_dir, qc_dir, export_dir, benchmark_dir, tracking_dir):
        path.mkdir(parents=True, exist_ok=True)

    generation_manifest_path = generation_dir / "manifest.json"
    provider_config = ProviderConfig(
        provider_id="local-fixture",
        model="fixture-smoke-model",
        mode="local",
        temperature=0.0,
    )
    blueprints = _smoke_blueprints()
    blueprint_map = {blueprint.task_id: blueprint for blueprint in blueprints}
    requests: list[GenerationRequest] = []
    scenarios: dict[str, ScenarioSample] = {}
    provider_payloads: dict[str, dict[str, Any]] = {}

    for offset, blueprint in enumerate(blueprints):
        scenario_sample = _build_scenario_sample(
            blueprint,
            primary_seed=primary_seed,
            offset=offset,
        )
        task_definition = _build_task_definition(blueprint)
        task_specification = _build_task_specification(blueprint)
        prompt_text, prompt_metadata = build_generation_prompt(
            task_definition,
            task_specification,
            scenario_sample,
            primary_seed + offset,
        )
        requests.append(
            GenerationRequest(
                request_id=f"{blueprint.task_id}-request",
                task_id=blueprint.task_id,
                scenario_sample=scenario_sample,
                prompt_text=prompt_text,
                provider=provider_config.provider_id,
                model=provider_config.model,
                seed=primary_seed + offset,
                prompt_metadata=prompt_metadata,
            )
        )
        scenarios[blueprint.task_id] = scenario_sample
        provider_payloads[blueprint.task_id] = {
            "scene_text": blueprint.scene_text,
            "question_text": blueprint.question_text,
            "answer": blueprint.answer_value,
            "rationale": blueprint.rationale,
            "latent_state": blueprint.latent_state,
        }

    runtime = GenerationRuntime(
        provider=_LocalFixtureGenerationProvider(provider_payloads),
        provider_config=provider_config,
        checkpoint_path=generation_manifest_path,
        max_retries=0,
    )
    generation_manifest = runtime.run(
        f"{task_pack.pack_id}-generation-smoke",
        requests,
        resume=False,
    )
    generation_manifest.prompt_template_version = "baseline-smoke-v1"
    generation_manifest.metadata = {
        "fixture_paths": task_pack.fixture_paths(),
        "task_ids": list(task_pack.task_ids),
    }
    generation_manifest.write_json(generation_manifest_path)

    canonical_samples: list[CanonicalSample] = []
    decisions = []
    rule_engine = RuleEngine()
    for item in generation_manifest.items:
        result = item.result
        if result is None:
            raise ValueError(f"generation result missing for {item.request_id}")
        blueprint = blueprint_map[item.task_id]
        canonical_sample = _canonical_sample_from_result(
            blueprint,
            result,
            scenarios[item.task_id],
        )
        canonical_samples.append(canonical_sample)
        decisions.append(
            rule_engine.evaluate(
                QualityCandidate(
                    candidate_id=canonical_sample.sample_id,
                    canonical_sample=canonical_sample,
                    generation_result=result,
                    generation_run_id=generation_manifest.run_id,
                    scenario_sample_id=scenarios[item.task_id].sample_id,
                    prompt_fingerprint=result.prompt_fingerprint,
                    metadata={"latent_expectations": blueprint.latent_state},
                )
            )
        )

    qc_report = build_qc_report(
        f"{task_pack.pack_id}-qc-smoke",
        decisions,
        metadata={
            "source_generation_run_id": generation_manifest.run_id,
            "fixture_paths": task_pack.fixture_paths(),
            "task_ids": task_pack.task_ids,
        },
    )
    qc_report_path = qc_dir / "report.json"
    qc_report.write_json(qc_report_path)

    export_records: list[ExportRecord] = []
    for sample, blueprint in zip(canonical_samples, blueprints):
        export_records.extend(export_sample_to_qa(sample, split="train"))
        export_records.extend(export_sample_to_open_qa(sample, split="train"))
        export_records.extend(
            export_sample_to_mcq(
                sample,
                _StaticDistractorStrategy(blueprint.distractors),
                split="train",
            )
        )

    export_manifest = write_export_manifest(
        export_dir,
        f"{task_pack.pack_id}-export-smoke",
        export_records,
        config_snapshot={
            "task_pack_id": task_pack.pack_id,
            "task_ids": list(task_pack.task_ids),
            "primary_seed": primary_seed,
        },
        source_qc_run_id=qc_report.run_id,
    )
    export_manifest_path = Path(export_manifest.artifact_paths["manifest"])
    _write_export_records(export_records, export_manifest)

    generation_ref = ArtifactReference(
        artifact_type="generation",
        run_id=generation_manifest.run_id,
        manifest_path=str(generation_manifest_path),
        artifact_paths={"manifest": str(generation_manifest_path)},
        metadata={"task_ids": task_pack.task_ids},
    )
    qc_ref = ArtifactReference(
        artifact_type="qc",
        run_id=qc_report.run_id,
        manifest_path=str(qc_report_path),
        artifact_paths={"report": str(qc_report_path)},
        metadata={"accepted": qc_report.metrics.accepted},
    )
    export_ref = ArtifactReference(
        artifact_type="export",
        run_id=export_manifest.run_id,
        manifest_path=str(export_manifest_path),
        artifact_paths=dict(export_manifest.artifact_paths),
        metadata={"formats": export_manifest.formats},
    )

    benchmark_layout = build_benchmark_layout(
        benchmark_dir,
        f"{task_pack.pack_id}-benchmark-smoke",
    )
    Path(benchmark_layout.run_dir).mkdir(parents=True, exist_ok=True)
    Path(benchmark_layout.artifacts_dir).mkdir(parents=True, exist_ok=True)
    Path(benchmark_layout.reports_dir).mkdir(parents=True, exist_ok=True)

    benchmark_manifest = BenchmarkRunManifest(
        run_id=f"{task_pack.pack_id}-benchmark-smoke",
        benchmark_id=task_pack.benchmark_id,
        config_snapshot=BenchmarkConfigSnapshot(
            config_path=config_path,
            prompt_template_version=generation_manifest.prompt_template_version,
            values={
                "task_pack_id": task_pack.pack_id,
                "task_ids": task_pack.task_ids,
                "fixture_paths": task_pack.fixture_paths(),
            },
        ),
        code_snapshot=BenchmarkCodeSnapshot(
            revision=revision,
            source_root="src",
            metadata={"task_pack_id": task_pack.pack_id},
        ),
        seed_inventory=SeedInventory(
            primary_seed=primary_seed,
            generation_seeds=[
                item.seed for item in generation_manifest.items if item.seed is not None
            ],
            sampler_seeds={"baseline": primary_seed},
        ),
        generation_manifest=generation_ref,
        qc_report=qc_ref,
        export_manifest=export_ref,
        artifact_refs=[generation_ref, qc_ref, export_ref],
        layout=benchmark_layout,
        tags=list(task_pack.tags),
        metrics={
            "accepted_candidates": float(qc_report.metrics.accepted),
            "acceptance_rate": qc_report.metrics.acceptance_rate,
            "task_count": float(len(task_pack.task_ids)),
        },
        metadata={
            "task_pack_id": task_pack.pack_id,
            "task_ids": task_pack.task_ids,
            "fixture_paths": task_pack.fixture_paths(),
            "smoke_only": True,
            "pipeline_helpers": [
                "GenerationRuntime",
                "RuleEngine",
                "build_qc_report",
                "export_sample_to_qa",
                "export_sample_to_open_qa",
                "export_sample_to_mcq",
                "write_export_manifest",
            ],
        },
    )
    benchmark_manifest.write_json(Path(benchmark_layout.manifest_path))

    tracker = LocalRunTracker(tracking_dir)
    tracked_run = tracker.track_run(
        benchmark_manifest,
        params={
            "task_pack_id": task_pack.pack_id,
            "task_ids": list(task_pack.task_ids),
            "config_path": config_path,
        },
        metrics=dict(benchmark_manifest.metrics),
        tags={"kind": "smoke", "benchmark_id": task_pack.benchmark_id},
        artifact_refs=benchmark_manifest.artifact_refs,
    )

    return TaskPackSmokeRun(
        task_pack=task_pack,
        generation_manifest=generation_manifest,
        qc_report=qc_report,
        export_manifest=export_manifest,
        benchmark_manifest=benchmark_manifest,
        tracking_summary={
            "tracked_run_id": tracked_run.run_id,
            "tracked_status": tracked_run.status,
            "tracked_params": dict(tracked_run.params),
            "artifact_ref_count": len(tracked_run.artifact_refs),
            "tracked_metrics": dict(tracked_run.metrics),
            "tracked_tags": dict(tracked_run.tags),
        },
    )
