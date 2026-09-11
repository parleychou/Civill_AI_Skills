# Caller contract

`agent-foreman` is deliberately **caller-agnostic**.

## Who may be the lead?

Any process or agent capable of reading this skill and invoking its CLI, including:

- OpenAI Codex
- Claude Code
- Pi
- another Agent Skills-compatible harness
- a custom agent
- an agy / Gemini worker
- an agent started by another agent

No caller name, vendor, or model family receives special authority.

## Lead responsibility

The current lead owns:

1. task scope and settled decisions;
2. choosing whether delegation is worthwhile;
3. reviewing consequential worker output;
4. recording the acceptance verdict for code;
5. integration and final user-facing completion claims.

The lead may designate another reviewer. Review authority is recorded as a string for auditability; it is not tied to a particular vendor.

## Recursive delegation

Recursive delegation is allowed:

```text
Lead Agent
  -> agent-foreman
      -> agy worker A
          -> agent-foreman
              -> agy worker B
```

A parent agy worker may therefore be the lead for a child agy worker.

When possible, propagate:

- `--caller`
- `--parent-run-id`
- environment `AGENT_FOREMAN_PARENT_RUN_ID`
- environment `AGENT_FOREMAN_DEPTH`

The default config does not set a maximum depth. Operators may add one locally to protect against accidental runaway recursion.

## Avoiding useless loops

This is an efficiency rule, not a caller restriction.

Delegate again only if the child can produce an independent, coherent result: a separate research angle, a bounded implementation, a black-box review, or work that meaningfully reduces the parent's context/cost.

Do not bounce the same unresolved task between agents with no new evidence or decision.
