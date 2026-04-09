"""Local runnable cece-agent loop (no chat app dependency).

Usage examples:
  python -m cece_agent.run --mode identify --input "登录页面支持手机号验证码登录"
  python -m cece_agent.run --mode generate --input-file prd.txt
  python -m cece_agent.run --mode review --input-file prd.txt --cases-file cases.json
  python -m cece_agent.run --mode pipeline --input-file prd.txt
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from skills.cece_agent import TestCaseGenerator, TestCaseReviewer, TestPointIdentifier


def _read_text(input_text: str | None, input_file: str | None) -> str:
    if input_text:
        return input_text
    if input_file:
        return Path(input_file).read_text(encoding="utf-8")
    raise ValueError("Please provide --input or --input-file")


def run_identify(feature_text: str, feature_name: str) -> dict[str, Any]:
    return TestPointIdentifier.identify(feature_text, feature=feature_name)


def run_generate(feature_text: str, feature_name: str) -> dict[str, Any]:
    points = run_identify(feature_text, feature_name)
    cases = TestCaseGenerator.generate_from_test_points(feature_name, points["test_points"])
    cases = TestCaseGenerator.enrich_frontend_scenarios(feature_text, cases)
    return {
        "feature": feature_name,
        "test_points": points["test_points"],
        "test_cases": cases,
    }


def run_review(feature_text: str, feature_name: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    points = run_identify(feature_text, feature_name)
    review = TestCaseReviewer.review_with_test_points(cases, points["test_points"])
    return {
        "feature": feature_name,
        "test_points": points["test_points"],
        "review": review,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cece-agent locally")
    parser.add_argument("--mode", choices=["identify", "generate", "review", "pipeline"], required=True)
    parser.add_argument("--feature", default="测试功能")
    parser.add_argument("--input", help="Requirement text")
    parser.add_argument("--input-file", help="Requirement file path")
    parser.add_argument("--cases-file", help="JSON file for existing test cases (review mode)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    args = parser.parse_args()

    feature_text = _read_text(args.input, args.input_file)

    if args.mode == "identify":
        output = run_identify(feature_text, args.feature)
    elif args.mode == "generate":
        output = run_generate(feature_text, args.feature)
    elif args.mode == "review":
        if not args.cases_file:
            raise ValueError("review mode requires --cases-file")
        cases = json.loads(Path(args.cases_file).read_text(encoding="utf-8"))
        output = run_review(feature_text, args.feature, cases)
    else:
        generated = run_generate(feature_text, args.feature)
        review = TestCaseReviewer.review_with_test_points(
            generated["test_cases"], generated["test_points"]
        )
        output = {
            "feature": args.feature,
            "test_points": generated["test_points"],
            "test_cases": generated["test_cases"],
            "review": review,
        }

    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
