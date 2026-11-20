---
name: etabs
version: 1.0.3
display_name: ETABS
display_name_en: ETABS
description_zh: 基于 COM 自动化接口驱动 ETABS 开展高层与多层建筑结构有限元建模、荷载组合配置、求解计算及内力位移提取。
description_en: Drives ETABS via COM automation for multistory and high-rise structural modeling, load combinations, finite element analysis, and internal force/displacement extraction.
license: Apache-2.0
---
# ETABS Structural Analysis & Design Guide (ETABS Router)

## Standard Calculation Pipeline (Workflow)

```
Attach to or Launch ETABS -> Verify Units -> Model Geometry & Assign Properties
  -> Configure Load Patterns & Combinations -> Save Model -> Run Analysis -> Extract Forces/Displacements & Verify Code Checks
```

## Primary Functional Modules Reference Table

The ETABS Open API (OAPI) is categorized into the following primary interfaces:

| Module Name | Responsibility | Functional Scope |
|---|---|---|
| **cFile** | File Operations | Model initialization, opening, saving, template importing |
| **cAnalyze** | Solver Execution | Running analysis, configuring degrees of freedom, solver status |
| **cAnalysisResults** | Response Extraction | Nodal displacements, story drifts, frame forces, shell stresses, reactions |
| **cFrameObj** | Frame Objects | Geometric creation, modification, and property assignment for beams/columns |
| **cAreaObj** | Shell/Area Objects | Floor slabs, shear walls, curved surface topology and thicknesses |
| **cPointObj** | Nodal Points | Joint coordinates, restraints, and concentrated nodal forces |
| **cLinkObj** | Link Elements | Isolators, dampers, gaps, and non-linear link elements |
| **cTendonObj** | Prestress Tendons | Tendon layout, profiles, and post-tensioning forces |
| **cPropFrame** | Frame Properties | Standard steel catalogs, concrete sections, and Section Designer shapes |
| **cPropArea** | Shell Properties | Rigid/semi-rigid diaphragms, wall/slab section stiffness modifiers |
| **cPropLineSpring** / **cPropPointSpring** | Spring Properties | Soil-structure interaction springs and elastic foundation constants |
| **cDatabaseTables** | Database Tables | Full tabular model export, batch importing, and low-level table editing |

## Key Execution Rules

### 1. Prioritize Attaching to Running Instances

Always initialize `comtypes.CoInitialize()` before making COM calls. Prefer attaching to an active ETABS process; prompt the user before starting a new instance. `cHelper.GetObject` returns `None` rather than raising an exception when no instance is found:

```python
import comtypes.client
import comtypes.gen

comtypes.CoInitialize()
helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

# 1) Attempt to attach to running instance
EtabsObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
if EtabsObject is None:
    # Ask before starting a new ETABS process.
    EtabsObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
    EtabsObject.ApplicationStart()

SapModel = EtabsObject.SapModel
```

### 2. Unit System Alignment

- Call `SapModel.GetPresentUnits()` before writing values. A model that already has a unit system keeps it. A new model uses `N_mm_C` (`9`).
- Unit codes: `lb_in_F=1`, `lb_ft_F=2`, `kip_in_F=3`, `kip_ft_F=4`, `kN_mm_C=5`, `kN_m_C=6`, `kgf_mm_C=7`, `kgf_m_C=8`, `N_mm_C=9`, `N_m_C=10`, `Ton_mm_C=11`, `Ton_m_C=12`, `kN_cm_C=13`, `kgf_cm_C=14`, `N_cm_C=15`, `Ton_cm_C=16`.
- `cFile.NewGridOnly` takes metres when the model is metric and feet when it is imperial, regardless of the active length unit. Convert grid spacing before that call.

### 3. Model Saving Requirements

Verify file paths via `SapModel.GetModelFilename(True)`. If untitled (`(Untitled)`), prompt the user or save the `.edb` file into a dedicated workspace folder; always call `SapModel.File.Save(filepath)` before running analysis to ensure result databases are generated properly.

## VB to Python Conversion (ByRef Arguments and Tuple Unpacking)

ETABS API documentation is written in Visual Basic syntax. When calling through Python `comtypes`, follow these conversion rules:

### Core Mechanism: ByRef Arguments and Return Tuples

Underlying COM methods return results by writing to pointer arguments. In Python, arguments marked `ByRef` in VB signatures require placeholder values upon call, and the function returns a **tuple** containing all output values followed by the return status code:

$$\text{Result Tuple} = (\text{Output}_1, \text{Output}_2, \dots, \text{RetCode})$$

Before each call, read the signature in the installed `CSi API ETABS.chm` or on https://wiki.csiamerica.com/display/etabs/ETABS+API. Count every argument. A parameter that is not marked optional must be passed. The Python return is `(ByRef outputs..., return code)`. Return code `0` is success. A non-zero code is an ETABS failure even when COM did not raise. `COMError` is the COM failure, not that return code.

An array marked `ByRef` in a VB signature is often an input, especially in DatabaseTables. Pass the real list. It is not in the returned tuple. If you are unsure, unpack by the length you actually received.

| VB | Pass | Receive |
|---|---|---|
| `ByVal String` | the string | not returned |
| `ByVal Double` | the number | not returned |
| `ByRef String` | `" "` | the string in the tuple |
| `ByRef Double` | `0.0` | the number in the tuple |
| `ByRef Long` | `0` | the number in the tuple |
| `ByRef` array used as output | `[]` | the list in the tuple |
| `ByRef` array used as input | the real list | not returned |

```python
# GetSelected(ByRef NumberItems As Long, ByRef ObjectType() As Long, ByRef ObjectName() As String) As Long
number_items, object_types, object_names, ret = SapModel.SelectObj.GetSelected(0, [], [])
```

`GetObject` returns `None` when ETABS is not running. Test that before using `SapModel`. Ask before `ApplicationStart()`.

### Database tables

- Storeys use `cStory.SetStories_2`. Do not write the storey table through DatabaseTables.
- `cGridSys.SetGridSys` sets the grid-system origin and rotation. It does not set grid lines. `GetGridSys_2` and `GetGridSysCartesian` only read lines. Grid lines are written through DatabaseTables.
- Before reading, call `GetAllTables` for the real table key and `GetAllFieldsInTable` for `FieldKey`, `FieldName`, and `Description`. Do not invent a table key.
- Before writing, read the current table with `GetTableForEditingArray` and use that shape as the template.
- Prefer `SetTableForEditingArray` with field keys and one row-major list of strings. `SetTableForEditingCSVString` uses display names in the header and localized cell text. A mismatch can make `ApplyEditedTables` report zero records or clear the table.
- After the edit, call `ApplyEditedTables` and read `NumFatal`, `NumErr`, `NumWarn`, `NumInfo`, and `ImportLog`.

```python
table_key = "..."  # from GetAllTables
table_version, number_fields, field_keys, field_names, descriptions, units, is_importable, ret = (
    SapModel.DatabaseTables.GetAllFieldsInTable(table_key, 0, 0, [], [], [], [], [])
)
number_records = 1
table_data = ["..."]  # number_records * len(field_keys) strings, row-major
table_version, ret = SapModel.DatabaseTables.SetTableForEditingArray(
    table_key, 0, list(field_keys), number_records, table_data
)
num_fatal, num_err, num_warn, num_info, import_log, ret = (
    SapModel.DatabaseTables.ApplyEditedTables(True, 0, 0, 0, 0, " ")
)
```

**Example**:

```python
# VB Signature:
# Function GetAllFrames(ByRef NumberItems As Long, ByRef FrameNames() As String) As Long

# Python Invocation:
# 1. Pass placeholders (0, [])
# 2. Unpack return tuple: (NumberItems, FrameNames, ret)
num_items, frame_names, ret = SapModel.FrameObj.GetAllFrames(0, [])

if ret == 0:
    print(f"Retrieved {num_items} frame objects: {frame_names}")
```

## Complete Workflow Automation Script

[scripts/unit_table.py](scripts/unit_table.py) is the unit-code list. A new model uses code 9, `N_mm_C`. [scripts/portal_frame.py](scripts/portal_frame.py) builds a concrete portal frame, assigns rectangular sections, fixes the bases, adds dead and live patterns, and can run the solver. Running either file with no arguments is a local self-check and does not start ETABS. Pass `--run` to `portal_frame.py` when ETABS is already open. Pass `--launch` only when a new ETABS process should be started.

---

## Official Documentation & Upstream API Sources

When verifying complex OAPI method signatures, DatabaseTables schema layouts, or ByRef parameter definitions, refer to the official Computers & Structures, Inc. (CSI) documentation:

- **CSI Knowledge Base (ETABS API Documentation)**: [https://wiki.csiamerica.com/display/etabs/ETABS+API](https://wiki.csiamerica.com/display/etabs/ETABS+API)
- **CSI America Documentation Portal**: [https://docs.csiamerica.com/](https://docs.csiamerica.com/)
- **Local Installed Primary Material**: The comprehensive compiled HTML help manual included with every ETABS installation:
  - `<ETABS_INSTALL_DIR>\CSi API ETABS.chm`

---

## Intellectual Property & Interoperability Notice

This skill provides open procedural automation workflows, interface scripts, and reference documentation for structural engineering and computational design. All third-party product names, software titles, registered trademarks, and logos referenced herein are the intellectual property of their respective owners. Mention of these systems is made solely for technical interoperability, compatibility identification, and execution routing. Use of this skill implies no affiliation, endorsement, sponsorship, or intellectual property rights claim.
