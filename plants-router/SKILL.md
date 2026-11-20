---
name: plants
version: 1.0.4
display_name: PlantS
display_name_en: PlantS
description_zh: 基于 MCP 通信通道操控工业建筑及工厂结构三维设计环境，支持梁柱斜撑建模、独立基础及工业通廊栈桥自动化装配。
description_en: Controls 3D industrial structural engineering environments via MCP channels, supporting framing members, foundations, and conveyor corridor automation.
license: Apache-2.0
---
# Industrial Plant & Structural Modeling Guide (PlantS Router)

Automate industrial plant design, spatial framing, pipe racks, conveyor trestles, and foundations through direct MCP channels.

## Standard Execution Pipeline: Connect -> Query -> Execute

All industrial modeling tasks follow a three-stage pipeline:

### Step 1: Establish Service Connection

Before invoking model operations, establish communication via `python_executor`:

```python
from Agent.software_link_kit.plants import connect_to_plants

result = connect_to_plants()
print(result)
```

Returning `True` confirms an active connection.
- With no path, reuse a running PlantS whose MCP channel is already up. If none is running, find the installation, copy `Interface\P3DTemplate\temp.p3d` into the workspace, and start that temporary project.
- `exe_path` alone still prefers a running process for that executable. A cold start without `project_path` opens a temporary project.
- `project_path` alone opens that project with the recorded or discovered executable.
- Do not store a user-supplied project path for a later task. The corridor script calls `connect_to_plants()` itself and reuses an open session.
- A successful connection injects the MCP functions and prints an `MCP_Connected` briefing of categories and injected data shapes.

```python
from Agent.software_link_kit.plants import connect_to_plants

result = connect_to_plants(
    exe_path=r"F:\software\GYP\BIMBase.exe",
    project_path=r"F:/software/GYP/test.p3d",
)
print(result)
```

Upon connection, available modeling functions are injected into the Python execution workspace, and an overview of categories is printed to stdout.

### Step 2: Dynamic Function Specification Lookup

After connecting, call `function_search` to look up available functions. Key categories include:
- `plantsmcp新建`: Creation of beams, columns, and bracings
- `plantsmcp修改`: Modifications to parameters, locations, and topology
- `plantsmcp查询`: Retrieval of entity properties and coordinates
- `plantsmcp截面`: Parametric and catalog section definitions
- `plantsmcp独立基础轮廓` / `plantsmcp独立基础截面`: Footing profiles and foundation geometry

**List Function Names Under a Category**:
```python
print(function_search(action="GetName", func_type="plantsmcp新建"))
```

**Get Detailed Parameter Signatures**:
```python
print(function_search(action="GetDescription", func_type="plantsmcp新建", func_names=["CreateBeam"]))
```

`function_search(action="GetType")` lists categories again. Look up every signature at the start of the task. Do not look up one function per loop iteration. If three lookups still do not expose a function that can do the task, tell the user the connected MCP surface cannot do it.

### Step 3: Script Assembly and Execution

Once function signatures are confirmed, assemble and execute the Python script:

```python
result = CreateBeam(start_point=[0, 0, 0], end_point=[6000, 0, 0])
print(result)
```

**Key Execution Rules**:
- Injected functions exist in the global script namespace; do NOT write `import` statements for them.
- Output intended for user review must be explicitly printed via `print()`.
- Coordinates are millimetres, `[x, y, z]`.
- A `DataKeyRef` is `{"class_id": "...", "data_id": "..."}` with string ids. It is a dict, not a Pydantic model. Do not call `model_dump()`.
- Rectangular sections use the current tool names:

```python
section_data = Generate_BarSectionData_Rectangle(width=300, height=300)
section_key = Find_Or_Add_BeamSection(section=section_data)
```

## DataKeyRef Data Structure Handling

Entity references (`DataKeyRef`) returned by MCP calls are standard Python `dict` structures; do NOT access them as object attributes:

```python
beam = CreateBeam(start_point=[0, 0, 0], end_point=[6000, 0, 0])
beam_key = beam["beam_key"]
print(beam_key["class_id"], beam_key["data_id"])
```

Do not use `beam.beam_key`, `beam_key.class_id`, or `beam_key.model_dump()`.

## Connection Health Check

If the environment reports an active connection but subsequent operations fail, check connection status:

```python
print(is_server_connected("plantsmcp"))
```

Only re-initiate connection if this probe returns `False`.

## Industrial Conveyor Corridor Automation

When creating or modifying industrial galleries, conveyor corridors, trestles, or pipe racks, invoke the parametric generator `scripts/conveyor_corridor.py` directly rather than constructing framing from scratch. Running that file with no arguments checks the default geometry and does not start PlantS.

**Parameter Table (`INDUSTRY_CORRIDOR_PARAMS`)**:
Copy only the values the user stated. Leave the rest at the script defaults.
- `length`: total length in mm. When set, `bay_length` is the target bay used to choose the bay count, then the bays are resized so they sum to `length`.
- `bay_length` / `bay_spacing`: target bay length in mm, default 3500.
- `num_bays` / `bay_count`: bay count only when `length` is omitted. When `length` is set, the script replaces this value. Do not take it from a sentence that also gives the total length.
- `width`: width in mm.
- `height` / `truss_height`: truss height in mm.
- `slope` / `slope_angle_deg`: slope in degrees.
- `origin`: `[x, y, z]` in mm.
- `side_v_apex`: `"bottom"` or `"top"`.
- `reverse_end_diagonals`: reverse the diagonals at each span end.
- `support_span_m`: support spacing in metres, default 30, recommended 20 to 36, maximum 60. Supports land on bay stations and are spaced as evenly as that grid allows.
- `support_indices`: station numbers. `None` uses `support_span_m`. `[]` builds no supports.
- `ground_z`: column base and footing top, in mm.
- `create_foundations`: default `True`.
- `foundation_type`: default `"StepCast"`.
- `foundation_steps`: default two rectangles, `2200x2200x500` and `1400x1400x400`, in mm.
- `foundation_angle_deg`: default 0.
- `chord_section`, `web_section`, `cross_brace_section`, `support_section`: section names.
- `material`: material name.

Set `INDUSTRY_CORRIDOR_EXE_PATH` or `INDUSTRY_CORRIDOR_PROJECT_PATH` in the same globals before executing the script when the user gave those paths.

**Standard Invocation Template**:

```python
from pathlib import Path
import Agent

INDUSTRY_CORRIDOR_PARAMS = {
    "length": 36000,
    "bay_length": 3500,
    "width": 3000,
    "height": 3800,
    "slope": 14,
}

script_path = (
    Path(Agent.__file__).resolve().parent
    / "skills"
    / "PlantS-Router"
    / "scripts"
    / "conveyor_corridor.py"
)

exec(compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec"), globals())
```

---

## Official Documentation & Upstream API Sources

For industrial BIM plant modeling, standard profile catalogs, and underlying platform protocols, consult the official platform developer resources:

- **BIMBase Developer Portal**: [https://open.bimbase.cn/](https://open.bimbase.cn/)
- **BIMBase Platform Documentation**: [https://www.bimbase.cn/](https://www.bimbase.cn/)
- **Local Installed Primary Material**: Template projects and MCP schema interfaces shipped with the installation:
  - `<PLANTS_DIR>\Interface\P3DTemplate\temp.p3d`

---

## Intellectual Property & Interoperability Notice

This skill provides open procedural automation workflows, interface scripts, and reference documentation for structural engineering and computational design. All third-party product names, software titles, registered trademarks, and logos referenced herein are the intellectual property of their respective owners. Mention of these systems is made solely for technical interoperability, compatibility identification, and execution routing. Use of this skill implies no affiliation, endorsement, sponsorship, or intellectual property rights claim.
