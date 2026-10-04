"""
Automated JSON-RPC 2.0 contract tests for the Career Engine Python Executa plugin.
Run with: python3 -m unittest tests/test_plugin.py (or pytest)
"""

from __future__ import annotations
import json
import subprocess
import unittest
from pathlib import Path

PLUGIN_PATH = (
    Path(__file__).resolve().parent.parent
    / "executas"
    / "career-engine-python"
    / "career_engine_plugin.py"
)


class TestCareerEngineExecuta(unittest.TestCase):
    def setUp(self) -> None:
        self.proc = subprocess.Popen(
            ["python3", str(PLUGIN_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def tearDown(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)

    def rpc(self, method: str, params: dict | None = None, req_id: int = 1) -> dict:
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params
        assert self.proc.stdin is not None
        assert self.proc.stdout is not None
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        return json.loads(line)

    def test_describe_and_health(self) -> None:
        desc = self.rpc("describe", req_id=1)
        self.assertEqual(desc["result"]["display_name"], "Career Engine")
        self.assertEqual(desc["result"]["tools"][0]["name"], "career")

        health = self.rpc("health", req_id=2)
        self.assertEqual(health["result"]["status"], "ready")

    def test_analyze_rewrite_cover_interview_flow(self) -> None:
        res = self.rpc(
            "invoke",
            {
                "tool": "career",
                "arguments": {
                    "action": "analyze",
                    "role_title": "Senior AI Engineer",
                    "company_name": "Anna Labs",
                    "resume_text": (
                        "Alex | alex@dev.io | https://github.com/alex\n"
                        "Experience:\n"
                        "- Architected Python and FastAPI services handling 90K requests/day.\n"
                        "- Worked on LLM Agents and prompt engineering pipelines."
                    ),
                    "job_description": (
                        "Hiring Senior AI Engineer skilled in Python, FastAPI, LLM Agents, "
                        "RAG & Vector DB, Docker, Kubernetes, and TypeScript."
                    ),
                },
            },
            req_id=3,
        )
        self.assertTrue(res["result"]["success"])
        scan = res["result"]["data"]["scan"]
        self.assertGreaterEqual(scan["overall_score"], 30)
        self.assertTrue(len(scan["matched_keywords"]) >= 2)
        self.assertTrue(len(scan["missing_keywords"]) >= 1)

        # Rewrite bullets
        rw = self.rpc(
            "invoke",
            {"tool": "career", "arguments": {"action": "rewrite_bullets"}},
            req_id=4,
        )
        self.assertTrue(rw["result"]["success"])
        self.assertGreaterEqual(len(rw["result"]["data"]["rewrites"]), 1)

        # Cover letter
        cl = self.rpc(
            "invoke",
            {"tool": "career", "arguments": {"action": "cover_letter", "tone": "technical"}},
            req_id=5,
        )
        self.assertTrue(cl["result"]["success"])
        self.assertIn("Application:", cl["result"]["data"]["email_subject"])

        # Interview prep
        iq = self.rpc(
            "invoke",
            {"tool": "career", "arguments": {"action": "interview_prep"}},
            req_id=6,
        )
        self.assertTrue(iq["result"]["success"])
        self.assertEqual(len(iq["result"]["data"]["questions"]), 5)


if __name__ == "__main__":
    unittest.main()
