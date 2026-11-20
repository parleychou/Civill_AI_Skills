---
name: staadpro
version: 1.0.4
display_name: STAADPro
display_name_en: STAADPro
description_zh: 自动化控制 STAAD.Pro 进行空间结构建模、荷载施加、有限元计算与响应结果提取。
description_en: Automates STAAD.Pro for spatial structural modeling, load application, finite element analysis, and response extraction.
license: Apache-2.0
---
# STAAD.Pro Automation Guide (OpenSTAAD Router)

Automate STAAD.Pro model geometry, loading, finite element analysis, force extraction, and design verification through the `openstaadpy` interface within `python_executor`.

## 1. Instance Attachment and Session Management

Call `os_analytical.connect()` to establish communication with the active model and obtain the control session:

```python
from openstaadpy import os_analytical

s = os_analytical.connect()   # Connect to currently active STAAD.Pro model
print(s.GetSTAADFile())       # Verify model file path and context
```

**Session Management Rules**:
- **Attachment Precondition**: STAAD.Pro must already be running with a structural model opened. `connect()` attaches to the running instance and does not launch software or open files silently. If no process is found, an `OsErrorBase` exception is raised; stop execution and instruct the user to open the target model in STAAD.Pro.
- **In-Place Persistence**: Engineering models reside in established directory structures; subsequent saves must call `s.SaveModel(True)` in-place. Never save models to arbitrary temporary paths, which breaks relative links and downstream deliverables.
- **Multi-Model Disambiguation**: When multiple models are open simultaneously, specify the exact path: `s = os_analytical.connect(r"C:/path/to/model.std")`.

## 2. OpenSTAAD Primary Functional Modules Reference Table

The OpenSTAAD library is organized into 39 primary functional modules:

| Module Category (Short Name) | Functional Scope & Responsibilities |
|---|---|
| Session/File (Root) `session-file-root` | Session & file management: open/save .std, global units, status checks, solve triggers |
| Geometry: Node `geometry_node` | Nodal geometry: creation, query, coordinate editing, merging, and selection sets |
| Geometry: Member `geometry_member` | Member geometry: creation, split/merge/intersect, renumbering, connectivity |
| Geometry: Plate `geometry_plate` | Plate/shell elements: 3-node/4-node generation, geometric properties, areas |
| Geometry: Solid `geometry_solid` | 8-node brick solids: 3D solid elements, connectivity, and queries |
| Geometry: Group `geometry_group` | Named entity groups: grouped collections of nodes, members, plates, and solids |
| Geometry: Physical Member `geometry_physical-member` | Physical members: merging multiple analytical members into a single design unit |
| Geometry: Parametric Surface `geometry_parametric-surface` | Parametric surfaces: surface boundary definition and automated plate meshing |
| Geometry: Misc `geometry_misc` | Geometric utilities: vertical axis detection, translation/mirroring, duplicate checks |
| Load: Cases & Combinations `load_cases-combinations` | Primary load cases & combinations: definition, load factors, and activation |
| Load: Nodal `load_nodal` | Nodal loads: concentrated forces, moments, and enforced settlements |
| Load: Member Loads `load_member-loads` | Member loads: uniform, concentrated, trapezoidal, thermal, and distributed moments |
| Load: Plate Loads `load_plate-loads` | Plate loads: surface pressure, hydrostatic pressure distributions, concentrated forces |
| Load: Self-weight & Floor `load_self-weight-floor` | Structural self-weight and one-way/two-way floor load distributions |
| Load: Wind `load_wind` | Wind loading: wind intensity profiles, exposure factors, and wind load generation |
| Load: Seismic `load_seismic` | Seismic definitions: response spectrum parameters, mass sources, and equivalent lateral forces |
| Load: Spectrum & Direct Analysis `load_spectrum-direct-analysis` | Dynamic response spectrum, notional horizontal forces, and direct analysis parameters |
| Load: Reference Loads `load_reference-loads` | Reference load definitions and container management |
| Load: Lists & Envelopes `load_lists-envelopes` | Load case filtering and extreme internal force envelopes |
| Property: Standard Table Sections `property_standard-table-sections` | Standard steel catalogs: profile names come from the open model through `GetProfileSectionNameList` |
| Property: Prismatic & Tapered `property_prismatic-tapered` | Parametric custom sections (rectangles, circles, tapered) and section properties |
| Property: UPT User Tables `property_upt-user-tables` | User-defined profile tables (UPT) and section binding |
| Property: Assign & Query Sections `property_assign-query-sections` | Section assignment, property queries, and material beta angle orientation |
| Property: Materials `property_materials` | Material definitions (modulus E, Poisson's ratio, density) and member assignments |
| Property: Member Specs `property_member-specs` | Member specifications: end releases, partial fixity, tension/compression-only, master-slave |
| Property: Plate Thickness & Element Specs `property_plate-thickness-element-specs` | Plate thicknesses, plane stress assumptions, in-plane rotational releases, offsets |
| Property: Fireproofing `property_fireproofing` | Fireproofing coating thickness and added self-weight (stiffness excluded) |
| Property: Custom Attributes `property_custom-attributes` | Custom metadata tags and entity attributes |
| Support `support` | Supports & foundations: fixed, pinned, spring releases, inclined supports, elastic footings |
| Output: Units & Status `output_units-status` | Output unit verification and analysis results availability checks |
| Output: Node & Support Results `output_node-support-results` | Nodal displacements, support reactions, base shears, and soil pressure checks |
| Output: Member Results `output_member-results` | Member end forces, section forces along length, local deformations, and stresses |
| Output: Plate & Solid Results `output_plate-solid-results` | Plate/solid stresses, membrane forces, bending moments, and von Mises stresses |
| Output: Dynamic & Buckling `output_dynamic-buckling` | Natural frequencies, modal shapes, mass participation factors, buckling factors |
| Output: Steel Design Results `output_steel-design-results` | Steel design check results: stress ratios, governing load combinations, design blocks |
| Command `command` | Solver commands: linear static, P-Delta, non-linear analysis, rigid floor diaphragms |
| Design `design` | Code design parameters and design group definitions |
| Table `table` | Reporting system: structure reports and cell read/write operations |
| View `view` | 3D viewport control: display modes (wireframe/render), force diagrams, programmatic selections |

## 3. Programming Rules & Type Mapping

`openstaadpy` encapsulates underlying COM interop marshalling; manual VARIANT handling is unnecessary:
- **Parameter Inputs**: Pass standard Python native types (integers, floats, lists such as `[1, 2, 3]`).
- **Return Values**: Returns native Python data structures (`list`, `tuple`, `int`, `float`, `str`, `dict`).
- **Case Sensitivity**: Function names must match official PascalCase naming exactly.
- **Typed Exceptions**: Negative error codes become `OsErrorBase` subclasses in `openstaadpy.os_analytical.oserrors`, including `OsNodeNotFound`, `OsInvalidArgument`, and `OsGroupAlreadyExists`. Some paths still raise `COMError`. Wrap a batch with `except (OsErrorBase, COMError)` and include the member or load case in the message. `View.CreateNewViewForSelections` and `View.SetLabel` do not have a confirmed return value. Try them on one object before using the return.

## 4. Engineering Units and Vertical Axis Conventions

OpenSTAAD interprets all numerical input according to the **current model input unit system**. Incorrect unit assignments result in severe calculation errors. Furthermore, the global vertical axis (Y-up vs Z-up) governs gravity direction and coordinate orientation.

```python
s.GetBaseUnit()               # 'English' or 'Metric'
s.GetInputUnitForLength()     # 'Meter', 'MilliMeter', 'Feet', etc.
s.GetInputUnitForForce()      # 'KiloNewton', 'Kilopound', etc.
s.Geometry.IsZUp()            # True = Z-up, False = Y-up
```

**Unit System Principles**:
- Models have a global base unit and separate input units. When they disagree, modulus, density, coordinates, and loads are all wrong and the API does not say so. `SetInputUnits` changes only the input units. The base unit is changed by the user in the STAAD.Pro startup Configuration, after the model is saved and closed. Tell the user that. Do not try to set the base unit from Python.
- Run the four checks above before geometry, loads, or results. If the user says kilonewtons and metres and the model is not that system, convert in Python before the call.
- When `IsZUp() == True`, vertical coordinates use Z and gravity direction code is 3; when `IsZUp() == False`, vertical coordinates use Y and gravity direction code is 2.
- Switch input units via `s.SetInputUnits(lengthUnit, forceUnit)` (e.g. `(4, 5)` represents meters and kiloNewtons).

## 5. Standard Structural Calculation Pipeline

Recommended workflow order:
```
Session Connect -> Verify Units & Vertical Axis -> Consult references/common_examples.md
  -> Build Geometry (Nodes & Members) -> Assign Sections & Materials -> Define Supports
  -> Define Load Cases & Combinations -> Insert Analysis Command (PerformAnalysis)
  -> Save Model (SaveModel) -> Execute Analysis (AnalyzeEx) -> Validate Solver Convergence
  -> Extract Internal Forces, Displacements & Code Check Ratios
```

**Key Execution Rules**:
- **Conflict Prevention**: A repeated material, section, or load-case name does not raise. The create call can become an update, and an assign call can return success without taking effect. That shows up later as `DENSITY NOT PROVIDED`. List what is already there. Reuse it, or pick a new name such as `MY_STEEL_01`. Materials: `GetIsotropicMaterialCount` and `GetIsotropicMaterialProperties` (the material name is the first item). Sections: `GetSectionPropertyList` and `GetSectionPropertyName`, then pass that id to `AssignBeamProperty`. Load cases: `GetPrimaryLoadCaseNumbers`. Use the id returned by `CreateNewPrimaryLoad` or `CreateNewPrimaryLoadEx2`. Do not hard-code 1, 2, and 3. `DeletePrimaryLoadCases(existing, False)` clears primary cases. The second argument is reference-load mode. After assigning a material, `GetBeamMaterialName(beam_id)` must be non-empty. If it is empty, `SaveModel(True)` and assign again.
- **Unified Geometric Index Space**: Members, plates, and solids share one id space. Use the ids returned by `AddNode`, `AddBeam`, `AddPlate`, and `AddSolid`. A chosen id that already exists is accepted and later reported as `MEMBER/ELEM. NO. n IS DUPLICATED`.
- **Insert Analysis Commands Explicitly**: After all load cases and combinations are constructed, invoke `s.Command.PerformAnalysis(0)` to write the analysis instruction; clear prior instructions with `s.Command.DeleteAllAnalysisCommands()` when re-running after model edits.
- **Solver Execution**: `s.AnalyzeEx(1, 0, 1)` starts the solver. It does not write `PERFORM ANALYSIS`. `silentMode=1` suppresses input dialogs. `hiddenMode=0` keeps the progress window visible. Hiding it can stall on an error. `waitTillComplete=1` blocks until the solver finishes. Codes: negative or 0 is a failure, 1 is still running, 2 is finished clean, 3 is finished with warnings, 4 has errors, 5 has not been analyzed. Follow it with `while s.IsAnalyzing(): pass` when the call can return before the solver is idle.
- **Status Verification**: `GetAnalysisStatus()` returns `ReturnValue`, `ReturnString`, and `NoOfErrors`. Read results only when `ReturnValue` is 2 or 3. On code 4 or `NoOfErrors > 0`, read the `.ANL` file for `*** ERROR MESSAGE ***`, then the commands that were actually written. `GetAnalysisErrorMessages()` is not available from STAAD 2024 onward.
- **Empty Results**: If a result is empty or zero, check analysis status, whether the load-case number is in `GetPrimaryLoadCaseNumbers()`, and whether the input units match the numbers you sent.

## 6. Operational Precautions

1. **Non-Interactive Batch Automation**: Agent scripts must run fully unattended without modal popups; save models using `s.SaveModel(True)`.
2. **Access Pre-Selected Entities**: Read user-selected entities via `s.Geometry.GetSelectedBeams()` or `s.Geometry.GetSelectedNodes()`; if empty, prompt the user to make a selection rather than hanging.
3. **Optimize COM Invocations**: Minimize per-call COM overhead by avoiding element-by-element loops. Retrieve full entity lists via `GetNodeList()` or `GetBeamList()`, and pass lists to batch assignment interfaces where supported.
4. **Output File Locations**: Write generated charts, CSV tables, and reports to `WORKSPACE_DIR` using absolute paths.
5. **Do Not Edit Raw .std Files Directly**: Edit the `.std` text only when the user asks for that edit and states the exact change. The order is `SaveModel(True)`, `CloseSTAADFile()`, `time.sleep(2)`, edit the file, `connect()` again, `OpenSTAADFile()`, then read a load case or a geometry query. The COM session from before the close is invalid. The sequence is in `references/common_examples.md`.

## 7. Workflow Automation Script

[scripts/code_tables.py](scripts/code_tables.py) records the unit, load-type, direction, group, country, and analysis-status codes used below. [scripts/staad_frame.py](scripts/staad_frame.py) builds a portal frame on an already-open model: metre and kilonewton units, nodes and beams, fixed bases (`CreateSupportFixed` then `AssignSupportToNode`), one dead-load case, and optional analysis (`PerformAnalysis` then `AnalyzeEx`). Running either file with no arguments is a local self-check and does not start STAAD.Pro. Pass `--run` to `staad_frame.py` only when a model is already open. Section names are assigned from the live catalog, as shown in [references/common_examples.md](references/common_examples.md).

---

## Official Documentation & Upstream API Sources

When verifying specific OpenSTAAD function return codes, COM syntax variations, or advanced analysis cards, consult the official Bentley OpenSTAAD reference resources:

- **Bentley OpenSTAAD Documentation Wiki**: [https://communities.bentley.com/products/ram-staad/w/structural_analysis_and_design__wiki/8568/openstaad-documentation](https://communities.bentley.com/products/ram-staad/w/structural_analysis_and_design__wiki/8568/openstaad-documentation)
- **Bentley Systems Documentation Portal**: [https://docs.bentley.com/](https://docs.bentley.com/)
- **openstaadpy Python Package Documentation**: [https://pypi.org/project/openstaadpy/](https://pypi.org/project/openstaadpy/)
- **Local Installed Primary Material**: COM Type Libraries and Interop assemblies located in the STAAD.Pro program directory:
  - `<STAAD_DIR>\STAAD\OpenSTAAD\OpenSTAAD.tlb`
  - `<STAAD_DIR>\STAAD\OpenSTAAD\Bentley.Interop.Staad.dll`

---

## Intellectual Property & Interoperability Notice

This skill provides open procedural automation workflows, interface scripts, and reference documentation for structural engineering and computational design. All third-party product names, software titles, registered trademarks, and logos referenced herein are the intellectual property of their respective owners. Mention of these systems is made solely for technical interoperability, compatibility identification, and execution routing. Use of this skill implies no affiliation, endorsement, sponsorship, or intellectual property rights claim.
