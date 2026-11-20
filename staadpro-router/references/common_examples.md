# OpenSTAAD call patterns

These notes describe the call order for a connected OpenSTAAD session: connect, units, geometry, sections and materials, member releases, supports, loads, analysis, then results. They are interoperability notes for this skill. Enumerations that are not listed here are in the Bentley OpenSTAAD documentation linked from `SKILL.md`:

https://communities.bentley.com/products/ram-staad/w/structural_analysis_and_design__wiki/8568/openstaad-documentation

Every snippet assumes the setup below. `s` is the connected session. `connect()` does not start STAAD.Pro and does not open a file.

```python
from openstaadpy import os_analytical

try:
    s = os_analytical.connect()
except Exception as exc:
    raise RuntimeError("Open the target model in STAAD.Pro before connecting.") from exc
```

## Connection and model info

```python
s.GetSTAADFile()
s.GetApplicationVersion()
s.GetBaseUnit()               # 'English' or 'Metric'
s.GetInputUnitForLength()
s.GetInputUnitForForce()

# The .std file must already be open in a STAAD.Pro instance.
s2 = os_analytical.connect(r"C:/models/tower.std")
```

## Units

```python
# Length: 0=Inch, 1 and 2=Feet, 3=cm, 4=Meter, 5=mm, 6=dm, 7=km
# Force: 0=Kip, 1=Pound, 2=kg, 3=t, 4=N, 5=kN, 6=MN, 7=daN
s.SetInputUnits(1, 0)         # feet + kip
s.SetInputUnits(4, 5)         # metre + kilonewton
s.SaveModel(True)
```

## Geometry

Use the `Add*` methods and keep the returned ids. Do not choose ids yourself.

```python
n1 = s.Geometry.AddNode(0.0, 0.0, 0.0)
n2 = s.Geometry.AddNode(30.0, 0.0, 0.0)
n3 = s.Geometry.AddNode(0.0, 20.0, 0.0)

b1 = s.Geometry.AddBeam(n1, n3)
new_plate = s.Geometry.AddPlate(n1, n2, n3)   # triangle: the fourth node is 0
# new_solid = s.Geometry.AddSolid(n1, n2, n3, n4, n5, n6, n7, n8)

s.Geometry.GetNodeCount();  s.Geometry.GetMemberCount()
s.Geometry.GetNodeList();   s.Geometry.GetBeamList()
s.Geometry.GetNodeCoordinates(1)
s.Geometry.GetMemberIncidence(1)
```

## Sections, materials, and beta angle

Section names must match the catalog that is loaded in the open model, including letter case. Chinese H sections use a lowercase `x`, for example `"HW250x250"`. Angles in that catalog use an uppercase `X`, for example `"L30X30X4"`. Ask the open model for names. Do not guess a name from memory.

```python
s.Property.GetProfileDatabaseList()
s.Property.GetProfileSectionTableList(5)                   # 5 = Chinese catalog
s.Property.GetProfileSectionNameList(5, keyword="HW250")
s.Property.GetProfileSectionNameList(5, shape="Angle")     # also "Wide Flange", "HSS Round"

# Country codes used here: 1 = American, 5 = Chinese.
# Other country codes are on the Bentley page for CreateBeamPropertyFromTable.
cc = 1
w14 = s.Property.CreateBeamPropertyFromTable(cc, "W14X90", 0, 0.0, 0.0)
s.Property.AssignBeamProperty([1, 3, 4], w14)

angle = s.Property.CreateAnglePropertyFromTable(cc, "L40404", 0, 0.0)
s.Property.AssignBeamProperty(list(range(14, 24)), angle)

s.Property.AssignMaterialToMember("STEEL", list(range(1, 24)))
# Built-in names also include CONCRETE and ALUMINUM.
# A Chinese catalog keyword such as "HW250" can return HW250x250 and HW250x255.
s.Property.AssignBetaAngle([3, 4], 90.0)
```

## Member end releases

```python
# Position: 0 = start, 1 = end. Release flags: [FX, FY, FZ, MX, MY, MZ], 1 = released.
# The third argument is the matching spring stiffness. A pure hinge uses 0.
start_mz = s.Property.CreateMemberReleaseSpec(0, [0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0])
s.Property.AssignMemberSpecToBeam([5], start_mz)

# Partial release: [MPX, MPY, MPZ], factors from 0 to 1. Create and assign each end.
start_my_mz = s.Property.CreateMemberPartialReleaseSpec(0, [0, 1, 1], [0.0, 0.99, 0.99])
end_my_mz = s.Property.CreateMemberPartialReleaseSpec(1, [0, 1, 1], [0.0, 0.99, 0.99])
s.Property.AssignMemberSpecToBeam(list(range(14, 24)), start_my_mz)
s.Property.AssignMemberSpecToBeam(list(range(14, 24)), end_my_mz)
```

Truss, tension-only, and compression-only specifications follow the same pattern: `CreateMemberTrussSpec` (or the matching create call) returns an id, then `AssignMemberSpecToBeam` assigns it.

## Supports

`CreateSupportFixed()` and `CreateSupportPinned()` take no node argument. They return a specification id. Assign that id with `AssignSupportToNode`.

```python
fixed_id = s.Support.CreateSupportFixed()
pinned_id = s.Support.CreateSupportPinned()
s.Support.AssignSupportToNode([1], fixed_id)
s.Support.AssignSupportToNode([2], pinned_id)
```

## Load cases, loads, and combinations

```python
# CreateNewPrimaryLoadEx2(title, load_type, case_number) returns the case number, or 0 on failure.
# Load type: 0=Dead, 1=Live, 2=Roof live, 3=Wind, 4=Seismic horizontal, 5=Seismic vertical.
# Further load-type codes are on the Bentley page for CreateNewPrimaryLoadEx2.
case1 = s.Load.CreateNewPrimaryLoadEx2("DEAD AND LIVE LOAD", 0, 1)
s.Load.SetLoadActive(case1)

s.Load.AddSelfWeightInXYZ(2, -1.0)    # direction 1=X, 2=Y, 3=Z

s.Load.AddNodalLoad([4], 0.0, -15.0, 0.0, 0.0, 0.0, 0.0)

# Direction 1-3 = local X/Y/Z, 4-6 = global X/Y/Z, 7-9 = projected X/Y/Z.
# d1 and d2 are start and end distances from the member start. (0, 0) covers the whole member.
# d3 is the offset from the shear center.
s.Load.AddMemberUniformForce(list(range(8, 14)), 2, -0.9, 0.0, 0.0, 0.0)

case2 = s.Load.CreateNewPrimaryLoadEx2("WIND FROM LEFT", 3, 2)
s.Load.SetLoadActive(case2)
s.Load.AddMemberUniformForce([1, 2], 4, 0.6, 0.0, 0.0, 0.0)   # 4 = global X

s.Load.CreateNewLoadCombination("75 PERCENT DL LL WL", 3)
s.Load.AddLoadAndFactorToCombination(3, 1, 0.75)
s.Load.AddLoadAndFactorToCombination(3, 2, 0.75)

s.Load.GetPrimaryLoadCaseCount()
s.Load.GetPrimaryLoadCaseNumbers()
```

## Save and analyze

`AnalyzeEx` starts the solver. It does not write the analysis command. After every primary case and combination exists, call `Command.PerformAnalysis(0)` once so `PERFORM ANALYSIS` is written after the loads. Calling it before the combinations, or skipping it, leaves the analysis command missing or out of order.

```python
s.Command.PerformAnalysis(0)
s.SaveModel(True)

# silentMode=1 suppresses input dialogs.
# hiddenMode=0 keeps the analysis window visible. Hiding it can stall on an error.
# waitTillComplete=1 blocks until the solver finishes.
status = s.AnalyzeEx(1, 0, 1)
# -1 aborted, 0 error, 1 running, 2 finished clean, 3 finished with warnings,
# 4 finished with errors, 5 not analyzed.
if status < 0:
    raise RuntimeError(f"Analysis failed with status {status}")
while s.IsAnalyzing():
    pass

info = s.GetAnalysisStatus()
if info["ReturnValue"] not in (2, 3):
    anl_path = s.GetSTAADFile().rsplit(".", 1)[0] + ".ANL"
    with open(anl_path, encoding="utf-8", errors="ignore") as handle:
        errors = [line.strip() for line in handle if "*** ERROR MESSAGE ***" in line]
    print("\n".join(errors) or "No *** ERROR MESSAGE *** block. Read the .ANL file.")
```

## Results

Read results only after analysis has finished with status 2 or 3.

```python
lc = 1

for beam_id in s.Geometry.GetBeamList()[:5]:
    try:
        start_forces = s.Output.GetMemberEndForces(beam_id, 0, lc, 0)
        end_forces = s.Output.GetMemberEndForces(beam_id, 1, lc, 0)
        print(beam_id, start_forces, end_forces)
    except Exception as exc:
        print(f"Member {beam_id} could not be read: {exc}")

for node_id in (1, 2):
    print(node_id, s.Output.GetSupportReactions(node_id, lc))

s.Output.GetNodeDisplacements(16, lc)
```

`GetMemberEndForces(member, end, case, system)` uses end `0` start / `1` end and system `0` local / `1` global. The force vector is `[FX, FY, FZ, MX, MY, MZ]`. Support reactions use global axes. Node displacements are `[dx, dy, dz, rx, ry, rz]`.

## Selection

`GetSelectedBeams()` and `GetSelectedNodes()` return immediately. An empty list means nothing is selected. Do not wait in a loop.

```python
selected_beams = s.Geometry.GetSelectedBeams()
selected_nodes = s.Geometry.GetSelectedNodes()
if not selected_beams:
    raise RuntimeError("Select members in STAAD.Pro, then run this step again.")
```

## Groups

Select by direction, read the ids, then store them in a named group. Group type `2` is a member group. Other group-type codes are on the Bentley page for `CreateGroupEx`.

```python
from openstaadpy.os_analytical.oserrors import OsGroupAlreadyExists

s.View.SelectMembersParallelTo("X")     # "X", "Y", or "Z"
beams = s.Geometry.GetSelectedBeams()
if beams:
    try:
        s.Geometry.CreateGroupEx(2, "_ParallelX", beams)
    except OsGroupAlreadyExists:
        s.Geometry.UpdateGroup("_ParallelX", 0, beams)   # 0 replace, 1 remove, 2 append
    s.Geometry.ClearMemberSelection()

s.View.SelectGroup("_ParallelX")
s.Geometry.SelectMultipleBeams([1, 2, 3])
```

## Save and export

```python
s.SaveModel(True)

import os
csv_path = os.path.join(WORKSPACE_DIR, "reactions.csv")
```

`WORKSPACE_DIR` is injected by `python_executor`. Write reports there.

## Do not edit .std text unless the user supplied the exact edit

The `.std` command layout is easy to corrupt. Edit the text only when the user explicitly asks for that edit and states the exact change. Release the file lock first, then reconnect.

```python
from openstaadpy import os_analytical
import time

s = os_analytical.connect()
std_path = s.GetSTAADFile()
s.SaveModel(True)

s.CloseSTAADFile()
time.sleep(2)

with open(std_path, "r", encoding="utf-8", errors="ignore") as handle:
    lines = handle.readlines()
# Apply only the edit the user specified.
with open(std_path, "w", encoding="utf-8") as handle:
    handle.writelines(lines)

s = os_analytical.connect()
s.OpenSTAADFile(std_path)
print(s.GetSTAADFile())
print(s.Load.GetPrimaryLoadCaseNumbers())
```

`SaveModel(True)` must run before `CloseSTAADFile()`. The COM session is invalid after close, so call `connect()` again. Keep the two-second wait so Windows can release the file lock. The first `GetSTAADFile()` after `OpenSTAADFile()` can be empty while the model is still loading. Confirm the edit by reading a load case or a geometry query before continuing.
