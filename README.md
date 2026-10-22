<div align="center">

# 🛡️ ContextGuard

**Real-Time Context Saturation Meter & Cognitive State Checkpointing Engine for AI Coding Agents**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: >=3.10](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Protocol: MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Zero-success.svg)](#features)

*Stop flying blind on token limits. Eliminate context rot, protect active goals, and prune dead tool noise with 1-click cognitive state carry-over.*

</div>

---

## 🚨 The Problem: Context Rot & Token Blindness

Modern AI coding agents (Claude Code, Cursor, Antigravity, Windsurf) suffer from a critical degradation curve:

1. **Token Blindness**: Developers have zero visibility into their context consumption until the agent suddenly slows down or hits hard window limits.
2. **Context Rot**: At 60k+ tokens, even frontier models experience attention dilution—they forget negative constraints (*"never use library X"*), hallucinate file boundaries, and repeat failed debugging attempts.
3. **The "Deathbed Compaction" Trap**: Standard agent auto-compaction triggers only when memory is already corrupted. It dumps unstructured, lossy narrative prose that discards exact test hashes, active git commits, and failure post-mortems.

---

## ⚡ The Solution: Dual-Layer Architecture

**ContextGuard** runs inside the **Model Context Protocol (MCP)** to provide real-time ambient monitoring and deterministic, structured state distillation:

```
┌────────────────────────────────────────────────────────┐
│  AI Coding Session (Claude Code / Cursor / IDE)        │
│                                                        │
│  Turn Footer:                                          │
│  ⚡ [Context: 42k/128k (32%) ▓▓▓░░░░░░░] SAFE          │
└──────────────────────────┬─────────────────────────────┘
                           │ Continuous Write-Through (0ms, 0 tokens)
                           ▼
┌────────────────────────────────────────────────────────┐
│  Layer 1: Deterministic Priority Ledger                │
│  - TIER 1 (Invariant): User rules, test truth, commit  │
│  - TIER 2 (Contextual): Milestones, hypotheses         │
│  - TIER 3 (Ephemeral): Raw terminal stdout, file dumps │
└──────────────────────────┬─────────────────────────────┘
                           │ Trigger at 75% Saturation Threshold
                           ▼
┌────────────────────────────────────────────────────────┐
│  Layer 2: On-Demand Cognitive Checkpoint Engine        │
│  - Compiles 5-Vector `checkpoint.json` & Markdown card │
│  - Keep vs Drop Differential (>95% tokens freed)       │
│  - Resets context cleanly with zero lost memory        │
└────────────────────────────────────────────────────────┘
```

---

## 🧠 The 5-Vector Cognitive Checkpoint

Instead of lossy conversational prose, ContextGuard synthesizes state into 5 orthogonal vectors:

1. **Goal Tree**: Active objective, completed milestones, current blocker.
2. **Ground Truth State**: Git branch, commit SHA, passing test paths, active modified files.
3. **The Graveyard (Negative Constraints)**: Dead-end approaches and mistakes to **NEVER** repeat.
4. **Locked Invariants**: System rules, security guidelines, architecture contracts.
5. **Next Vector**: Exact immediate action to execute upon resumption.

---

## 📦 Installation

### Option 1: Run instantly with `uvx`
```bash
uvx context-guard
```

### Option 2: Install via `pip`
```bash
pip install -e .
context-guard
```

---

## ⚙️ Agent Configuration

### 1. Antigravity IDE / Gemini CLI (`mcp_config.json`)
```json
{
  "mcpServers": {
    "ContextGuard": {
      "command": "python",
      "args": ["-m", "context_guard.server", "--root", "."]
    }
  }
}
```

### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "context-guard": {
      "command": "context-guard",
      "args": ["--root", "/path/to/project"]
    }
  }
}
```

### 3. Cursor IDE (`settings.json`)
```json
{
  "mcp": {
    "servers": {
      "context-guard": {
        "command": "python",
        "args": ["-m", "context_guard.server", "--root", "."]
      }
    }
  }
}
```

---

## 🧩 Exposed MCP Tools

| Tool | Parameters | Description |
|---|---|---|
| `get_context_status` | `window_limit?`, `add_tokens?` | Returns active token count, percentage, gauge bar, and saturation tier (`SAFE`, `WARNING`, `CRITICAL`). |
| `record_invariant` | `rule`, `category?` | Locks a critical rule or architecture invariant into Tier 1 (never dropped). |
| `record_mistake` | `mistake`, `reason?` | Registers a failed attempt in the Graveyard so the model never repeats it. |
| `record_milestone` | `milestone`, `status?` | Tracks progress milestones along the active goal tree. |
| `compile_checkpoint` | `primary_goal?`, `active_milestone?`, `next_step?` | Synthesizes the 5-vector state into `checkpoint.json` and human-readable `ACTIVE_CHECKPOINT.md`. |
| `get_keep_drop_diff` | none | Generates a differential report showing tokens saved and items kept vs dropped. |
| `flush_context` | none | Purges Tier 3 ephemeral noise and outputs a clean bootstrap prompt for instant resumption. |
| `render_badge` | none | Renders a 1-line markdown status badge for agent response footers. |

---

## 🖥️ Interactive Showcase Demo

Run the terminal showcase:
```bash
python -m context_guard.demo
```

---

## 🧪 Testing

Run comprehensive unit tests across meter, ledger, pruner, and MCP handlers:
```bash
python -m unittest discover -s tests -v
```

---

## 📄 License

MIT © [Rohit Kumar Khamrai](https://github.com/rohitkhamrai)
