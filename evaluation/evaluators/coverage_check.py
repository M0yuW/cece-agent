"""Coverage and quality checks with category mapping."""

from __future__ import annotations

from typing import Any


CASE_TYPE_TO_DIM = {
    "normal": {"functional", "state"},
    "edge": {"boundary", "validation"},
    "error": {"error", "error_code", "permission"},
    "ui": {"ui"},
    "api": {"api", "idempotency", "data_consistency"},
}


def score_test_point_coverage(test_points: list[dict[str, Any]], expected_dims: list[str], must_cover: list[str]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    found = {str(p.get("category", "")).lower() for p in test_points}

    expected_hit = len(found.intersection(set(expected_dims)))
    expected_score = int(12 * (expected_hit / max(1, len(expected_dims))))

    must_missing = sorted(set(must_cover) - found)
    must_score = int(8 * ((len(must_cover) - len(must_missing)) / max(1, len(must_cover))))
    if must_missing:
        reasons.append("关键测试点缺失: " + ", ".join(must_missing))

    return expected_score + must_score, reasons


def score_case_coverage(cases: list[dict[str, Any]], must_cover: list[str]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    covered_dims: set[str] = set()
    for case in cases:
        ct = str(case.get("case_type", "")).lower()
        covered_dims.update(CASE_TYPE_TO_DIM.get(ct, set()))

    missing = sorted(set(must_cover) - covered_dims)
    score = int(10 * ((len(must_cover) - len(missing)) / max(1, len(must_cover))))
    if missing:
        reasons.append("用例覆盖不足: " + ", ".join(missing))
    return score, reasons


def score_case_quality(cases: list[dict[str, Any]]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    if not cases:
        return 0, ["无用例可评估"]

    executable = 0
    verifiable = 0
    titles: list[str] = []

    for case in cases:
        steps = case.get("steps", [])
        expects = case.get("expected_result", [])
        title = str(case.get("title", "")).strip().lower()
        titles.append(title)
        if isinstance(steps, list) and len(steps) >= 1:
            executable += 1
        if isinstance(expects, list) and all(str(e).strip() for e in expects) and len(expects) >= 1:
            verifiable += 1

    exec_score = int(8 * executable / len(cases))
    verify_score = int(5 * verifiable / len(cases))

    dup_count = len(titles) - len(set(titles))
    dedup_score = 2 if dup_count == 0 else 0
    if dup_count > 0:
        reasons.append(f"发现重复标题用例 {dup_count} 条")

    return exec_score + verify_score + dedup_score, reasons
