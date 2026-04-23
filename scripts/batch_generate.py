#!/usr/bin/env python3
"""
Batch-generate benchmark data for all D1 dimensions × all formats.

Self-contained: reads prompt templates + fragments, calls LLM API directly,
writes JSONL output. No smdgf installation required.

Usage:
    python3 scripts/batch_generate.py --skip-qc -n 5              # 全量5条
    python3 scripts/batch_generate.py --dim 1.3 -n 5              # 只跑1.3.x
    python3 scripts/batch_generate.py --format mcq -n 5            # 只跑单选
    python3 scripts/batch_generate.py --dry-run                    # 预览
    python3 scripts/batch_generate.py --parallel 4 -n 5            # 4路并发
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
RUNS_DIR = PROJECT_ROOT / "runs"

FORMATS = ["mcq", "mcq_multi", "judge", "open_qa"]

SCENE_DOMAIN_PAIRS = [
    "①学术科研  ②艺术创作",
    "①体育竞技  ②法律纠纷",
    "①医疗健康  ②社区邻里",
    "①旅行探险  ②历史文化考据",
    "①技术发明  ②公益志愿服务",
    "①军事战略  ②环保生态",
    "①宗教信仰  ②金融投资",
    "①教育教学  ②娱乐综艺",
    "①建筑设计  ②农业种植",
    "①新闻媒体  ②心理咨询",
    "①考古发掘  ②电子竞技",
    "①外交谈判  ②手工匠人",
    "①航天航空  ②餐饮美食",
    "①时尚设计  ②消防救援",
    "①哲学辩论  ②物流运输",
    "①音乐演出  ②刑侦破案",
    "①婚恋交友  ②科幻创作",
    "①海洋探索  ②古董鉴定",
    "①创业融资  ②传统武术",
    "①天文观测  ②社工帮扶",
]
TEMPLATE_MAP = {
    "mcq": "base_mcq.txt",
    "mcq_multi": "base_mcq_multi.txt",
    "judge": "base_judge.txt",
    "open_qa": "base_open_qa.txt",
}


# ── config ──────────────────────────────────────────────────

def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── prompt assembly ─────────────────────────────────────────

FORMAT_DOMAIN_OFFSET = {"mcq": 0, "mcq_multi": 5, "judge": 10, "open_qa": 15}


def build_prompt(task_id: str, fmt: str, sample_idx: int = 0) -> str:
    template_path = TEMPLATES_DIR / TEMPLATE_MAP[fmt]
    fragment_path = PROMPTS_DIR / task_id / f"fragment_{fmt}.txt"
    template = template_path.read_text(encoding="utf-8")
    fragment = fragment_path.read_text(encoding="utf-8")
    offset = FORMAT_DOMAIN_OFFSET.get(fmt, 0)
    domains = SCENE_DOMAIN_PAIRS[(offset + sample_idx) % len(SCENE_DOMAIN_PAIRS)]
    fragment = fragment.replace("{{scene_domains}}", domains)
    return template.replace("{{fragment}}", fragment)


# ── LLM call ────────────────────────────────────────────────

def call_llm(prompt: str, cfg: dict, seed: int) -> dict:
    """Call LLM via httpx (works with OpenAI-compatible and Anthropic APIs)."""
    import httpx

    provider = cfg.get("provider", "openai")
    model = cfg.get("model", "gpt-4o")
    api_key = cfg.get("api_key", "")
    api_base = cfg.get("api_base", "").rstrip("/")
    temperature = cfg.get("temperature", 0.7)

    if provider == "anthropic":
        url = f"{api_base}/v1/messages" if api_base else "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": 16384,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        for attempt in range(3):
            try:
                resp = httpx.post(url, headers=headers, json=body, timeout=600)
                resp.raise_for_status()
                data = resp.json()
                text = data["content"][0]["text"]
                return {"ok": True, "text": text, "model": data.get("model", model)}
            except Exception as e:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return {"ok": False, "error": str(e)}
    else:
        url = f"{api_base}/chat/completions" if api_base else "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "messages": [{"role": "user", "content": prompt}],
        }
        for attempt in range(3):
            try:
                resp = httpx.post(url, headers=headers, json=body, timeout=600)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                return {"ok": True, "text": text, "model": data.get("model", model)}
            except Exception as e:
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
                    continue
                return {"ok": False, "error": str(e)}


# ── discovery ───────────────────────────────────────────────

def discover_tasks() -> list[str]:
    tasks = []
    for d in sorted(PROMPTS_DIR.iterdir()):
        if d.is_dir() and d.name.startswith(("1.", "2.", "3.")):
            if any(f.name.startswith("fragment_") for f in d.iterdir() if f.is_file()):
                tasks.append(d.name)
    return tasks


def task_has_format(task_id: str, fmt: str) -> bool:
    return (PROMPTS_DIR / task_id / f"fragment_{fmt}.txt").exists()


# ── single job ──────────────────────────────────────────────

def run_one(task_id: str, fmt: str, sample_idx: int, cfg: dict,
            seed: int, output_dir: Path) -> dict:
    """Generate one sample. Returns result dict."""
    try:
        prompt = build_prompt(task_id, fmt, sample_idx)
        result = call_llm(prompt, cfg, seed + sample_idx)

        record = {
            "task_id": task_id,
            "format": fmt,
            "sample_idx": sample_idx,
            "seed": seed + sample_idx,
            "model": result.get("model", ""),
            "success": result["ok"],
            "timestamp": datetime.now().isoformat(),
        }

        if result["ok"]:
            record["response"] = result["text"]
        else:
            record["error"] = result.get("error", "unknown")

        return record
    except Exception as e:
        return {
            "task_id": task_id,
            "format": fmt,
            "sample_idx": sample_idx,
            "success": False,
            "error": traceback.format_exc(),
        }


# ── main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch-generate all D1 dimensions")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dim", type=str, help="Dimension prefix filter (e.g. 1.3)")
    parser.add_argument("--format", type=str, help="Single format (mcq/mcq_multi/judge/open_qa)")
    parser.add_argument("-n", "--num-samples", type=int, default=1, help="Samples per task+format")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-c", "--config", type=str, default="config.yaml")
    parser.add_argument("--skip-qc", action="store_true", help="(placeholder for compat)")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    tasks = discover_tasks()
    if args.dim:
        tasks = [t for t in tasks if t.startswith(args.dim)]

    formats = [args.format] if args.format else FORMATS

    jobs = []
    for task_id in tasks:
        for fmt in formats:
            if task_has_format(task_id, fmt):
                for si in range(args.num_samples):
                    jobs.append((task_id, fmt, si))

    n_unique = len(set((t, f) for t, f, _ in jobs))
    print(f"{'='*60}")
    print(f"  Batch Generation")
    print(f"  Task×Format combos: {n_unique}")
    print(f"  Samples per combo:  {args.num_samples}")
    print(f"  Total API calls:    {len(jobs)}")
    print(f"  Parallel workers:   {args.parallel}")
    print(f"  Config:             {args.config}")
    print(f"{'='*60}")

    if args.dry_run:
        for task_id, fmt, si in jobs:
            if si == 0:
                print(f"  {task_id:50s} {fmt} x{args.num_samples}")
        print(f"\nDry run. {len(jobs)} API calls would be made.")
        return

    cfg = load_config(args.config)
    batch_name = datetime.now().strftime("batch-%Y%m%d-%H%M%S")
    batch_dir = RUNS_DIR / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nBatch: {batch_name}")
    print(f"Output: {batch_dir}/\n")

    succeeded = 0
    failed = 0
    all_results = []
    start = time.time()

    def process(job):
        task_id, fmt, si = job
        return run_one(task_id, fmt, si, cfg, args.seed, batch_dir)

    if args.parallel <= 1:
        for i, job in enumerate(jobs):
            task_id, fmt, si = job
            label = f"{task_id}/{fmt}[{si}]"
            print(f"[{i+1}/{len(jobs)}] {label} ...", end=" ", flush=True)
            rec = process(job)
            all_results.append(rec)
            if rec["success"]:
                print("OK")
                succeeded += 1
            else:
                print("FAIL")
                failed += 1
                if args.verbose:
                    print(f"  Error: {rec.get('error', '')[:200]}")
    else:
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = {pool.submit(process, job): job for job in jobs}
            done_count = 0
            for future in as_completed(futures):
                done_count += 1
                rec = future.result()
                all_results.append(rec)
                label = f"{rec['task_id']}/{rec['format']}[{rec.get('sample_idx',0)}]"
                status = "OK" if rec["success"] else "FAIL"
                print(f"[{done_count}/{len(jobs)}] {label} {status}")
                if rec["success"]:
                    succeeded += 1
                else:
                    failed += 1
                    if args.verbose:
                        print(f"  Error: {rec.get('error', '')[:200]}")

    # write results: one JSONL per task+format
    for rec in all_results:
        if not rec["success"]:
            continue
        task_dir = batch_dir / rec["task_id"]
        task_dir.mkdir(parents=True, exist_ok=True)
        out_path = task_dir / f"{rec['format']}.jsonl"
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # summary
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  Done in {elapsed:.1f}s")
    print(f"  Succeeded: {succeeded}/{len(jobs)}")
    print(f"  Failed:    {failed}/{len(jobs)}")
    print(f"  Output:    {batch_dir}/")
    print(f"{'='*60}")

    # write batch manifest
    manifest = {
        "batch_name": batch_name,
        "timestamp": datetime.now().isoformat(),
        "config": {k: v for k, v in cfg.items() if k != "api_key"},
        "total_jobs": len(jobs),
        "succeeded": succeeded,
        "failed": failed,
        "elapsed_seconds": round(elapsed, 1),
    }
    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if failed:
        print(f"\nFailed jobs:")
        for rec in all_results:
            if not rec["success"]:
                print(f"  {rec['task_id']}/{rec['format']}[{rec.get('sample_idx',0)}]: {rec.get('error','')[:150]}")


if __name__ == "__main__":
    main()
