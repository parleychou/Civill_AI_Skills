# Structural Plan Tool Map

## Overview

This file maps the current project tools and core modules for the structural plan layout workflow.

The goal is not to duplicate algorithm rules, but to show which tool to call at each workflow stage.

## Core Modules

### Geometry extraction and CAD access

- [tools/draw_axes_and_columns.py](/E:/2026/20260313_02上海院项目/tools/draw_axes_and_columns.py)
  - `resolve_target_document`
  - `extract_layout_geometry`
  - `ensure_layer`
  - CAD extraction entry for axes, columns, look lines, openings, stairs, wall raw geometry

### Main beam system

- [main_beam_layout.py](/E:/2026/20260313_02上海院项目/main_beam_layout.py)
  - `build_main_beams_from_axes`
  - `build_axis_validation_repair_beams`
  - `attach_hosting_axes`
  - `beam_number_label`

### Cantilever beams

- [cantilever_layout.py](/E:/2026/20260313_02上海院项目/cantilever_layout.py)
  - `build_cantilever_beams`
  - `beam_number_label`

### Edge beams

- [edge_beam_layout.py](/E:/2026/20260313_02上海院项目/edge_beam_layout.py)
  - `build_edge_beams`
  - `beam_number_label`

### Slab topology

- [slab_topology.py](/E:/2026/20260313_02上海院项目/slab_topology.py)
  - `build_slabs_from_beams`
  - used by secondary-beam recursion and slab debugging

### Wall centerlines

- [wall_centerline.py](/E:/2026/20260313_02上海院项目/wall_centerline.py)
  - `extract_wall_geometries`
  - `build_wall_centerlines`

### Secondary beams

- [secondary_beam_layout.py](/E:/2026/20260313_02上海院项目/secondary_beam_layout.py)
  - `build_secondary_beams`
  - `beam_number_label`

## Drawing Tools

### Full integrated drawing

- [tools/draw_main_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_main_beams.py)
  - integrated drawing entry for:
    - main beams
    - validation beams
    - cantilever beams
    - edge beams
    - secondary beams

### Slab and wall debug drawing

- [tools/draw_slab_wall_debug.py](/E:/2026/20260313_02上海院项目/tools/draw_slab_wall_debug.py)
  - debug entry for:
    - slab outlines
    - slab ids
    - wall centerlines
    - wall ids

### Secondary-only drawing

- [tools/draw_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_secondary_beams.py)
  - only redraws secondary beams and their ids

## Cleanup Tools

### Full auto cleanup

- [tools/clear_auto_beams.py](/E:/2026/20260313_02上海院项目/tools/clear_auto_beams.py)
  - clears all auto-generated beam layers

### Secondary-only cleanup

- [tools/clear_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/clear_secondary_beams.py)
  - clears only secondary-beam lines and ids

## Verification and Inspection Tools

### Secondary verification

- [tools/validate_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/validate_secondary_beams.py)
  - reports:
    - secondary count
    - generation source distribution
    - wall alignment failures
    - stair intersection failures
    - opening intersection failures

### Secondary global inspection

- [tools/inspect_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/inspect_secondary_beams.py)
  - prints slabs, walls, wall centerlines, secondary beams, angle distribution

### Slab-scoped inspection

- [tools/inspect_slab_secondary_hits.py](/E:/2026/20260313_02上海院项目/tools/inspect_slab_secondary_hits.py)
  - check which secondary beams hit a specific slab

- [tools/inspect_slab_wall_candidates.py](/E:/2026/20260313_02上海院项目/tools/inspect_slab_wall_candidates.py)
  - inspect wall candidates inside a target slab

- [tools/inspect_root_slab_recursive_chain.py](/E:/2026/20260313_02上海院项目/tools/inspect_root_slab_recursive_chain.py)
  - inspect recursive generation chain from a root slab

### Targeted recursive / wall debugging

- [tools/inspect_slab6_recursive_chain.py](/E:/2026/20260313_02上海院项目/tools/inspect_slab6_recursive_chain.py)
- [tools/inspect_slab9_recursive_chain.py](/E:/2026/20260313_02上海院项目/tools/inspect_slab9_recursive_chain.py)
- [tools/inspect_slab9_wall_sequence.py](/E:/2026/20260313_02上海院项目/tools/inspect_slab9_wall_sequence.py)
- [tools/inspect_wall137_generated_beams.py](/E:/2026/20260313_02上海院项目/tools/inspect_wall137_generated_beams.py)
- [tools/inspect_wall34_failure.py](/E:/2026/20260313_02上海院项目/tools/inspect_wall34_failure.py)

Use these when a user points to a specific slab or wall and the normal validation summary is not enough.

## Documentation Sources

### Current wall-centerline rule source

- [2026-03-17-wall-centerline-generation-rules.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-17-wall-centerline-generation-rules.md)

### Current secondary-beam rule source

- [2026-03-18-secondary-beam-current-rules.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-18-secondary-beam-current-rules.md)

### Historical beam design notes

- [2026-03-16-main-beam-validation-rule.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-16-main-beam-validation-rule.md)
- [2026-03-16-edge-beam-generation-rules.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-16-edge-beam-generation-rules.md)
- [2026-03-16-secondary-beam-generation-rules.md](/E:/2026/20260313_02上海院项目/docs/plans/2026-03-16-secondary-beam-generation-rules.md)

## Recommended Execution Paths

### Path A: Full structural plan regeneration

1. [tools/draw_main_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_main_beams.py)
2. Targeted inspect tools if a slab or wall is wrong
3. If the issue is secondary-only, switch to the secondary-only tool path

### Path B: Secondary-only iteration

1. [tools/clear_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/clear_secondary_beams.py)
2. [tools/draw_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/draw_secondary_beams.py)
3. [tools/validate_secondary_beams.py](/E:/2026/20260313_02上海院项目/tools/validate_secondary_beams.py)
4. Slab-scoped inspect tools if needed

### Path C: Rule/documentation maintenance

1. Update the relevant plan document in [docs/plans](/E:/2026/20260313_02上海院项目/docs/plans)
2. Keep the skill in sync if the workflow order changes
3. Verify the affected tool path still matches the documented order
