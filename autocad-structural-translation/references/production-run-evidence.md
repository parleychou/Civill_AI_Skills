# Production-run evidence and limits

## Measured whole-drawing run

On 2026-09-07 the workflow was exercised on `标准构件整理.dwg`, a drawing distinct
from the small learning exemplar:

| Measure | Result |
|---|---:|
| Source database entities | 33,878 |
| Chinese display fields | 1,699 |
| Unique Chinese strings | 1,006 |
| Existing author translations skipped | 150 |
| New English MTEXT written | 524 |
| Existing pilot English retained | 8 |
| Manual-placement exceptions | 135 |
| Proxy/flattening gaps reported | 487 |

Final accounting was 524 translated, 150 existing translations, 280 table-header or
narrow-cell exclusions, 418 sample/library exclusions, 184 title-block exclusions,
eight pilot translations, and 135 manual placements: 1,699 total. The source SHA-256
remained unchanged. The output contained 532 non-empty EN-layer MTEXT objects.

## Proven lessons

Inventory/accounting scales beyond the exemplar; spatial-grid rehearsal prevents
impractical all-pairs work; copy safety, COM retry, journaling, and resume are necessary;
existing bilingual content is the main duplicate risk; measured glyph width beats
character heuristics; dense tables/notes need grouped columns or manual review.

## Limits

The run did not prove universal handling for Tianzheng/proxy/zombie text, xrefs,
dynamic blocks, MINSERT, non-planar normals, viewport transforms, or every TABLE/MLeader
field representation. Ancestor boxes may over-block. Its classification rules and
537-entry glossary were tailored to one drawing and are not reusable defaults.

The 135 exceptions demonstrate an honest automatic-placement boundary: 53 long note
lines, 29 short dense labels, 28 numbered specification items, 21 tube-schedule rows,
and four titles or brief notes.
