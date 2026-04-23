# Social Mind Data Generation Framework

这个仓库是一个 Python 框架，用于以可复现、面向流水线的方式构建 social-mind 基准数据集。

当前状态：

- Phase 1-6 已实现并通过验证。
- 代码库已经支持契约定义、场景采样、生成运行时、QC、导出、benchmark 打包，以及本地运行追踪。
- 对外 CLI 目前还比较小。
- 完整流水线当前主要通过 Python API 使用。

## 这个项目现在能做什么

仓库目前已经可以支持如下工作流：

1. 定义任务契约和任务规格。
2. 定义可复用的场景模板，包括角色、关系和潜在状态。
3. 基于随机种子进行确定性场景采样。
4. 构建 prompt，并通过与 provider 无关的运行时执行生成任务。
5. 应用 QC 规则并产出 QC 报告。
6. 将 canonical sample 导出为 `qa`、`mcq` 和 `open_qa`。
7. 将生成、QC 和导出产物打包为 benchmark run manifest。
8. 在本地追踪 benchmark runs，并在之后进行对比。
9. 运行内置 baseline smoke flow，对本地端到端流水线做一次冒烟验证。

## 当前公开 CLI 覆盖范围

安装后的 `smdgf` CLI 当前提供：

- `smdgf contracts inspect`
- `smdgf contracts validate`
- `smdgf sampling preview`
- `smdgf yaml assemble-prompt`（从 YAML 契约仅组装 `prompt_text`，不调模型）
- `smdgf generate`（模板 + `prompts/**/*.txt` → 调用模型 → 质控 → 导出）

生成、QC、导出、benchmark 打包和运行追踪已经实现，但目前还是 Python 模块，还没有全部作为一等 CLI 命令暴露出来。

## 环境要求

- Python `>=3.11`
- 建议使用虚拟环境

在仓库根目录执行安装：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

安装完成后，`smdgf` 命令应该会在当前激活环境中可用。

如果你暂时不想安装包，也可以直接这样使用：

```bash
PYTHONPATH=src python3 -m smdgf.cli.main --help
```

运行测试：

```bash
pytest -q
```

## 仓库结构

主要模块：

- `src/smdgf/schemas/`：任务、场景、规格和 canonical sample 的强类型契约
- `src/smdgf/samplers/`：确定性采样辅助逻辑
- `src/smdgf/generation/`：provider 抽象、prompt 组装、运行时和 manifest
- `src/smdgf/qc/`：QC 模型、规则、judge、去重和报告
- `src/smdgf/export/`：QA/MCQ/open-QA 导出器和导出 manifest
- `src/smdgf/benchmark/`：benchmark manifest、运行追踪和 baseline smoke task pack
- `src/smdgf/cli/`：当前 CLI 入口

常用 fixture：

- `tests/fixtures/task_definition_valid.yaml`
- `tests/fixtures/task_spec_valid.yaml`
- `tests/fixtures/scene_template_valid.yaml`

## 快速开始

### 1. 通过 CLI 校验契约

校验 task definition：

```bash
smdgf contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
```

如果未安装包：

```bash
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
```

校验 task specification：

```bash
smdgf contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
```

如果未安装包：

```bash
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
```

预览一个确定性采样场景：

```bash
smdgf sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

如果未安装包：

```bash
PYTHONPATH=src python3 -m smdgf.cli.main sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

### 2. 运行内置端到端 Smoke Flow

如果你想先跑一个最短、最完整的示例，直接使用内置 baseline task pack：

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

这个 smoke flow 实际会覆盖：

- `GenerationRuntime`
- prompt 组装
- QC 规则评估和 `build_qc_report()`
- `export_sample_to_qa()`
- `export_sample_to_open_qa()`
- `export_sample_to_mcq()`
- `write_export_manifest()`
- benchmark manifest 打包
- `LocalRunTracker`

这是当前仓库里最值得参考的集成路径。

## 完整使用说明

这一部分展示如何把框架当作一组可组合的构建块来使用。

### 第 1 步：加载并校验结构化契约

你可以直接从文件进行校验：

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

你也可以在内存中注册任务定义：

```python
from smdgf.registry import TaskRegistry

registry = TaskRegistry()
registry.register(task_definition)
print([task.task_id for task in registry.list()])
```

需要注意：

- `TaskRegistry` 当前只存在于内存中。
- 还没有持久化的 task catalog 后端。

### 第 2 步：做确定性场景采样

```python
from smdgf.samplers import SamplingContext, sample_scenario

context = SamplingContext(seed=17)
scenario_sample = sample_scenario(scene_template, context)

print(scenario_sample.sample_id)
print(scenario_sample.sampled_slots)
print(scenario_sample.latent_state_assignments)
```

这一步会给你：

- sampled slots
- sampled roles
- sampled relations
- sampled latent state assignments
- 带 seed 的 provenance

### 第 3 步：构建 Prompt

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

`prompt_metadata` 中包含：

- `task_id`
- `scenario_sample_id`
- `seed`
- `question_ids`
- `prompt_fingerprint`

### 第 4 步：通过 Runtime 执行生成

框架提供了一个与 provider 无关的 generation runtime。你可以接 LiteLLM，也可以接自己的 provider 实现。

下面是一个最小本地 stub 示例：

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

当前 runtime 已支持：

- checkpointed manifests
- resumable runs
- retry handling
- provider/model/prompt provenance

### 第 5 步：把生成输出转换为 Canonical Sample

这个框架有意将“生成”与“canonical sample 构建”分开。

也就是说：

- runtime 负责给你生成结果和 provenance
- 你的任务逻辑负责把模型输出转换成 `CanonicalSample`

最小示例：

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

需要注意：

- 目前还没有通用的公开适配器，把“generation result”直接转成 `CanonicalSample`
- 内置 smoke task pack 是当前最好的参考实现

### 第 6 步：运行 QC

基础 QC 是基于规则的，直接作用在 canonical sample 上：

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

当前 QC 包括：

- 结构校验
- 确定性规则
- judge hooks
- duplicate 和 near-duplicate 支持
- review queue 和 rejection manifest 生成

### 第 7 步：导出通过审核的 Canonical Samples

QA 和 open-QA 导出：

```python
from smdgf.export.qa import export_sample_to_open_qa, export_sample_to_qa

qa_records = export_sample_to_qa(canonical_sample, split="train")
open_qa_records = export_sample_to_open_qa(canonical_sample, split="train")
```

MCQ 导出需要一个 distractor strategy：

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

写出 export manifest：

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

### 第 8 步：打包一个 Benchmark Run

当 generation、QC 和 export 都已经完成后，可以把它们打包成一个 benchmark manifest：

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

### 第 9 步：追踪并比较 Benchmark Runs

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

比较两个 run：

```python
comparison = compare_runs(all_runs[0], all_runs[1])
print(comparison.metric_deltas)
print(comparison.changed_tags)
```

## 当前推荐的使用方式

现在比较推荐两种使用模式：

### 模式 A：对整套栈做 Smoke Test

当你需要下面这些东西时，使用 `build_baseline_taskpack()` 加 `smoke_taskpack_run()`：

- 一个纯本地的健康检查
- 一条具体可参考的流水线
- 一次覆盖 generation、QC、export、benchmark 打包和 tracking 的集成测试

### 模式 B：构建你自己的任务流水线

当你需要下面这些能力时，直接使用 Python API：

- 自定义 task definitions
- 自定义 canonicalization 逻辑
- 自定义 provider 集成
- 自定义 QC 策略
- 自定义 export 布局和 benchmark 打包

## 当前限制

下面这些边界目前比较重要：

- CLI 还不是一个完整的 orchestration 工具。
- `TaskRegistry` 目前只在内存中工作。
- 还没有通用的公开适配器把“原始生成输出”转换为 canonical sample。
- 还没有持久化实验数据库；默认 tracking 是本地 JSON。
- Human review 已经体现在数据模型和 QC 产物里，但还没有做成完整产品流程。

## 最实用的第一批命令

如果你想用最短路径确认项目能跑起来：

```bash
pip install -e ".[dev]"
pytest -q
smdgf contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
smdgf contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
smdgf sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

如果你是不安装、直接从仓库运行：

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_definition_valid.yaml --kind task-definition
PYTHONPATH=src python3 -m smdgf.cli.main contracts validate tests/fixtures/task_spec_valid.yaml --kind task-spec
PYTHONPATH=src python3 -m smdgf.cli.main sampling preview tests/fixtures/scene_template_valid.yaml --seed 17
```

然后再跑 smoke pack：

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

## 相关文件

如果你读完这份说明后还想继续看代码，建议从下面这些文件开始：

- [src/smdgf/cli/main.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/cli/main.py)
- [src/smdgf/schemas/task.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/schemas/task.py)
- [src/smdgf/schemas/spec.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/schemas/spec.py)
- [src/smdgf/samplers/scenario.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/samplers/scenario.py)
- [src/smdgf/generation/runtime.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/generation/runtime.py)
- [src/smdgf/qc/rules.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/qc/rules.py)
- [src/smdgf/export/manifest.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/export/manifest.py)
- [src/smdgf/benchmark/taskpack.py](/Users/lei/projects/i/DataGenerationFramework/src/smdgf/benchmark/taskpack.py)
