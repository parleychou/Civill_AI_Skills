# Existing-English counterpart confidence

## Evidence record

Generate candidates from every visible English-bearing occurrence in the same layout.
For each pair record stable IDs/raw strings, visibility, layout/container/ancestry,
projected XY distance and row overlap, shared table/leader/dimension/detail relationship,
normalized word similarity, protected tokens/directions, and competing candidates.

The first pass occurs before new translation. It may use a previously reviewed project
glossary or observed bilingual term as `search_english`; otherwise it emits nearby
structurally associated English as `uncertain` for semantic review. It must not invent
a final translation merely to justify a skip.

## Classification

`confirmed` requires semantic/token agreement plus spatial or structural association.
The production thresholds are candidate-ranking signals:

- Row-band candidate: horizontal gap 0–3000 and word overlap at least 0.5.
- Any-direction candidate: distance at most 1600 and overlap at least 0.8.

They do not directly mutate decisions. A reviewer or stronger semantic check confirms
that the English describes this exact source occurrence.

Use `uncertain` for multiple plausible candidates, abbreviations, hidden/frozen English,
incomplete clauses, weak structural association, or X/Y and similar directional
conflicts. Use `rejected` for another insert occurrence, another row, distant titles,
identifiers such as `WL`/`M12`, or protected-token mismatch.

## Skip discipline

Only a confirmed candidate becomes `already_translated`. Record its occurrence ID and
evidence, then add no translation and no placement. Existing imperfect wording remains
untouched unless editing is requested. One English label cannot cover repeated Chinese
occurrences without explicit one-to-many evidence. A false skip loses engineering
information; an uncertain candidate can be inspected without changing the drawing.
