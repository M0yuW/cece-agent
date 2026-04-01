"""Test case review helpers for cece-agent skill."""

from __future__ import annotations

from typing import Any

from .prompts import REVIEW_PROMPT, SYSTEM_PROMPT


class TestCaseReviewer:
    """Heuristic checks that complement LLM review reasoning."""

    required_sections = [
        "总体评价",
        "严重问题",
        "一般问题",
        "优化建议",
        "缺失测试点",
    ]

    @staticmethod
    def build_prompt(test_cases: str, feature_context: str = "") -> str:
        return (
            f"{SYSTEM_PROMPT}\n\n{REVIEW_PROMPT}\n\n"
            f"feature_context:\n{feature_context or '(未提供)'}\n\n"
            f"test_cases:\n{test_cases}"
        ).strip()

    @staticmethod
    def quick_diagnostics(cases: list[dict[str, Any]]) -> dict[str, list[str]]:
        """Run deterministic checks before/after LLM review."""
        severe: list[str] = []
        moderate: list[str] = []
        suggestions: list[str] = []

        titles: set[str] = set()
        for i, case in enumerate(cases, start=1):
            title = str(case.get("title", "")).strip()
            if not title:
                severe.append(f"Case#{i} 缺少 title")
            elif title.lower() in titles:
                moderate.append(f"Case#{i} 标题重复：{title}")
            else:
                titles.add(title.lower())

            if not case.get("steps"):
                severe.append(f"Case#{i} 缺少 steps，无法执行")
            if not case.get("expected_result"):
                severe.append(f"Case#{i} 缺少 expected_result，无法验证")

            case_type = str(case.get("case_type", "")).strip().lower()
            if case_type not in {
                "normal",
                "edge",
                "error",
                "security",
                "permission",
                "ui",
                "compatibility",
                "accessibility",
            }:
                suggestions.append(
                    f"Case#{i} 的 case_type={case.get('case_type')} 建议标准化"
                )

        present_types = {str(c.get("case_type", "")).lower() for c in cases}
        for expected in ("normal", "edge", "error"):
            if expected not in present_types:
                moderate.append(f"缺少 {expected} 类型用例")
        if "ui" not in present_types:
            suggestions.append("可补充 UI 页面交互类用例（渲染/按钮状态/反馈文案）")

        return {
            "severe": severe,
            "moderate": moderate,
            "suggestions": suggestions,
        }

    @classmethod
    def review_with_test_points(
        cls, cases: list[dict[str, Any]], test_points: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Review cases with test-point traceability as the baseline."""
        diagnostics = cls.quick_diagnostics(cases)
        case_titles = " ".join(str(c.get("title", "")) for c in cases).lower()
        missing_points: list[str] = []
        for point in test_points:
            category = str(point.get("category", "")).strip().lower()
            if category and category not in case_titles:
                missing_points.append(category)

        critical = diagnostics["severe"]
        normal = diagnostics["moderate"]
        suggestions = diagnostics["suggestions"]
        if missing_points:
            normal.append("未覆盖测试点: " + ", ".join(sorted(set(missing_points))))

        return {
            "summary": "用例评审完成，已基于测试点进行覆盖检查。",
            "critical_issues": critical,
            "normal_issues": normal,
            "suggestions": suggestions,
            "missing_test_points": sorted(set(missing_points)),
            "improved_cases": [],
        }
