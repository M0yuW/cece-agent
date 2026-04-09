"""Test point identification for cece-agent.

This module provides deterministic local behavior so cece-agent can run without
chat apps and without mandatory remote model dependency.
"""

from __future__ import annotations

from typing import Any

from .prompts import SYSTEM_PROMPT, TEST_POINT_PROMPT


class TestPointIdentifier:
    """Identify structured test points from requirement text."""

    base_catalog: list[tuple[str, str, str]] = [
        ("functional", "核心业务流程与关键功能入口可达", "high"),
        ("validation", "输入字段合法性与必填校验", "high"),
        ("boundary", "关键字段边界值与长度边界", "high"),
        ("error", "异常输入与失败路径反馈", "high"),
        ("state", "状态流转前后行为一致", "medium"),
        ("permission", "不同角色/权限访问差异", "medium"),
        ("error_code", "错误码或错误提示语义正确", "medium"),
    ]

    frontend_keywords = {"页面", "按钮", "表单", "跳转", "loading", "empty", "error", "前端", "ui"}
    api_keywords = {"接口", "api", "endpoint", "http", "status code", "幂等", "请求", "响应"}
    data_keywords = {"事务", "一致性", "并发", "回滚", "缓存", "同步", "最终一致"}

    @staticmethod
    def build_prompt(feature_context: str) -> str:
        return f"{SYSTEM_PROMPT}\n\n{TEST_POINT_PROMPT}\n\nfeature_context:\n{feature_context}".strip()

    @classmethod
    def identify(cls, feature_context: str, feature: str | None = None) -> dict[str, Any]:
        text = feature_context.lower()
        output: dict[str, Any] = {
            "feature": (feature or "未命名功能").strip() or "未命名功能",
            "test_points": [
                {
                    "category": category,
                    "description": desc,
                    "risk_level": risk,
                }
                for category, desc, risk in cls.base_catalog
            ],
        }

        if any(k in text for k in cls.frontend_keywords):
            output["test_points"].append(
                {
                    "category": "ui",
                    "description": "表单输入、按钮状态、提示文案、页面跳转与 loading/empty/error 视图",  # noqa: E501
                    "risk_level": "high",
                }
            )

        if any(k in text for k in cls.api_keywords):
            output["test_points"].append(
                {
                    "category": "api",
                    "description": "接口请求/响应契约、状态码、超时与重试行为",
                    "risk_level": "high",
                }
            )
            output["test_points"].append(
                {
                    "category": "idempotency",
                    "description": "重复提交/重复请求时结果一致，不产生脏数据",
                    "risk_level": "high",
                }
            )

        if any(k in text for k in cls.data_keywords):
            output["test_points"].append(
                {
                    "category": "data_consistency",
                    "description": "跨服务/缓存/数据库数据一致性与延迟一致性窗口",
                    "risk_level": "high",
                }
            )

        return output
