# Routing policy

## Delegate by default

Use the external worker when the task is bounded and substantial enough that offloading saves Codex context or inference cost:

- locating code, dependencies, call paths, TODOs, or likely bug sites;
- summarizing many files or a subsystem;
- first-pass debugging or code review;
- generating or extending tests;
- repetitive/boilerplate changes;
- documentation updates;
- straightforward implementations with a clear specification and limited blast radius.

## Codex remains primary

Keep these with Codex, though the worker may provide non-authoritative research:

- architecture and cross-system design decisions;
- security, authentication, authorization, cryptography, or secrets;
- destructive operations and broad data migrations;
- public API/ABI compatibility decisions;
- build/release/deployment/publishing actions;
- ambiguous changes with a large blast radius;
- final review, integration, and user-facing completion claims.

## Cost rule

Delegation is useful only when expected worker savings exceed orchestration and review overhead. Do not delegate tiny edits, trivial lookups, or work Codex already has fully in context.

## Write rule

For implementation, the external worker may edit files and run bounded development commands only inside the isolated worktree created by `cheap_agent.py`. Codex reviews the resulting diff and tests before calling `approve ... --verdict accept`, and `apply` refuses unapproved runs.
