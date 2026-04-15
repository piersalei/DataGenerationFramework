"""Deterministic quality-control validation and rules."""

from __future__ import annotations

import re
from typing import Callable, Iterable, Optional

from smdgf.qc.models import QualityCandidate, QualityDecision, QualityFinding, RuleResult

RuleCallable = Callable[[QualityCandidate], RuleResult]


def _normalize_text(value: object) -> str:
    text = str(value or "").casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _answer_text(value: object) -> str:
    if isinstance(value, dict):
        parts = [f"{key} {value[key]}" for key in sorted(value)]
        return " ".join(parts)
    return str(value)


def _lookup_nested(mapping: object, path: str) -> object:
    current = mapping
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_candidate_structure(candidate: QualityCandidate) -> list[QualityFinding]:
    """Validate basic canonical-sample structure before soft QC runs."""

    findings: list[QualityFinding] = []
    sample = candidate.canonical_sample
    questions = sample.questions
    answers = sample.answers

    if not questions:
        findings.append(
            QualityFinding(
                finding_id=f"{candidate.candidate_id}:missing-questions",
                source_id="structure",
                severity="critical",
                message="candidate must include at least one canonical question",
                decision_hint="reject",
            )
        )

    if not answers:
        findings.append(
            QualityFinding(
                finding_id=f"{candidate.candidate_id}:missing-answers",
                source_id="structure",
                severity="critical",
                message="candidate must include at least one canonical answer",
                decision_hint="reject",
            )
        )

    question_ids = [question.question_id for question in questions]
    duplicate_question_ids = sorted(
        question_id for question_id in set(question_ids) if question_ids.count(question_id) > 1
    )
    if duplicate_question_ids:
        findings.append(
            QualityFinding(
                finding_id=f"{candidate.candidate_id}:duplicate-questions",
                source_id="structure",
                severity="error",
                message="candidate contains duplicate question ids",
                decision_hint="reject",
                evidence={"question_ids": duplicate_question_ids},
            )
        )

    question_id_set = set(question_ids)
    unknown_answer_ids = sorted(
        answer.question_id for answer in answers if answer.question_id not in question_id_set
    )
    if unknown_answer_ids:
        findings.append(
            QualityFinding(
                finding_id=f"{candidate.candidate_id}:unknown-answer-ids",
                source_id="structure",
                severity="error",
                message="candidate answers reference unknown questions",
                decision_hint="reject",
                evidence={"question_ids": unknown_answer_ids},
            )
        )

    return findings


def answer_leakage_rule(candidate: QualityCandidate) -> RuleResult:
    """Reject questions that directly leak their semantic answer."""

    findings: list[QualityFinding] = []
    answer_map = {answer.question_id: answer for answer in candidate.canonical_sample.answers}

    for question in candidate.canonical_sample.questions:
        answer = answer_map.get(question.question_id)
        if answer is None:
            continue
        answer_text = _normalize_text(_answer_text(answer.value))
        question_text = _normalize_text(question.text)
        if answer_text and len(answer_text) >= 3 and answer_text in question_text:
            findings.append(
                QualityFinding(
                    finding_id=f"{candidate.candidate_id}:{question.question_id}:answer-leakage",
                    source_id="answer-leakage",
                    severity="error",
                    message="question text leaks the expected answer",
                    decision_hint="reject",
                    evidence={
                        "question_id": question.question_id,
                        "question_text": question.text,
                        "answer_text": _answer_text(answer.value),
                    },
                )
            )

    return RuleResult(rule_id="answer-leakage", passed=not findings, findings=findings)


def latent_consistency_rule(candidate: QualityCandidate) -> RuleResult:
    """Reject candidates whose latent state violates explicit expectations."""

    findings: list[QualityFinding] = []
    expectations = candidate.metadata.get("latent_expectations", {})
    if not isinstance(expectations, dict):
        return RuleResult(rule_id="latent-consistency", passed=True, findings=findings)

    for path, expected in sorted(expectations.items()):
        actual = _lookup_nested(candidate.canonical_sample.latent_state, path)
        if actual != expected:
            findings.append(
                QualityFinding(
                    finding_id=f"{candidate.candidate_id}:{path}:latent-consistency",
                    source_id="latent-consistency",
                    severity="error",
                    message="latent state does not match the configured expectation",
                    decision_hint="reject",
                    evidence={"path": path, "expected": expected, "actual": actual},
                )
            )

    return RuleResult(rule_id="latent-consistency", passed=not findings, findings=findings)


class RuleEngine:
    """Run deterministic QC rules and derive one normalized QC decision."""

    def __init__(self, rules: Optional[Iterable[RuleCallable]] = None) -> None:
        self.rules = list(rules or [answer_leakage_rule, latent_consistency_rule])

    def add_rule(self, rule: RuleCallable) -> None:
        """Register an additional deterministic QC rule."""

        self.rules.append(rule)

    def evaluate(self, candidate: QualityCandidate) -> QualityDecision:
        """Evaluate a candidate with structural checks plus registered rules."""

        findings = validate_candidate_structure(candidate)
        applied_rules = ["structure"]

        for rule in self.rules:
            result = rule(candidate)
            applied_rules.append(result.rule_id)
            findings.extend(result.findings)

        status = "accept"
        if any(finding.decision_hint == "reject" for finding in findings):
            status = "reject"
        elif any(finding.decision_hint == "review" for finding in findings):
            status = "review"

        return QualityDecision(
            candidate_id=candidate.candidate_id,
            status=status,
            findings=findings,
            applied_rules=applied_rules,
            review_required=status == "review",
        )
