import json
import subprocess
import unittest


class EvaluationRunnerTests(unittest.TestCase):
    def test_eval_runner_outputs_report(self):
        proc = subprocess.run(
            ["python", "-m", "evaluation.run_eval"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(proc.stdout)
        self.assertIn("reports", payload)
        self.assertIn("avg_score", payload)
        self.assertGreaterEqual(payload["sample_count"], 1)


if __name__ == "__main__":
    unittest.main()
