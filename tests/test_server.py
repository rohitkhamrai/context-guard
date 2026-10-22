"""Unit tests for ContextGuard MCP Server."""
import json
import tempfile
import unittest
from pathlib import Path

from context_guard.server import ContextGuardServer


class TestContextGuardServer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.server = ContextGuardServer(workspace_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        res = self.server.handle_request(req)
        self.assertEqual(res["result"]["serverInfo"]["name"], "context-guard")

    def test_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = self.server.handle_request(req)
        tool_names = [t["name"] for t in res["result"]["tools"]]
        self.assertIn("get_context_status", tool_names)
        self.assertIn("record_invariant", tool_names)
        self.assertIn("record_mistake", tool_names)
        self.assertIn("compile_checkpoint", tool_names)
        self.assertIn("flush_context", tool_names)
        self.assertIn("render_badge", tool_names)

    def test_tool_calls_end_to_end(self):
        # 1. Record invariant
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "record_invariant", "arguments": {"rule": "Do not touch prod without dry run"}},
        }
        res = self.server.handle_request(req)
        self.assertIn("Invariant locked", res["result"]["content"][0]["text"])

        # 2. Record mistake
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "record_mistake", "arguments": {"mistake": "Unescaped SQL query", "reason": "SQL injection vulnerability"}},
        }
        res = self.server.handle_request(req)
        self.assertIn("Mistake registered", res["result"]["content"][0]["text"])

        # 3. Check status
        req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "get_context_status", "arguments": {"window_limit": 1_000_000}},
        }
        res = self.server.handle_request(req)
        status_data = json.loads(res["result"]["content"][0]["text"])
        self.assertIn("current_tokens", status_data)
        self.assertEqual(status_data["saturation_level"], "SAFE")

        # 4. Render badge
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "render_badge", "arguments": {}},
        }
        res = self.server.handle_request(req)
        badge_text = res["result"]["content"][0]["text"]
        self.assertIn("Context:", badge_text)
        self.assertIn("SAFE", badge_text)

        # 5. Compile checkpoint
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "compile_checkpoint",
                "arguments": {
                    "primary_goal": "Refactor API",
                    "active_milestone": "Testing",
                    "next_step": "Deploy",
                },
            },
        }
        res = self.server.handle_request(req)
        cp_data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(cp_data["goal_tree"]["primary_goal"], "Refactor API")
        self.assertEqual(len(cp_data["the_graveyard"]), 1)


if __name__ == "__main__":
    unittest.main()
