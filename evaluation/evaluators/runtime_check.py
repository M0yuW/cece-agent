"""Runtime checks for local executability."""

from __future__ import annotations

import json
import subprocess


def run_pipeline_runtime(feature: str, requirement: str) -> tuple[bool, str]:
    cmd = [
        "python",
        "-m",
        "cece_agent.run",
        "--mode",
        "pipeline",
        "--feature",
        feature,
        "--input",
        requirement,
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        payload = json.loads(proc.stdout)
    except Exception as exc:  # noqa: BLE001
        return False, f"pipeline 启动失败: {exc}"

    if not all(k in payload for k in ("test_points", "test_cases", "review")):
        return False, "pipeline 输出缺少关键字段"
    return True, ""
