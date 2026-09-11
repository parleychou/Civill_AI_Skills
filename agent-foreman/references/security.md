# Security, isolation, and review boundary

Agent Foreman does not restrict which agent may call which agent. Its hard boundary is **integration**, not topology.

## Isolation

Every repository task is launched from an isolated detached Git worktree. The current source working state is mirrored into a baseline snapshot so the worker sees the caller's current code while its own changes remain separable.

This protects the source working tree from direct worker edits.

## Review state

Implementation runs move through:

```text
running/completed
  -> pending_review
      -> accepted
      -> needs_fix
      -> rejected
  -> applied
```

A continuation resets a write run to `pending_review`.

`apply` refuses to modify the source working tree unless an explicit `accept` verdict has been recorded.

## Reviewer identity

Reviewer identity is not vendor-locked. It can be:

- Codex
- Claude Code
- another lead agent
- a designated reviewer agent
- a parent agy agent reviewing a child agy worker

The important property is that acceptance is an explicit lead/reviewer action after inspecting evidence.

## What to review

Before acceptance, inspect at least:

- actual diff and changed-file set;
- requested scope vs. scope drift;
- correctness and edge cases;
- tests/build/lint actually run;
- dependency/build/public API changes;
- secrets or generated artifacts;
- conflicts with other workers or settled design decisions.

After apply, validate the source working tree again.

## Delivery

Agent Foreman's automatic path stops at applying an accepted patch. It does not automatically push, merge, publish, release, or deploy.

If the user explicitly requests those actions, the current lead handles or separately authorizes them after review.
