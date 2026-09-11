# Migration from cheap-agent

`cheap-agent` v1 assumed Codex was always the lead. `agent-foreman` removes that assumption.

Key changes:

- renamed `cheap-agent` → `agent-foreman`;
- caller can be Codex, Claude Code, Pi, custom agent, or agy;
- recursive agent/agy delegation is allowed;
- review gate records a generic lead/designated reviewer instead of "Codex approval";
- agy-staff is the preferred worker runtime;
- worktree isolation and accepted-verdict-before-apply remain mandatory;
- state moved from Codex-specific directories to `~/.agent-foreman/` (override with `AGENT_FOREMAN_HOME`).
