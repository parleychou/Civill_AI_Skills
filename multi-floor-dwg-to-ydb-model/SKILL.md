---
name: multi-floor-dwg-to-ydb-model
description: Use when building a full multi-story YDB model from multiple AutoCAD DWG floor plans in this project, especially when the task involves batch-reading floors like 2F-6F, generating structural layout per floor, aligning floors by axis network, and exporting one combined YDB model.
---

# Multi-Floor DWG To YDB Model

## Overview

This skill is the project workflow for:

- 批量读取多个楼层 DWG
- 提取每层轴网、柱、梁、楼板等结构数据
- 自动完成每层结构平面布置
- 基于轴网把各层坐标对齐到统一基准
- 导出一个完整的多层 `YDB` 总模型

Use it in `E:\2026\20260313_02上海院项目` when the user wants a building-level model rather than a single-floor plan.

## When to Use

Use this skill when the user is asking to:

- 批量处理 `2F-6F`、`2F-7F` 或更多楼层 DWG
- 自动生成整栋楼的结构平面结果
- 将多层平面合并成一个总 `YDB`
- 依据轴网对齐各层坐标
- 从当前 AutoCAD 已打开图纸批量生成结构模型

Do not use this skill for:

- 只处理一层图纸
- 只修某一类梁或某一个洞口规则
- 只导出单层 `YDB`

## Core Principle

Always split the work into three stages:

1. Per-floor structural layout
2. Cross-floor axis-based alignment
3. Unified multi-floor YDB export

Do not jump straight to total-model export before every floor has been generated and checked.

Current stable project rule:

- building-level export should rebuild each floor from source geometry, not rely on whatever auto graphics happened to remain in CAD
- AutoCAD COM may be unstable during batch runs, so every document open/read/draw/export step should use retry logic

## Cross-Floor Column Rule

Before generating the upper floor layout, compare the current floor and the immediately lower floor columns.

If a column exists on the lower floor but no matching column exists on the upper floor within the project tolerance, that lower-floor column must be inherited upward and included in the upper-floor layout.

Execution rule:

- run column comparison in floor order from low to high
- before comparison, use the adjacent floors' axis networks to map the lower-floor columns into the upper floor's local coordinate system
- if upper and lower columns are the same physical column but their actual centers differ because the section size changes, use the lower-floor aligned center as the model center
- for that matched upper-floor column, store the actual offset as column eccentricity and export it through `EccX` / `EccY`
- inherited columns participate in the upper floor beam layout, not only in export
- the inheritance is recursive, so a column inherited to `3F` may continue to be inherited to `4F` if it is still absent there
- mark inherited columns in intermediate data so they can be audited when needed
- after inheritance, renumber the upper floor column ids before drawing and export

Additional stable roof rule:

- for the top floor, the inherited lower-floor columns must be applied before regenerating the roof main-beam system
- after roof columns are inherited, rebuild roof main beams, validation beams, cantilever beams, and edge beams from the updated roof column set
- do not keep a stale pre-inheritance roof primary-beam result

## Required Inputs

Before execution, confirm or state the default layer mapping:

- axes: `通-轴网-轴线`
- columns: `建-结构-钢砼`
- architectural look lines: `建-看线-平剖面`, `建-看线1`
- slab openings: `建-看线-楼板开洞`
- stairs: `楼梯间轮廓线`
- walls: `建-结构-气体`, `建-结构-砌体`
- doors/windows: `建-饰材-平面门窗`

Special top-floor mapping rule:

- if the roof floor is `7F`, use `建-看线3` to determine the roof plan layout range
- for `7F`, `建-看线3` is a roof scope layer, not an opening layer
- for `7F`, `楼梯间轮廓线` should be treated as whole opening regions and merged into `opening_regions`

If the user does not override them, explicitly say that the default mapping is being used.

## Floor-Level Workflow

### Step 1: Open or resolve each target DWG

Use:

- [tools/run_multi_floor_layout.py](/E:/2026/20260313_02上海院项目/tools/run_multi_floor_layout.py)

Current default floor batch:

- `2F,3F,4F,5F,6F`

The script will:

- resolve an already-open document when possible
- open the DWG if needed
- retry AutoCAD COM calls when AutoCAD is busy

### Step 2: Build each floor layout

Use:

- [floor_layout_pipeline.py](/E:/2026/20260313_02上海院项目/floor_layout_pipeline.py)

This pipeline must produce for each floor:

- `axes`
- `columns`
- `main_beams`
- `validation_beams`
- `cantilever_beams`
- `edge_beams`
- `wall_centerlines`
- `secondary_beams`
- `broken_beam_segments`
- `slabs`

Important:

- upper-floor `columns` must already include any inherited lower-floor columns before main beam generation starts
- do not postpone missing-column补齐 to the YDB export stage only
- for matched columns with size-driven center offset, the layout center follows the lower floor, while the actual drawn/exported position is represented by eccentricity
- for `7F`, first determine the roof valid range from `建-看线3`, then remove columns inside roof opening regions, then rebuild the roof primary beam system
- roof openings must block both columns and beams

### Step 3: Draw validated results back to each DWG

Use:

- [tools/draw_main_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_main_beams.py)
- [tools/run_multi_floor_layout.py](/E:/2026/20260313_02上海院项目/tools/run_multi_floor_layout.py)

Drawing requirements:

- every beam must carry a `section`
- ids and section labels must both be drawn
- output must land on the project auto layers

## Alignment Rules

### Step 4: Align floors by axis network

Use:

- [floor_alignment.py](/E:/2026/20260313_02上海院项目/floor_alignment.py)

Current project rule:

- each floor keeps its own nodes and axis rows
- do not merge nodes or axis numbers across floors
- alignment is only a whole-floor coordinate transform
- use the axis network to compute a floor translation into the unified building coordinate system
- apply the same translation to axes, columns, beams, slabs, and other geometric payloads for that floor

### Step 4A: Roof-floor stable rules

For the topmost roof floor:

- first run the normal roof workflow using the roof's own columns, look lines, openings, and primary beam logic
- columns should be aligned to the lower floor by axis network before final roof beam generation
- roof primary beams are local:
  `main_beams`, `validation_beams`, `cantilever_beams`, and `edge_beams` must be generated from the roof floor itself
- do not wholesale inherit the lower floor primary beam system onto the roof

For roof secondary beams:

- do not automatically place secondary beams inside roof opening regions
- do not automatically place secondary beams outside the final roof look-line range
- first build the final roof slab regions from the roof primary beam system
- then compare each final roof slab directly against the aligned lower-floor wall and secondary-beam geometry
- if the aligned lower floor has secondary beams inside that roof slab region, copy the full set of lower-floor secondary beams that belong to that roof slab region
- if the aligned lower floor has no secondary beam in that roof slab region, use roof cross-beam fallback for that slab only
- when selecting lower-floor secondary beams for a roof slab, allow beams whose full segment is inside the slab as well as beams whose midpoint is inside the slab
- this direct roof-slab-to-lower-beam comparison is the stable rule; do not require an intermediate “matched lower slab” object first

Current verified check result for this rule:

- the `7F` target roof slabs can be checked one by one against aligned `6F` partition walls and secondary beams
- a stable result means each roof target slab's copied secondary-beam count matches the lower-floor secondary-beam count found inside that same roof slab region

## Combined YDB Export

### Step 5: Export the total model

Use:

- [tools/export_multi_floor_ydb.py](/E:/2026/20260313_02上海院项目/tools/export_multi_floor_ydb.py)

Current export behavior:

- reads each floor DWG
- collects generated structural geometry
- re-applies lower-to-upper column inheritance to the floor column set before writing YDB
- exports column eccentricity for matched upper-floor columns whose actual position is offset from the inherited model center
- keeps floor-local node and axis systems independent in YDB
- creates one `tblStdFlr` row and one `tblFloor` row per floor
- writes aligned floor geometry into one combined `.ydb`
- for the roof floor, export the rebuilt local primary beam system plus the verified lower-floor-referenced secondary-beam result

Default command:

```bash
python E:\2026\20260313_02上海院项目\tools\export_multi_floor_ydb.py --floors 2F,3F,4F,5F,6F
```

Default output:

- [outputs/2F_6F_building_model.ydb](/E:/2026/20260313_02上海院项目/outputs/2F_6F_building_model.ydb)

## Performance Guidance

For total-model export, prefer rebuilding the floor layouts from source geometry instead of trusting stale CAD auto objects, especially after rule iterations.

Recommended sequence:

1. `python tools\run_multi_floor_layout.py --floors 2F,3F,4F,5F,6F,7F`
2. `python tools\export_multi_floor_ydb.py --floors 2F,3F,4F,5F,6F,7F`

## Verification

Before claiming success, verify:

1. each floor DWG has been processed
2. each floor has beam ids and size labels
3. the total YDB contains multiple `tblStdFlr` and `tblFloor` rows
4. the target database passes the project YDB validation script
5. for `7F`, compare each target roof slab against aligned `6F` partition walls and secondary beams
6. for `7F`, confirm the copied lower-floor secondary-beam count matches slab by slab, or that the slab correctly falls back to roof cross beams

Use:

- [tools/inspect_ydb_schema.py](/E:/2026/20260313_02上海院项目/tools/inspect_ydb_schema.py)
- [tools/export_multi_floor_ydb.py](/E:/2026/20260313_02上海院项目/tools/export_multi_floor_ydb.py)
- [tools/run_multi_floor_layout.py](/E:/2026/20260313_02上海院项目/tools/run_multi_floor_layout.py)
- [validate_yjk_db.py](/E:/2026/20260313_02上海院项目/.agents/skills/yjk-database/scripts/validate_yjk_db.py)

Recommended verification commands:

```bash
python E:\2026\20260313_02上海院项目\tests\test_floor_alignment.py
python E:\2026\20260313_02上海院项目\tests\test_main_beam_layout.py
python E:\2026\20260313_02上海院项目\tests\test_draw_main_beams.py
python E:\2026\20260313_02上海院项目\tests\test_export_plan_to_ydb.py
python E:\2026\20260313_02上海院项目\tests\test_secondary_beam_layout.py
python E:\2026\20260313_02上海院项目\tests\test_top_floor_beam_inheritance.py
python E:\2026\20260313_02上海院项目\tools\inspect_7f_vs_6f_secondary.py
python E:\2026\20260313_02上海院项目\.agents\skills\yjk-database\scripts\validate_yjk_db.py --reference E:\2026\20260313_02上海院项目\.agents\skills\yjk-database\ydbs\mini.ydb --target E:\2026\20260313_02上海院项目\outputs\2F_7F_building_model.ydb
```

## Common Mistakes

- Trying to merge node ids across floors.
- Trying to reuse one floor's axis ids as a global building axis table.
- Exporting the total model before each floor drawing has been regenerated.
- Recomputing geometry unnecessarily when the generated auto layers already contain the validated result.
- Forgetting that floor alignment is a coordinate translation, not a requirement to merge floor-local topology identifiers.
- Only补柱 in the export stage but not in the upper-floor layout stage.
- Ignoring section-size-induced upper/lower column center offsets instead of exporting them as eccentricity.
- Treating `建-看线3` as a roof opening layer instead of a roof scope layer.
- Forgetting to merge `楼梯间轮廓线` into roof opening regions.
- Reusing a pre-inheritance roof primary beam result after the roof columns have changed.
- Letting the roof keep generic open-slab cross beams when the lower floor already provides the intended beam layout.
- Requiring a fragile one-to-one lower-slab match before copying roof secondary beams, instead of comparing directly against the final roof slab region.
- Reporting success without checking `tblStdFlr` and `tblFloor` row counts.

## Output Expectation

When using this skill, always report:

- which floors were processed
- whether the per-floor layout was rebuilt or read from generated auto objects
- the alignment transform used for each floor
- the final output YDB path
- the validation result
