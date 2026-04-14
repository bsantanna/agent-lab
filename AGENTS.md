# AGENTS.md

This file is the vendor-neutral coordination contract for AI tooling in this repository.

## Source of Truth

Shared reusable intent lives here:
- `.claude/CLAUDE.md`
- `.claude/skills/*/SKILL.md`
- `.mcp.json`

Those files are the canonical implementation-neutral specs. Vendor-specific directories are adapters, not the source of truth.
Tool-local files such as `.claude/settings.local.json` are not part of the shared contract.

## Cross-Tool Rules

- Keep shared behavior and domain knowledge in implementation-neutral source files.
- Treat vendor-specific directories such as `.codex/` as generated or adapter layers.
- Use progressive context loading. Do not preload every skill or specialty document by default.
- When the user asks for a specific specialty such as `quant`, `seo`, `software-engineering`, or `quaks-generator`, load only the matching adapter context for the active tool.
- If the user uses slash-like syntax such as `/quant`, interpret that as an intent to activate the corresponding specialty, even if the current CLI does not support custom slash commands natively.
- Prefer the active tool's native mechanisms for scoped instructions, custom agents, prompts, or subagents instead of forcing another vendor's UX model.

## Reference Implementations

Use the adapter that matches the current tool:

- Codex:
  Read `.codex/AGENTS.md` for the Codex-specific behavior.
  Use `./codex-skill <name>` for skill-scoped sessions.
  Use `.codex/skills/<name>/AGENTS.md` for progressive context loading.
  Use `.codex/agents/<name>.toml` for specialist agents.

- Claude Code:
  Read `.claude/CLAUDE.md`.
  Treat `.claude/skills/*/SKILL.md` as the skill system.

- Gemini CLI:
  Read `GEMINI.md`.
  Use `.gemini/skills/<name>/SKILL.md` for skill activation.
  Follow behavioral mandates in `GEMINI.md` for tool-specific alignment.

- another future CLI:

## Adapter Policy

- Root `AGENTS.md` should stay vendor-neutral.
- Tool-specific behavior belongs in the matching adapter directory.
- If a tool cannot support a feature directly, approximate it with the closest native mechanism instead of copying another vendor's surface API.
- After updating shared specs in `.claude/`, regenerate or refresh any adapter layers that depend on them.
