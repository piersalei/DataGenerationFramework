#!/usr/bin/env python3
"""
将 batch_generate.py 的输出批量导出为人工审核用的 Markdown 文件。

用法:
    python3 scripts/batch_export_review.py runs/batch-20260422-223335
    python3 scripts/batch_export_review.py runs/batch-20260422-223335 --dim 1.2
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORMAT_LABELS = {
    "mcq": "单选题",
    "mcq_multi": "多选题",
    "judge": "判断+理由题",
    "open_qa": "开放回答题",
}
FORMAT_ORDER = ["mcq", "mcq_multi", "judge", "open_qa"]

DIM_NAMES = {
    "1.1": "认知状态建模",
    "1.2": "情感情绪建模",
    "1.3": "意图动机建模",
    "1.4": "人格偏好建模",
    "1.5": "元认知建模",
}


def _fix_json(text: str) -> str:
    """Fix common LLM JSON issues: unescaped quotes inside strings."""
    result = []
    in_string = False
    i = 0
    while i < len(text):
        c = text[i]
        if c == '\\' and in_string:
            result.append(c)
            i += 1
            if i < len(text):
                result.append(text[i])
            i += 1
            continue
        if c == '"':
            if not in_string:
                in_string = True
                result.append(c)
            else:
                next_non_ws = i + 1
                while next_non_ws < len(text) and text[next_non_ws] in ' \t\n\r':
                    next_non_ws += 1
                if next_non_ws < len(text) and text[next_non_ws] in ':,}]\n\r':
                    in_string = False
                    result.append(c)
                elif i + 1 >= len(text):
                    in_string = False
                    result.append(c)
                else:
                    result.append('\\"')
            i += 1
            continue
        result.append(c)
        i += 1
    return ''.join(result)


def extract_json(text: str):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        m = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
        if m:
            text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_fix_json(text))


def load_responses(batch_dir: Path, task_id: str) -> dict[str, list]:
    """Load and parse all responses for a task."""
    task_dir = batch_dir / task_id
    result = {}
    for fmt in FORMAT_ORDER:
        jf = task_dir / f"{fmt}.jsonl"
        if not jf.exists():
            continue
        items = []
        for line in jf.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if not rec.get("success"):
                continue
            try:
                parsed = extract_json(rec["response"])
                if isinstance(parsed, list):
                    items.extend(parsed)
                elif isinstance(parsed, dict):
                    items.append(parsed)
            except (json.JSONDecodeError, KeyError):
                continue
        if items:
            result[fmt] = items
    return result


def render_mcq_item(item: dict, num: int) -> list[str]:
    lines = [f"### 单选题 {num}\n"]
    label = item.get("情境标签", "")
    if label:
        lines.append(f"**【情境标签】** {label}\n")
    lines.append(f"**【情境】** {item.get('情境', '')}\n")
    lines.append(f"**【问题】** {item.get('问题', '')}\n")
    lines.append("**【选项】**\n")
    for k in ["A", "B", "C", "D", "E"]:
        if k in item:
            lines.append(f"- {k}. {item[k]}")
    lines.append("")
    lines.append(f"**【答案】** {item.get('答案', '')}\n")
    distractor = item.get("干扰项设计说明") or item.get("干扰项设计方向说明")
    if distractor and isinstance(distractor, dict):
        lines.append("**【干扰项设计说明】**\n")
        for dk, dv in distractor.items():
            lines.append(f"- **{dk}**：{dv}")
        lines.append("")
    lines.append("---\n")
    return lines


def render_mcq_multi_item(item: dict, num: int) -> list[str]:
    lines = [f"### 多选题 {num}\n"]
    label = item.get("情境标签", "")
    if label:
        lines.append(f"**【情境标签】** {label}\n")
    lines.append(f"**【情境】** {item.get('情境', '')}\n")
    lines.append(f"**【问题】** {item.get('问题', '')}\n")
    lines.append("**【选项】**\n")
    for k in ["A", "B", "C", "D", "E"]:
        if k in item:
            lines.append(f"- {k}. {item[k]}")
    lines.append("")
    lines.append(f"**【答案】** {item.get('答案', '')}\n")
    distractor = item.get("干扰项设计说明") or item.get("干扰项设计方向说明")
    if distractor and isinstance(distractor, dict):
        lines.append("**【干扰项设计说明】**\n")
        for dk, dv in distractor.items():
            lines.append(f"- **{dk}**：{dv}")
        lines.append("")
    lines.append("---\n")
    return lines


def render_judge_item(item: dict, num: int) -> list[str]:
    lines = [f"### 判断+理由题 {num}\n"]
    label = item.get("情境标签", "")
    if label:
        lines.append(f"**【情境标签】** {label}\n")
    lines.append(f"**【情境】** {item.get('情境', '')}\n")
    lines.append(f"**【判断问题】** {item.get('判断问题', '')}\n")
    lines.append(f"**【判断结论】** {item.get('判断结论', '')}\n")
    reasoning = item.get("推理要点", {})
    if reasoning and isinstance(reasoning, dict):
        lines.append("**【推理要点】**\n")
        for idx, (rk, rv) in enumerate(reasoning.items(), 1):
            lines.append(f"{idx}. **{rk}：** {rv}")
        lines.append("")
    elif reasoning:
        lines.append(f"**【推理要点】** {reasoning}\n")
    lines.append("---\n")
    return lines


def render_open_qa_item(item: dict, num: int) -> list[str]:
    lines = [f"### 开放回答题 {num}\n"]
    label = item.get("情境标签", "")
    if label:
        lines.append(f"**【情境标签】** {label}\n")
    lines.append(f"**【情境】** {item.get('情境', '')}\n")

    qa_list = item.get("问题列表", [])
    if qa_list:
        for qi, qa in enumerate(qa_list, 1):
            lines.append(f"**【问题 {qi}】** {qa.get('问题', '')}\n")
            lines.append(f"**【参考答案】** {qa.get('答案', '')}\n")
            explanation = qa.get("解析", "")
            if explanation:
                lines.append(f"**【解析】** {explanation}\n")
    else:
        question = item.get("问题", "")
        if isinstance(question, list):
            lines.append("**【问题】**\n")
            for q in question:
                lines.append(f"- {q}")
            lines.append("")
        else:
            lines.append(f"**【问题】** {question}\n")

        answer = item.get("参考答案要点", item.get("答案", ""))
        if isinstance(answer, list):
            lines.append("**【参考答案要点】**\n")
            for a in answer:
                lines.append(f"- {a}")
            lines.append("")
        elif isinstance(answer, dict):
            lines.append("**【参考答案要点】**\n")
            for ak, av in answer.items():
                lines.append(f"- **{ak}：** {av}")
            lines.append("")
        else:
            lines.append(f"**【参考答案要点】** {answer}\n")

    lines.append("---\n")
    return lines


RENDERERS = {
    "mcq": render_mcq_item,
    "mcq_multi": render_mcq_multi_item,
    "judge": render_judge_item,
    "open_qa": render_open_qa_item,
}


def export_task(batch_dir: Path, task_id: str, output_dir: Path) -> Path | None:
    all_data = load_responses(batch_dir, task_id)
    if not all_data:
        return None

    # extract dim number for title
    dim_num = ".".join(task_id.split(".")[:2])
    dim_name = DIM_NAMES.get(dim_num, "")
    subdim = task_id.split(".")[0:3]
    subdim_id = ".".join(subdim) if len(subdim) >= 3 else task_id

    lines = [
        f"# {task_id} 审核文档",
        f"",
        f"**二级维度：** {dim_num} {dim_name}",
        f"**三级维度：** {subdim_id}",
        f"**批次：** {batch_dir.name}",
        f"",
    ]

    total = sum(len(v) for v in all_data.values())
    lines.append(f"**题目总数：** {total}\n")

    for fmt in FORMAT_ORDER:
        items = all_data.get(fmt)
        if not items:
            continue
        label = FORMAT_LABELS.get(fmt, fmt)
        lines.append(f"## {label}（共 {len(items)} 题）\n")
        renderer = RENDERERS[fmt]
        for idx, item in enumerate(items, 1):
            lines.extend(renderer(item, idx))

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{task_id}.review.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="批量导出审核Markdown")
    parser.add_argument("batch_dir", type=Path, help="批次目录 (runs/batch-xxx)")
    parser.add_argument("--dim", type=str, help="只导出某个维度前缀 (如 1.2)")
    parser.add_argument("-o", "--output", type=Path, default=None, help="输出目录，默认 <batch_dir>/review/")
    args = parser.parse_args()

    batch_dir = args.batch_dir
    output_dir = args.output or (batch_dir / "review")

    task_dirs = sorted([
        d.name for d in batch_dir.iterdir()
        if d.is_dir() and d.name.startswith(("1.", "2.", "3."))
    ])

    if args.dim:
        task_dirs = [t for t in task_dirs if t.startswith(args.dim)]

    print(f"Batch: {batch_dir.name}")
    print(f"Tasks: {len(task_dirs)}")
    print(f"Output: {output_dir}/\n")

    exported = 0
    for task_id in task_dirs:
        out = export_task(batch_dir, task_id, output_dir)
        if out:
            total = sum(
                len(v) for v in load_responses(batch_dir, task_id).values()
            )
            print(f"  {task_id}: {total} items -> {out.name}")
            exported += 1
        else:
            print(f"  {task_id}: no data, skipped")

    # generate index
    index_lines = ["# 审核文档索引\n", f"**批次：** {batch_dir.name}\n"]
    for task_id in task_dirs:
        md_file = output_dir / f"{task_id}.review.md"
        if md_file.exists():
            index_lines.append(f"- [{task_id}]({task_id}.review.md)")
    (output_dir / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")

    print(f"\nDone. Exported {exported} review files to {output_dir}/")


if __name__ == "__main__":
    main()
