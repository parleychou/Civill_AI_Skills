# Object coverage and extraction checklist

## Inventory is broader than editable text

Scan database objects, build a graph of their containment and references, then resolve
their visible occurrences. Keep the complete definition inventory even for unused
blocks, but do not place translations for unused definitions in model space. Record
unused-definition Chinese as definition-only inventory, not a visible occurrence.

`doc.Blocks` includes layout blocks and anonymous blocks. Enumerate all of it; identify
layout blocks using `IsLayout` and `block.Layout.Name`. `acad.iter_layouts()` skips
model space by default. Use `skip_model=False` if choosing that traversal instead.
`acad.iter_objects('Text')` alone cannot satisfy this task.

| Family | Extract and preserve | How to add English later |
|---|---|---|
| TEXT | TextString, style, Height, ScaleFactor, Alignment, InsertionPoint, TextAlignmentPoint, Rotation, Normal, ObliqueAngle, Backward, UpsideDown, raw control codes | Separate MTEXT near the source; never replace the original by default. |
| MTEXT | Raw TextString, Width, Height, attachment, rotation/direction, line spacing, background mask, inline font/color/height/width changes, fields | Preserve formatting in source; create English with its own suitable box. Check bilingual clauses first. |
| Attribute reference | GetAttributes and GetConstantAttributes on every insert; TextString, TagString, Invisible, MTextAttribute, MTextAttributeContent and lock position | Overlay in that insert occurrence's layout; use a source key containing the insert path. |
| ATTDEF | Definition text, default value, PromptString, TagString, Constant/Invisible flags | Defaults/prompts/tags are metadata unless actually displayed. Do not rename tags or translate prompts in a graphical translation task. |
| All dimensions | TextOverride, TextPrefix/Suffix, alternate prefixes/suffixes, TextPosition, TextHeight/TextStyle, TextRotation, Measurement, TextColor, scale, tolerances and formatting | Separate English annotation near the displayed dimension label. Preserve measurement and `<>`/`[]` semantics; never edit generated `*D` contents. |
| LEADER | Annotation reference/handle and coordinates; recurse into linked text, tolerance or block | Translate the annotation once, avoiding duplicate extraction through both routes. Preserve leader topology. |
| MLEADER: MTEXT | ContentType, TextString, TextStyleName, TextHeight, TextWidth, TextRotation, TextLocation if exposed, attachment/landing and leader geometry | Overlay or a deliberately managed bilingual annotation; preserve leader attachment. |
| MLEADER: block | ContentBlockName, actual content block, ATTDEF identifiers and `GetBlockAttributeValue` for each applicable definition ObjectID | Resolve each instance's actual values, not only the default definition strings. |
| TABLE | Every row/column, GetText, GetCellType, formulas, merged-cell spans, cell style/height/alignment, block content, fields, multiple content items when supported | Fit bilingual content within cells or add a clearly associated translation table/overlay. Do not overwrite formulas or assume blank GetText means no content. |
| Tolerance/FCF | TextString and formatting/symbol codes; leader association | Preserve geometric tolerance symbols and values; translate only prose. |
| Ordinary/nested insert | Name, EffectiveName, origin, insertion, rotation, XYZ scale, Normal, layer/color inheritance, child entities | Traverse actual Name. Maintain every instance path and compose transforms. Do not explode. |
| Dynamic insert | Actual anonymous Name as well as EffectiveName, GetDynamicBlockProperties, visibility state, attributes and displayed geometry | Check the visible evaluated state. Do not assume the named authoring block equals the visible instance. |
| MINSERT / arrays | Rows, Columns, offsets and each instance location; associative arrays may be proxy/custom objects | Expand every visible occurrence and preserve a row/column path. The bundled flattener reports MINSERT as unsupported. |
| Xref | Path, load state, host insertion transform, host overrides, clipping, visible children; referenced DWG if authorized | Preserve reference file by default; place host overlays or work on an explicitly requested copy of the reference. Unloaded references are coverage gaps. |
| Fields | Raw `%<...>%` expressions and evaluated displayed values; nesting and formatting | Preserve expression, IDs and formatting. Translate surrounding prose; report fields whose displayed content cannot be read. |
| Proxy/custom AEC/TSSD objects | ObjectName, available text properties, bounding box and visual appearance | Report unreadable content. Use available object-enabler/ActiveX interfaces if supported; no Lisp or exploding as a fallback. |
| PDF/DGN underlay, image, OLE | Reference/embedding metadata, clipping and rendered visible content | These may have Chinese without a TextString. Explicitly inventory and arrange a permitted visual/OCR path; do not claim text-free from a failed property probe. |
| SHAPE, exploded text, linework | Shapes, font glyphs, suspicious groups of curves representing characters | Vector strokes cannot reliably be translated from TextString. Treat visible Chinese as a visual-review item. |
| Hyperlink/XData/dictionaries | Descriptions or custom metadata when in scope; inspect actual displayed field linkage | Do not translate URLs, keys, handles, regapp names or layer/style names merely because they contain Chinese. Never create dictionaries just to inspect them. |

## Attributes: avoid missing or moving them twice

The learned host returned `KeyError: 9` from comtypes for all attribute arrays. The
scanner's `prepare_comtypes()` adds missing VT_DISPATCH/VT_UNKNOWN mappings only for
that Python process. After applying it, call both attribute methods and cast each
returned object via `acad.best_interface()`. An empty tuple is a successful empty
result; an exception is not. On the learned drawing, six attribute references were
successfully read, with empty values; no Chinese attribute value was inferred.

Attribute references attached to a top-level insert already have drawing coordinates.
For a nested insert they are expressed in the containing block's coordinate system.
Transform through ancestors, not through their own insert a second time. Constant
definitions need their own coordinate interpretation checked against the actual API
return; treat uncertain results as blocked rather than assuming the reference case.

## Geometry and occurrence coordinates

For a planar +Z block, apply block-origin subtraction, scale (including negative
scale), insert rotation, translation, then all parent transforms. The helper computes
XY affine transforms. Nonuniform/mirrored transforms can shear or mirror text: computed
anchors and conservative bounds do not prove readable orientation. Use AutoCAD's
rendered result before final placement. Do not edit the shared definition unless all
instances are deliberately in scope.

Maintain two records: definition coordinates/properties and occurrence coordinates/
effective properties. A block named `*D...` is usually generated dimension display;
its Chinese text is evidence for the owner dimension, not a second independently
translatable source. Keep it in the raw inventory and avoid double-placing it.

Project collision geometry into the relevant drawing/viewport plane. Many source
objects in this exemplar have nonzero and inconsistent Z, while English is at Z=0.
They still visually overlap in plan. A 3D box separation test would miss this.

## Extraction completeness and actual helper limits

Record per-layout/block expected Count, successfully enumerated entities, attribute
counts, classes encountered, populated text fields, CJK occurrences, property errors,
bbox errors and unresolved object families. Inventory tables/fields/proxies as gaps
until their family-specific inspection is finished. No change or save is necessary
to inspect this sample.

`inspect_drawing.py` captures all sample families, attributes, leader links, scalar
dimension properties, basic tables, MTEXT, styles and layers. The table and MLeader
block adapters deliberately report richer content as gaps; they are not certified
complete for those unobserved families. Unknown classes and field expressions are
flagged. Extension dictionaries, dynamic visibility, clipped references, annotation
scales per viewport, native glyph extents and raster/OCR need explicit supplemental
work in future drawings. `analyze_inventory.py` is a planar occurrence resolver, not
a universal drawing parser. Do not erase its warnings to make a report pass.

Before claiming completeness, review blocks with no visible insert, attached
attributes separately from ATTDEF, owner links for dimensions, and all unclassified
objects. Reconcile counts and explain discrepancies. Different totals for database
entities and inserted occurrences are expected and must not be conflated.

## Verified API references

- [pyautocad API](https://pyautocad.readthedocs.io/en/latest/api.html): connection,
  iteration, best-interface conversion and point helpers.
- [GetBoundingBox](https://help.autodesk.com/cloudhelp/2024/ESP/AutoCAD-LT-ActiveX-Reference/files/GUID-A20C361C-BBF0-4EAB-8BE7-709154CEEE09.htm): output corners are WCS-axis-aligned.
- [Attribute extraction](https://help.autodesk.com/cloudhelp/2015/ENU/AutoCAD-ActiveX/files/GUID-C34E2AE8-A2D0-4781-8B5B-BC3E226E8B94.htm): attribute values are instance references.
- [MLeader block attribute values](https://help.autodesk.com/cloudhelp/2024/ENU/AutoCAD-LT-ActiveX-Reference/files/GUID-9422DC8E-FB16-46C7-B9E9-ECE703C814D2.htm).
- [Dimension properties](https://help.autodesk.com/cloudhelp/2025/ENU/AutoCAD-LT-ActiveX-Reference/files/GUID-C832CDC5-59AA-466F-B4BA-EFC133834A1E.htm): text override, text position, measurement and prefixes are distinct.
- [Polyline bulges](https://help.autodesk.com/cloudhelp/2025/ITA/AutoCAD-LT-ActiveX-Reference/files/GUID-6AC9CF99-7230-4333-859A-1CBACB57B5BA.htm): nonzero bulges represent arcs, not straight segments.

Use the installed version's type library or Autodesk documentation when extending
an adapter. Published pages may show Lisp examples; use only their ActiveX signatures
through pyautocad, never execute the Lisp examples.
