"""Unit tests for CheckpointPruner."""
import tempfile
import unittest
from pathlib import Path

from context_guard.ledger import ContextLedger, PriorityTier
from context_guard.pruner import CheckpointPruner


class TestCheckpointPruner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ledger = ContextLedger(workspace_root=self.root)
        self.pruner = CheckpointPruner(workspace_root=self.root, ledger=self.ledger)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compile_checkpoint(self):
        self.ledger.record_rule("Never modify shared configuration without confirmation.")
        self.ledger.record_mistake("Hardcoded secret in settings.py")
        self.ledger.record_milestone("Designed schema", status="completed")

        checkpoint = self.pruner.compile_checkpoint(
            primary_goal="Build ContextGuard",
            active_milestone="Checkpoint Pruner",
            next_step="Write comprehensive tests",
        )

        self.assertEqual(checkpoint["goal_tree"]["primary_goal"], "Build ContextGuard")
        self.assertIn("Never modify shared configuration without confirmation.", checkpoint["invariants"])
        self.assertEqual(len(checkpoint["the_graveyard"]), 1)

        # Verify artifacts written
        self.assertTrue(self.pruner.checkpoint_json_path.is_file())
        self.assertTrue(self.pruner.checkpoint_md_path.is_file())
        md_text = self.pruner.checkpoint_md_path.read_text(encoding="utf-8")
        self.assertIn("Build ContextGuard", md_text)
        self.assertIn("The Graveyard", md_text)

    def test_keep_vs_drop_diff_and_flush(self):
        # 1 Invariant
        self.ledger.record_rule("Keep this high signal invariant.")
        # 1 Huge Ephemeral dump
        self.ledger.record_event("stdout", "dump line\n" * 100, tier=PriorityTier.TIER_3_EPHEMERAL)

        diff = self.pruner.generate_keep_vs_drop_diff()
        self.assertGreater(diff["dropped_tokens"], diff["kept_tokens"])
        self.assertGreaterEqual(diff["reduction_percentage"], 50.0)

        # Execute flush
        res = self.pruner.execute_flush()
        self.assertTrue(res["success"])
        self.assertEqual(res["surviving_events"], 1)

        # Resumption prompt
        prompt = self.pruner.render_clean_resumption_prompt()
        self.assertIn("Resuming from ContextGuard Checkpoint", prompt)


if __name__ == "__main__":
    unittest.main()
