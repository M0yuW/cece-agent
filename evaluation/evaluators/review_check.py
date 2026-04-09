"""Review capability checks."""

from __future__ import annotations

from typing import Any


PROBLEM_MAP = {
    "漏边界": ["boundary", "edge", "边界"],
    "漏异常": ["error", "异常"],
    "步骤不清晰": ["steps", "步骤"],
    "预期不明确": ["expected", "预期"],
    "冗余重复": ["重复", "冗余"],
    "优先级不合理": ["priority", "优先级"],
}


def score_review(report: dict[str, Any], seed_problems: list[str]) -> tuple[int, list[str], list[str]]:
    reasons: list[str] = []
    hints: list[str] = []

    if not isinstance(report, dict):
        return 0, ["review 输出非法"], ["确保 review 返回 JSON 对象"]

    core_keys = {
        "summary",
        "critical_issues",
        "normal_issues",
        "suggestions",
        "missing_test_points",
        "improved_cases",
    }
    if not core_keys.issubset(set(report.keys())):
        reasons.append("review 输出缺少核心字段")

    bag = " ".join(
        [
            str(report.get("summary", "")),
            " ".join(map(str, report.get("critical_issues", []))),
            " ".join(map(str, report.get("normal_issues", []))),
            " ".join(map(str, report.get("suggestions", []))),
            " ".join(map(str, report.get("missing_test_points", []))),
        ]
    ).lower()

    hit = 0
    missed: list[str] = []
    for problem in seed_problems:
        kws = PROBLEM_MAP.get(problem, [problem.lower()])
        if any(k.lower() in bag for k in kws):
            hit += 1
        else:
            missed.append(problem)

    score = int(15 * (hit / max(1, len(seed_problems))))
    if missed:
        reasons.append("review 未识别问题: " + ", ".join(missed))

    improved_cases = report.get("improved_cases", [])
    if isinstance(improved_cases, list) and improved_cases:
        executable = all(c.get("steps") and c.get("expected_result") for c in improved_cases)
        if executable:
            score += 5
        else:
            reasons.append("improved_cases 存在不可执行项")
            hints.append("确保每条 improved_case 都有 steps 与 expected_result")
    else:
        reasons.append("improved_cases 为空")
        hints.append("增加自动修复策略，补齐缺失测试点与坏用例")

    return score, reasons, hints
