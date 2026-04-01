import json
import unittest

from skills.cece_agent.test_case_generator import TestCaseGenerator
from skills.cece_agent.test_case_reviewer import TestCaseReviewer


class FrontendScenarioTests(unittest.TestCase):
    def test_enrich_frontend_scenarios_adds_ui_cases(self):
        context = "登录页面有手机号输入框和提交按钮，点击后跳转首页"
        base_cases = [
            {
                "id": "TC-001",
                "feature": "登录",
                "title": "登录成功",
                "preconditions": ["用户存在"],
                "steps": ["输入正确凭证", "点击登录"],
                "test_data": {},
                "expected_result": ["登录成功"],
                "priority": "P0",
                "case_type": "normal",
            }
        ]
        enriched = TestCaseGenerator.enrich_frontend_scenarios(context, base_cases)
        types = {item["case_type"] for item in enriched}
        self.assertIn("ui", types)
        self.assertIn("accessibility", types)
        self.assertGreaterEqual(len(enriched), len(base_cases) + 2)

    def test_non_frontend_context_keeps_cases(self):
        context = "创建订单接口，参数包含 user_id 和 item_id"
        base_cases = [
            {
                "id": "TC-API-001",
                "feature": "订单接口",
                "title": "创建订单成功",
                "preconditions": ["库存充足"],
                "steps": ["调用创建接口"],
                "test_data": {"user_id": 1, "item_id": 2},
                "expected_result": ["返回成功"],
                "priority": "P0",
                "case_type": "normal",
            }
        ]
        enriched = TestCaseGenerator.enrich_frontend_scenarios(context, base_cases)
        self.assertEqual(enriched, TestCaseGenerator.normalize(base_cases))

    def test_reviewer_suggests_ui_when_missing(self):
        diagnostics = TestCaseReviewer.quick_diagnostics(
            [
                {
                    "title": "仅接口成功",
                    "steps": ["调用接口"],
                    "expected_result": ["成功"],
                    "case_type": "normal",
                }
            ]
        )
        self.assertTrue(any("UI" in msg for msg in diagnostics["suggestions"]))

    def test_to_json_output_valid(self):
        payload = [
            {
                "id": "TC-001",
                "feature": "登录",
                "title": "登录成功",
                "preconditions": [],
                "steps": ["step"],
                "test_data": {},
                "expected_result": ["ok"],
                "priority": "P1",
                "case_type": "normal",
            }
        ]
        text = TestCaseGenerator.to_json(payload)
        parsed = json.loads(text)
        self.assertEqual(parsed[0]["id"], "TC-001")


if __name__ == "__main__":
    unittest.main()
