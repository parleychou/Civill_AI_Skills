# Routing policy

Agent Foreman separates **who leads** from **who works**.

## Personas

| Need | Preferred agy-staff persona |
|---|---|
| General bounded work | `staffer` |
| Repository / technical survey | `researcher` |
| Independent critique, code/plan review | `reviewer` |
| Scoped code modification | `implementer` |
| Small tool-free question | `ask` |

The current lead can override the mapping.

## Delegate when

Delegation is most useful when the assignment is substantial and coherent enough to justify a handoff:

- repository exploration across many files;
- code-path and dependency mapping;
- first-pass debugging;
- independent review;
- test generation;
- repetitive or mechanical implementation;
- a bounded feature/fix with clear acceptance criteria;
- documentation or migration analysis;
- a second-model opinion.

## Keep with the lead when

Keep work local when handoff/review costs more than doing it directly, or when the lead already has all needed context.

Consequential decisions may still be researched or challenged by workers, but the current lead owns acceptance and integration.

## Parallelism

Parallelize assignments that share little mutable state, such as separate research angles or black-box reviews.

Editing workers require separate worktrees. Agent Foreman creates a separate isolated worktree per run, so multiple implementation runs may proceed independently. The lead must reconcile cross-worker assumptions before accepting patches.

## Cost rule

Use a cheaper worker only when expected savings exceed delegation, collection, and review overhead. Cost is one routing signal, not the only signal; independent-model coverage can be valuable even when raw token cost is similar.
