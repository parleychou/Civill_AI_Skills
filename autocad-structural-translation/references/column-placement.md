# Column placement for tables and aligned notes

## When to use

Use column mode for at least three vertically aligned sources in the same layout and
detail/table container with compatible height, spacing, and row order. Typical cases
are schedule rows and multi-line notes where independent English cannot fit beside
every Chinese line. Similar X coordinates alone are insufficient; require a shared
table, note paragraph, border, or aligned sequence.

## Rehearsal

1. Sort rows by source Y and retain every source key.
2. Estimate each English row conservatively; estimates only test feasibility.
3. Test right- and left-side columns outside source/table bounds.
4. Preserve row order and visible source association.
5. Check all translated boxes, inter-row spacing, geometry/text, maximum distance,
   and table/detail boundaries.
6. Return all placements only if the complete group passes. Otherwise return one
   blocked group with diagnostics.

## Live measurement and atomic write

Measure each row with the target AutoCAD style. Recalculate the group from actual glyph
extents. If wrapping changes height, recheck the complete group. If any row fails,
delete only that run's new group handles and leave sources unchanged.

Do not force text into narrow cells, overwrite formulas/content, mask borders, or make
a detached list with ambiguous row association. If no clear column fits, preserve the
translations and source coordinates for manual placement.
