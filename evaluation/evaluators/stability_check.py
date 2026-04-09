"""Stability checks for output shape (non-exact-match tolerant)."""

from __future__ import annotations

from skills.cece_agent import TestCaseGenerator, TestPointIdentifier


def score_stability(feature: str, requirement: str) -> tuple[int, list[str]]:
    reasons: list[str] = []
    p1 = TestPointIdentifier.identify(requirement, feature)
    p2 = TestPointIdentifier.identify(requirement, feature)

    c1 = TestCaseGenerator.generate_from_test_points(feature, p1["test_points"])
    c2 = TestCaseGenerator.generate_from_test_points(feature, p2["test_points"])

    # 不要求文本完全一致，只要求结构稳定
    k1 = set(c1[0].keys()) if c1 else set()
    k2 = set(c2[0].keys()) if c2 else set()
    score = 0
    if len(p1.get("test_points", [])) == len(p2.get("test_points", [])):
        score += 5
    else:
        reasons.append("测试点数量不稳定")

    if k1 == k2 and k1:
        score += 5
    else:
        reasons.append("用例字段结构不稳定")

    return score, reasons
