"""Test case generation helpers for cece-agent skill."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

from .prompts import GENERATION_PROMPT, SYSTEM_PROMPT


@dataclass
class TestCase:
    id: str
    feature: str
    title: str
    preconditions: list[str]
    steps: list[str]
    test_data: dict[str, Any]
    expected_result: list[str]
    priority: str
    case_type: str


class TestCaseGenerator:
    """Lightweight formatter/validator for generated test cases.

    This class does not call an LLM directly; it standardizes output and can be
    wrapped by nanobot tools/skills runtime.
    """

    required_fields = {
        "id",
        "feature",
        "title",
        "preconditions",
        "steps",
        "test_data",
        "expected_result",
        "priority",
        "case_type",
    }
    frontend_keywords = {
        "页面",
        "按钮",
        "表单",
        "输入框",
        "弹窗",
        "点击",
        "跳转",
        "前端",
        "h5",
        "web",
        "ui",
        "界面",
        "列表页",
        "详情页",
        "提交",
        "禁用",
        "加载",
    }

    @staticmethod
    def build_prompt(feature_context: str) -> str:
        return f"{SYSTEM_PROMPT}\n\n{GENERATION_PROMPT}\n\nfeature_context:\n{feature_context}".strip()

    @classmethod
    def is_frontend_feature(cls, feature_context: str) -> bool:
        text = feature_context.lower()
        return any(keyword in text for keyword in cls.frontend_keywords)

    @classmethod
    def validate_cases(cls, cases: list[dict[str, Any]]) -> list[str]:
        issues: list[str] = []
        seen_titles: set[str] = set()

        for i, case in enumerate(cases, start=1):
            missing = cls.required_fields - set(case.keys())
            if missing:
                issues.append(f"Case#{i} missing fields: {sorted(missing)}")

            title = str(case.get("title", "")).strip().lower()
            if title:
                if title in seen_titles:
                    issues.append(f"Case#{i} duplicated title: {case.get('title')}")
                seen_titles.add(title)

            if not case.get("steps"):
                issues.append(f"Case#{i} has empty steps")
            if not case.get("expected_result"):
                issues.append(f"Case#{i} has empty expected_result")

        return issues

    @staticmethod
    def normalize(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in cases:
            tc = TestCase(
                id=str(item.get("id", "")).strip(),
                feature=str(item.get("feature", "")).strip(),
                title=str(item.get("title", "")).strip(),
                preconditions=list(item.get("preconditions", [])),
                steps=list(item.get("steps", [])),
                test_data=dict(item.get("test_data", {})),
                expected_result=list(item.get("expected_result", [])),
                priority=str(item.get("priority", "P2")).strip() or "P2",
                case_type=str(item.get("case_type", "normal")).strip() or "normal",
            )
            normalized.append(asdict(tc))
        return normalized

    @classmethod
    def enrich_frontend_scenarios(
        cls, feature_context: str, cases: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Add baseline page-level scenarios when context is frontend-oriented."""
        normalized = cls.normalize(cases)
        if not cls.is_frontend_feature(feature_context):
            return normalized

        existing_titles = {str(case.get("title", "")).strip().lower() for case in normalized}
        feature_name = next(
            (str(case.get("feature", "")).strip() for case in normalized if case.get("feature")),
            "前端页面功能",
        )

        baseline_cases = [
            TestCase(
                id="TC-UI-001",
                feature=feature_name,
                title="页面首屏渲染与默认状态展示正确",
                preconditions=["用户已进入目标页面"],
                steps=["打开页面", "观察首屏默认数据与控件状态"],
                test_data={},
                expected_result=["页面可正常渲染", "关键控件显示正确", "默认文案与状态符合需求"],
                priority="P1",
                case_type="ui",
            ),
            TestCase(
                id="TC-UI-002",
                feature=feature_name,
                title="提交按钮禁用态、加载态与防重复点击生效",
                preconditions=["页面含提交类按钮"],
                steps=["输入合法数据", "快速连续点击提交按钮"],
                test_data={},
                expected_result=["首次点击后按钮进入加载或禁用态", "不会重复提交", "请求完成后状态恢复"],
                priority="P1",
                case_type="ui",
            ),
            TestCase(
                id="TC-UI-003",
                feature=feature_name,
                title="错误提示文案和定位反馈清晰可见",
                preconditions=["页面含校验字段"],
                steps=["输入非法数据并触发校验", "观察错误提示位置与文案"],
                test_data={"invalid_input": "非法样例"},
                expected_result=["错误提示靠近问题字段", "文案可理解且可操作", "页面不出现卡死或布局错乱"],
                priority="P1",
                case_type="accessibility",
            ),
        ]

        for item in baseline_cases:
            if item.title.lower() not in existing_titles:
                normalized.append(asdict(item))
        return normalized

    @classmethod
    def to_json(cls, cases: list[dict[str, Any]], indent: int = 2) -> str:
        return json.dumps(cls.normalize(cases), ensure_ascii=False, indent=indent)

    @classmethod
    def generate_from_test_points(
        cls, feature: str, test_points: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate minimal runnable test cases from identified test points."""
        generated: list[dict[str, Any]] = []
        for idx, point in enumerate(test_points, start=1):
            category = str(point.get("category", "functional")).lower()
            generated.append(
                {
                    "id": f"TC-{idx:03d}",
                    "feature": feature,
                    "title": f"{feature} - {category} 场景验证",
                    "preconditions": ["系统服务可用", "测试账号准备完成"],
                    "steps": [f"执行 {category} 相关操作", "观察系统行为与反馈"],
                    "test_data": {"category": category},
                    "expected_result": [str(point.get("description", "行为符合预期"))],
                    "priority": "P0" if point.get("risk_level") == "high" else "P1",
                    "case_type": cls._map_case_type(category),
                }
            )
        return cls.normalize(generated)

    @staticmethod
    def _map_case_type(category: str) -> str:
        mapping = {
            "functional": "normal",
            "validation": "edge",
            "boundary": "edge",
            "error": "error",
            "state": "normal",
            "permission": "error",
            "api": "api",
            "ui": "ui",
            "idempotency": "api",
            "data_consistency": "api",
            "error_code": "error",
        }
        return mapping.get(category, "normal")
