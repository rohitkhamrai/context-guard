"""Unit tests for ContextMeter."""
import unittest

from context_guard.meter import ContextMeter, SaturationLevel


class TestContextMeter(unittest.TestCase):
    def setUp(self):
        self.meter = ContextMeter(window_limit=100_000, warning_threshold=0.70, critical_threshold=0.85)

    def test_estimate_tokens(self):
        text = "Hello world! This is a test."
        tokens = ContextMeter.estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text))

    def test_saturation_levels(self):
        # 0% - Safe
        self.meter.update_usage(10_000)
        self.assertEqual(self.meter.level, SaturationLevel.SAFE)
        self.assertEqual(self.meter.usage_percentage, 10.0)

        # 72% - Warning
        self.meter.update_usage(72_000)
        self.assertEqual(self.meter.level, SaturationLevel.WARNING)

        # 90% - Critical
        self.meter.update_usage(90_000)
        self.assertEqual(self.meter.level, SaturationLevel.CRITICAL)

    def test_gauge_bar_rendering(self):
        self.meter.update_usage(50_000)
        bar = self.meter.render_gauge_bar(width=10, unicode_mode=True)
        self.assertIn("▓", bar)
        self.assertIn("░", bar)

    def test_render_badge(self):
        self.meter.update_usage(30_000)
        badge = self.meter.render_badge(locked_invariants=4)
        self.assertIn("Context:", badge)
        self.assertIn("SAFE", badge)
        self.assertIn("4 Invariants Locked", badge)

        # Test warning badge
        self.meter.update_usage(78_000)
        warning_badge = self.meter.render_badge()
        self.assertIn("HEAVY", warning_badge)


if __name__ == "__main__":
    unittest.main()
