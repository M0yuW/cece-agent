"""Unified evaluation entry for cece-agent.

Run:
  python -m evaluation.run_eval
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.evaluators.coverage_check import (
    score_case_coverage,
    score_case_quality,
    score_test_point_coverage,
)
from evaluation.evaluators.review_check import score_review
from evaluation.evaluators.runtime_check import run_pipeline_runtime
from evaluation.evaluators.schema_check import (
    check_cases_schema,
    check_test_points_schema,
)
from evaluation.evaluators.stability_check import score_stability
from skills.cece_agent import TestCaseGenerator, TestCaseReviewer, TestPointIdentifier


ROOT = Path(__file__).resolve().parent


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def synthesize_bad_cases(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    if not cases:
        return [], ["步骤不清晰", "预期不明确"]

    bad = [dict(cases[0])]
    bad[0]["steps"] = []
    bad[0]["expected_result"] = []
    bad[0]["priority"] = "P3"

    if len(cases) > 1:
        dup = dict(cases[1])
        dup["title"] = bad[0].get("title", "重复标题")
        bad.append(dup)

    seed = ["漏边界", "漏异常", "步骤不清晰", "预期不明确", "冗余重复", "优先级不合理"]
    return bad, seed


def evaluate_requirement_sample(sample: dict[str, Any]) -> dict[str, Any]:
    name = sample["sample_name"]
    feature = sample["feature"]
    requirement = sample["requirement"]

    runtime_pass, runtime_err = run_pipeline_runtime(feature, requirement)
    runtime_score = 20 if runtime_pass else 0

    points = TestPointIdentifier.identify(requirement, feature)
    cases = TestCaseGenerator.generate_from_test_points(feature, points["test_points"])
    cases = TestCaseGenerator.enrich_frontend_scenarios(requirement, cases)

    schema_tp_score, schema_tp_reasons = check_test_points_schema(points)
    schema_case_score, schema_case_reasons = check_cases_schema(cases, sample["required_fields"])
    schema_score = min(20, schema_tp_score + schema_case_score)

    tp_cov_score, tp_reasons = score_test_point_coverage(
        points["test_points"], sample["expected_dimensions"], sample["must_cover_points"]
    )
    case_cov_score, case_cov_reasons = score_case_coverage(cases, sample["must_cover_points"])
    coverage_score = min(25, tp_cov_score + case_cov_score)

    quality_score, quality_reasons = score_case_quality(cases)

    bad_cases, seed = synthesize_bad_cases(cases)
    review = TestCaseReviewer.review_with_test_points(bad_cases, points["test_points"])
    review_score, review_reasons, review_hints = score_review(review, seed)

    stability_score, stability_reasons = score_stability(feature, requirement)

    total = runtime_score + schema_score + coverage_score + quality_score + review_score + stability_score
    total = min(100, total)

    fail_reasons = []
    fail_reasons.extend([runtime_err] if runtime_err else [])
    fail_reasons.extend(schema_tp_reasons + schema_case_reasons + tp_reasons + case_cov_reasons + quality_reasons + review_reasons + stability_reasons)
    improvement_hints = list(dict.fromkeys(review_hints + [
        "补齐 must_cover_points 对应 case_type",
        "对高风险测试点优先生成 P0/P1 用例",
        "在 review 阶段增强重复用例与优先级检测",
    ]))

    return {
        "sample_name": name,
        "runtime_pass": runtime_pass,
        "runtime_score": runtime_score,
        "schema_score": schema_score,
        "coverage_score": coverage_score,
        "quality_score": quality_score,
        "review_score": review_score,
        "stability_score": stability_score,
        "total_score": total,
        "fail_reasons": [r for r in fail_reasons if r],
        "improvement_hints": improvement_hints,
    }


def evaluate_bad_review_sample(sample: dict[str, Any]) -> dict[str, Any]:
    feature = sample["feature"]
    requirement = sample["requirement"]
    bad_cases = sample["bad_cases"]
    seed = sample["seed_problems"]

    runtime_pass, runtime_err = run_pipeline_runtime(feature, requirement)
    runtime_score = 20 if runtime_pass else 0

    points = TestPointIdentifier.identify(requirement, feature)
    review = TestCaseReviewer.review_with_test_points(bad_cases, points["test_points"])

    schema_score = 20 if isinstance(review, dict) else 0
    coverage_score = 15  # review-only sample
    quality_score = 10  # review-only sample
    review_score, review_reasons, review_hints = score_review(review, seed)
    stability_score = 5

    total = min(100, runtime_score + schema_score + coverage_score + quality_score + review_score + stability_score)
    fail_reasons = ([runtime_err] if runtime_err else []) + review_reasons

    return {
        "sample_name": sample["sample_name"],
        "runtime_pass": runtime_pass,
        "runtime_score": runtime_score,
        "schema_score": schema_score,
        "coverage_score": coverage_score,
        "quality_score": quality_score,
        "review_score": review_score,
        "stability_score": stability_score,
        "total_score": total,
        "fail_reasons": [r for r in fail_reasons if r],
        "improvement_hints": review_hints,
    }


def main() -> None:
    req_samples = load_json(ROOT / "datasets" / "requirements.json")
    bad_sample = load_json(ROOT / "datasets" / "bad_test_cases.json")

    reports = [evaluate_requirement_sample(s) for s in req_samples]
    reports.append(evaluate_bad_review_sample(bad_sample))

    overall = {
        "sample_count": len(reports),
        "avg_score": round(sum(r["total_score"] for r in reports) / len(reports), 2),
        "pass_count": sum(1 for r in reports if r["total_score"] >= 70),
        "reports": reports,
    }

    print(json.dumps(overall, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
