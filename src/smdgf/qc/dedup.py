"""Duplicate and near-duplicate detection helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

from smdgf.qc.models import DuplicateCluster, QualityCandidate


def _normalize_text(value: str) -> str:
    text = value.casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def _question_signature(candidate: QualityCandidate) -> str:
    return " || ".join(
        sorted(_normalize_text(question.text) for question in candidate.canonical_sample.questions)
    )


def _answer_signature(candidate: QualityCandidate) -> str:
    normalized = []
    for answer in candidate.canonical_sample.answers:
        value = answer.value
        if isinstance(value, dict):
            parts = [f"{key}:{value[key]}" for key in sorted(value)]
            normalized.append(f"{answer.question_id}={'|'.join(parts)}")
        else:
            normalized.append(f"{answer.question_id}={value}")
    return " || ".join(sorted(_normalize_text(item) for item in normalized))


def _latent_signature(candidate: QualityCandidate) -> str:
    items = []
    for owner, state in sorted(candidate.canonical_sample.latent_state.items()):
        if isinstance(state, dict):
            for key, value in sorted(state.items()):
                items.append(f"{owner}.{key}={value}")
        else:
            items.append(f"{owner}={state}")
    return " || ".join(_normalize_text(item) for item in items)


def fingerprint_candidate(candidate: QualityCandidate) -> str:
    """Build a stable exact-duplicate fingerprint from canonical semantics."""

    payload = "##".join(
        [
            candidate.canonical_sample.task_id,
            _question_signature(candidate),
            _answer_signature(candidate),
            _latent_signature(candidate),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _token_set(candidate: QualityCandidate) -> set[str]:
    text = " ".join(
        [candidate.canonical_sample.scene_text or "", _question_signature(candidate), _answer_signature(candidate)]
    )
    normalized = _normalize_text(text)
    return {token for token in normalized.split(" ") if token}


def detect_duplicates(candidates: Iterable[QualityCandidate]) -> list[DuplicateCluster]:
    """Group exact duplicates by stable fingerprint."""

    buckets = {}
    for candidate in candidates:
        fingerprint = fingerprint_candidate(candidate)
        buckets.setdefault(fingerprint, []).append(candidate)

    clusters = []
    for fingerprint, members in sorted(buckets.items()):
        if len(members) < 2:
            continue
        member_ids = [candidate.candidate_id for candidate in members]
        clusters.append(
            DuplicateCluster(
                cluster_id=f"exact:{fingerprint[:12]}",
                cluster_type="exact",
                member_ids=member_ids,
                reason="matching canonical fingerprint",
                score=1.0,
                representative_id=member_ids[0],
            )
        )
    return clusters


def detect_near_duplicates(
    candidates: Iterable[QualityCandidate],
    *,
    threshold: float = 0.6,
) -> list[DuplicateCluster]:
    """Group near-duplicates using deterministic token-overlap similarity."""

    ordered = list(candidates)
    token_sets = {candidate.candidate_id: _token_set(candidate) for candidate in ordered}
    clusters = []
    used_pairs = set()

    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            pair = (left.candidate_id, right.candidate_id)
            left_tokens = token_sets[left.candidate_id]
            right_tokens = token_sets[right.candidate_id]
            if not left_tokens or not right_tokens:
                continue
            overlap = left_tokens & right_tokens
            union = left_tokens | right_tokens
            score = len(overlap) / len(union)
            if score < threshold:
                continue
            if pair in used_pairs:
                continue
            used_pairs.add(pair)
            clusters.append(
                DuplicateCluster(
                    cluster_id=f"near:{left.candidate_id}:{right.candidate_id}",
                    cluster_type="near",
                    member_ids=[left.candidate_id, right.candidate_id],
                    reason="high token overlap across canonical content",
                    score=round(score, 4),
                    representative_id=left.candidate_id,
                )
            )

    return clusters
