# Conventions measured from 新块.dwg

## Evidence and scope

Learned on 2026-09-07 from the live drawing
`E:/2026/20260907_图纸翻译/新块.dwg`, AutoCAD `24.3s (LMS Tech)`.
The user-selected example contains 203 objects. Insert `916` contains the eight
English MTEXT objects in block `A$C9c9f536b`. Their definition handles are `91B`–`922`.
The English child objects are not individually preselected: selection is inherited
from the containing insert. A TEXT-only or top-level-only scan would miss all eight.

The full database scan found 1,781 entities: 114 dimensions, 62 TEXT, 122 MTEXT,
251 block references, one ATTDEF and geometric entities. The 122 MTEXT include
dimension display text in anonymous blocks; there are only eight English exemplars.
There are two layouts (408 model-space entities and an empty paper-space layout),
125 non-layout definitions, 799 resolved occurrences and 35 Chinese display fields.
Eleven Chinese occurrences are selected; eight have existing English and three do
not. Full occurrence disposition before the trial was eight existing translations
and 27 without a confirmed counterpart.

The clean scan reported zero extraction errors and zero planar-flattening gaps.
Preselection was retained; DBMOD remained 17. The source already had unsaved changes
before inspection. The learning scan did not mutate it. A later copy-only trial added
all 27 missing translations, skipped eight confirmed counterparts, retained every
Chinese source, and found no changes to pre-existing object properties. AutoCAD-native
WMF exports were visually reviewed; long notes and span labels were refined on the copy.
The original disk SHA-256 remained unchanged.

## Exact English formatting

| Property | Observed value | Consequence for later work |
|---|---|---|
| Entity | AcDbMText, all eight | Prefer English MTEXT for wrapping flexibility. |
| Style | TSSD_Rein | Inspect actual style and font availability in each target drawing. |
| Font files | Tssdeng.shx + Tssdchn.shx bigfont | Preserve the observed lettering where these fonts exist; report substitution. |
| Style width factor | 0.7 | This is a style property; MTEXT has no TEXT ScaleFactor in this sample. |
| Height | 350 drawing units | Consistent within this detail; do not impose 350 on drawings with different scales. |
| Color | Explicit ACI 6, RGB 255/0/255 | Magenta is explicit, not inherited from the insert's orange layer. |
| Child layer | 0 | Inside this block it inherits the insertion layer. |
| Insert layer | S-BEAM_CON, layer ACI 40 | Effective English layer is S-BEAM_CON, while explicit color remains 6. |
| EN layer | Exists, ACI 6, on/unlocked/plottable | Suitable default for new standalone English; not the actual exemplar child layer. |
| Rotation/normal | 0 radians, +Z | All English remains horizontal; one paired Chinese label is rotated about 5°. |
| Attachment | 1, top-left | English anchor is box top-left, unlike Chinese TEXT baseline anchors. |
| Direction | 1, left-to-right | Keep English left-to-right. |
| Line spacing | Factor 1.0, style 1 | Preserve unless wrapping calls for a reviewed adjustment. |
| BackgroundFill | False | Do not conceal geometry with a mask as a collision “fix”. |
| Width | 9267.723830161663 for every exemplar | Incidental wide box; do not blindly reuse. It overstates short-label occupancy. |
| Insert transform | Unit scale, 0 rotation, origin (0,0,0) | English model XY = child XY + (93140.72993122804,-294739.44677969546). |

Do not change global `TSSD_Rein` properties to tune one translation: that can change
existing reinforcement annotations. Reuse the style as-is, or use an explicitly
named derived style only when the task calls for a font/style change.

## Chinese source formatting

Most paired Chinese is TEXT with style `###HGV`, SHX fonts `###hgv.shx` and
`##hgv.shx`, width factor 0.75, layer `TEXT`, ACI 256 (ByLayer) resolving to 7.
Paired heights vary: 450, 600, 675 and 900. The title `WL与钢梁搭接详图` uses
explicit ACI 7. Dimension `8D5` uses dimension style `TSSD_10_100`, text style
`TSSD_Dimension`, text height 300, layer `DIM`, explicit dimension TextColor 7.
Entity ByLayer color on DIM would be green; the actual dimension text color is 7.
Read text-specific color overrides as well as entity and layer color.

## Observed translation pairs and source-relative offsets

Offsets below use source anchor -> English top-left anchor in the Chinese text's
local XY frame. `h` is the source text height. Positive `u` follows its baseline;
positive `v` is above it. They are measurements, not universal gap rules. TEXT and
MTEXT anchors differ; use rendered bounds for clearance.

| Source handle / Chinese | English occurrence | u/h | v/h | English h / Chinese h |
|---|---|---:|---:|---:|
| 8E5 / WL与钢梁搭接详图 | 916/91B — Detailed Drawing of WL and Steel Beam Lapping | 0.751 | -0.581 | 0.389 |
| 75A / 中间跨 | 916/91C — Middle Span | 0.057 | -1.094 | 0.519 |
| 801 / 钢梁 | 916/91D — Steel Beam | -2.393 | -0.262 | 0.778 |
| 6E4 / 檩托详图 | 916/91E — Purlin Bracket | 0.306 | -0.570 | 0.583 |
| 75B / 边跨 | 916/91F — Side Span | 0.594 | -0.839 | 0.519 |
| 8C5 / 钢梁 | 916/920 — Steel Beam | 0.805 | -0.302 | 0.778 |
| 8D5 / 外挑尺寸 | 916/921 — Overhang Dimension | -0.179 | 3.040 | 1.167 |
| 824 / 钢梁 | 916/922 — Steel Beam | 1.455 | 1.399 | 0.583 |

The source of `824` is rotated 5°; English rotation delta is -5°. The dimension
translation is above its Chinese source, unlike most titles. The steel-beam callouts
use different sides/offsets. A single fixed “put it below” rule would not reproduce
these examples. Prefer a nearby clear position with the learned visual hierarchy.

## Wording, uncertainties and what not to infer

Preserve the six observed phrases exactly when applicable. `Purlin Bracket` labels
the `檩托详图` title; it is an abbreviated translation and omits “Detail”. Record
this quality difference but skip adding another translation to that title. The two
separate `檩托` callouts at `769` and `832` are still untranslated: the remote title
translation does not cover them. `Purlin Bracket` can be reused for those terms in a
future requested translation, with a new occurrence-specific placement check.

`详平面` at `8E2` has no English counterpart. “See Plan” is a possible future
translation, not an observed phrase in this drawing. Likewise “Purlin Bracket Detail”
may be a fuller title wording, but should not replace existing wording without an
editing request. The `250mm` and `180/200/220mm` applicability notes are outside the
selected set and still must appear in whole-drawing inventory.

No reviewed bilingual TABLE, MLEADER, MTEXT-with-inline-formatting, xref, rotated
English, or attribute example exists in this sample. Their extraction/writing rules
are engineering workflow requirements, not learned formatting facts. Native glyphs
and trial placements were reviewed through AutoCAD WMF exports, but that is not plot
preview proof for every layout, viewport, lineweight, or font environment.
