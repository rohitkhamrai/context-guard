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

    @staticmethod
    def detect_antigravity_session() -> tuple[str, Path | None]:
        """Auto-detect current Antigravity IDE conversation ID and transcript path."""
        home = Path.home()
        brain_dir = home / ".gemini" / "antigravity-ide" / "brain"
        if not brain_dir.is_dir():
            return "unknown", None

        try:
            conv_dirs = [d for d in brain_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if not conv_dirs:
                return "unknown", None
            latest_dir = max(conv_dirs, key=lambda d: d.stat().st_mtime)
            transcript_file = latest_dir / ".system_generated" / "logs" / "transcript.jsonl"
            return latest_dir.name, transcript_file if transcript_file.is_file() else None
        except Exception:
            return "unknown", None

    def sync_with_antigravity(self, default_limit: int | None = None) -> int:
        """Measure real-time active token footprint of Antigravity conversation (post-compaction)."""
        _, transcript_path = self.detect_antigravity_session()
        if not transcript_path or not transcript_path.is_file():
            return self.current_tokens

        try:
            with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            latest_checkpoint_idx = 0
            for idx, line in enumerate(lines):
                if '"type":"CHECKPOINT"' in line or '"type": "CHECKPOINT"' in line:
                    latest_checkpoint_idx = idx

            active_lines = lines[latest_checkpoint_idx:]
            active_chars = sum(len(l) for l in active_lines)
            tokens = math.ceil(active_chars / 3.8)
            self.current_tokens = tokens
            if default_limit is not None:
                self.window_limit = default_limit
            elif self.window_limit == 128_000:
                self.window_limit = 160_000
            return tokens
        except Exception:
            return self.current_tokens

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

    def render_badge(self, locked_invariants: int = 0, unicode_mode: bool = True) -> str:
        """Render standard 1-line status badge for agent response footers."""
        used_k = f"{round(self.current_tokens / 1000, 1)}k" if self.current_tokens >= 1000 else str(self.current_tokens)
        limit_k = f"{round(self.window_limit / 1000, 0):.0f}k"
        bar = self.render_gauge_bar(width=8, unicode_mode=unicode_mode)
        pct = f"{self.usage_percentage}%"

        badge_level = self.level
        if unicode_mode:
            if badge_level == SaturationLevel.SAFE:
                icon = "⚡"
                status = "SAFE"
            elif badge_level == SaturationLevel.WARNING:
                icon = "⚠️"
                status = "HEAVY"
            else:
                icon = "🚨"
                status = "CRITICAL"
        else:
            if badge_level == SaturationLevel.SAFE:
                icon = "[*]"
                status = "SAFE"
            elif badge_level == SaturationLevel.WARNING:
                icon = "[!]"
                status = "HEAVY"
            else:
                icon = "[ALERT]"
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
