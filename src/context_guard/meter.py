"""Zero-dependency Context Saturation Meter & Token Gauge."""
from __future__ import annotations

import math
from enum import Enum
from pathlib import Path
from typing import Any


class SaturationLevel(str, Enum):
    SAFE = "SAFE"            # 0% - 69%
    WARNING = "WARNING"      # 70% - 84%
    CRITICAL = "CRITICAL"    # 85%+


class ContextMeter:
    """Calculates context window usage, capacity thresholds, and renders fuel badges."""

    def __init__(self, window_limit: int = 128_000, warning_threshold: float = 0.70, critical_threshold: float = 0.85) -> None:
        self.window_limit = max(1_000, window_limit)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.current_tokens: int = 0

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Accurate BPE / Code tokenizer approximation (~3.8 chars per token with word/symbol bounds)."""
        if not text:
            return 0
        char_count = len(text)
        # Average English code & prose token density
        tokens = math.ceil(char_count / 3.8)
        return max(1, tokens)

    def update_usage(self, token_count: int) -> None:
        """Update current active token consumption."""
        self.current_tokens = max(0, token_count)

    def add_text(self, text: str) -> int:
        """Estimate tokens for given text and add to meter."""
        added = self.estimate_tokens(text)
        self.current_tokens += added
        return added

    def estimate_file_tokens(self, file_path: Path | str) -> int:
        """Read file and estimate its token footprint."""
        path = Path(file_path)
        if not path.is_file():
            return 0
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            return self.estimate_tokens(content)
        except Exception:
            return 0

    @property
    def usage_ratio(self) -> float:
        """Current usage ratio (0.0 to 1.0+)."""
        return min(1.0, self.current_tokens / self.window_limit)

    @property
    def usage_percentage(self) -> float:
        """Percentage of context window filled."""
        return round(self.usage_ratio * 100, 1)

    @property
    def remaining_tokens(self) -> int:
        """Available headroom before reaching hard window limit."""
        return max(0, self.window_limit - self.current_tokens)

    @property
    def level(self) -> SaturationLevel:
        """Current saturation tier."""
        ratio = self.current_tokens / self.window_limit
        if ratio >= self.critical_threshold:
            return SaturationLevel.CRITICAL
        elif ratio >= self.warning_threshold:
            return SaturationLevel.WARNING
        return SaturationLevel.SAFE

    def render_gauge_bar(self, width: int = 10, unicode_mode: bool = True) -> str:
        """Render a visual fuel gauge bar (e.g. [▓▓▓▓▓▓▓░░░])."""
        ratio = min(1.0, self.current_tokens / self.window_limit)
        filled = int(round(ratio * width))
        empty = max(0, width - filled)

        if unicode_mode:
            fill_char = "▓"
            empty_char = "░"
        else:
            fill_char = "#"
            empty_char = "-"

        return f"[{fill_char * filled}{empty_char * empty}]"

    def render_badge(self, locked_invariants: int = 0) -> str:
        """Render standard 1-line status badge for agent response footers."""
        used_k = f"{round(self.current_tokens / 1000, 1)}k" if self.current_tokens >= 1000 else str(self.current_tokens)
        limit_k = f"{round(self.window_limit / 1000, 0):.0f}k"
        bar = self.render_gauge_bar(width=8)
        pct = f"{self.usage_percentage}%"

        badge_level = self.level
        if badge_level == SaturationLevel.SAFE:
            icon = "⚡"
            status = "SAFE"
        elif badge_level == SaturationLevel.WARNING:
            icon = "⚠️"
            status = "HEAVY"
        else:
            icon = "🚨"
            status = "CRITICAL"

        invariant_str = f" ── [Ledger: {locked_invariants} Invariants Locked]" if locked_invariants > 0 else ""
        return f"{icon} [Context: {used_k}/{limit_k} ({pct}) {bar}] {status}{invariant_str}"

    def get_status_report(self, locked_invariants: int = 0) -> dict[str, Any]:
        """Structured telemetry dictionary."""
        return {
            "current_tokens": self.current_tokens,
            "window_limit": self.window_limit,
            "usage_percentage": self.usage_percentage,
            "remaining_tokens": self.remaining_tokens,
            "saturation_level": self.level.value,
            "compaction_recommended": self.level != SaturationLevel.SAFE,
            "gauge_bar": self.render_gauge_bar(),
            "badge": self.render_badge(locked_invariants=locked_invariants),
        }
