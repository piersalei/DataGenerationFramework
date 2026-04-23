"""Generation CLI: smdgf generate command."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from smdgf.generation import (
    Config,
    GenerationRequest,
    GenerationRuntime,
    DirectHTTPProvider,
    PromptBuilder,
)
from smdgf.export.manifest import write_export_manifest
from smdgf.export.mcq import export_sample_to_mcq
from smdgf.export.qa import export_sample_to_open_qa, export_sample_to_qa
from smdgf.qc import QualityCandidate, RuleEngine
from smdgf.qc.reports import build_qc_report
from smdgf.schemas.canonical import (
    CanonicalAnswer,
    CanonicalQuestion,
    CanonicalSample,
    ProvenanceRecord,
)


app = typer.Typer(help="生成任务数据: 构建 prompt → 调用大模型 → 质控 → 导出.")


# ─────────────────────────────────────────────────────────────
# 默认响应解析器：把模型输出文本解析为 CanonicalSample
# 用户可继承 ResponseParser 覆盖 parse() 自定义解析逻辑
# ─────────────────────────────────────────────────────────────

class ResponseParser:
    """解析模型 response_text 为多条 CanonicalSample（每样本一题一答，便于导出与质检）。"""

    def parse(self, response_text: str, task_id: str, request_id: str, seed: int | None = None) -> list[CanonicalSample]:
        payload = self._extract_json(response_text)
        samples = self._normalize(payload)
        if not samples:
            raise ValueError(f"无法从模型输出解析出数据: {response_text[:200]}")

        if not isinstance(samples[0], dict):
            raise ValueError(f"无法从模型输出解析出数据: {response_text[:200]}")

        # 判断+理由题：{ 情境, 判断问题, 判断结论, 推理要点 }
        if self._is_judge_item(samples[0]):
            return self._parse_judge_items(samples, task_id, request_id, seed)

        # 开放回答题：{ 情境, 问题: [...], 参考答案要点: [...] }
        if self._is_open_answer_item(samples[0]):
            return self._parse_open_answer_items(samples, task_id, request_id, seed)

        # 嵌套：{ 情境, 问题列表|questions: [ { 问题, 答案, ... }, ... ] } → 每道小题一条样本
        if self._is_nested_scenario_block(samples[0]):
            return self._parse_nested_scenario(samples[0], task_id, request_id, seed)

        # 扁平：Json 数组，每项一行表格 { 情境, 问题编号, 问题, A..D, 答案 } → 每行一条样本
        if self._is_flat_mcq_row_list(samples):
            return self._parse_flat_mcq_rows(samples, task_id, request_id, seed)

        raise ValueError(f"无法识别的模型输出结构: {response_text[:200]}")

    def _is_nested_scenario_block(self, block: dict) -> bool:
        ql = block.get("问题列表") or block.get("questions")
        if not isinstance(ql, list) or not ql or not isinstance(ql[0], dict):
            return False
        q0 = ql[0]
        return "问题" in q0 or "question" in q0

    def _is_flat_mcq_row_list(self, rows: list) -> bool:
        return all(
            isinstance(r, dict) and ("问题" in r or "question" in r) and not self._is_nested_scenario_block(r)
            for r in rows
        )

    def _parse_nested_scenario(
        self, s: dict, task_id: str, request_id: str, seed: int | None
    ) -> list[CanonicalSample]:
        scene_text = (s.get("情境") or s.get("scene") or "").strip() or None
        out: list[CanonicalSample] = []
        inner_idx = 0

        for q_data in s.get("问题列表") or s.get("questions", []):
            if not isinstance(q_data, dict):
                continue
            q_id = q_data.get("问题编号") or q_data.get("id") or inner_idx
            q_text = (q_data.get("问题") or q_data.get("question") or "").strip()
            if not q_text:
                continue
            q_key = str(q_id)
            answer_val = q_data.get("答案") or q_data.get("answer") or ""
            rationale = q_data.get("解析") or q_data.get("rationale", "")

            sid = f"{request_id}-n{inner_idx}"
            inner_idx += 1
            out.append(CanonicalSample(
                sample_id=sid,
                task_id=task_id,
                scene_text=scene_text,
                questions=[CanonicalQuestion(
                    question_id=q_key,
                    text=q_text,
                    target_capability=task_id,
                )],
                answers=[CanonicalAnswer(
                    question_id=q_key,
                    value=answer_val,
                    rationale=rationale if rationale else None,
                )],
                provenance=ProvenanceRecord(
                    source="llm-generation",
                    model_id="",
                    seed=seed,
                ),
            ))

        if not out:
            raise ValueError(f"嵌套结构中未解析到任何小题: {request_id}")
        return out

    def _parse_flat_mcq_rows(
        self, rows: list[dict], task_id: str, request_id: str, seed: int | None
    ) -> list[CanonicalSample]:
        """解析「多行表格」Json 数组：每行一条样本；答案列可为选项字母或原文。"""
        out: list[CanonicalSample] = []
        out_idx = 0

        for row in rows:
            if not isinstance(row, dict):
                continue
            scene = (row.get("情境") or row.get("scene") or "").strip() or None
            q_text = (row.get("问题") or row.get("question") or "").strip()
            if not q_text:
                continue

            sid = f"{request_id}-r{out_idx}"
            out_idx += 1
            answer_val = self._resolve_flat_row_answer(row)
            opts = {k: row[k] for k in ("A", "B", "C", "D", "E") if k in row}

            label = (row.get("情境标签") or "").strip()
            distractor_info = row.get("干扰项设计说明")
            latent = {}
            if opts:
                latent["mcq_options"] = [opts]
            if label:
                latent["情境标签"] = label
            if distractor_info:
                latent["干扰项设计说明"] = distractor_info

            out.append(CanonicalSample(
                sample_id=sid,
                task_id=task_id,
                scene_text=scene,
                latent_state=latent,
                questions=[CanonicalQuestion(
                    question_id="q0",
                    text=q_text,
                    target_capability=task_id,
                )],
                answers=[CanonicalAnswer(
                    question_id="q0",
                    value=answer_val,
                    rationale=None,
                )],
                provenance=ProvenanceRecord(
                    source="llm-generation",
                    model_id="",
                    seed=seed,
                ),
            ))

        if not out:
            raise ValueError(f"扁平表格中未解析到任何小题: {request_id}")
        return out

    @staticmethod
    def _resolve_flat_row_answer(row: dict) -> str:
        raw = row.get("答案") or row.get("answer") or ""
        s = str(raw).strip()
        if len(s) == 1 and s.upper() in "ABCDE":
            key = s.upper()
            cell = row.get(key) if key in row else row.get(s.lower())
            if cell is not None and str(cell).strip():
                return str(cell).strip()
        return s

    def _is_judge_item(self, item: dict) -> bool:
        return "判断问题" in item or "判断结论" in item

    def _is_open_answer_item(self, item: dict) -> bool:
        return "参考答案要点" in item and isinstance(item.get("问题"), list)

    def _parse_judge_items(
        self, items: list[dict], task_id: str, request_id: str, seed: int | None
    ) -> list[CanonicalSample]:
        out: list[CanonicalSample] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            scene = (item.get("情境") or "").strip() or None
            q_text = (item.get("判断问题") or "").strip()
            conclusion = (item.get("判断结论") or "").strip()
            reasoning = item.get("推理要点", {})
            label = (item.get("情境标签") or "").strip()

            sid = f"{request_id}-j{idx}"
            out.append(CanonicalSample(
                sample_id=sid,
                task_id=task_id,
                scene_text=scene,
                latent_state={"情境标签": label} if label else {},
                questions=[CanonicalQuestion(
                    question_id="q0",
                    text=q_text,
                    target_capability=task_id,
                )],
                answers=[CanonicalAnswer(
                    question_id="q0",
                    value=conclusion,
                    rationale=json.dumps(reasoning, ensure_ascii=False) if reasoning else None,
                )],
                provenance=ProvenanceRecord(
                    source="llm-generation",
                    model_id="",
                    seed=seed,
                ),
            ))
        if not out:
            raise ValueError(f"判断题中未解析到任何小题: {request_id}")
        return out

    def _parse_open_answer_items(
        self, items: list[dict], task_id: str, request_id: str, seed: int | None
    ) -> list[CanonicalSample]:
        out: list[CanonicalSample] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            scene = (item.get("情境") or "").strip() or None
            questions_raw = item.get("问题", [])
            answers_raw = item.get("参考答案要点", [])
            label = (item.get("情境标签") or "").strip()

            q_text = "\n".join(questions_raw) if isinstance(questions_raw, list) else str(questions_raw)
            a_text = "\n".join(answers_raw) if isinstance(answers_raw, list) else str(answers_raw)

            sid = f"{request_id}-o{idx}"
            out.append(CanonicalSample(
                sample_id=sid,
                task_id=task_id,
                scene_text=scene,
                latent_state={"情境标签": label} if label else {},
                questions=[CanonicalQuestion(
                    question_id="q0",
                    text=q_text,
                    target_capability=task_id,
                )],
                answers=[CanonicalAnswer(
                    question_id="q0",
                    value=a_text,
                    rationale=None,
                )],
                provenance=ProvenanceRecord(
                    source="llm-generation",
                    model_id="",
                    seed=seed,
                ),
            ))
        if not out:
            raise ValueError(f"开放题中未解析到任何小题: {request_id}")
        return out

    def _extract_json(self, text: str) -> Any:
        """从模型输出中提取 JSON（支持 Markdown 代码块或裸 JSON）。"""
        text = text.strip()
        # 去掉 Markdown 代码块包裹
        m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if m:
            text = m.group(1)
        else:
            # 尝试找 JSON 数组或对象
            m = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
            if m:
                text = m.group(1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            text = self._fix_unescaped_quotes(text)
            return json.loads(text)

    @staticmethod
    def _fix_unescaped_quotes(text: str) -> str:
        """修复 JSON 字符串值内未转义的双引号（LLM 常见问题）。"""
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

    def _normalize(self, payload: Any) -> list[dict]:
        """把各种 JSON 结构 normalize 为 list[dict]。"""
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            has_scene = "情境" in payload or "scene" in payload
            inner_questions = None
            if isinstance(payload.get("问题列表"), list):
                inner_questions = payload["问题列表"]
            elif isinstance(payload.get("questions"), list):
                inner_questions = payload["questions"]
            # 单个场景对象：{ 情境, 问题列表: [...] }，不能把「问题列表」当成顶层数组拆开
            if has_scene and inner_questions is not None:
                return [payload]
            for key in ("题目列表", "问题列表", "scenarios", "data", "items", "questions"):
                if key in payload:
                    val = payload[key]
                    return val if isinstance(val, list) else [val]
            return [payload]
        return []


# ─────────────────────────────────────────────────────────────
# 干扰项策略
# ─────────────────────────────────────────────────────────────

EMOTION_POOL = ["生气", "高兴", "悲伤", "尴尬", "担心", "感动", "嫉妒", "后悔"]


class FixedDistractorStrategy:
    """从固定情绪池中选干扰项。"""
    strategy_id = "fixed-emotion-pool"

    def generate(self, sample, question, answer):
        correct = str(answer.value)
        opts = [e for e in EMOTION_POOL if e != correct]
        import random
        random.shuffle(opts)
        return opts[:3]


# ─────────────────────────────────────────────────────────────
# generate 命令
# ─────────────────────────────────────────────────────────────

@app.command(name="generate")
def generate_cmd(
    task_id: str = typer.Argument(..., help="任务 ID，对应 prompts/{task_id}/ 目录"),
    format: str = typer.Option("mcq", "--format", "-f", help="输出格式: mcq / qa / open_qa"),
    config: Path = typer.Option(Path("config.yaml"), "--config", "-c", help="配置文件路径"),
    output: Path = typer.Option(Path("runs"), "--output", "-o", help="输出根目录"),
    batch: str = typer.Option(None, "--batch", "-b", help="批次名（同一批次的不同题型归到同一目录，不填则用时间戳）"),
    num_samples: int = typer.Option(1, "--num-samples", "-n", help="生成几条数据"),
    seed: int = typer.Option(42, "--seed", "-s", help="随机种子"),
    resume: bool = typer.Option(False, "--resume", help="从断点续跑（跳过已完成的请求）"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="打印详细输出"),
    skip_qc: bool = typer.Option(False, "--skip-qc", help="跳过质控，直接导出所有数据"),
) -> None:
    """执行完整流水线：构建 prompt → 调用大模型 → 质控 → 导出。"""
    # 1. 加载配置
    if not config.exists():
        typer.secho(f"配置文件不存在: {config}，使用默认配置", fg=typer.colors.YELLOW)
        cfg = Config("openai")
    else:
        cfg = Config.from_file(config)

    # 2. 构建 prompt
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        typer.secho(f"prompts 目录不存在: {prompts_dir}", fg=typer.colors.RED)
        raise typer.Exit(1)

    builder = PromptBuilder(prompts_dir)
    available = builder.list_formats()
    if format not in available:
        typer.secho(f"不支持的格式: {format}，可用: {available}", fg=typer.colors.RED)
        raise typer.Exit(1)

    num_questions = num_samples * 2  # 每组 2 题
    try:
        prompt_text = builder.build(task_id, format=format, context={"num_questions": num_questions, "total_rows": num_questions * 2})
    except FileNotFoundError:
        typer.secho(f"未找到 fragment: prompts/{task_id}/fragment_{format}.txt", fg=typer.colors.RED)
        raise typer.Exit(1)

    if verbose:
        typer.secho(f"[Prompt 构建完成，长度: {len(prompt_text)} 字符]", fg=typer.colors.CYAN)

    # 3. 构建请求
    batch_name = batch or datetime.now().strftime('%Y%m%d-%H%M%S')
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    run_id = f"{task_id}-{format}-{timestamp}"
    output_dir = output / task_id / batch_name / format
    (output_dir / "generation").mkdir(parents=True, exist_ok=True)

    requests = []
    for i in range(num_samples):
        requests.append(GenerationRequest(
            request_id=f"{task_id}-{format}-{i}",
            task_id=task_id,
            scenario_sample=None,
            prompt_text=prompt_text,
            provider=cfg.provider,
            model=cfg.model,
            seed=seed + i,
        ))

    # 4. 调用大模型
    typer.secho(f"[调用大模型: {cfg.provider}/{cfg.model}]", fg=typer.colors.GREEN)
    runtime = GenerationRuntime(
        provider=DirectHTTPProvider(),
        provider_config=cfg.to_provider_config(),
        checkpoint_path=output_dir / "generation" / "manifest.json",
        max_retries=2,
    )
    manifest = runtime.run(run_id, requests, resume=resume)

    completed = [item for item in manifest.items if item.result and item.result.status == "completed"]
    typer.secho(f"[生成完成: {len(completed)}/{len(manifest.items)} 成功]", fg=typer.colors.GREEN)

    failed_items = [
        item
        for item in manifest.items
        if item.status == "failed" or (item.result and item.result.status == "failed")
    ]
    if failed_items:
        typer.secho("生成失败明细（便于排查 API / 模型 / 代理配置）:", fg=typer.colors.RED)
        for item in failed_items:
            err = item.error or (item.result.error if item.result else None)
            if err:
                typer.secho(f"  • {item.request_id}: [{err.error_type}] {err.message}", fg=typer.colors.RED)
            elif item.result and item.result.response_text is None:
                typer.secho(f"  • {item.request_id}: 无响应内容（status={item.result.status}）", fg=typer.colors.RED)
            else:
                typer.secho(f"  • {item.request_id}: 未知失败（请用 --verbose 重试）", fg=typer.colors.RED)

    if not completed:
        typer.secho("没有成功的数据，跳过质控和导出", fg=typer.colors.YELLOW)
        return

    # 5. 质控（可选）
    if skip_qc:
        typer.secho("[跳过质控，直接导出...]", fg=typer.colors.YELLOW)
        parsed_samples = []
        parser = ResponseParser()
        for item in completed:
            try:
                split = parser.parse(
                    item.result.response_text,
                    task_id,
                    item.request_id,
                    seed=item.seed,
                )
                for sample in split:
                    sample.provenance.model_id = item.result.model_id
                    sample.scene_payload["generation_request_id"] = item.request_id
                    parsed_samples.append((item, sample))
                typer.secho(f"  ✓ {item.request_id}: 解析 {len(split)} 条小题", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"  ✗ {item.request_id}: 解析失败 {e}", fg=typer.colors.RED)
        canonical_samples = [(item, sample, None) for item, sample in parsed_samples]
    else:
        typer.secho("[执行质控...]", fg=typer.colors.CYAN)
        parser = ResponseParser()
        engine = RuleEngine()
        qc_decisions = []
        canonical_samples = []

        for item in completed:
            try:
                split = parser.parse(
                    item.result.response_text,
                    task_id,
                    item.request_id,
                    seed=item.seed,
                )
                for sample in split:
                    sample.provenance.model_id = item.result.model_id
                    sample.scene_payload["generation_request_id"] = item.request_id

                    decision = engine.evaluate(QualityCandidate(
                        candidate_id=sample.sample_id,
                        canonical_sample=sample,
                        generation_result=item.result,
                        generation_run_id=run_id,
                        scenario_sample_id=sample.sample_id,
                        prompt_fingerprint=item.prompt_fingerprint,
                    ))
                    qc_decisions.append(decision)
                    canonical_samples.append((item, sample, decision))
                typer.secho(f"  ✓ {item.request_id}: 质控 {len(split)} 条小题", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"  解析/质控失败 {item.request_id}: {e}", fg=typer.colors.RED)

        qc_report = build_qc_report(run_id, qc_decisions)
        qc_report_path = output_dir / "qc" / "report.json"
        qc_report_path.parent.mkdir(parents=True, exist_ok=True)
        qc_report_path.write_text(qc_report.model_dump_json(indent=2), encoding="utf-8")
        typer.secho(f"[质控完成: 接受 {qc_report.metrics.accepted} / {qc_report.metrics.total_candidates}]", fg=typer.colors.CYAN)

    # 6. 导出
    typer.secho("[导出数据...]", fg=typer.colors.CYAN)
    all_records = []
    distractor_strategy = FixedDistractorStrategy()

    for item, sample, decision in canonical_samples:
        if not skip_qc and decision is not None and decision.status != "accept":
            if verbose:
                typer.secho(f"  导出跳过（质控拒绝）: {sample.sample_id}", fg=typer.colors.YELLOW)
            continue

        records = []
        records.extend(export_sample_to_qa(sample, split="train"))
        records.extend(export_sample_to_open_qa(sample, split="train"))
        records.extend(export_sample_to_mcq(sample, distractor_strategy, split="train"))
        all_records.extend(records)

        if verbose:
            typer.secho(f"  ✓ {sample.sample_id}: {len(records)} 条记录", fg=typer.colors.GREEN)

    if skip_qc:
        # 跳过质控时，直接把解析好的 canonical sample 写到一个 JSONL 文件
        raw_path = output_dir / "samples.jsonl"
        lines = [sample.model_dump_json(ensure_ascii=False) for _, sample in parsed_samples]
        raw_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        typer.secho(f"[导出完成: {len(parsed_samples)} 条记录 → {raw_path}]", fg=typer.colors.GREEN)
        typer.secho(f"\n结果目录: {output_dir}")
        return

    if all_records:
        export_manifest = write_export_manifest(
            output_dir / "export",
            run_id,
            all_records,
            config_snapshot={"model": cfg.model, "task_id": task_id, "format": format, "num_samples": num_samples},
            source_qc_run_id=run_id,
        )
        formats = ", ".join(export_manifest.formats)
        typer.secho(f"[导出完成: {len(all_records)} 条记录，格式: {formats}]", fg=typer.colors.GREEN)
    else:
        typer.secho("没有通过质控的数据，跳过导出", fg=typer.colors.YELLOW)

    typer.secho(f"\n结果目录: {output_dir}")
