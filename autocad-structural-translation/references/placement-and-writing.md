# Placement, writing and verification

## First decision: skip or place

Only `needs_translation` is eligible for new English. An `already_translated` item
has no proposed English or placement. An uncertain counterpart needs inspection;
uncertainty is not authorization to add another label. Recheck immediately before
writing, and update the in-memory text index after each successful insertion. This
avoids duplicates within the same run as well as on repeated runs.

## Identify the correct local plane and scale

Use the visible layout/detail coordinate system. A source inside a nested block needs
its full occurrence transform. Do not apply an insert transform twice to attribute
references. For non-+Z normals, mirrored/nonuniform blocks or viewports, explicitly
derive OCS/WCS/view transforms and verify a known point before placing anything.
The bundled XY flattener is not sufficient for those cases.

The exemplar has INSUNITS=4 (millimetres), CANNOSCALE=1:1 and DIMSCALE=1, but its
detail geometry is drawn at enlarged size. The printed `1:10` text does not establish
the current geometric scale. Measure representative Chinese text and compare the
target detail with the reference. Use 350 English height only for comparable scale.
For other drawings choose height from local annotation conventions and plotted
readability. Record the conversion; do not multiply by both insertion scale and
annotation scale twice.

Use source baseline direction `u=(cos θ,sin θ)` and its left normal
`v=(-sin θ,cos θ)`. For displacement Δ from Chinese anchor to English anchor,
`along/h = dot(Δ,u)/h` and `above/h = dot(Δ,v)/h`. This lets offsets follow rotated
Chinese without requiring English to share its rotation. The learned English is
horizontal, including the 5° source case. A vertical/different-rotation target needs
a local readability decision, since that style was not demonstrated in the sample.

TEXT insertion is usually a baseline point; non-left-justified TEXT uses alignment
points. MTEXT insertion depends on AttachmentPoint. Dimension TextPosition describes
the label location, not the extent of the whole dimension. Never derive a visible
gap by subtracting anchors alone.

## Measure text and identify obstacles

Record two types of boxes: the MTEXT container box and the occupied/rendered text
extent, when available. Autodesk GetBoundingBox yields a WCS-axis-aligned box, not an
oriented glyph polygon. The sample's short MTEXT labels each report width 9267.72,
so treating every full box as ink creates false collisions. Conversely, estimating
width from character count alone may underestimate SHX glyphs or inline formatting.

For new text, set its final style, height, rotation, attachment and wrapping width,
then call Update and regenerate before measuring. Where the host exposes reliable
actual-width/height or native plotted glyph bounds, compare them to the box. Otherwise
retain a conservative box and inspect the native appearance. A short tight box is
safer than copying 9267.72 to every label. Do not declare clearance from an unverified
character-count estimate or by making background masks conceal existing elements.

Obstacles include the source Chinese, every other Chinese/English label, dimensions
(labels, dimension lines, extension lines, arrowheads), leader segments, block symbols,
member outlines, reinforcement, hatches, borders and table cells. Ignore nonplotting
construction geometry only when the relevant layout/plot state justifies it. Layer
visibility, clipping and block inheritance must be considered. Existing English is
an obstacle even when it was outside the user's selection.

Compare projected XY/viewport geometry regardless of Z separation. Include new English
already placed earlier in this run. To avoid false collisions from an entire large
block or dimension bounding box, first use the box for a broad-phase search, then
inspect its child geometry/label components. Anonymous dimension display blocks can
provide read-only geometry evidence; never edit them.

Detailed checks:

1. Expand text footprints by a recorded clearance (initial unlearned default:
   0.15–0.25 of English height). Include lineweight at plotted scale if material.
2. Use box overlap for broad-phase rejection. Treat touching as conflict.
3. Check line/leader segment intersections with the expanded text box, including
   crossing segments whose endpoints lie outside the box.
4. Use arc/circle and polyline bulge geometry for curved segments. A nonzero bulge
   cannot be approximated as its straight chord without a bounded error margin.
5. Treat dense hatch or opaque/image regions as occupied unless rendering proves
   blank space. Do not place on dimension values, arrows or structural member lines.
6. For unknown bounds or unreadable geometry, mark the candidate unverified. Numerical
   silence is not a pass. Resolve visually or report the placement as blocked.

`translation_rules.rectangle_overlap` and `segment_hits_box` are tested primitives,
not a complete collision engine. They do not implement arcs, hatch topology, text
glyphs, font substitution, viewport clipping or projected 3D geometry. Use them only
for their documented inputs; extend the adapter or fail closed for other geometry.

## Candidate search and selection

Start with the corresponding learned role (title, span label, beam callout, dimension
label), then search neighboring clear positions. Most titles sit below Chinese,
while the dimension and rotated-beam examples sit above. Try lower/upper sides with
left/center alignment to the source footprint, then modest lateral shifts. A useful
initial search is ±0.5h, ±1h and ±2h along the source baseline and adjacent normal
offsets; these are new search defaults, not measured universal standards.

For each candidate, store anchor/box, height, width, rotation, obstacle handles,
minimum clearance and rejection reasons. Reject overlapping, unreadable, wrong-detail
or ambiguous-association placements. Among feasible candidates minimize visible
edge-to-edge source distance, then prefer the learned side/alignment and less wrapping.
Do not accept a remote empty area merely because it is easy to fit there. Keep the
English inside the same detail region where possible. If a larger move would make
association unclear, record `blocked` or propose a clear callout for review.

If nothing fits: wrap at phrase boundaries and enlarge the box into verified blank
space; try the opposite side; then a modest lateral shift. Do not change engineering
geometry, remove Chinese, reduce technical content or make text unreadably small.
Do not impose an arbitrary maximum distance as evidence of a valid translation pair.

## Concrete pyautocad write pattern (future translation tasks)

The following function is an implementation example, not a complete translator. It
accepts only a prepared, validated placement for ordinary planar text. The caller
must have completed source-identity, existing-English, layout, collision and scope
checks. It uses only ActiveX objects obtained through pyautocad. It does not run Lisp.

```python
from pyautocad import APoint

def add_reviewed_mtext(acad, owner_space, plan, new_object_log):
    # plan: english, anchor=[x,y,z], width, height, rotation radians,
    # style, layer, color_aci, source_key; values already checked by caller.
    doc = acad.doc
    if not plan['english'] or plan['width'] <= 0 or plan['height'] <= 0:
        raise ValueError('Nonempty text and positive dimensions required')
    doc.TextStyles.Item(plan['style'])  # Fail if style missing; never silently substitute.
    doc.Layers.Item(plan['layer'])
    obj = None
    doc.StartUndoMark()
    try:
        obj = acad.best_interface(owner_space.AddMText(
            APoint(*plan['anchor']), plan['width'], plan['english']))
        new_object_log.append({'source_key': plan['source_key'], 'handle': obj.Handle})
        # Persist the new handle immediately in the run's JSON log here.
        obj.StyleName = plan['style']
        obj.Height = plan['height']
        obj.Width = plan['width']
        obj.Layer = plan['layer']
        obj.Color = plan['color_aci']
        obj.AttachmentPoint = 1  # top-left
        obj.Rotation = plan['rotation']
        obj.InsertionPoint = APoint(*plan['anchor'])  # apply after attachment/rotation
        obj.LineSpacingFactor = 1.0
        obj.LineSpacingStyle = 1
        obj.BackgroundFill = False
        obj.Update()
        doc.Regen(1)  # all viewports; ACAD.acAllViewports if available
        box = obj.GetBoundingBox()
        return obj, box  # caller must check final box and native appearance
    except Exception:
        if obj is not None:
            obj.Delete()  # only the newly created object, never its source
        raise
    finally:
        doc.EndUndoMark()
```

Select `owner_space` by the source's layout (`layout.Block` from the selected
document). `acad.model` is appropriate only for model space. For a block-contained
source, use a layout overlay at its resolved occurrence position by default. It is
not safe to edit the shared block definition merely to handle one occurrence.
For newly added standalone English, layer EN with explicit ACI 6 is the documented
default where it exists. If it is missing, creating it is a normal scoped translation
step, but verify the target project's layer policy and record the choice.

Save a recovery copy of the current in-memory state before mutation, including any
unsaved user changes. A filesystem copy alone captures only the last disk save. Use
a unique output path and verified `doc.SaveAs` semantics when working on a translated
copy; note that SaveAs changes the active document identity. Bind all later checks
and manifests to that output. Never overwrite an existing output without deliberate
authorization. Record each created handle to disk as soon as it exists, and do not
retry a timed-out create blindly: inspect the handle/log or rescan first.

Recheck live source text before each write. On an exception, preserve checkpoints;
delete only a confirmed newly created object from that failed insertion, log deletion
and revalidate state. StartUndoMark groups actions but does not automatically roll
them back. Do not use a global Undo that may remove user edits performed meanwhile.

## Completion verification

The V2 helpers separate responsibilities: `scope_manifest.py` freezes selected or
drawing scope; `counterpart_candidates.py` emits review evidence;
`placement_planner.py` provides a duplicate-safe spatial index and atomic column
rehearsal; `apply_translations.py` defaults to a dry run and journals copy-only
pyautocad writes; `verify_translation.py` reconciles saved results. These are
guardrails, not substitutes for semantic and visual engineering review.

For every new object verify English content, layer/effective color, style/font,
height/width, rotation, attachment, visibility, layout, overlap and source proximity.
Save and reopen the translated copy when practical.

Document-level calls (`Documents.Open`, `Activate`, `Save`, `SaveAs`, `Close`) are the
most likely place to meet a busy AutoCAD. Observed here: `Close` issued right after
`Open` raised `COMError -2147418111` (`RPC_E_CALL_REJECTED`, “被呼叫方拒绝接收呼叫”)
while the drawing was still loading. **The rejected call had in fact executed** — the
document was closed and the file on disk was untouched. So a rejection is not evidence
of a failed operation, and it is not a reason to abandon the run. Re-read actual state
(`Documents.Count`, `doc.FullName`, `doc.Saved`, file size/mtime) and only then decide.
Never respond by re-saving, re-opening over the result, or restoring a backup before
that check. Wrap each document-level call in the same bounded retry the read helper
uses (`inspect_drawing.py` `Scanner.call`: retry only on `-2147418111` and
`-2147417846`, short sleep, limited attempts), and allow a full second between opening
a drawing and the next call. Inspect model space and each
layout and plot preview; clipping, missing SHX fonts and viewport scale are not
detectable from string extraction alone. If native visual checks cannot be performed,
state that limitation and do not claim fully verified collision-free output.

Compare pre-existing handles and key properties against the baseline: text/field raw
values, geometry, dimensions' Measurement/TextOverride, block transforms, styles and
layers. New layer/object additions may be expected; unexplained original changes are
failures. Check user changes separately instead of undoing them.

Rescan and produce an occurrence-level report. All retained Chinese must have a
disposition. A repeated dry-run after successful translation must select zero new
objects for addition; do not translate an English object just because it contains a
member mark that also appears in Chinese. Keep terminology-quality issues separate
from the existing-translation skip decision.
