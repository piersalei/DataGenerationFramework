# Social Mind 数据生成框架 — 小组使用指南

> 核心思路：人只写 few-shot 示例片段，框架模板自动合并，调用大模型得到结果。

---

## 一、环境准备

```bash
git clone <仓库地址>
cd DataGenerationFramework
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -e ".[dev]"
```

---

## 二、Prompt 管理方式

每个任务的每种格式只需要写一个纯文本 `fragment_{format}.txt`，其他由框架模板合并（扩展名固定为 `.txt`，不按 Markdown 文件解析）。

```
prompts/
  templates/
    base_mcq.txt       # 选择题模板
    base_qa.txt        # 问答题模板
    base_open_qa.txt   # 开放式问答模板
  emotion.contrasting/
    fragment_mcq.txt    # 你写的选择题 few-shot
    fragment_qa.txt     # 你写的问答题 few-shot
    fragment_open_qa.txt # 你写的开放式问答 few-shot
```

### fragment_{format}.txt 怎么写

只写示例和任务规则，不用写角色设定、输出格式等套话。例如 `fragment_mcq.txt`：

```
### 示例问题：
| 情境| 问题编号| 问题| A | B | C | D | 答案|
| 小红的男朋友邀请小芳去看电影。| 1 | 小丽会有怎样的心情？| 生气| 开心| 悲伤| 尴尬| A |
| 小红的男朋友邀请小芳去看电影。| 2 | 小芳会有怎样的心情？| 生气| 开心| 悲伤| 尴尬| D |

### 说明：
这些问题都有共同点：（丙做了）一件事，对甲和乙造成了不同影响。
- 生成至少{{num_questions}}组新问题。
```

`{{num_questions}}` 这种占位符会在合并时自动替换。

### YAML 契约 → 仅生成 prompt_text（与模板路线并行）

不调模型、不质控、不导出，只输出 `build_generation_prompt` 的结果：

```bash
smdgf yaml assemble-prompt \
  --task-definition examples/emotion_contrasting/task_definition.yaml \
  --task-specification examples/emotion_contrasting/task_specification.yaml \
  --scene-template examples/emotion_contrasting/scene_template.yaml \
  --seed 42 \
  -o /tmp/prompt_from_yaml.txt
```

---

## 三、配置（模型 / Provider / API Key / Base URL）

所有配置在一个地方完成，支持 OpenAI / Anthropic / Ollama。

### 方式 A：从 config.yaml 加载（推荐）

创建 `config.yaml`：

```yaml
provider: openai          # openai / anthropic / ollama
model: gpt-4o-mini       # 模型名
api_key: sk-...           # 不填则从环境变量读
api_base: https://your-proxy.com/v1  # 用第三方代理时填
temperature: 0.0
```

```python
from pathlib import Path
from smdgf.generation import Config

cfg = Config.from_file(Path("config.yaml"))
```

### 方式 B：代码中直接配置

```python
from smdgf.generation import Config

# OpenAI
cfg = Config("openai", model="gpt-4o-mini", api_key="sk-...", api_base="https://your-proxy.com/v1")

# Anthropic
cfg = Config("anthropic", model="claude-3-5-sonnet-20241022", api_key="sk-ant-...")

# Ollama 本地
cfg = Config("ollama", model="llama3", api_base="http://localhost:11434")
```

---

## 四、生成脚本

```python
#!/usr/bin/env python3
"""情绪对比推理数据生成"""
from pathlib import Path
from smdgf.generation import Config, PromptBuilder, GenerationRequest, LiteLLMGenerationProvider

# 1. 加载配置
cfg = Config.from_file(Path("config.yaml"))

# 2. 构建 prompt
builder = PromptBuilder(Path("prompts"))
FORMAT = "mcq"  # mcq / qa / open_qa
PROMPT = builder.build(
    "emotion.contrasting",
    format=FORMAT,
    context={"num_questions": 10, "total_rows": 20},
)

# 3. 调用大模型
provider = LiteLLMGenerationProvider()
request = GenerationRequest(
    request_id=f"emotion-gen-{FORMAT}",
    task_id="emotion.contrasting",
    scenario_sample=None,
    prompt_text=PROMPT,
    provider=cfg.provider,
    model=cfg.model,
    seed=42,
)

result = provider.generate(request, cfg.to_provider_config())

if result.status == "completed":
    print(result.response_text)
else:
    print(f"失败: {result.error.message}")
```

运行：

```bash
python generate_emotion.py
```

---

## 五、参考

- `prompts/templates/base_mcq.txt` — 选择题模板
- `prompts/templates/base_qa.txt` — 问答题模板
- `prompts/templates/base_open_qa.txt` — 开放式问答模板
- `prompts/emotion.contrasting/fragment_mcq.txt` — 示例片段
- `src/smdgf/generation/config.py` — 配置封装
- `src/smdgf/generation/prompt_builder.py` — 模板合并
