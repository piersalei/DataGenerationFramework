#!/usr/bin/env python3
"""
Batch-generate prompt fragment files for all D1 dimensions.

Reads the D1 主体心智层.md file, parses dimension definitions,
calls an LLM to generate dimension-specific content for each question type,
then writes fragment files to prompts/<dim_id>.<dim_name_en>/.

Usage:
    python scripts/generate_prompts.py [--dry-run] [--dim 1.3.1]
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent
D1_FILE = PROJECT_ROOT / "D1 主体心智层.md"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
EXISTING_EXAMPLE_DIR = PROMPTS_DIR / "1.2.1.basic_emotion_recognition"

# ---------- dimension registry ----------

DIMENSIONS = {
    # 1.1 认知状态建模
    "1.1.1": {"cn": "信念归因推断", "en": "belief_attribution_inference", "parent": "1.1", "parent_cn": "认知状态建模"},
    "1.1.2": {"cn": "知识状态区分", "en": "knowledge_state_distinction", "parent": "1.1", "parent_cn": "认知状态建模"},
    "1.1.3": {"cn": "信念不一致检测", "en": "belief_inconsistency_detection", "parent": "1.1", "parent_cn": "认知状态建模"},
    "1.1.4": {"cn": "认知偏差识别", "en": "cognitive_bias_identification", "parent": "1.1", "parent_cn": "认知状态建模"},
    # 1.2 情感情绪建模 (already done, skip by default)
    "1.2.1": {"cn": "基本情绪识别", "en": "basic_emotion_recognition", "parent": "1.2", "parent_cn": "情感情绪建模", "done": True},
    "1.2.2": {"cn": "复合情绪解析", "en": "compound_emotion_analysis", "parent": "1.2", "parent_cn": "情感情绪建模", "done": True},
    "1.2.3": {"cn": "隐性情绪推断", "en": "implicit_emotion_inference", "parent": "1.2", "parent_cn": "情感情绪建模", "done": True},
    "1.2.4": {"cn": "情绪调节策略理解", "en": "emotion_regulation_strategy", "parent": "1.2", "parent_cn": "情感情绪建模", "done": True},
    # 1.3 意图动机建模
    "1.3.1": {"cn": "即时行动意图识别", "en": "immediate_intent_recognition", "parent": "1.3", "parent_cn": "意图动机建模"},
    "1.3.2": {"cn": "深层动机溯因", "en": "deep_motivation_attribution", "parent": "1.3", "parent_cn": "意图动机建模"},
    "1.3.3": {"cn": "意图-行为一致性判断", "en": "intent_behavior_consistency", "parent": "1.3", "parent_cn": "意图动机建模"},
    "1.3.4": {"cn": "多层意图层级解析", "en": "multi_level_intent_analysis", "parent": "1.3", "parent_cn": "意图动机建模"},
    # 1.4 人格偏好建模
    "1.4.1": {"cn": "人格特质推断", "en": "personality_trait_inference", "parent": "1.4", "parent_cn": "人格偏好建模"},
    "1.4.2": {"cn": "价值观偏好识别", "en": "value_preference_identification", "parent": "1.4", "parent_cn": "人格偏好建模"},
    "1.4.3": {"cn": "情境化行为风格预测", "en": "contextual_behavior_prediction", "parent": "1.4", "parent_cn": "人格偏好建模"},
    # 1.5 元认知建模
    "1.5.1": {"cn": "认知边界感知", "en": "cognitive_boundary_awareness", "parent": "1.5", "parent_cn": "元认知建模"},
    "1.5.2": {"cn": "信念确定性元判断", "en": "belief_certainty_metajudgment", "parent": "1.5", "parent_cn": "元认知建模"},
    "1.5.3": {"cn": "认知策略选择推理", "en": "cognitive_strategy_reasoning", "parent": "1.5", "parent_cn": "元认知建模"},
}

# ---------- parse D1 file ----------

def parse_d1():
    """Extract parent-level and child-level definitions from D1 file."""
    text = D1_FILE.read_text(encoding="utf-8")
    parent_defs = {}
    child_defs = {}

    # parent: # 1.X 标题\n\n定义段落
    for m in re.finditer(r'^# (\d+\.\d+)\s+(.+?)\n\n(.*?)(?=\n# |\Z)', text, re.M | re.S):
        pid = m.group(1)
        body = m.group(3).strip()
        first_para = body.split("\n\n")[0].strip()
        parent_defs[pid] = first_para

    # child: ## 1.X.Y 标题\n\n定义段落
    for m in re.finditer(r'^## (\d+\.\d+\.\d+)\s+(.+?)\n\n(.*?)(?=\n## |\n# |\Z)', text, re.M | re.S):
        cid = m.group(1)
        body = m.group(3).strip()
        first_para = body.split("\n\n")[0].strip()
        child_defs[cid] = first_para

    return parent_defs, child_defs

# ---------- load existing examples ----------

def load_examples():
    """Load the 1.2.1 examples as reference."""
    examples = {}
    for fname in ["fragment_mcq.txt", "fragment_mcq_multi.txt", "fragment_judge.txt", "fragment_open_qa.txt"]:
        fpath = EXISTING_EXAMPLE_DIR / fname
        if fpath.exists():
            examples[fname] = fpath.read_text(encoding="utf-8")
    return examples

# ---------- LLM generation ----------

def generate_fragment(client, dim_id, dim_info, parent_def, child_def, qtype, example_content):
    """Call Claude to generate a fragment file for one dimension + question type."""

    qtype_map = {
        "fragment_mcq.txt": "单选题（高难度·专家级）",
        "fragment_mcq_multi.txt": "多选题（高难度·专家级）",
        "fragment_judge.txt": "判断+理由题（高难度·专家级）",
        "fragment_open_qa.txt": "开放回答题（高难度·专家级）",
    }

    prompt = f"""你是 SocMind-Bench 评测基准的题目设计专家，精通心理学理论。

我需要你为以下维度生成一个 prompt fragment 文件（用于指导LLM生成评测题目）。

## 目标维度
- 二级维度：{dim_info['parent']} {dim_info['parent_cn']}
- 三级维度：{dim_id} {dim_info['cn']}
- 题目类型：{qtype_map[qtype]}

## 二级维度定义
{parent_def}

## 三级维度定义
{child_def}

## 参考示例
以下是 1.2.1 基本情绪识别 的同类型 fragment 文件，请严格参照其格式和结构，但内容要完全适配目标维度：

```
{example_content}
```

## 要求
1. 严格保持参考示例的整体结构（维度定义 → 难度要求 → 题目格式规范 → 要求）
2. 维度定义部分：二级维度定义根据目标维度适当精简（保留核心含义），三级维度定义完整使用我提供的定义
3. 难度要求：所有题型统一使用高难度（专家级），包含情境复杂度和选项迷惑度两个维度，与示例保持一致
4. 题目格式规范：根据目标维度的专业特点，设计专门的：
   - 情境要求（什么样的场景能测出这个能力）
   - 问题句式（聚焦该维度核心能力的提问方式）
   - 干扰项设计方向（该维度特有的常见错误类型）
   - 如适用，引用相关心理学理论
5. 只输出 fragment 文件的完整内容，不要有任何额外说明

直接输出文件内容："""

    import time
    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise

# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Batch-generate prompt fragments")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without generating")
    parser.add_argument("--dim", type=str, help="Generate only this dimension (e.g. 1.3.1)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    parent_defs, child_defs = parse_d1()
    examples = load_examples()
    qtypes = ["fragment_mcq.txt", "fragment_mcq_multi.txt", "fragment_judge.txt", "fragment_open_qa.txt"]

    # determine which dimensions to process
    to_process = []
    for dim_id, info in DIMENSIONS.items():
        if args.dim and dim_id != args.dim:
            continue
        if info.get("done") and not args.force:
            continue
        to_process.append((dim_id, info))

    print(f"Dimensions to process: {len(to_process)}")
    for dim_id, info in to_process:
        print(f"  {dim_id} {info['cn']} ({info['en']})")

    if args.dry_run:
        print(f"\nTotal files to generate: {len(to_process) * len(qtypes)}")
        return

    client = Anthropic()
    total = len(to_process) * len(qtypes)
    done = 0

    for dim_id, info in to_process:
        dir_name = f"{dim_id}.{info['en']}"
        dim_dir = PROMPTS_DIR / dir_name
        dim_dir.mkdir(parents=True, exist_ok=True)

        parent_def = parent_defs.get(info["parent"], "")
        child_def = child_defs.get(dim_id, "")

        if not child_def:
            print(f"  WARNING: No definition found for {dim_id} in D1 file, skipping")
            continue

        for qtype in qtypes:
            out_path = dim_dir / qtype
            if out_path.exists() and not args.force:
                print(f"  SKIP {out_path.name} (exists)")
                done += 1
                continue

            example = examples.get(qtype, "")
            print(f"  [{done+1}/{total}] Generating {dim_id}/{qtype}...", end=" ", flush=True)

            try:
                content = generate_fragment(client, dim_id, info, parent_def, child_def, qtype, example)
                out_path.write_text(content, encoding="utf-8")
                print("OK")
            except Exception as e:
                print(f"ERROR: {e}")

            done += 1

    print(f"\nDone. Generated {done} files in {PROMPTS_DIR}/")

if __name__ == "__main__":
    main()
