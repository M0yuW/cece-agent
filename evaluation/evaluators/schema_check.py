"""Schema checks for cece-agent outputs."""

from __future__ import annotations

from typing import Any


def check_test_points_schema(payload: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if isinstance(payload, dict) and isinstance(payload.get("test_points"), list):
        score += 5
    else:
        reasons.append("test_points 结构非法")
        return score, reasons

    required = {"category", "description", "risk_level"}
    points = payload.get("test_points", [])
    if not points:
        reasons.append("test_points 为空")
        return score, reasons

    valid_count = 0
    for p in points:
        if required.issubset(set(p.keys())):
            valid_count += 1
    ratio = valid_count / len(points)
    score += int(10 * ratio)
    if ratio < 1.0:
        reasons.append("部分测试点字段缺失")

    return score, reasons


def check_cases_schema(cases: list[dict[str, Any]], required_fields: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if not isinstance(cases, list) or not cases:
        return 0, ["test_cases 为空或非法"]

    field_set = set(required_fields)
    complete = 0
    for case in cases:
        if field_set.issubset(set(case.keys())):
            complete += 1
    ratio = complete / len(cases)
    score += int(15 * ratio)
    if ratio < 1.0:
        reasons.append("部分用例缺少必填字段")

    # basic type shape
    shape_ok = all(isinstance(c.get("steps", []), list) and isinstance(c.get("expected_result", []), list) for c in cases)
    if shape_ok:
        score += 5
    else:
        reasons.append("steps/expected_result 类型不稳定")

    return score, reasons
