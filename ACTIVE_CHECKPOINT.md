# 🧠 ContextGuard: Active Cognitive Checkpoint

> Checkpoint generated at `2026-10-22 09:47:31`

## 1. Goal Tree
- **Primary Goal**: Build Precision-MCP and ContextGuard for AI coding agents
- **Active Milestone**: Live ContextGuard Demonstration
### Completed Milestones:
  - [COMPLETED] Scaffolded ContextGuard architecture

## 2. Ground Truth State
- **Git Branch**: `master`
- **Latest Commit**: `d49623c`
- **Modified Files**: `.agents/`

## 3. The Graveyard (Mistakes & Dead-Ends to Avoid)
- ❌ MISTAKE TO AVOID: Imported raw regex inside tight loop (Reason: Caused 14x latency regression)
- ❌ MISTAKE TO AVOID: Bypassed PrecisionMCP with whole-file view_file reads (Reason: Flooded context window and diluted instruction adherence)

## 4. Locked Invariants & Rules
- 🔒 Never modify legacy database schemas without differential parity tests.
- 🔒 Always enforce zero external dependencies in core runtime.
- 🔒 MISTAKE TO AVOID: Imported raw regex inside tight loop (Reason: Caused 14x latency regression)
- 🔒 Standard library only: zero external dependencies for agent tools
- 🔒 MISTAKE TO AVOID: Bypassed PrecisionMCP with whole-file view_file reads (Reason: Flooded context window and diluted instruction adherence)

## 5. Next Execution Vector
👉 **Review live Keep vs Drop differential and user feedback**
