"""将批次生成结果（JSONL）导出为人工审核用的 Markdown 文件。

用法:
    python3.11 scripts/export_review.py runs/1.2.1.basic_emotion_recognition/v1
    python3.11 scripts/export_review.py runs/1.2.1.basic_emotion_recognition/v1 -o review.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FORMAT_LABELS = {
    "mcq": "单选题",
    "mcq_multi": "多选题",
    "judge": "判断+理由题",
    "open_qa": "开放回答题",
}

FORMAT_ORDER = ["mcq", "mcq_multi", "judge", "open_qa"]


def load_samples(batch_dir: Path) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for fmt in FORMAT_ORDER:
        jf = batch_dir / fmt / "samples.jsonl"
        if not jf.exists():
            continue
        samples = []
        for line in jf.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                samples.append(json.loads(line))
        if samples:
            result[fmt] = samples
    return result


def get_option_letter(opts: dict, value: str) -> str:
    for k, v in opts.items():
        if v == value:
            return k
    return value


def render_mcq(samples: list[dict], counter_start: int = 1) -> list[str]:
    lines = []
    for i, s in enumerate(samples):
        num = counter_start + i
        lines.append(f"### 单选题 {num}\n")
        lines.append(f"**【情境】** {s['scene_text']}\n")
        lines.append(f"**【问题】** {s['questions'][0]['text']}\n")

        opts = {}
        if s.get("latent_state", {}).get("mcq_options"):
            opts = s["latent_state"]["mcq_options"][0]

        lines.append("**【选项】**\n")
        for k in sorted(opts.keys()):
            lines.append(f"- {k}. {opts[k]}")
        lines.append("")

        answer_val = s["answers"][0]["value"]
        answer_letter = get_option_letter(opts, answer_val)
        lines.append(f"**【答案】** {answer_letter}\n")

        distractor = s.get("latent_state", {}).get("干扰项设计说明")
        if distractor and isinstance(distractor, dict):
            lines.append("**【干扰项设计方向说明】**\n")
            for dk, dv in distractor.items():
                lines.append(f"- {dk}：{dv}")
            lines.append("")

        lines.append("---\n")
    return lines


def render_mcq_multi(samples: list[dict], counter_start: int = 1) -> list[str]:
    lines = []
    for i, s in enumerate(samples):
        num = counter_start + i
        lines.append(f"### 多选题 {num}\n")
        lines.append(f"**【情境】** {s['scene_text']}\n")
        lines.append(f"**【问题】** {s['questions'][0]['text']}\n")

        opts = {}
        if s.get("latent_state", {}).get("mcq_options"):
            opts = s["latent_state"]["mcq_options"][0]

        lines.append("**【选项】**\n")
        for k in sorted(opts.keys()):
            lines.append(f"- {k}. {opts[k]}")
        lines.append("")

        answer_val = s["answers"][0]["value"]
        lines.append(f"**【答案】** {answer_val}\n")

        distractor = s.get("latent_state", {}).get("干扰项设计说明")
        if distractor and isinstance(distractor, dict):
            lines.append("**【干扰项设计方向说明】**\n")
            for dk, dv in distractor.items():
                lines.append(f"- {dk}：{dv}")
            lines.append("")

        lines.append("---\n")
    return lines


def render_judge(samples: list[dict], counter_start: int = 1) -> list[str]:
    lines = []
    for i, s in enumerate(samples):
        num = counter_start + i
        lines.append(f"### 判断+理由题 {num}\n")
        lines.append(f"**【情境】** {s['scene_text']}\n")
        lines.append(f"**【判断问题】** {s['questions'][0]['text']}\n")
        lines.append(f"**【判断结论】** {s['answers'][0]['value']}\n")

        rationale = s["answers"][0].get("rationale")
        if rationale:
            try:
                r = json.loads(rationale)
                lines.append("**【推理要点】**\n")
                lines.append(f"1. **可观测信号描述：** {r.get('可观测信号描述', '')}")
                lines.append(f"2. **信号与信念落差识别：** {r.get('信号与信念落差识别', '')}")
                lines.append(f"3. **真实信念推断结论：** {r.get('真实信念推断结论', '')}")
                lines.append("")
            except (json.JSONDecodeError, TypeError):
                lines.append(f"**【推理要点】** {rationale}\n")

        lines.append("---\n")
    return lines


def render_open_qa(samples: list[dict], counter_start: int = 1) -> list[str]:
    lines = []
    for i, s in enumerate(samples):
        num = counter_start + i
        lines.append(f"### 开放回答题 {num}\n")
        lines.append(f"**【情境】** {s['scene_text']}\n")
        lines.append(f"**【问题】** {s['questions'][0]['text']}\n")

        answer = s["answers"][0]["value"]
        lines.append(f"**【参考答案要点】** {answer}\n")

        rationale = s["answers"][0].get("rationale")
        if rationale:
            lines.append(f"**【解析】** {rationale}\n")

        lines.append("---\n")
    return lines


RENDERERS = {
    "mcq": render_mcq,
    "mcq_multi": render_mcq_multi,
    "judge": render_judge,
    "open_qa": render_open_qa,
}


def export_review_md(batch_dir: Path, output_path: Path | None = None) -> Path:
    batch_dir = Path(batch_dir)
    task_id = batch_dir.parent.name
    batch_name = batch_dir.name

    all_data = load_samples(batch_dir)
    if not all_data:
        print(f"未找到任何 samples.jsonl: {batch_dir}")
        sys.exit(1)

    lines = [
        f"# {task_id} 审核文档",
        f"",
        f"**批次：** {batch_name}",
        f"",
    ]

    total = sum(len(v) for v in all_data.values())
    lines.append(f"**题目总数：** {total}\n")

    for fmt in FORMAT_ORDER:
        samples = all_data.get(fmt)
        if not samples:
            continue
        label = FORMAT_LABELS.get(fmt, fmt)
        lines.append(f"## {label}（共 {len(samples)} 题）\n")
        renderer = RENDERERS[fmt]
        lines.extend(renderer(samples))

    if output_path is None:
        output_path = batch_dir / "review.md"

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="将批次 JSONL 导出为审核 Markdown")
    parser.add_argument("batch_dir", type=Path, help="批次目录路径，如 runs/1.2.1.xxx/v1")
    parser.add_argument("-o", "--output", type=Path, default=None, help="输出文件路径，默认写到批次目录下 review.md")
    args = parser.parse_args()

    out = export_review_md(args.batch_dir, args.output)
    print(f"已生成审核文档: {out}")
