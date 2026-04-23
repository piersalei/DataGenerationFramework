# SocMind-Bench 数据生成框架 — 使用指南

> 一句话理解：你写 prompt 片段（fragment），框架负责拼接模板、调用 LLM、解析响应、质控、导出 JSONL。

---

## 一、环境准备

```bash
git clone <仓库地址>
cd DataGenerationFramework
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install -e ".[dev]"
```

验证安装成功：

```bash
smdgf --help
```

---

## 二、配置模型

编辑项目根目录 `config.yaml`：

```yaml
provider: anthropic          # openai / anthropic / ollama
model: claude-opus-4-6      # 模型名称
api_key: sk-...              # 不填则从环境变量读取（OPENAI_API_KEY / ANTHROPIC_API_KEY）
api_base: https://your-proxy.com  # 第三方代理地址（可选）
temperature: 0.0
```

---

## 三、项目核心概念

### 3.1 维度体系

项目评测 AI 的「社会心智」能力，D1（主体心智层）包含 **5 个二级维度、17 个三级维度**：


| 二级维度       | 三级维度示例           | task_id 示例                           |
| ---------- | ---------------- | ------------------------------------ |
| 1.1 认知状态建模 | 信念归因推断、知识状态区分…   | `1.1.1.belief_attribution_inference` |
| 1.2 情感情绪建模 | 基本情绪识别、复合情绪解析…   | `1.2.1.basic_emotion_recognition`    |
| 1.3 意图动机建模 | 即时意图识别、深层动机溯因…   | `1.3.1.immediate_intent_recognition` |
| 1.4 人格偏好建模 | 人格特质推断、价值观偏好识别…  | `1.4.1.personality_trait_inference`  |
| 1.5 元认知建模  | 认知边界感知、信念确定性元判断… | `1.5.1.cognitive_boundary_awareness` |


### 3.2 题目格式

每个三级维度有 **4 种题型**，各对应一个 fragment 文件：


| 题型     | fragment 文件              | 说明             |
| ------ | ------------------------ | -------------- |
| 单选题    | `fragment_mcq.txt`       | 4选1，考查精确判断     |
| 多选题    | `fragment_mcq_multi.txt` | 多选，考查全面性       |
| 判断+理由题 | `fragment_judge.txt`     | 一致/不一致判断 + 推理链 |
| 开放回答题  | `fragment_open_qa.txt`   | 自由作答，考查深度分析    |


### 3.3 Prompt 拼接机制

```
prompts/
  templates/
    base_mcq.txt            ← 框架模板（定义角色、输出 JSON 格式）
    base_judge.txt
    base_open_qa.txt
    base_mcq_multi.txt
  1.2.1.basic_emotion_recognition/
    fragment_mcq.txt         ← 你写的：维度定义 + 难度要求 + 题目格式规范 + 生成要求
    fragment_judge.txt
    fragment_open_qa.txt
    fragment_mcq_multi.txt
```

运行时，框架把 `base_{format}.txt` 中的 `{{fragment}}` 替换为你的 fragment 内容，组成完整 prompt 发给 LLM。

**你只需要关心 fragment 文件的内容。**

---

## 四、生成数据

### 4.1 单任务生成（`smdgf generate`）

```bash
# 生成 1.2.1 基本情绪识别的单选题，调用模型 1 次（每次生成 10 道题）
smdgf generate 1.2.1.basic_emotion_recognition --format mcq

# 调用模型 3 次，共得到 30 道题
smdgf generate 1.2.1.basic_emotion_recognition --format mcq -n 3

# 生成判断题
smdgf generate 1.2.1.basic_emotion_recognition --format judge

# 跳过质控（调试时用，直接输出 samples.jsonl）
smdgf generate 1.2.1.basic_emotion_recognition --format mcq --skip-qc

# 断点续跑（中断后继续，跳过已完成的请求）
smdgf generate 1.2.1.basic_emotion_recognition --format mcq -n 5 --resume

# 详细输出
smdgf generate 1.2.1.basic_emotion_recognition --format mcq -v
```

**参数速查：**


| 参数                  | 说明                                               | 默认值           |
| ------------------- | ------------------------------------------------ | ------------- |
| `TASK_ID`（位置参数）     | `prompts/` 下的目录名                                 | 必填            |
| `--format, -f`      | `mcq` / `mcq_multi` / `judge` / `open_qa` / `qa` | `mcq`         |
| `--num-samples, -n` | 调用 LLM 的次数（每次按 prompt 要求生成 10 道题）                | `1`           |
| `--seed, -s`        | 随机种子                                             | `42`          |
| `--config, -c`      | 配置文件路径                                           | `config.yaml` |
| `--output, -o`      | 输出根目录                                            | `runs/`       |
| `--batch, -b`       | 批次名（用于分组）                                        | 自动时间戳         |
| `--resume`          | 断点续跑                                             | `False`       |
| `--skip-qc`         | 跳过质控                                             | `False`       |
| `--verbose, -v`     | 详细输出                                             | `False`       |


### 4.2 批量生成（`scripts/batch_generate.py`）

一次跑所有维度的所有题型：

```bash
# 预览要执行的任务（不调用模型）
python scripts/batch_generate.py --dry-run

# 跑所有维度的单选题，每个维度调用 1 次
python scripts/batch_generate.py --format mcq

# 只跑 1.2.x 系列
python scripts/batch_generate.py --dim 1.2

# 每个维度 × 题型调用 3 次，4 线程并行
python scripts/batch_generate.py -n 3 --parallel 4

# 跑全部维度 × 全部题型
python scripts/batch_generate.py
```

**参数速查：**


| 参数           | 说明                           | 默认值           |
| ------------ | ---------------------------- | ------------- |
| `--dry-run`  | 只预览，不调用模型                    | `False`       |
| `--dim`      | 只处理指定前缀的维度（如 `1.2`、`1.3.1`）  | 全部            |
| `--format`   | 只跑指定题型                       | 全部题型          |
| `-n`         | 每个 task × format 组合调用 LLM 几次 | `1`           |
| `--seed`     | 基础种子                         | `42`          |
| `-c`         | 配置文件路径                       | `config.yaml` |
| `--parallel` | 并行线程数                        | `1`           |
| `--skip-qc`  | 跳过质控                         | `False`       |


### 4.3 推荐的生成流程

```bash
# 第一步：先跑一个维度的一种题型验证效果
smdgf generate 1.2.1.basic_emotion_recognition --format mcq --skip-qc -v

# 第二步：检查输出质量
python scripts/batch_export_review.py runs/1.2.1.basic_emotion_recognition/

# 第三步：满意后批量生成
python scripts/batch_generate.py -n 1 --parallel 4
```

---

## 五、输出结构

### 正常流程（带质控）

```
runs/
  1.2.1.basic_emotion_recognition/
    1.2.1.basic_emotion_recognition-mcq-20260423-120000/
      generation/
        manifest.json        # 每个请求的状态、token 用量、原始响应
      qc/
        report.json          # 质控报告（通过率、拒绝原因、待审队列）
      export/
        manifest.json
        artifacts/
          mcq-train.jsonl    # 最终导出数据
```

### 跳过质控（`--skip-qc`）

```
runs/
  1.2.1.basic_emotion_recognition/
    1.2.1.basic_emotion_recognition-mcq-20260423-120000/
      generation/
        manifest.json
      samples.jsonl          # 解析成功的原始样本（无质控、无拆分导出）
```

### 批量生成（`batch_generate.py`）

```
runs/
  batch-20260423-120000/
    manifest.json            # 批次汇总
    1.2.1.basic_emotion_recognition/
      mcq.jsonl
      judge.jsonl
      ...
    1.3.1.immediate_intent_recognition/
      mcq.jsonl
      ...
```

---

## 六、查看与审核生成结果

```bash
# 把批量生成的 JSONL 转成可读 Markdown
python scripts/batch_export_review.py runs/batch-20260423-120000

# 只看某个维度
python scripts/batch_export_review.py runs/batch-20260423-120000 --dim 1.2

# 单次运行的结果审核
python scripts/export_review.py runs/1.2.1.basic_emotion_recognition/xxx/
```

---

## 七、编写 / 修改 Prompt Fragment

### 7.1 Fragment 文件结构

每个 fragment 文件的标准结构：

```
### 维度定义
二级维度和三级维度的定义文本

---

### 难度要求
统一为高难度（专家级），包含情境复杂度和选项迷惑度两个维度

---

### 题目格式规范（题型，共10题）
- 心理学理论基础
- 情境要求
- 题目结构说明
- 干扰项设计方向

### 要求
- 生成10道xxx题，均为高难度（专家级）
- 10道题必须使用10个完全不同的情境场景
- 其他约束...
```

### 7.2 难度设计

所有题型统一使用高难度（专家级），从两个正交维度施压：

**维度A — 情境复杂度：**

- 3个以上主体，各自持有不同或矛盾的信息/立场
- 多轮交互中信息发生反转
- 嵌套心理状态（A认为B认为C觉得……）
- 存在误导性线索和红鲱鱼信息

**维度B — 选项迷惑度（选择题 / 判断题）：**

- 正确答案与最强干扰项仅在细微处有差异
- 干扰项在其他情境下可能成立
- 不得出现一眼可排除的"送分选项"

### 7.3 批量生成新维度的 Fragment

如果需要为新维度自动生成 fragment 文件：

```bash
# 预览哪些维度会被处理
python scripts/generate_prompts.py --dry-run

# 生成单个维度
python scripts/generate_prompts.py --dim 1.3.1

# 覆盖已有文件重新生成
python scripts/generate_prompts.py --dim 1.3.1 --force

# 生成所有缺失维度
python scripts/generate_prompts.py
```

脚本会调用 Claude 参照 `1.2.1` 的模板为每个维度生成 4 种题型的 fragment 文件。

---

## 八、常见问题

### Q: `-n` 参数和 prompt 里的"10道题"是什么关系？

`-n` 控制调用 LLM 的**次数**，每次调用按 prompt 要求生成 **10 道题**。所以 `-n 3` 会得到约 30 道题。

### Q: 生成出来的题目同质化怎么办？

1. prompt 已约束「10道题必须使用10个完全不同的情境场景」
2. 多次调用（`-n > 1`）时换不同 seed：`--seed 42`、`--seed 123`
3. 检查 fragment 中的情境要求是否足够具体

### Q: API 调用中断了怎么办？

加 `--resume` 重跑，框架会自动跳过已完成的请求。

### Q: 怎么切换模型？

改 `config.yaml` 的 `provider` 和 `model` 字段即可。`batch_generate.py` 对 Anthropic 和 OpenAI 兼容 API 都支持。

### Q: 输出的 JSONL 怎么用？

每行是一个 JSON 对象，包含 `context`（情境）、`question`（问题）、`answer`（答案）、`options`（选项，仅选择题）等字段。可以直接用 Python `json.loads()` 逐行读取。

---

## 九、文件索引


| 路径                                       | 说明                       |
| ---------------------------------------- | ------------------------ |
| `config.yaml`                            | 模型配置                     |
| `prompts/templates/base_*.txt`           | 框架模板（通常不需要修改）            |
| `prompts/{task_id}/fragment_*.txt`       | 任务 prompt 片段（**主要编辑对象**） |
| `scripts/batch_generate.py`              | 批量生成脚本                   |
| `scripts/generate_prompts.py`            | 批量生成 fragment 文件         |
| `scripts/batch_export_review.py`         | 批量导出可读 Markdown          |
| `src/smdgf/cli/main.py`                  | CLI 入口                   |
| `src/smdgf/generation/prompt_builder.py` | Prompt 模板拼接逻辑            |
| `src/smdgf/generation/runtime.py`        | 生成运行时（断点续跑、重试）           |
| `src/smdgf/qc/rules.py`                  | 质控规则引擎                   |
| `D1 主体心智层.md`                            | D1 维度体系完整定义              |


