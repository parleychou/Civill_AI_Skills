# Large-drawing workflow

## Scale safely

Keep expensive work offline: inventory, resolve occurrences, freeze scope, classify
roles, build a reviewed glossary, generate counterpart candidates, rehearse placement,
review gaps, dry-run, then write serially with a journal. Save/reopen/rescan and require
zero repeat additions.

Use a spatial grid instead of all-pairs collision checks. Deduplicate obstacles returned
from multiple cells. A 4000-unit grid worked for the measured production drawing but is
configuration, not a universal constant.

## Avoid drawing-specific rules

Do not reuse coordinate constants. Detect candidate title blocks, legends, samples,
tables, and note regions from block/container names, borders, layers, styles, height
clusters, repetition, and nearby content. Save reviewed inclusions/exclusions and their
evidence in the run manifest. Vocabulary lists are clues, not portable truth.

Treat ancestor insert boxes for unbounded proxy children as conservative,
reduced-confidence barriers. They may falsely block space; never interpret them as
proof that no geometric space exists.

Offline width estimates use a conservative glyph factor (default 0.50) only to screen
candidates. Live AutoCAD measurement controls final width. Increase distance only by a
reviewed second-stage policy and stop at the engineering-detail boundary.

Resume from the output copy, never the source. Orphan cleanup requires the logged
handle, expected text, run identity, and incomplete state. If ownership is uncertain,
stop rather than delete.
