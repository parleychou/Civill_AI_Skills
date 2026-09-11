# Agent Foreman

**Agent Foreman（AI 工头）** is the v2 successor to `cheap-agent`.

It is a caller-agnostic orchestration and governance Skill:

```text
Any Lead Agent
   │
   ├─ Codex
   ├─ Claude Code
   ├─ Pi
   ├─ custom agent
   └─ agy itself
        │
        ▼
   Agent Foreman
        │
   routing / isolation / provenance
        │
        ▼
     agy-staff
   staffer / researcher / reviewer / implementer
        │
        ▼
  isolated Git worktree
        │
        ▼
 Lead / Reviewer Gate
 accept / needs-fix / reject
        │
        ▼
      source tree
```

The key change from `cheap-agent` is that **Codex is no longer hard-coded as the lead**. The current caller owns review/integration responsibility, and an agy worker may recursively delegate to another agy worker.

## Requirements

- Python 3.10+
- Git
- Preferred: `agy-staff` + Node.js + Antigravity CLI
- Fallback: Antigravity CLI (`agy`) directly

## Install as a Skill

### Claude Code

```text
python scripts/install.py --target claude
```

Installs to `~/.claude/skills/agent-foreman`.

### Codex

```text
python scripts/install.py --target codex
```

Installs to `~/.agents/skills/agent-foreman` by default. Use `--legacy-codex` for the legacy `~/.codex/skills` path.

### Both

```text
python scripts/install.py --target both
```

Any other Agent Skills-compatible harness can copy the folder to its normal skills directory. Any agent that can execute Python may also call `scripts/agent_foreman.py` directly without native Skill installation.

## Runtime setup

Install agy-staff in the harness where available, or set:

```text
AGY_STAFF_COMPANION=/path/to/agy-staff/companion/agy-companion.mjs
```

Then:

```text
python scripts/agent_foreman.py doctor --repo .
```

## Typical flow

```text
python scripts/agent_foreman.py dispatch --repo . --persona implementer --task "..." --caller claude-code
python scripts/agent_foreman.py collect --run-id <id> --wait 10m
# inspect diff + tests
python scripts/agent_foreman.py verdict --run-id <id> --decision accept --reviewer claude-code --notes "..."
python scripts/agent_foreman.py apply --run-id <id> --repo .
python scripts/agent_foreman.py cleanup --run-id <id>
```

See `SKILL.md` for the agent-facing workflow.
