# Social Mind Data Generation Framework

This repository is a Python framework for building social-mind benchmark datasets in a reproducible, pipeline-oriented way.

Current status:

- Phase 1-6 are implemented and verified.
- The codebase supports contracts, scenario sampling, generation runtime, QC, export, benchmark packaging, and local run tracking.
- The public CLI is still small.
- The full pipeline is available primarily through the Python API.

## What The Project Can Do Today

The repository can already support this workflow:

1. Define task contracts and task specifications.
2. Define reusable scene templates with roles, relations, and latent states.
3. Sample deterministic scenarios from seeds.
4. Build prompts and run generation jobs through a provider-agnostic runtime.
5. Apply QC rules and produce QC reports.
6. Export canonical samples to `qa`, `mcq`, and `open_qa`.
7. Package generation, QC, and export artifacts into a benchmark run manifest.
8. Track benchmark runs locally and compare them later.
9. Run a built-in baseline smoke flow that exercises the end-to-end local pipeline.

## What The Public CLI Covers Right Now

The installed `smdgf` CLI currently exposes:

- `smdgf contracts inspect`
- `smdgf contracts validate`
- `smdgf sampling preview`

Generation, QC, export, benchmark packaging, and tracking are implemented as Python modules, not as first-class CLI commands yet.

## Requirements

- Python `>=3.11`
- Recommended: a virtual environment

Install from the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

After that, the `smdgf` command should be available in the active environment.

If you do not want to install the package yet, use:

```bash
PYTHONPATH=src python3 -m smdgf.cli.main --help
```

Run the test suite:

```bash
pytest -q
```

## Repository Map

Main modules:

- `src/smdgf/schemas/`: typed contracts for tasks, scenes, specs, and canonical samples
- `src/smdgf/samplers/`: deterministic sampling helpers
- `src/smdgf/generation/`: provider abstraction, prompt assembly, runtime, and manifests
- `src/smdgf/qc/`: QC models, rules, judges, dedup, and reports
- `src/smdgf/export/`: QA/MCQ/open-QA exporters and export manifests
- `src/smdgf/benchmark/`: benchmark manifests, tracking, and baseline smoke task pack
- `src/smdgf/cli/`: current CLI surface

Useful fixtures:

- `tests/fixtures/task_definition_valid.yaml`
- `tests/fixtures/task_spec_valid.yaml`
- `tests/fixtures/scene_template_valid.yaml`

## Quick Start

### 1. Validate Contracts From The CLI

Validate a task definition:

```bash
smdgf contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
```

Without installation:

```bash
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
```

Validate a task specification:

```bash
smdgf contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
```

Without installation:

```bash
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
```

Preview a deterministic sampled scenario:

```bash
smdgf sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

Without installation:

```bash
PYTHONPATH=src python3 -m smdgf.cli.main sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

### 2. Run The Built-In End-To-End Smoke Flow

If you want the shortest complete example, use the built-in baseline task pack:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from smdgf.benchmark.taskpack import build_baseline_taskpack, smoke_taskpack_run

repo_root = Path(".").resolve()
task_pack = build_baseline_taskpack(repo_root)

with TemporaryDirectory() as tmp:
    run = smoke_taskpack_run(task_pack, Path(tmp))

    print("benchmark_run_id:", run.benchmark_manifest.run_id)
    print("export_formats:", run.export_manifest.formats)
    print("tracking_summary:", run.tracking_summary)
```

What this smoke flow actually exercises:

- `GenerationRuntime`
- prompt assembly
- QC rule evaluation and `build_qc_report()`
- `export_sample_to_qa()`
- `export_sample_to_open_qa()`
- `export_sample_to_mcq()`
- `write_export_manifest()`
- benchmark manifest packaging
- `LocalRunTracker`

This is the best reference integration path in the repository today.

## Complete Usage Guide

This section shows how to use the framework as composable building blocks.

### Step 1. Load And Validate Structured Contracts

You can validate from files:

```python
from pathlib import Path
import yaml

from smdgf.schemas import TaskDefinition, TaskSpecification, SceneTemplate

task_definition = TaskDefinition.model_validate(
    yaml.safe_load(Path("tests/fixtures/task_definition_valid.yaml").read_text())
)
task_specification = TaskSpecification.model_validate(
    yaml.safe_load(Path("tests/fixtures/task_spec_valid.yaml").read_text())
)
scene_template = SceneTemplate.model_validate(
    yaml.safe_load(Path("tests/fixtures/scene_template_valid.yaml").read_text())
)
```

You can also register task definitions in memory:

```python
from smdgf.registry import TaskRegistry

registry = TaskRegistry()
registry.register(task_definition)
print([task.task_id for task in registry.list()])
```

Important note:

- `TaskRegistry` is currently in-memory only.
- There is no persistent task catalog backend yet.

### Step 2. Sample A Scenario Deterministically

```python
from smdgf.samplers import SamplingContext, sample_scenario

context = SamplingContext(seed=17)
scenario_sample = sample_scenario(scene_template, context)

print(scenario_sample.sample_id)
print(scenario_sample.sampled_slots)
print(scenario_sample.latent_state_assignments)
```

This gives you:

- sampled slots
- sampled roles
- sampled relations
- sampled latent state assignments
- provenance with the seed

### Step 3. Build A Prompt

```python
from smdgf.generation.prompts import build_generation_prompt

prompt_text, prompt_metadata = build_generation_prompt(
    task_definition,
    task_specification,
    scenario_sample,
    seed=17,
)

print(prompt_text)
print(prompt_metadata)
```

The prompt metadata includes:

- `task_id`
- `scenario_sample_id`
- `seed`
- `question_ids`
- `prompt_fingerprint`

### Step 4. Run Generation Through The Runtime

The framework provides a provider-agnostic generation runtime. You can plug in LiteLLM or your own provider implementation.

Minimal local stub example:

```python
from pathlib import Path

from smdgf.generation import (
    GenerationRequest,
    GenerationResult,
    GenerationRuntime,
    GenerationUsage,
    ProviderConfig,
)


class LocalStubProvider:
    def generate(self, request: GenerationRequest, config: ProviderConfig) -> GenerationResult:
        return GenerationResult(
            request_id=request.request_id,
            provider_id=config.provider_id,
            model_id=config.model,
            prompt_text=request.prompt_text,
            prompt_fingerprint=request.prompt_metadata.get("prompt_fingerprint"),
            response_text='{"answer": "grateful"}',
            status="completed",
            seed=request.seed,
            usage=GenerationUsage(prompt_tokens=10, completion_tokens=4, total_tokens=14),
        )


provider_config = ProviderConfig(
    provider_id="local-stub",
    model="fixture-smoke-model",
    mode="local",
    temperature=0.0,
)

request = GenerationRequest(
    request_id="req-1",
    task_id=task_definition.task_id,
    scenario_sample=scenario_sample,
    prompt_text=prompt_text,
    provider=provider_config.provider_id,
    model=provider_config.model,
    seed=17,
    prompt_metadata=prompt_metadata,
)

runtime = GenerationRuntime(
    provider=LocalStubProvider(),
    provider_config=provider_config,
    checkpoint_path=Path("runs/generation/manifest.json"),
    max_retries=0,
)

generation_manifest = runtime.run("demo-generation-run", [request], resume=False)
generation_item = generation_manifest.items[0]
print(generation_item.status)
print(generation_item.result.response_text)
```

What the runtime already supports:

- checkpointed manifests
- resumable runs
- retry handling
- provider/model/prompt provenance

### Step 5. Convert Generation Output Into A Canonical Sample

This framework deliberately separates generation from canonical-sample construction.

That means:

- the runtime gives you generated outputs and provenance
- your task logic decides how to convert model output into a `CanonicalSample`

Minimal example:

```python
from smdgf.schemas import CanonicalAnswer, CanonicalQuestion, CanonicalSample, ProvenanceRecord

canonical_sample = CanonicalSample(
    sample_id="sample-1",
    task_id=task_definition.task_id,
    scene_text="Mina receives unexpected help before a presentation.",
    latent_state={"Mina": {"emotion": "grateful"}},
    questions=[
        CanonicalQuestion(
            question_id="q1",
            text="How does Mina feel?",
            target_capability="emotion",
        )
    ],
    answers=[
        CanonicalAnswer(
            question_id="q1",
            value="grateful",
            rationale="The help reduces pressure before the presentation.",
        )
    ],
    provenance=ProvenanceRecord(
        source="demo",
        model_id=generation_item.result.model_id,
        prompt_id=generation_item.result.prompt_fingerprint,
        seed=generation_item.result.seed,
    ),
)
```

Important note:

- there is no generic public “generation result -> canonical sample” adapter yet
- the built-in smoke task pack contains the best reference implementation for this handoff

### Step 6. Run QC

Basic QC is rule-driven and works on canonical samples:

```python
from smdgf.qc import QualityCandidate, RuleEngine
from smdgf.qc.reports import build_qc_report

candidate = QualityCandidate(
    candidate_id=canonical_sample.sample_id,
    canonical_sample=canonical_sample,
    generation_result=generation_item.result,
    generation_run_id=generation_manifest.run_id,
    scenario_sample_id=scenario_sample.sample_id,
    prompt_fingerprint=generation_item.result.prompt_fingerprint,
)

decision = RuleEngine().evaluate(candidate)
qc_report = build_qc_report(
    "demo-qc-run",
    [decision],
    metadata={"source_generation_run_id": generation_manifest.run_id},
)

qc_report.write_json(Path("runs/qc/report.json"))
print(decision.status)
print(qc_report.metrics.model_dump())
```

QC currently includes:

- structural validation
- deterministic rules
- judge hooks
- duplicate and near-duplicate support
- review queue and rejection manifest generation

### Step 7. Export Approved Canonical Samples

QA and open-QA exports:

```python
from smdgf.export.qa import export_sample_to_open_qa, export_sample_to_qa

qa_records = export_sample_to_qa(canonical_sample, split="train")
open_qa_records = export_sample_to_open_qa(canonical_sample, split="train")
```

MCQ export needs a distractor strategy:

```python
from smdgf.export.mcq import export_sample_to_mcq


class StaticDistractorStrategy:
    strategy_id = "static"

    def generate(self, sample, question, answer):
        return ["relieved", "embarrassed", "angry"]


mcq_records = export_sample_to_mcq(
    canonical_sample,
    StaticDistractorStrategy(),
    split="train",
)
```

Write an export manifest:

```python
from smdgf.export.manifest import write_export_manifest

all_records = []
all_records.extend(qa_records)
all_records.extend(open_qa_records)
all_records.extend(mcq_records)

export_manifest = write_export_manifest(
    Path("runs/export"),
    "demo-export-run",
    all_records,
    config_snapshot={"seed": 17},
    source_qc_run_id=qc_report.run_id,
)

print(export_manifest.formats)
print(export_manifest.artifact_paths)
```

### Step 8. Package A Benchmark Run

After generation, QC, and export exist, package them into one benchmark manifest:

```python
from pathlib import Path

from smdgf.benchmark.models import (
    ArtifactReference,
    BenchmarkCodeSnapshot,
    BenchmarkConfigSnapshot,
    BenchmarkRunManifest,
    SeedInventory,
    build_benchmark_layout,
)

benchmark_layout = build_benchmark_layout(Path("runs/benchmark"), "demo-benchmark-run")
Path(benchmark_layout.run_dir).mkdir(parents=True, exist_ok=True)
Path(benchmark_layout.artifacts_dir).mkdir(parents=True, exist_ok=True)
Path(benchmark_layout.reports_dir).mkdir(parents=True, exist_ok=True)

generation_ref = ArtifactReference(
    artifact_type="generation",
    run_id=generation_manifest.run_id,
    manifest_path="runs/generation/manifest.json",
    artifact_paths={"manifest": "runs/generation/manifest.json"},
)
qc_ref = ArtifactReference(
    artifact_type="qc",
    run_id=qc_report.run_id,
    manifest_path="runs/qc/report.json",
    artifact_paths={"report": "runs/qc/report.json"},
)
export_ref = ArtifactReference(
    artifact_type="export",
    run_id=export_manifest.run_id,
    manifest_path=export_manifest.artifact_paths["manifest"],
    artifact_paths=dict(export_manifest.artifact_paths),
)

benchmark_manifest = BenchmarkRunManifest(
    run_id="demo-benchmark-run",
    benchmark_id="demo-benchmark",
    config_snapshot=BenchmarkConfigSnapshot(
        config_path="configs/demo.yaml",
        prompt_template_version=generation_manifest.prompt_template_version,
        values={"seed": 17},
    ),
    code_snapshot=BenchmarkCodeSnapshot(
        revision="workspace",
        source_root="src",
    ),
    seed_inventory=SeedInventory(
        primary_seed=17,
        generation_seeds=[17],
        sampler_seeds={"scenario": 17},
    ),
    generation_manifest=generation_ref,
    qc_report=qc_ref,
    export_manifest=export_ref,
    artifact_refs=[generation_ref, qc_ref, export_ref],
    layout=benchmark_layout,
    metrics={"accepted_candidates": float(qc_report.metrics.accepted)},
)

benchmark_manifest.write_json(Path(benchmark_layout.manifest_path))
```

### Step 9. Track And Compare Benchmark Runs

```python
from pathlib import Path

from smdgf.benchmark.tracker import LocalRunTracker, compare_runs

tracker = LocalRunTracker(Path("runs/tracking"))

tracked_run = tracker.track_run(
    benchmark_manifest,
    params={"seed": 17, "config_path": "configs/demo.yaml"},
    metrics=dict(benchmark_manifest.metrics),
    tags={"stage": "demo"},
    artifact_refs=benchmark_manifest.artifact_refs,
)

same_run = tracker.get_run(tracked_run.run_id)
all_runs = tracker.list_runs()

print(same_run.params)
print(len(all_runs))
```

To compare two runs:

```python
comparison = compare_runs(all_runs[0], all_runs[1])
print(comparison.metric_deltas)
print(comparison.changed_tags)
```

## Recommended Ways To Use The Project Right Now

Use the project in one of two modes:

### Mode A. Smoke-Test The Whole Stack

Use `build_baseline_taskpack()` plus `smoke_taskpack_run()` when you want:

- a local-only sanity check
- a concrete reference flow
- an integration test over generation, QC, export, benchmark packaging, and tracking

### Mode B. Build Your Own Task Pipeline

Use the Python API when you want:

- custom task definitions
- custom canonicalization logic
- custom provider integration
- custom QC policies
- custom export layouts and benchmark packaging

## Current Limitations

These are the important boundaries to know:

- The CLI is not yet a full orchestrator.
- `TaskRegistry` is in-memory only.
- There is no generic public “raw generation output -> canonical sample” adapter.
- There is no persistent experiment database; tracking is local JSON by default.
- Human review exists in the data model and QC artifacts, but not yet as a full product workflow.

## Practical First Commands

If you want the shortest path to confidence:

```bash
pip install -e ".[dev]"
pytest -q
smdgf contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
smdgf contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
smdgf sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

If you are running directly from the repo without installation:

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
PYTHONPATH=src python3 -m smdgf.cli.main sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

Then run the smoke pack:

```bash
python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from smdgf.benchmark.taskpack import build_baseline_taskpack, smoke_taskpack_run

repo_root = Path(".").resolve()
with TemporaryDirectory() as tmp:
    run = smoke_taskpack_run(build_baseline_taskpack(repo_root), Path(tmp))
    print(run.benchmark_manifest.run_id)
    print(run.export_manifest.formats)
    print(run.tracking_summary)
PY
```

## Relevant Files

If you want to keep reading the code after this guide:

- [src/smdgf/cli/main.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/cli/main.py)
- [src/smdgf/schemas/task.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/schemas/task.py)
- [src/smdgf/schemas/spec.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/schemas/spec.py)
- [src/smdgf/samplers/scenario.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/samplers/scenario.py)
- [src/smdgf/generation/runtime.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/generation/runtime.py)
- [src/smdgf/qc/rules.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/qc/rules.py)
- [src/smdgf/export/manifest.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/export/manifest.py)
- [src/smdgf/benchmark/taskpack.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/benchmark/taskpack.py)
