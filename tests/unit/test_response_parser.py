"""Tests for generation CLI ResponseParser (model output → CanonicalSample)."""

from __future__ import annotations

import json

import pytest

from smdgf.generation.cli import ResponseParser


def test_parse_flat_mcq_json_array_splits_one_row_per_sample() -> None:
    text = """```json
[
  {"情境": "场景一", "问题编号": 1, "问题": "甲的心情？", "A": "高兴", "B": "生气", "C": "悲伤", "D": "尴尬", "答案": "B"},
  {"情境": "场景一", "问题编号": 2, "问题": "乙的心情？", "A": "高兴", "B": "生气", "C": "悲伤", "D": "尴尬", "答案": "A"}
]
```"""
    p = ResponseParser()
    rows = p.parse(text, task_id="t1", request_id="req-0", seed=1)

    assert len(rows) == 2
    assert rows[0].sample_id == "req-0-r0"
    assert rows[0].scene_text == "场景一"
    assert len(rows[0].questions) == 1
    assert rows[0].questions[0].text == "甲的心情？"
    assert rows[0].answers[0].value == "生气"
    assert rows[0].latent_state["mcq_options"] == [
        {"A": "高兴", "B": "生气", "C": "悲伤", "D": "尴尬"},
    ]
    assert rows[1].sample_id == "req-0-r1"
    assert rows[1].answers[0].value == "高兴"


def test_parse_nested_scenario_splits_one_sample_per_question() -> None:
    payload = {
        "情境": "单一情境",
        "问题列表": [
            {"问题编号": 1, "问题": "Q1？", "答案": "x"},
            {"问题编号": 2, "问题": "Q2？", "答案": "y"},
        ],
    }
    p = ResponseParser()
    rows = p.parse(json.dumps(payload, ensure_ascii=False), task_id="t1", request_id="r1")

    assert len(rows) == 2
    assert rows[0].sample_id == "r1-n0"
    assert rows[0].scene_text == "单一情境"
    assert [q.question_id for q in rows[0].questions] == ["1"]
    assert rows[0].answers[0].value == "x"
    assert rows[1].sample_id == "r1-n1"
    assert [q.question_id for q in rows[1].questions] == ["2"]


def test_parse_rejects_unknown_shape() -> None:
    p = ResponseParser()
    with pytest.raises(ValueError, match="无法识别"):
        p.parse('{"foo": 1}', task_id="t", request_id="r")
