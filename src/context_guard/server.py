"""Model Context Protocol (MCP) JSON-RPC 2.0 stdio Server for ContextGuard."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .ledger import ContextLedger, PriorityTier
from .meter import ContextMeter, SaturationLevel
from .pruner import CheckpointPruner

SERVER_NAME = "context-guard"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


class ContextGuardServer:
    """Zero-dependency stdio MCP server for ContextGuard."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.meter = ContextMeter(window_limit=128_000)
        self.ledger = ContextLedger(self.workspace_root)
        self.pruner = CheckpointPruner(self.workspace_root, ledger=self.ledger)

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                },
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": self.list_tools()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                res = self.call_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": res}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing '{tool_name}': {str(e)}"}],
                        "isError": True,
                    },
                }

        else:
            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method '{method}' not found"},
                }
            return None

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_context_status",
                "description": "Calculate active context saturation, token count, fuel gauge bar, and warning tier.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "window_limit": {"type": "integer", "description": "Context window size in tokens (default 128000)"},
                        "add_tokens": {"type": "integer", "description": "Optional token delta to add to meter"},
                    },
                },
            },
            {
                "name": "record_invariant",
                "description": "Lock a critical rule or constraint into Tier 1 (never dropped during compaction).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rule": {"type": "string", "description": "Rule or constraint text"},
                        "category": {"type": "string", "description": "Category (e.g. rule, architecture, security)"},
                    },
                    "required": ["rule"],
                },
            },
            {
                "name": "record_mistake",
                "description": "Record a failed attempt or anti-pattern in the Graveyard so the agent never repeats it.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mistake": {"type": "string", "description": "What failed or was invalid"},
                        "reason": {"type": "string", "description": "Why it failed"},
                    },
                    "required": ["mistake"],
                },
            },
            {
                "name": "record_milestone",
                "description": "Record milestone progress on the active goal tree.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "milestone": {"type": "string", "description": "Milestone description"},
                        "status": {"type": "string", "description": "Status (e.g. completed, in_progress)"},
                    },
                    "required": ["milestone"],
                },
            },
            {
                "name": "compile_checkpoint",
                "description": "Synthesize the 5-vector cognitive checkpoint into checkpoint.json and ACTIVE_CHECKPOINT.md.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "primary_goal": {"type": "string", "description": "Primary goal being pursued"},
                        "active_milestone": {"type": "string", "description": "Current milestone in progress"},
                        "next_step": {"type": "string", "description": "Immediate next action vector"},
                    },
                },
            },
            {
                "name": "get_keep_drop_diff",
                "description": "Inspect differential comparison between preserved high-signal state and droppable ephemeral noise.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "flush_context",
                "description": "Flush Tier 3 ephemeral noise and output a clean bootstrap prompt for fresh context.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "render_badge",
                "description": "Render a clean 1-line context fuel gauge markdown badge for agent response footers.",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def call_tool(self, name: str, args: dict[str, Any]) -> str:
        if name == "get_context_status":
            custom_limit = args.get("window_limit")
            if "add_tokens" in args:
                self.meter.current_tokens += args["add_tokens"]
            else:
                # Auto-sync with live Antigravity IDE conversation
                synced = self.meter.sync_with_antigravity(default_limit=custom_limit)
                if synced <= 0:
                    stats = self.ledger.get_stats()
                    if stats["total_estimated_tokens"] > self.meter.current_tokens:
                        self.meter.current_tokens = stats["total_estimated_tokens"]

            if custom_limit:
                self.meter.window_limit = custom_limit

            invariants = len(self.ledger.get_invariants())
            report = self.meter.get_status_report(locked_invariants=invariants)
            return json.dumps(report, indent=2)

        elif name == "record_invariant":
            rule = args["rule"]
            category = args.get("category", "rule")
            event = self.ledger.record_event(category, rule, tier=PriorityTier.TIER_1_INVARIANT)
            self.meter.add_text(rule)
            return f"Invariant locked into Tier 1 (ID {event['id']}): '{rule}'"

        elif name == "record_mistake":
            mistake = args["mistake"]
            reason = args.get("reason", "")
            event = self.ledger.record_mistake(mistake, why=reason)
            self.meter.add_text(mistake + " " + reason)
            return f"Mistake registered in Graveyard (ID {event['id']}): '{mistake}'"

        elif name == "record_milestone":
            milestone = args["milestone"]
            status = args.get("status", "completed")
            event = self.ledger.record_milestone(milestone, status=status)
            self.meter.add_text(milestone)
            return f"Milestone recorded [{status.upper()}]: '{milestone}'"

        elif name == "compile_checkpoint":
            goal = args.get("primary_goal", "")
            milestone = args.get("active_milestone", "")
            next_step = args.get("next_step", "")
            checkpoint = self.pruner.compile_checkpoint(
                primary_goal=goal,
                active_milestone=milestone,
                next_step=next_step,
            )
            return json.dumps(checkpoint, indent=2)

        elif name == "get_keep_drop_diff":
            diff = self.pruner.generate_keep_vs_drop_diff()
            return json.dumps(diff, indent=2)

        elif name == "flush_context":
            res = self.pruner.execute_flush()
            bootstrap_prompt = self.pruner.render_clean_resumption_prompt()
            output = {
                "flush_summary": res,
                "clean_resumption_prompt": bootstrap_prompt,
            }
            return json.dumps(output, indent=2)

        elif name == "render_badge":
            self.meter.sync_with_antigravity()
            invariants = len(self.ledger.get_invariants())
            return self.meter.render_badge(locked_invariants=invariants)

        raise ValueError(f"Unknown tool: '{name}'")

    def run_stdio(self) -> None:
        """Run MCP stdio JSON-RPC loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except Exception:
                continue
            res = self.handle_request(req)
            if res is not None:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="ContextGuard MCP stdio server")
    parser.add_argument("--root", default=".", help="Workspace root directory")
    args = parser.parse_args()

    server = ContextGuardServer(workspace_root=args.root)
    server.run_stdio()


if __name__ == "__main__":
    main()
