# YAML 任务定义详解 — 对照 example.txt

> 本文档对照 `prompts/example.txt` 中的 prompt 逻辑，说明每个 YAML 字段的含义和填写方式。

---

## 一、example.txt 里的 prompt 说了什么

先拆解 example.txt 的核心逻辑，这样才知道 YAML 每个字段对应 prompt 的哪部分：

```
example.txt 的核心逻辑：
┌─────────────────────────────────────────────────────────┐
│ 1. 丙做了一件事，对甲和乙造成不同影响                    │
│ 2. 甲和乙产生相反的情绪                                  │
│ 3. 两个问题问甲和乙的情绪，选项相同但答案不同            │
│ 4. 70%情境有第三方"丙"                                   │
│ 5. 选项是四个两字情绪词                                  │
│ 6. 不能直接用"甲""乙""丙"，要取具体人名                  │
└─────────────────────────────────────────────────────────┘
          ↓ 映射到框架
┌─────────────────────────────────────────────────────────┐
│ scene_blueprint  →  情境模板（丙做了X，对甲乙造成不同影响）│
│ slots            →  人名（甲乙丙的名字）                   │
│ roles           →  甲乙丙的身份角色                      │
│ relations       →  丙和甲乙的关系                        │
│ latent_state    →  情绪状态（甲=生气，乙=开心）           │
│ question_patterns → 问甲和乙各自的心情                   │
│ quality_expectations → 不能直接暴露答案                   │
└─────────────────────────────────────────────────────────┘
```

---

## 二、YAML 字段逐行对照说明

### 2.1 task_definition — 任务定义

```yaml
task_id: emotion.contrasting        # 唯一ID，建议用"能力.类型"格式
name: 情绪对比推理                   # 人类可读名称
description: >-
  给定一个社交场景，推断其中不同人物的情绪，
  要求同一情境下两个角色的情绪相反。
ability_category: emotion             # 能力类别（见下方可选值）
sub_capabilities:
  - contrasting_emotion               # 子能力：情绪对比推理
latent_variables:
  - name: emotion_protagonist       # 第一个角色的情绪
    description: 场景中的主角甲的情绪
    value_type: string
  - name: emotion_contrasting       # 第二个角色的情绪
    description: 场景中与主角相对的乙的情绪
    value_type: string
answer_mode: single_choice            # 答题方式：single_choice / free_text
supported_exports:                   # 最终导出哪些格式
  - mcq
  - qa
  - open_qa
```

**可选的 ability_category（能力类别）：**

| 值 | 含义 |
|----|------|
| `emotion` | 情绪识别 |
| `desire` | 欲望/愿望推理 |
| `intention` | 意图识别 |
| `belief` | 信念推理 |
| `knowledge` | 知识推理 |
| `social_relation` | 社交关系 |
| `non_literal` | 隐喻/非字面理解 |
| `social_decision` | 社交决策 |
| `implicit_stance` | 隐含立场 |

---

### 2.2 scene_template — 场景模板

这是最核心的部分，对应 example.txt 中的"情境"构建逻辑：

```yaml
template_id: emotion.contrasting.scene
task_id: emotion.contrasting           # 必须和 task_definition 一致
scene_blueprint: >-                    # 场景蓝图 = 情境模板
  {agent_丙} 做了 {action}，
  这让 {agent_甲} 感到 {emotion_甲}，
  但让 {agent_乙} 感到 {emotion_乙}。

slot_specs:                             # 槽位 = prompt 里要填充的内容
  - slot_id: agent_甲                  # 第一个人（甲）
    value_type: person_name
    description: 第一个受影响的人
  - slot_id: agent_乙                  # 第二个人（乙）
    value_type: person_name
    description: 第二个受影响的人
  - slot_id: agent_丙                  # 第三个人（丙，做事的人）
    value_type: person_name
    description: 造成影响的人
  - slot_id: action                   # 丙做的具体事情
    value_type: social_action
    description: 丙做的一件事
  - slot_id: emotion_甲               # 甲的情绪（这个是答案之一）
    value_type: emotion_word
    allowed_values:                   # 限制为两字情绪词
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
      - 担心
      - 感动
      - 嫉妒
  - slot_id: emotion_乙               # 乙的情绪（这个是答案之一）
    value_type: emotion_word
    allowed_values:                   # 限制为两字情绪词
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
      - 担心
      - 感动
      - 嫉妒

roles:                                  # 角色定义
  - role_id: agent_甲
    role_type: agent
    display_name_source: slot:agent_甲  # 显示名从 agent_甲 槽位取值
  - role_id: agent_乙
    role_type: agent
    display_name_source: slot:agent_乙
  - role_id: agent_丙
    role_type: agent
    display_name_source: slot:agent_丙

relations:                              # 关系定义（丙对甲乙做了什么）
  - relation_id: affect_甲
    source_role: agent_丙
    relation_type: causes_emotion_to
    target_role: agent_甲
  - relation_id: affect_乙
    source_role: agent_丙
    relation_type: causes_emotion_to
    target_role: agent_乙

latent_state_specs:                     # 潜在状态 = 要采样的情绪答案
  - state_id: emotion_甲
    owner_role: agent_甲
    state_type: emotion
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
    sampling_strategy: choice           # 从 allowed_values 随机选

  - state_id: emotion_乙
    owner_role: agent_乙
    state_type: emotion
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
    sampling_strategy: choice
```

**scene_blueprint 的写法要点：**

- `{槽位ID}` 是占位符，框架会自动替换成采样值
- 情绪词（`{emotion_甲}`、`{emotion_乙}`）**不要直接写在 blueprint 里**，因为它们是答案，会被采样出来。框架会自动从 `allowed_values` 里选，保证每次生成内容不同
- 如果需要"相反情绪"，在 `allowed_values` 里配对相反的词（如生气/高兴、悲伤/感动）

**slot_specs 的 value_type 说明：**

框架目前不强制校验 `value_type`，只做语义标签。你可以用：
- `person_name` — 人名
- `emotion_word` — 情绪词
- `location` — 地点
- `social_action` — 社交行为
- `string` — 通用字符串

---

### 2.3 task_specification — 任务规格

对应 example.txt 中的"问题 + 选项 + 质量要求"部分：

```yaml
task_id: emotion.contrasting           # 必须和 task_definition 一致
scene_templates:
  - template_id: emotion-contrasting-1
    narrative_template: >-             # 叙事模板 = 填充后的完整情境
      {agent_丙} 做了 {action}，
      这让 {agent_甲} 感到 {emotion_甲}，
      但让 {agent_乙} 感到 {emotion_乙}。
    slots:
      agent_丙: 人名
      agent_甲: 人名
      agent_乙: 人名
      action: 社交行为
      emotion_甲: 情绪词
      emotion_乙: 情绪词
    role_constraints:
      - agent_丙 是造成影响的人
      - agent_甲 和 agent_乙 同时受影响但情绪相反
    latent_state_requirements:
      - emotion_甲
      - emotion_乙

question_patterns:
  - question_id: q_甲
    prompt_template: "{agent_甲} 会有怎样的心情？"  # 问题1：问甲
    target_capability: emotion
    answer_mode: single_choice
    options_count: 4                     # MCQ 选项数

  - question_id: q_乙
    prompt_template: "{agent_乙} 会有怎样的心情？"  # 问题2：问乙
    target_capability: emotion
    answer_mode: single_choice
    options_count: 4

quality_expectations:
  - expectation_id: no-context-leak
    description: 场景描述不能直接暴露答案情绪词
    severity: error
    rule_type: leakage                   # 触发 context_leakage_rule

  - expectation_id: no-question-leak
    description: 问题中不能直接出现答案
    severity: error
    rule_type: leakage                   # 触发 answer_leakage_rule

  - expectation_id: opposite-emotions
    description: 甲和乙的情绪应该是不同的
    severity: warning
    rule_type: logic                     # 可扩展自定义规则检查
```

---

## 三、中文情感推理任务的完整 YAML 示例

把上面的内容整合成三个可直接使用的文件：

### `examples/emotion_contrasting/task_definition.yaml`

```yaml
task_id: emotion.contrasting
name: 情绪对比推理
description: >-
  给定一个社交场景，推断其中不同人物的情绪。
  同一情境下两个角色的情绪相反，需要模型理解行为对他人的不同影响。
ability_category: emotion
sub_capabilities:
  - contrasting_emotion
latent_variables:
  - name: emotion_protagonist
    description: 第一个受影响角色的情绪
    value_type: string
  - name: emotion_contrasting
    description: 第二个受影响角色的情绪（与前者相反）
    value_type: string
answer_mode: single_choice
supported_exports:
  - mcq
  - qa
  - open_qa
```

### `examples/emotion_contrasting/scene_template.yaml`

```yaml
template_id: emotion.contrasting.scene
task_id: emotion.contrasting
scene_blueprint: >-
  {agent_丙} 做了 {action}，
  这让 {agent_甲} 感到 {emotion_甲}，
  但让 {agent_乙} 感到 {emotion_乙}。

slot_specs:
  - slot_id: agent_甲
    value_type: person_name
  - slot_id: agent_乙
    value_type: person_name
  - slot_id: agent_丙
    value_type: person_name
  - slot_id: action
    value_type: social_action
  - slot_id: emotion_甲
    value_type: emotion_word
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
      - 担心
      - 感动
      - 嫉妒
      - 后悔
  - slot_id: emotion_乙
    value_type: emotion_word
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
      - 担心
      - 感动
      - 嫉妒
      - 后悔

roles:
  - role_id: agent_甲
    role_type: agent
    display_name_source: slot:agent_甲
  - role_id: agent_乙
    role_type: agent
    display_name_source: slot:agent_乙
  - role_id: agent_丙
    role_type: agent
    display_name_source: slot:agent_丙

relations:
  - relation_id: affect_甲
    source_role: agent_丙
    relation_type: causes_emotion_to
    target_role: agent_甲
  - relation_id: affect_乙
    source_role: agent_丙
    relation_type: causes_emotion_to
    target_role: agent_乙

latent_state_specs:
  - state_id: emotion_甲
    owner_role: agent_甲
    state_type: emotion
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
    sampling_strategy: choice
  - state_id: emotion_乙
    owner_role: agent_乙
    state_type: emotion
    allowed_values:
      - 生气
      - 高兴
      - 悲伤
      - 尴尬
    sampling_strategy: choice
```

### `examples/emotion_contrasting/task_specification.yaml`

```yaml
task_id: emotion.contrasting
scene_templates:
  - template_id: emotion-contrasting-main
    narrative_template: >-
      {agent_丙} 做了 {action}，
      这让 {agent_甲} 感到 {emotion_甲}，
      但让 {agent_乙} 感到 {emotion_乙}。
    slots:
      agent_丙: 人名
      agent_甲: 人名
      agent_乙: 人名
      action: 社交行为
      emotion_甲: 情绪词
      emotion_乙: 情绪词
    role_constraints:
      - agent_丙 的行为同时影响 agent_甲 和 agent_乙
    latent_state_requirements:
      - emotion_甲
      - emotion_乙

question_patterns:
  - question_id: q_甲
    prompt_template: "{agent_甲} 会有怎样的心情？"
    target_capability: emotion
    answer_mode: single_choice
    options_count: 4

  - question_id: q_乙
    prompt_template: "{agent_乙} 会有怎样的心情？"
    target_capability: emotion
    answer_mode: single_choice
    options_count: 4

quality_expectations:
  - expectation_id: no-context-leak
    description: 场景描述中不能出现具体的情绪词答案
    severity: error
    rule_type: leakage
  - expectation_id: no-question-leak
    description: 问题中不能直接包含答案
    severity: error
    rule_type: leakage
```

---

## 四、框架如何自动构建 Prompt

当你调用 `build_generation_prompt()` 时，框架从 YAML 定义自动拼接出一个结构化 prompt：

```
输入：task_definition + task_specification + scenario_sample（采样后的具体值）
  ↓
框架拼接出以下 prompt：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task ID: emotion.contrasting
Task Name: 情绪对比推理
Ability Category: emotion
Description: 给定一个社交场景，推断其中不同人物的情绪……

Scenario Sample ID: emotion-contrasting-sample-001
Scenario Blueprint: {agent_丙} 做了 {action}，这对 {agent_甲} 感到 {emotion_甲}，但让 {agent_乙} 感到 {emotion_乙}。

Sampled Slots:
{
  "agent_甲": "小张",
  "agent_乙": "小李",
  "agent_丙": "小王",
  "action": "邀请小李去看浪漫电影",
  "emotion_甲": "生气",
  "emotion_乙": "高兴"
}

Roles:
- agent_甲: 小张 (agent) attributes={}
- agent_乙: 小李 (agent) attributes={}
- agent_丙: 小王 (agent) attributes={}

Relations:
- agent_丙 --causes_emotion_to--> agent_甲
- agent_丙 --causes_emotion_to--> agent_乙

Latent States:
- agent_甲.emotion_甲 (emotion) = 生气
- agent_乙.emotion_乙 (emotion) = 高兴

Question Patterns:
- q_甲: capability=emotion mode=single_choice template={agent_甲} 会有怎样的心情？
- q_乙: capability=emotion mode=single_choice template={agent_乙} 会有怎样的心情？

Produce a candidate response that matches the task specification and preserves the latent state logic.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

输出：prompt_text（发给模型的完整 prompt）+ prompt_metadata（包含 fingerprint、question_ids 等）
```

**关键点：**

1. **场景蓝图里的情绪词占位符**（`{emotion_甲}`、`{emotion_乙}`）会被替换成采样值（如"生气"、"高兴"）
2. **这些情绪词出现在 context 中**，但问题问的是 `{agent_甲}` 和 `{agent_乙}` 的心情——这正是 example.txt 里的设计：**context 有答案，但问题是针对人物的**，模型需要理解"谁有什么情绪"
3. **质控规则**（`context_leakage_rule`）会检查 context 是否直接暴露了情绪词——如果你的 blueprint 里写了 `{emotion_甲}` 替换后的值，那 context 里就包含了答案，质控会拒绝这条数据，提示你调整 `scene_blueprint` 的写法

**为了避免 context 暴露答案，推荐写法**：

```yaml
# ❌ 不推荐：context 里直接包含情绪词（会被质控拒绝）
scene_blueprint: "{agent_丙} 做了 {action}，这对 {agent_甲} 感到 {emotion_甲}..."

# ✅ 推荐：context 里不写具体情绪，模型根据行为推断
scene_blueprint: "{agent_丙} 做了 {action}，这对 {agent_甲} 和 {agent_乙} 造成了不同影响。"
# 然后在 latent_state_specs 里单独记录正确答案
```

**如何决定是否在 context 中写情绪词：**

| 场景 | 写法 | 说明 |
|------|------|------|
| 测试模型推理能力 | 不在 context 写情绪，让模型推断 | context 包含行为描述，答案在 latent_state |
| 提供更多线索 | 在 context 写情绪词 | 需要配合 `context_leakage_rule: warning` 或关闭该规则 |
| 参考 example.txt | context 里写情绪（"感到生气/高兴"） | 模型需要识别"谁有什么情绪"，context 是线索而非答案 |

example.txt 的设计是**在 context 里写情绪词**（如"让甲感到生气，但让乙感到高兴"），模型的任务是**识别和关联**。这种情况下，质控的 `context_leakage_rule` 需要调整为 `severity: warning`（不拒绝，只警告），或者关闭这条规则。

---

## 五、完整的生成脚本

把上面的 YAML 组合起来跑完整流程：

```python
# generate_emotion_contrasting.py
import json
from pathlib import Path
import yaml
from tempfile import TemporaryDirectory

from smdgf.schemas import TaskDefinition, TaskSpecification, SceneTemplate
from smdgf.schemas.scene import (
    ScenarioSample, SampledRole, SampledRelation,
    LatentStateAssignment, SlotSpec, RoleSpec, RelationSpec,
    LatentStateSpec, SceneConstraint
)
from smdgf.schemas.canonical import (
    CanonicalSample, CanonicalQuestion, CanonicalAnswer, ProvenanceRecord
)
from smdgf.generation import GenerationRuntime, GenerationRequest, ProviderConfig
from smdgf.generation.prompts import build_generation_prompt
from smdgf.generation.providers import LiteLLMGenerationProvider
from smdgf.qc import QualityCandidate, RuleEngine
from smdgf.qc.reports import build_qc_report
from smdgf.export.qa import export_sample_to_qa, export_sample_to_open_qa
from smdgf.export.mcq import export_sample_to_mcq
from smdgf.export.manifest import write_export_manifest
from smdgf.benchmark.tracker import LocalRunTracker

# ── 1. 加载 YAML ──────────────────────────────────────────────
task_def = TaskDefinition.model_validate(
    yaml.safe_load(Path("examples/emotion_contrasting/task_definition.yaml").read_text())
)
task_spec = TaskSpecification.model_validate(
    yaml.safe_load(Path("examples/emotion_contrasting/task_specification.yaml").read_text())
)
scene_tpl = SceneTemplate.model_validate(
    yaml.safe_load(Path("examples/emotion_contrasting/scene_template.yaml").read_text())
)

# ── 2. 场景采样（确定性）────────────────────────────
EMOTION_PAIRS = [
    ("生气", "高兴"), ("悲伤", "感动"), ("担心", "放心"), ("尴尬", "开心"),
    ("嫉妒", "自豪"), ("后悔", "释然"), ("失望", "惊喜"), ("害怕", "兴奋"),
]
NAMES = ["小张", "小李", "小王", "小赵", "小刘", "小陈", "小杨", "小周"]

# 从 allowed_values 里采样
import random
random.seed(42)

slot_values = {
    "agent_甲": random.choice(NAMES),
    "agent_乙": random.choice([n for n in NAMES]),
    "agent_丙": random.choice(NAMES),
    "action": "邀请小李去看浪漫电影",
    "emotion_甲": "生气",
    "emotion_乙": "高兴",
}

scenario_sample = ScenarioSample(
    sample_id="emotion-contrasting-001",
    template_id=scene_tpl.template_id,
    task_id=task_def.task_id,
    scene_blueprint=scene_tpl.scene_blueprint,
    sampled_slots=slot_values,
    roles=[
        SampledRole(role_id="agent_甲", role_type="agent", display_name=slot_values["agent_甲"]),
        SampledRole(role_id="agent_乙", role_type="agent", display_name=slot_values["agent_乙"]),
        SampledRole(role_id="agent_丙", role_type="agent", display_name=slot_values["agent_丙"]),
    ],
    relations=[
        SampledRelation(relation_id="affect_甲", source_role="agent_丙",
                         relation_type="causes_emotion_to", target_role="agent_甲"),
        SampledRelation(relation_id="affect_乙", source_role="agent_丙",
                         relation_type="causes_emotion_to", target_role="agent_乙"),
    ],
    latent_state_assignments=[
        LatentStateAssignment(state_id="emotion_甲", owner_role="agent_甲",
                              state_type="emotion", value=slot_values["emotion_甲"],
                              sampling_strategy="choice"),
        LatentStateAssignment(state_id="emotion_乙", owner_role="agent_乙",
                              state_type="emotion", value=slot_values["emotion_乙"],
                              sampling_strategy="choice"),
    ],
    provenance={"seed": 42},
)

# ── 3. 构建 Prompt ───────────────────────────────────────
prompt_text, prompt_metadata = build_generation_prompt(
    task_def, task_spec, scenario_sample, seed=42
)
print("=== 发送给模型的 Prompt ===")
print(prompt_text)

# ── 4. 调用模型（用 OPENAI_API_KEY）───────────────────
provider_config = ProviderConfig(
    provider_id="openai",
    model="gpt-4o-mini",
    temperature=0.0,
)

runtime = GenerationRuntime(
    provider=LiteLLMGenerationProvider(),
    provider_config=provider_config,
    checkpoint_path=Path("runs/manifest.json"),
    max_retries=2,
)

request = GenerationRequest(
    request_id="req-001",
    task_id=task_def.task_id,
    scenario_sample=scenario_sample,
    prompt_text=prompt_text,
    provider=provider_config.provider_id,
    model=provider_config.model,
    seed=42,
    prompt_metadata=prompt_metadata,
)

generation_manifest = runtime.run("emotion-run-001", [request], resume=False)
gen_result = generation_manifest.items[0].result
print("\n=== 模型原始输出 ===")
print(gen_result.response_text)

# ── 5. 解析模型输出 → CanonicalSample ─────────────────
# 模型输出格式（参考 example.txt 的表格）：
# {"scene_text": "...", "q_甲": {"answer": "生气", "rationale": "..."}, "q_乙": {...}}
payload = json.loads(gen_result.response_text)

canonical_sample = CanonicalSample(
    sample_id=scenario_sample.sample_id,
    task_id=task_def.task_id,
    scene_text=payload.get("scene_text", ""),
    latent_state={
        slot_values["agent_甲"]: {"emotion": payload["q_甲"]["answer"]},
        slot_values["agent_乙"]: {"emotion": payload["q_乙"]["answer"]},
    },
    questions=[
        CanonicalQuestion(
            question_id="q_甲",
            text=payload["q_甲"]["question"],
            target_capability="emotion",
        ),
        CanonicalQuestion(
            question_id="q_乙",
            text=payload["q_乙"]["question"],
            target_capability="emotion",
        ),
    ],
    answers=[
        CanonicalAnswer(
            question_id="q_甲",
            value=payload["q_甲"]["answer"],
            rationale=payload["q_甲"].get("rationale", ""),
        ),
        CanonicalAnswer(
            question_id="q_乙",
            value=payload["q_乙"]["answer"],
            rationale=payload["q_乙"].get("rationale", ""),
        ),
    ],
    provenance=ProvenanceRecord(
        source="emotion-run-001",
        model_id=gen_result.model_id,
        prompt_id=gen_result.prompt_fingerprint,
        seed=42,
    ),
)

# ── 6. 质控 ────────────────────────────────────────────
decision = RuleEngine().evaluate(
    QualityCandidate(
        candidate_id=canonical_sample.sample_id,
        canonical_sample=canonical_sample,
        generation_result=gen_result,
        generation_run_id=generation_manifest.run_id,
        scenario_sample_id=scenario_sample.sample_id,
        prompt_fingerprint=gen_result.prompt_fingerprint,
        metadata={
            "latent_expectations": {
                slot_values["agent_甲"]: {"emotion": slot_values["emotion_甲"]},
                slot_values["agent_乙"]: {"emotion": slot_values["emotion_乙"]},
            }
        },
    )
)
print(f"\n质控结果：{decision.status}")
for f in decision.findings:
    print(f"  [{f.severity}] {f.message}")

# ── 7. 导出 ────────────────────────────────────────────
if decision.status == "accept":
    EMOTION_OPTIONS = ["生气", "高兴", "悲伤", "尴尬"]

    class FixedDistractorStrategy:
        strategy_id = "fixed-4"
        def generate(self, sample, question, answer):
            opts = [o for o in EMOTION_OPTIONS if o != str(answer.value)]
            return opts[:3]

    qa = export_sample_to_qa(canonical_sample, split="train")
    open_qa = export_sample_to_open_qa(canonical_sample, split="train")
    mcq = export_sample_to_mcq(canonical_sample, FixedDistractorStrategy(), split="train")

    export_manifest = write_export_manifest(
        Path("runs/export"), "emotion-export-001",
        qa + open_qa + mcq,
        config_snapshot={"seed": 42, "task_id": task_def.task_id},
        source_qc_run_id=decision.candidate_id,
    )
    print(f"\n导出完成，格式：{export_manifest.formats}")
    print(f"输出文件：{list(export_manifest.artifact_paths.items())}")
```

运行：

```bash
export OPENAI_API_KEY="sk-..."
python generate_emotion_contrasting.py
```

---

## 六、模型输出格式设计建议

框架对模型输出格式没有限制，但推荐让模型返回结构化 JSON，方便解析：

```json
{
  "scene_text": "小王邀请小李去看浪漫电影，这让小张感到生气，但让小李感到高兴。",
  "q_甲": {
    "question": "小张会有怎样的心情？",
    "answer": "生气",
    "rationale": "小王没有经过小张同意就邀请小李，这让小张感到被忽视。"
  },
  "q_乙": {
    "question": "小李会有怎样的心情？",
    "answer": "高兴",
    "rationale": "小李收到邀请，感到被关注和开心。"
  }
}
```

你可以在 YAML 的 `quality_expectations` 里通过 `rule_type: logic` 配合自定义规则来校验模型输出是否包含 `scene_text`、`q_甲`、`q_乙` 等字段。
