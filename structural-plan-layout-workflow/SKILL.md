---
name: structural-plan-layout-workflow
description: Use when working on AutoCAD structural floor plan layout generation in this project, especially when the task involves the end-to-end workflow across axes, columns, main beams, cantilever beams, edge beams, wall centerlines, secondary beams, drawing, numbering, cleanup, or verification.
---

# Structural Plan Layout Workflow

## Overview

This skill is the project-level workflow for generating and validating the structural floor layout in `E:\2026\20260313_02上海院项目`.

Use it when the task is part of the full plane-layout pipeline rather than a single isolated utility edit. The skill does not replace the existing modules. It tells you what order to use them in, what must be verified at each stage, and what output is considered complete.

## When to Use

Use this skill when the user is asking to:

- 重新生成整层结构平面
- 梳理平面布置流程
- 从轴网、柱、建筑图元逐步生成各类梁
- 校核主梁、悬挑梁、封边梁、隔墙中线、次梁
- 清理并重画某一类构件
- 形成“规则 + 工具 + 调用顺序”的统一工作流

Do not use this skill for isolated edits that only touch one unrelated utility or one non-layout file.

## Core Principle

Always follow the same top-down dependency order:

1. 轴网与结构边界
2. 柱与主梁关系
3. 主梁与主梁校核补梁
4. 悬挑梁
5. 封边梁
6. 隔墙中线
7. 次梁
8. 出图、编号、截面标注、验证

If a later component is wrong, check its direct upstream dependency first instead of adding local patches.

## Required Workflow

### Step 1: Extract axes, columns, and base geometry

Use:

- [tools/draw_axes_and_columns.py](/E:/2026/20260313_02上海院项目/tools/draw_axes_and_columns.py)

Primary extraction entry:

- `extract_layout_geometry(doc)`

Expected outputs include:

- `axes`
- `columns`
- `look_lines`
- `opening_regions`
- `stair_regions`
- wall and door/window raw geometry

Current roof-specific extraction rule:

- for `7F`, use `建-看线3` to determine the roof plan scope
- for `7F`, do not treat `建-看线3` as an opening source
- for `7F`, merge `楼梯间轮廓线` into `opening_regions` so the whole stair void is blocked during roof layout

At this step, treat the axis system as the structural reference frame and build the structural boundary from the axis network before generating dependent members.

### Step 2: Build main beams and column-main-beam relationships

Use:

- [main_beam_layout.py](/E:/2026/20260313_02上海院项目/main_beam_layout.py)

Primary functions:

- `build_main_beams_from_axes(columns, axes)`
- `build_axis_validation_repair_beams(columns, axes, existing_beams, look_lines, opening_regions)`
- `attach_hosting_axes(columns, axes)`

Main beams and validation beams must be established before any cantilever, edge, or secondary-beam logic runs.

Current roof-specific primary-beam rule:

- if roof columns changed after lower-floor inheritance, rebuild roof `main_beams`, `validation_beams`, `cantilever_beams`, and `edge_beams`
- do not keep a stale roof beam result generated before the final roof column set was established

### Step 3: Build cantilever beams

Use:

- [cantilever_layout.py](/E:/2026/20260313_02上海院项目/cantilever_layout.py)

Primary function:

- `build_cantilever_beams(columns, existing_main_beams, look_lines, boundary_polygon, opening_regions=None, existing_cantilevers=None)`

Do not generate edge beams or secondary beams before cantilever beams are stable, because later stages depend on cantilever endpoints and the updated beam network.

### Step 4: Build edge beams

Use:

- [edge_beam_layout.py](/E:/2026/20260313_02上海院项目/edge_beam_layout.py)

Primary function:

- `build_edge_beams(look_lines, boundary_polygon, main_beams, cantilever_beams, existing_edge_beams, stair_regions=None, opening_regions=None)`

If edge-beam behavior is wrong, validate geometry and overlap logic before changing downstream slab or secondary-beam rules.

### Step 5: Extract walls and build wall centerlines

Use:

- [wall_centerline.py](/E:/2026/20260313_02上海院项目/wall_centerline.py)

Primary functions:

- `extract_wall_geometries(layout_geometry)`
- `build_wall_centerlines(walls, openings)`

Current project rule:

- wall centerlines are generated before secondary beams
- secondary-beam generation must reuse the finished wall centerlines and must not reprocess wall outlines again

### Step 6: Build secondary beams

Use:

- [secondary_beam_layout.py](/E:/2026/20260313_02上海院项目/secondary_beam_layout.py)

Primary function:

- `build_secondary_beams(slabs, wall_centerlines, existing_beams, stair_regions=None, opening_regions=None)`

Current stable workflow:

- build slabs from the current beam network
- for root slabs, only stair boundaries can pre-split the root slab; opening boundaries must not split the root slab
- before ordinary slab-direction checks, allow the forbidden-trimmed wall-direction fallback for local stair/opening-controlled wall candidates
- then evaluate ordinary wall-based beams in this order: short-span wall beam first, long-span wall beam only when the slab still contains walls but the short-span pass generated none
- add one wall-based beam and rebuild topology
- recurse only into child slabs that truly lie within the current parent slab
- after a wall-based beam splits the slab, if a child slab has no remaining wall-beam candidate, does not intersect stair/opening forbidden regions, and both spans are greater than `6000mm`, add cross beams in that child slab
- if a slab still has valid wall candidates, do not add cross beams yet

Respect the current project rules already implemented in the module:

- 次梁轴线必须与隔墙中线重合
- 两端必须搭接到已有梁
- 不与楼梯区、洞口区相交
- 与主梁近平行且小于 `1000mm` 的候选跳过
- 同一墙可在多个子板中继续生成
- `SLAB-017` 类场景下，局部禁区裁剪后的墙向候选优先于宽泛兜底候选
- `SLAB-023` 类场景下，先生成墙下次梁，再对无剩余隔墙且两向大于 `6000mm` 的子楼板补十字梁

Current stable roof-floor secondary-beam rule:

- roof primary beams are generated from the roof floor itself
- roof secondary beams are handled separately after the final roof primary slabs are known
- for each final roof slab, directly compare the aligned lower-floor partition walls and secondary beams against that roof slab region
- if the aligned lower floor has secondary beams in that roof slab region, copy the full lower-floor secondary-beam set for that roof slab
- if the aligned lower floor has no secondary beams in that roof slab region, use roof cross-beam fallback for that slab only
- do not place roof secondary beams inside roof opening regions
- do not place roof secondary beams outside the final roof look-line range
- when deciding whether a lower-floor secondary beam belongs to a roof slab, accept either full-segment containment or midpoint containment

### Step 6A: Assign beam section sizes before drawing

Before any beam is ready for drawing, numbering, or export, its section must be assigned from span-based rules.

Use these requirements:

- every generated beam must carry a `section` payload before drawing
- the section must be determined from beam span using the project span-to-section rule for that beam type
- the section payload should include at least `width`, `depth`, and `label`
- if a beam has no section, the workflow is not complete yet

For secondary beams specifically:

- after `build_secondary_beams(...)` returns, assign section sizes based on each secondary beam's final span
- do not skip section assignment just because the geometry is already correct
- the drawing stage must consume the assigned `section["label"]`

### Step 6B: Draw and mark beam size labels on the drawing

When drawing beams, always write both the beam id and the beam section label to the drawing.

Use:

- [tools/draw_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_secondary_beams.py)
- [tools/draw_main_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_main_beams.py)

Drawing requirements:

- beam line goes to the correct beam line layer
- beam id goes to the correct id layer
- beam section label goes to `beam_name_auto`
- if a regenerated beam set has ids but no size labels, treat that as incomplete output and fix the section-assignment step first

### Step 7: Export to YDB

Use:

- [tools/export_plan_to_ydb.py](/E:/2026/20260313_02上海院项目/tools/export_plan_to_ydb.py)

Export requirements:

- prefer exporting with the current generated structural result rather than re-reading arbitrary manual graphics
- before exporting slabs, explicitly break all beam lines at every valid beam-beam intersection across the full final beam network
- regenerate slab regions only from that broken beam-segment network; do not infer slabs directly from the unsplit original beam list
- beam sections written to YDB must come from the span-based `section` already assigned in the layout workflow
- build slab regions from the final broken beam network before export
- every exported slab must carry a thickness determined from slab span, using the project's span-to-thickness rule
- use the slab short span as the primary thickness control value
- if `建-看线-楼板开洞` forms an opening region whose covered area reaches at least `90%` of a slab region, export that slab region as a room hole by setting `tblSlab.RoomIsHole = 1`
- when a slab region is exported as a room hole, keep its geometry in `tblSlab` so the opening room is preserved in YDB
- YDB `tblBeamSeg.Rotation` is not the beam's plan-direction angle
- this rotation represents rotation around the beam axis
- unless the user explicitly asks for a nonzero torsional/section rotation, export every beam with `Rotation = 0.0`
- do not derive YDB beam rotation from `start/end` plan geometry

For detailed current rules, read:

- [2026-03-18-secondary-beam-current-rules.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-18-secondary-beam-current-rules.md)

## Numbering Rules

Always keep generated members numbered through the module-provided numbering helpers instead of inventing ad hoc labels.

Use:

- [main_beam_layout.py](/E:/2026/20260313_02上海院项目/main_beam_layout.py) -> `beam_number_label`
- [cantilever_layout.py](/E:/2026/20260313_02上海院项目/cantilever_layout.py) -> `beam_number_label`
- [edge_beam_layout.py](/E:/2026/20260313_02上海院项目/edge_beam_layout.py) -> `beam_number_label`
- [secondary_beam_layout.py](/E:/2026/20260313_02上海院项目/secondary_beam_layout.py) -> `beam_number_label`

For walls and slabs, use the existing debug/inspection numbering workflow instead of inventing a second numbering system:

- [tools/draw_slab_wall_debug.py](/E:/2026/20260313_02上海院项目/tools/draw_slab_wall_debug.py)

## Execution Entrypoints

### Full layout drawing

Use:

- [tools/draw_main_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_main_beams.py)

### Secondary-only redraw

Use:

- [tools/draw_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_secondary_beams.py)

Use this when the user only wants to clear and redraw secondary beams without touching the rest of the beam system.

### Secondary-only cleanup

Use:

- [tools/clear_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/clear_secondary_beams.py)

### Secondary verification

Use:

- [tools/validate_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/validate_secondary_beams.py)

## Verification Order

Before claiming the layout is correct, verify in this order:

1. Run focused tests for the affected module.
2. Run the relevant draw or inspect tool.
3. Check counts and source distribution.
4. Check geometric constraints.
5. Confirm that ids and section-size labels are both present on the drawing.
6. Only then report the result.

For secondary beams, the default verification command set is:

1. `python tests\test_secondary_beam_layout.py`
2. `python tools\draw_secondary_beams.py` or `python tools\clear_secondary_beams.py`
3. `python tools\validate_secondary_beams.py`

## Tool Directory

Read the tool map before extending or replacing the workflow:

- [references/tool-map.md](/E:/2026/20260313_02上海院项目/.agents/skills/structural-plan-layout-workflow/references/tool-map.md)

## Common Mistakes

- Generating secondary beams before wall centerlines are finalized.
- Using global candidate priority across all slabs instead of root-slab-local recursion.
- Reprocessing wall outlines during secondary-beam generation.
- Letting opening boundaries split root slabs before secondary-beam decisions.
- Adding cross beams to child slabs that still contain wall candidates.
- Adding cross beams to child slabs that still intersect stair/opening forbidden regions.
- Treating geometry generation as complete before assigning span-based beam sections.
- Drawing beam ids without also drawing beam section labels on `beam_name_auto`.
- Redrawing all beam types when the user only asked to redraw one type.
- Reporting a count or a “fixed” result without running the verification tool.
- Adding new debug scripts when an existing inspect tool already covers the same step.

## Output Expectation

When using this skill, always produce:

- the exact workflow stage being executed
- the tool or module used
- whether numbering is preserved/generated
- whether section-size labels were generated
- the verification result

If the task is documentation-oriented, update or create a plan/rule document under:

- [docs/plans](/E:/2026/20260313_02上海院项目/docs/plans)

## Layer Confirmation Before Execution

Before running this workflow, always confirm the drawing-layer mapping with the user first.

The current default input layers are:

- axes: `通-轴网-轴线`
- columns: `建-结构-钢砼`
- architectural look lines: `建-看线-平剖面`, `建-看线1`
- slab openings: `建-看线-楼板开洞`
- stairs: `楼梯间轮廓线`
- walls: `建-结构-气体`, `建-结构-砌体`
- doors/windows: `建-饰材-平面门窗`

The current auto-generated output layers are:

- `project_boundary_auto`
- `grid_axis_auto`
- `grid_axis_id_auto`
- `column_outline_auto`, `column_mark_auto`, `column_id_auto`
- `main_beam_line_auto`, `main_beam_id_auto`
- `main_beam_validation_auto`, `main_beam_validation_id_auto`, `beam_validation_name_auto`
- `cantilever_beam_line_auto`, `cantilever_beam_id_auto`
- `edge_beam_line_auto`, `edge_beam_id_auto`
- `secondary_beam_line_auto`, `secondary_beam_id_auto`
- `beam_name_auto`
- `slab_outline_auto`, `slab_id_auto`
- `wall_centerline_auto`, `wall_id_auto`

When starting the workflow, ask the user to confirm the input-object layers one object type at a time, or ask them to provide all mappings in one batch.

Minimum required confirmations:

1. axis layer
2. column layer
3. look-line layers
4. opening layer
5. stair layer
6. wall layers

Recommended additional confirmation:

1. door/window layer

If the user does not provide overrides, explicitly state that you are using the current default layer mapping.

Use this template document when collecting the mapping:

- [docs/plans/2026-03-23-structural-plan-layer-template.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-23-structural-plan-layer-template.md)
