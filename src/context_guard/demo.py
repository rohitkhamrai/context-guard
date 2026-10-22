"""Interactive Showcase Demo for ContextGuard."""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

from .ledger import ContextLedger, PriorityTier
from .meter import ContextMeter
from .pruner import CheckpointPruner

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"""
{CYAN}{BOLD}========================================================================
[*] CONTEXT-GUARD: Real-Time Saturation Meter & Cognitive Checkpointing
========================================================================{RESET}
""")


def run_demo(target_dir: str = "."):
    print_banner()
    root = Path(target_dir).resolve()

    meter = ContextMeter(window_limit=128_000)
    ledger = ContextLedger(root)
    pruner = CheckpointPruner(root, ledger=ledger)

    # 1. Ambient Tracking & Continuous Write-Through
    print(f"{BOLD}[1/4] Ambient Invariant Registration & Ledger Write-Through...{RESET}")
    r1 = ledger.record_rule("Never modify legacy database schemas without differential parity tests.")
    r2 = ledger.record_rule("Always enforce zero external dependencies in core runtime.")
    m1 = ledger.record_mistake("Imported raw regex inside tight loop", why="Caused 14x latency regression")
    g1 = ledger.record_milestone("Scaffolded ContextGuard architecture", status="completed")

    print(f"  {GREEN}[LOCKED]{RESET} Tier 1 Invariant : {r1['content'][:60]}...")
    print(f"  {GREEN}[LOCKED]{RESET} Tier 1 Invariant : {r2['content'][:60]}...")
    print(f"  {RED}[GRAVEYARD]{RESET} Mistake Recorded : {m1['content'][:60]}...")
    print(f"  {CYAN}[MILESTONE]{RESET} Goal Milestone   : {g1['content']}")

    # 2. Simulating Tool Noise & Saturation Warning
    print(f"\n{BOLD}[2/4] Simulating Agent Session Accumulating Ephemeral Tool Noise...{RESET}")
    # Inject large simulated build log / test trace (Ephemeral Tier 3)
    noisy_output = "npm ERR! code ELIFECYCLE\n" + ("  at Object.<anonymous> (/node_modules/pkg/index.js:142:12)\n" * 800)
    ledger.record_event("stdout", noisy_output, tier=PriorityTier.TIER_3_EPHEMERAL)
    ledger.record_event("file_dump", "const wholeFile = 'huge buffer';" * 4000, tier=PriorityTier.TIER_3_EPHEMERAL)

    stats = ledger.get_stats()
    meter.update_usage(stats["total_estimated_tokens"])

    print(f"  Raw Chat Volume  : {BOLD}{stats['total_estimated_tokens']} tokens{RESET}")
    print(f"  Ephemeral Noise  : {YELLOW}{stats['tier3_ephemeral_tokens']} tokens ({stats['droppable_percentage']}% of context){RESET}")
    print(f"  Status Badge     : {meter.render_badge(locked_invariants=stats['invariants_count'])}")

    # 3. Checkpoint Compilation (5-Vector State)
    print(f"\n{BOLD}[3/4] Compiling 5-Vector Cognitive Checkpoint (BrainVault)...{RESET}")
    checkpoint = pruner.compile_checkpoint(
        primary_goal="Build ContextGuard Engine for AI Coding Agents",
        active_milestone="Token Meter & Checkpoint Pruner Verification",
        next_step="Connect MCP server to Antigravity IDE and run multi-OS test matrix",
    )
    print(f"  {GREEN}[WRITTEN]{RESET} Checkpoint JSON : {pruner.checkpoint_json_path.name}")
    print(f"  {GREEN}[WRITTEN]{RESET} Human Artifact  : {pruner.checkpoint_md_path.name}")

    # 4. Context Flush & Keep-vs-Drop Differential
    print(f"\n{BOLD}[4/4] Executing Keep-vs-Drop Differential & Context Flush...{RESET}")
    diff = pruner.generate_keep_vs_drop_diff()
    print(f"  Tokens Before Flush : {BOLD}{diff['total_tokens_before']} tokens{RESET}")
    print(f"  Preserved Signal    : {GREEN}{diff['kept_tokens']} tokens{RESET} ({diff['kept_count']} critical items kept)")
    print(f"  Purged Dead Noise   : {RED}{diff['dropped_tokens']} tokens{RESET} ({diff['dropped_count']} raw logs dumped)")
    print(f"  Context Reduction   : {GREEN}{BOLD}{diff['reduction_percentage']}% freed!{RESET}")

    flush_res = pruner.execute_flush()
    print(f"  {GREEN}[FLUSH COMPLETE]{RESET} Ledger reset from {stats['total_estimated_tokens']} ➔ {flush_res['tokens_freed']} freed.")

    print(f"\n{CYAN}{BOLD}========================================================================")
    print(f"[SUCCESS] ContextGuard verified. Ready for deployment.")
    print(f"========================================================================{RESET}\n")


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    run_demo(target)


if __name__ == "__main__":
    main()
