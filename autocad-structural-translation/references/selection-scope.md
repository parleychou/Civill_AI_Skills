# Selected-object scope

## Boundary rule

Capture `PickfirstSelectionSet` before any operation that can disturb it. Store the
active full path and selected top-level handles. Selected mode authorizes translation
only for:

1. A selected text-bearing object itself.
2. A visible text-bearing descendant reached through that selected insert occurrence.
3. A selected dimension's text-bearing property, not its anonymous display children.
4. Selected attribute references and selected table/MLeader content that the scanner
   can resolve to a stable occurrence/property key.

A selected block definition name or child definition handle is not global authority.
For example, selecting insert `Model/A` may authorize `Model/A/T1`; it does not
authorize `Model/B/T1`, even when A and B reference the same definition.

## Global evidence, local writes

Inventory the entire drawing read-only. This is necessary because English outside the
selection may already translate a selected source, unselected objects are obstacles,
and nearby context may determine structural meaning.

Global inspection never expands write scope. An unselected Chinese source receives no
`needs_translation`, placement, or new handle. Represent it outside the decision
universe, or as a non-actionable exclusion when a full audit table requires all rows.

## Staleness and verification

Freeze `selected_handles`, `source_keys`, source raw strings, inventory hash, and active
path. Before writing, require the live Pickfirst handle set to equal the frozen set.
Abort if it differs; do not silently recapture a new selection. Immediately before
each insertion, re-read the source property.

Final verification fails if any placement has a source key outside the frozen set,
including descendants of unselected sibling inserts. Report selected top-level objects
and in-scope Chinese occurrences as separate counts.
