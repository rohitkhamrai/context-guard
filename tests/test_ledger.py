"""Unit tests for ContextLedger."""
import tempfile
import unittest
from pathlib import Path

from context_guard.ledger import ContextLedger, PriorityTier


class TestContextLedger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.ledger = ContextLedger(workspace_root=self.root)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_deterministic_classification(self):
        # Invariant rule
        tier = self.ledger.classify_content("You must NEVER mutate the legacy database without backup.")
        self.assertEqual(tier, PriorityTier.TIER_1_INVARIANT)

        # Ephemeral log trace
        trace = "Traceback (most recent call last):\n" + "\n".join(f"  File foo.py, line {i}" for i in range(40))
        tier_trace = self.ledger.classify_content(trace)
        self.assertEqual(tier_trace, PriorityTier.TIER_3_EPHEMERAL)

        # Contextual summary
        tier_normal = self.ledger.classify_content("Refactored authentication middleware to use JWT.")
        self.assertEqual(tier_normal, PriorityTier.TIER_2_CONTEXTUAL)

    def test_record_and_persist(self):
        r = self.ledger.record_rule("Always enforce zero-dependency standard.")
        self.assertEqual(r["tier"], PriorityTier.TIER_1_INVARIANT.value)

        m = self.ledger.record_mistake("Used bare exceptions", why="Caught system exit")
        self.assertEqual(m["category"], "graveyard")

        # Verify disk persistence
        new_ledger = ContextLedger(workspace_root=self.root)
        self.assertEqual(len(new_ledger.events), 2)
        invariants = new_ledger.get_invariants()
        self.assertIn("Always enforce zero-dependency standard.", invariants)

    def test_stats_and_graveyard(self):
        self.ledger.record_rule("Rule 1")
        self.ledger.record_mistake("Mistake 1")
        self.ledger.record_event("stdout", "some long output\n" * 50, tier=PriorityTier.TIER_3_EPHEMERAL)

        stats = self.ledger.get_stats()
        self.assertEqual(stats["total_events"], 3)
        self.assertGreater(stats["tier3_ephemeral_tokens"], 0)
        self.assertGreater(stats["droppable_percentage"], 0)

        graveyard = self.ledger.get_graveyard()
        self.assertEqual(len(graveyard), 1)
        self.assertIn("Mistake 1", graveyard[0])


if __name__ == "__main__":
    unittest.main()
