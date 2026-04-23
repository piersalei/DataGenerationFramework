#!/usr/bin/env python3
"""将 JSONL（每行一个 JSON 对象）转为单个 JSON 数组文件，便于阅读或交给其它工具。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_jsonl(path: Path) -> list[object]:
    rows: list[object] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{line_no}: JSON 解析失败: {e}") from e
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("jsonl", type=Path, help="输入 .jsonl 路径")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出 .json 路径（默认：与输入同目录、同名 .json）",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="美化缩进（默认 2；设为 0 则紧凑一行）",
    )
    args = p.parse_args()

    if not args.jsonl.is_file():
        sys.exit(f"文件不存在: {args.jsonl}")

    out = args.output
    if out is None:
        out = args.jsonl.with_suffix(".json")

    data = load_jsonl(args.jsonl)
    indent = None if args.indent <= 0 else args.indent
    out.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print(f"已写入 {len(data)} 条记录 → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
