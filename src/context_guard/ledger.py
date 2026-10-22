"""Continuous Write-Through State Ledger with Deterministic Priority Tagging."""
from __future__ import annotations

import json
import os
import re
import time
from enum import Enum
from pathlib import Path
from typing import Any

from .meter import ContextMeter


class PriorityTier(str, Enum):
    TIER_1_INVARIANT = "TIER_1_INVARIANT"    # Never drop: Rules, Test Truth, Negative Constraints
    TIER_2_CONTEXTUAL = "TIER_2_CONTEXTUAL"  # Summarize: Milestones, Architectural Decisions
    TIER_3_EPHEMERAL = "TIER_3_EPHEMERAL"    # Drop on flush: Raw stdout, Large File Reads, Grep Dumps


# Regex patterns for automatic deterministic priority tagging
INVARIANT_PATTERNS = [
    re.compile(r"\b(never|do not|must not|don't|always|invariant|constraint|rule|forbidden)\b", re.IGNORECASE),
    re.compile(r"\b(exit code 0|exit code 1|ran \d+ tests|failing|passing|commit [0-9a-f]{7,40})\b", re.IGNORECASE),
]

EPHEMERAL_PATTERNS = [
    re.compile(r"(Traceback \(most recent call last\):|\.py:\d+: [A-Z]|npm ERR!|fatal error:)", re.IGNORECASE),
    re.compile(r"^\s*(\[diff_block_start\]|diff --git|@@ -\d+,\d+ \+\d+,\d+ @@)", re.MULTILINE),
]


class ContextLedger:
    """Manages continuous event streaming, priority categorization, and persistence."""

    def __init__(self, workspace_root: Path | str = ".", storage_file: str = ".context_guard_ledger.json") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.storage_path = self.workspace_root / storage_file
        self.events: list[dict[str, Any]] = []
        self.load()

    def classify_content(self, text: str, category: str = "general") -> PriorityTier:
        """Deterministically assign priority tier to incoming content without LLM overhead."""
        text_lower = text.lower()

        # Explicit user rules & constraints
        if category in ("rule", "invariant", "negative_constraint", "graveyard", "test_result"):
            return PriorityTier.TIER_1_INVARIANT

        for pattern in INVARIANT_PATTERNS:
            if pattern.search(text_lower):
                return PriorityTier.TIER_1_INVARIANT

        # Ephemeral noise: long text with logs or diff dumps
        line_count = len(text.splitlines())
        if line_count > 35 or category in ("stdout", "stderr", "file_dump", "grep_results"):
            return PriorityTier.TIER_3_EPHEMERAL

        for pattern in EPHEMERAL_PATTERNS:
            if pattern.search(text):
                return PriorityTier.TIER_3_EPHEMERAL

        return PriorityTier.TIER_2_CONTEXTUAL

    def record_event(
        self,
        category: str,
        content: str,
        tier: PriorityTier | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an event with deterministic tier classification and atomic write-through."""
        if tier is None:
            tier = self.classify_content(content, category=category)

        token_est = ContextMeter.estimate_tokens(content)
        event = {
            "id": len(self.events) + 1,
            "timestamp": time.time(),
            "category": category,
            "tier": tier.value,
            "tokens": token_est,
            "content": content,
            "metadata": metadata or {},
        }
        self.events.append(event)
        self.save()
        return event

    def record_rule(self, rule: str) -> dict[str, Any]:
        """Convenience method to register a Tier 1 active rule/invariant."""
        return self.record_event("rule", rule, tier=PriorityTier.TIER_1_INVARIANT)

    def record_mistake(self, mistake: str, why: str = "") -> dict[str, Any]:
        """Convenience method to record a mistake in the graveyard."""
        text = f"MISTAKE TO AVOID: {mistake}"
        if why:
            text += f" (Reason: {why})"
        return self.record_event("graveyard", text, tier=PriorityTier.TIER_1_INVARIANT)

    def record_milestone(self, milestone: str, status: str = "completed") -> dict[str, Any]:
        """Record goal progress."""
        return self.record_event("milestone", f"[{status.upper()}] {milestone}", tier=PriorityTier.TIER_2_CONTEXTUAL)

    def get_tier_events(self, tier: PriorityTier) -> list[dict[str, Any]]:
        """Retrieve all events belonging to a specific tier."""
        return [e for e in self.events if e["tier"] == tier.value]

    def get_invariants(self) -> list[str]:
        """Extract all locked Tier 1 invariant statements."""
        tier1 = self.get_tier_events(PriorityTier.TIER_1_INVARIANT)
        return [e["content"] for e in tier1]

    def get_graveyard(self) -> list[str]:
        """Extract all negative constraints and avoided mistakes."""
        return [
            e["content"]
            for e in self.events
            if e["tier"] == PriorityTier.TIER_1_INVARIANT and e["category"] in ("graveyard", "negative_constraint")
        ]

    def get_stats(self) -> dict[str, Any]:
        """Compute token breakdown across all three priority tiers."""
        total_tokens = sum(e["tokens"] for e in self.events)
        tier1_tokens = sum(e["tokens"] for e in self.events if e["tier"] == PriorityTier.TIER_1_INVARIANT.value)
        tier2_tokens = sum(e["tokens"] for e in self.events if e["tier"] == PriorityTier.TIER_2_CONTEXTUAL.value)
        tier3_tokens = sum(e["tokens"] for e in self.events if e["tier"] == PriorityTier.TIER_3_EPHEMERAL.value)

        return {
            "total_events": len(self.events),
            "total_estimated_tokens": total_tokens,
            "tier1_invariant_tokens": tier1_tokens,
            "tier2_contextual_tokens": tier2_tokens,
            "tier3_ephemeral_tokens": tier3_tokens,
            "droppable_percentage": round((tier3_tokens / max(1, total_tokens)) * 100, 1),
            "invariants_count": len(self.get_tier_events(PriorityTier.TIER_1_INVARIANT)),
        }

    def clear(self) -> None:
        """Clear memory and reset ledger on disk."""
        self.events = []
        if self.storage_path.is_file():
            try:
                self.storage_path.unlink()
            except Exception:
                pass

    def save(self) -> None:
        """Atomic write-through to disk."""
        data = {
            "version": "1.0",
            "last_updated": time.time(),
            "events": self.events,
        }
        tmp = self.storage_path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            os.replace(tmp, self.storage_path)
        except Exception:
            pass

    def load(self) -> bool:
        """Load ledger from storage file."""
        if not self.storage_path.is_file():
            return False
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.events = data.get("events", [])
            return True
        except Exception:
            return False
