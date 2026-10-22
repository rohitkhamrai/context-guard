"""Cognitive Checkpoint Pruner & Keep-vs-Drop Distillation Engine."""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from .ledger import ContextLedger, PriorityTier
from .meter import ContextMeter


class CheckpointPruner:
    """Compiles the 5-vector cognitive state and executes clean context compaction."""

    def __init__(self, workspace_root: Path | str = ".", ledger: ContextLedger | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.ledger = ledger or ContextLedger(self.workspace_root)
        self.checkpoint_json_path = self.workspace_root / ".context_guard_checkpoint.json"
        self.checkpoint_md_path = self.workspace_root / "ACTIVE_CHECKPOINT.md"

    def detect_ground_truth(self) -> dict[str, Any]:
        """Detect git branch, commit SHA, and modified files if available."""
        truth: dict[str, Any] = {
            "git_branch": "unknown",
            "git_commit": "unknown",
            "active_modified_files": [],
        }
        try:
            res_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res_branch.returncode == 0:
                truth["git_branch"] = res_branch.stdout.strip()

            res_commit = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res_commit.returncode == 0:
                truth["git_commit"] = res_commit.stdout.strip()

            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res_status.returncode == 0:
                truth["active_modified_files"] = [
                    line.strip().split()[-1] for line in res_status.stdout.splitlines() if line.strip()
                ]
        except Exception:
            pass
        return truth

    def compile_checkpoint(
        self,
        primary_goal: str = "",
        active_milestone: str = "",
        next_step: str = "",
        custom_invariants: list[str] | None = None,
    ) -> dict[str, Any]:
        """Synthesize the 5-vector structured cognitive checkpoint from ledger and environment."""
        ground_truth = self.detect_ground_truth()

        # Invariants & Rules
        invariants = list(self.ledger.get_invariants())
        if custom_invariants:
            for inv in custom_invariants:
                if inv not in invariants:
                    invariants.append(inv)

        # Graveyard (Mistakes to avoid)
        graveyard = list(self.ledger.get_graveyard())

        # Goal Tree extraction
        milestone_events = [e["content"] for e in self.ledger.events if e["category"] == "milestone"]
        goal_tree = {
            "primary_goal": primary_goal or "Active Engineering Task",
            "completed_milestones": milestone_events,
            "active_milestone": active_milestone or "In Progress",
        }

        checkpoint_data = {
            "version": "1.0",
            "timestamp": time.time(),
            "goal_tree": goal_tree,
            "ground_truth": ground_truth,
            "the_graveyard": graveyard,
            "invariants": invariants,
            "next_vector": next_step or "Resume implementation",
        }

        # Write to JSON
        self.checkpoint_json_path.write_text(json.dumps(checkpoint_data, indent=2), encoding="utf-8")

        # Write Markdown artifact
        md_content = self.render_checkpoint_markdown(checkpoint_data)
        self.checkpoint_md_path.write_text(md_content, encoding="utf-8")

        return checkpoint_data

    def generate_keep_vs_drop_diff(self) -> dict[str, Any]:
        """Calculate differential between preserved high-signal state and dropped noise."""
        stats = self.ledger.get_stats()
        kept_tokens = stats["tier1_invariant_tokens"] + stats["tier2_contextual_tokens"]
        dropped_tokens = stats["tier3_ephemeral_tokens"]
        total_tokens = stats["total_estimated_tokens"]

        kept_items = [
            f"[{e['category'].upper()}] {e['content'][:80]}..."
            for e in self.ledger.events
            if e["tier"] in (PriorityTier.TIER_1_INVARIANT.value, PriorityTier.TIER_2_CONTEXTUAL.value)
        ]
        dropped_items = [
            f"[{e['category'].upper()}] {e['content'][:80]}..."
            for e in self.ledger.events
            if e["tier"] == PriorityTier.TIER_3_EPHEMERAL.value
        ]

        reduction_pct = round((dropped_tokens / max(1, total_tokens)) * 100, 1)

        return {
            "total_tokens_before": total_tokens,
            "kept_tokens": kept_tokens,
            "dropped_tokens": dropped_tokens,
            "reduction_percentage": reduction_pct,
            "kept_count": len(kept_items),
            "dropped_count": len(dropped_items),
            "sample_kept": kept_items[:5],
            "sample_dropped": dropped_items[:5],
        }

    def render_checkpoint_markdown(self, data: dict[str, Any]) -> str:
        """Render high-taste GSD Markdown artifact for the active checkpoint."""
        gt = data.get("ground_truth", {})
        goals = data.get("goal_tree", {})
        graveyard = data.get("the_graveyard", [])
        invariants = data.get("invariants", [])

        lines = [
            "# 🧠 ContextGuard: Active Cognitive Checkpoint",
            "",
            f"> Checkpoint generated at `{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('timestamp', time.time())))}`",
            "",
            "## 1. Goal Tree",
            f"- **Primary Goal**: {goals.get('primary_goal', 'N/A')}",
            f"- **Active Milestone**: {goals.get('active_milestone', 'N/A')}",
        ]

        completed = goals.get("completed_milestones", [])
        if completed:
            lines.append("### Completed Milestones:")
            for m in completed:
                lines.append(f"  - {m}")

        lines.extend([
            "",
            "## 2. Ground Truth State",
            f"- **Git Branch**: `{gt.get('git_branch', 'unknown')}`",
            f"- **Latest Commit**: `{gt.get('git_commit', 'unknown')}`",
        ])

        mod_files = gt.get("active_modified_files", [])
        if mod_files:
            lines.append(f"- **Modified Files**: {', '.join(f'`{f}`' for f in mod_files)}")

        lines.extend([
            "",
            "## 3. The Graveyard (Mistakes & Dead-Ends to Avoid)",
        ])
        if graveyard:
            for g in graveyard:
                lines.append(f"- ❌ {g}")
        else:
            lines.append("- *(No negative constraints recorded yet)*")

        lines.extend([
            "",
            "## 4. Locked Invariants & Rules",
        ])
        if invariants:
            for inv in invariants:
                lines.append(f"- 🔒 {inv}")
        else:
            lines.append("- *(No invariants locked)*")

        lines.extend([
            "",
            "## 5. Next Execution Vector",
            f"👉 **{data.get('next_vector', 'Resume implementation')}**",
            "",
        ])

        return "\n".join(lines)

    def execute_flush(self) -> dict[str, Any]:
        """Prune Tier 3 noise from ledger, keeping only Tier 1 & Tier 2."""
        diff = self.generate_keep_vs_drop_diff()

        # Compile checkpoint if not already compiled
        if not self.checkpoint_json_path.is_file():
            self.compile_checkpoint()

        # Retain only Tier 1 and Tier 2 events
        surviving = [
            e
            for e in self.ledger.events
            if e["tier"] in (PriorityTier.TIER_1_INVARIANT.value, PriorityTier.TIER_2_CONTEXTUAL.value)
        ]
        self.ledger.events = surviving
        self.ledger.save()

        return {
            "success": True,
            "tokens_freed": diff["dropped_tokens"],
            "reduction_percentage": diff["reduction_percentage"],
            "surviving_events": len(surviving),
            "checkpoint_json": str(self.checkpoint_json_path),
            "checkpoint_markdown": str(self.checkpoint_md_path),
        }

    def render_clean_resumption_prompt(self) -> str:
        """Generate a dense, token-minimal bootstrap prompt for fresh or compacted context."""
        if not self.checkpoint_json_path.is_file():
            return "No checkpoint found."

        try:
            data = json.loads(self.checkpoint_json_path.read_text(encoding="utf-8"))
        except Exception as e:
            return f"Error loading checkpoint: {e}"

        goals = data.get("goal_tree", {})
        graveyard = data.get("the_graveyard", [])
        invariants = data.get("invariants", [])
        next_vec = data.get("next_vector", "")

        prompt_lines = [
            "# Resuming from ContextGuard Checkpoint (Zero Noise)",
            f"Active Goal: {goals.get('primary_goal')}",
            f"Milestone: {goals.get('active_milestone')}",
            "Negative Constraints (NEVER repeat):",
        ]
        for g in graveyard[:5]:
            prompt_lines.append(f"  - {g}")

        prompt_lines.append("Locked Invariants:")
        for inv in invariants[:5]:
            prompt_lines.append(f"  - {inv}")

        prompt_lines.append(f"Immediate Action: {next_vec}")
        return "\n".join(prompt_lines)
