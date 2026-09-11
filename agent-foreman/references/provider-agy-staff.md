# agy-staff provider

Agent Foreman prefers `keli-wen/agy-staff` as its execution runtime because agy-staff already supplies personas, background jobs, continuation, model selection, and telemetry.

Project:

https://github.com/keli-wen/agy-staff

## Harness-native installation

### Claude Code

```text
claude plugin marketplace add keli-wen/agy-staff
claude plugin install agy@agy-staff
```

### Codex

```text
codex plugin marketplace add https://github.com/keli-wen/agy-staff
codex plugin add agy@agy-staff
```

Pi is also supported by agy-staff. Other callers do not need to be a named supported harness: they can invoke Agent Foreman's Python CLI and point it to `agy-companion.mjs`.

## Companion discovery

Agent Foreman looks for the agy-staff companion in this order:

1. `AGY_STAFF_COMPANION` environment variable;
2. `runtime.agy_staff_companion` in `config.json`;
3. common Claude/Codex plugin cache and marketplace directories.

If automatic discovery fails, set:

```text
AGY_STAFF_COMPANION=/absolute/path/to/agy-staff/companion/agy-companion.mjs
```

The provider runs the companion from the isolated worktree, so agy-staff's "real working tree" is the temporary worktree rather than the source tree.

## Background jobs

For `staffer`, `researcher`, `reviewer`, and `implementer`, agy-staff returns a background job ID. Agent Foreman records that ID and uses agy-staff's `wait`/`continue` lifecycle.

`ask` is synchronous.

## Fallback

If agy-staff cannot be found and `direct-agy` remains in `provider_priority`, Agent Foreman falls back to direct Antigravity CLI invocation. This preserves portability but does not reproduce all agy-staff job/persona behavior.
