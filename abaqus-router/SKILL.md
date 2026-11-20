---
name: abaqus
version: 1.0.4
display_name: Abaqus
display_name_en: Abaqus
description_zh: 提供对 Abaqus/SIMULIA 有限元分析全流程的自动化控制能力，涵盖几何建模、非线性材料、网格剖分、接触设定、分析步工况与求解计算及 ODB 后处理。
description_en: Provides comprehensive automation for SIMULIA Abaqus finite element analysis, covering geometry modeling, nonlinear materials, meshing, contact interactions, load steps, and ODB post-processing.
license: Apache-2.0
---
# Abaqus Finite Element Automation Guide (Abaqus Router)

## Milestone Workflow

Finite element automation tasks must proceed through distinct milestones:
```
Session Connect & Version Handshake -> Milestone Definition & Analysis Spec -> Consult Verified References
  -> Milestone Script Execution -> Physical Validation & Convergence Checks
```

### Step 1: Establish Connection and Version Verification

Establish communication with the Abaqus kernel in an isolated environment and verify the active version:

```python
import json
import os
from Agent import abaqus

connection = abaqus.connect(workspace_dir=os.getcwd())
print(json.dumps(connection, ensure_ascii=False, default=str))
```

If `ok` returns `false`, report the connection failure immediately.

### Step 2: Milestone Decomposition and Specification Management

Decompose complex simulations into distinct milestones. Execute only the milestone the user asked for. Do not continue into job submission, ODB reading, or closing Abaqus on your own.
- If the user names an existing model and that model is absent, report that and stop. Do not create a model with the same name.
- Check name collisions before creating an object. Do not overwrite an existing object unless the user asked for that.
- A full analysis, a job submit, or a pass/fail result needs one `analysis_spec` from `references/analysis-spec.md`. A query, a geometry-only edit, or a modeling step that does not submit a job does not. Record analysis type, units, materials, geometry, steps, boundary conditions, connections, loads, mesh, outputs, and acceptance criteria. On a validation failure, report the gaps. Do not invent a material, a unit system, a boundary condition, contact, `nlgeom`, or an acceptance limit.
- Run `scripts/spec_check.py` once after the analysis configuration is complete and before the first submit. Run it again only when the spec changes and a later submit or result check needs it. Stop on `FAIL` or `UNSUPPORTED`. Give `WARN` to the user with the evidence. Do not treat `WARN` as permission to edit the spec.

### Step 3: Script Assembly and Execution

Execute milestone scripts through `abaqus.execute`:

```python
import json
import os
from Agent import abaqus

abaqus_script = r'''
from abaqus import mdb, session
from abaqusConstants import *

# Milestone Abaqus kernel code
# model = mdb.models['Model-1']
# ...
'''

response = abaqus.execute(
    code=abaqus_script,
    timeout=120,
    workspace_dir=os.getcwd(),
)
print(json.dumps(response, ensure_ascii=False, default=str))
```

**Execution Guidelines**:
- Import `abaqusConstants` explicitly. Import `abaqus` or `odbAccess` only when that milestone uses them.
- Names passed to Abaqus `name=` follow CAE naming rules. A name the kernel accepts but the GUI tree hides is not success. Do not invent `_name`, `name_`, or `__name`.
- A write that the user does not need data from should not define `result`. When data is required, return only that structure.
- A mesh milestone reads `getMeshControl` on the target region and, after generation, `element.type` and `getMeshStats`. `setElementType` returning without error does not prove the element type. Do not infer a structured mesh from a cell's face count. The rules are in `references/mesh.md`.
- A long script may be a plain `.py` file passed as `abaqus.execute(file_path=..., workspace_dir=os.getcwd(), timeout=...)`.
- `timeout` limits that script call. It does not wait for a solver.
- Confirm method and repository names in the installed Scripting Reference (`abaqus doc` or https://help.3ds.com/) before writing them. Calls look like `receiver.name(...)`, including selectors such as `FaceArray.getByBoundingBox(...)`. Repositories such as `Part.faces` and `Part.cells` are not calls. Typical build calls are `Mdb.Model`, `Model.ConstrainedSketch`, `ConstrainedSketch.rectangle`, `Model.Part`, and `Part.BaseSolidExtrude`.

### Step 4: Response Parsing and Diagnostics

- Judge the call with the top-level `ok` and `error`. The inner `result` is business data only.
- After a successful milestone, stop. Do not take a screenshot, walk the whole model, or run a second script to repeat the check.
- On failure, do not retry automatically. Read `error.recovery` for the real object type, available members, call signature, close keyword names, and repository keys. If that evidence locates the bad name or argument, report it. Confirm the symbol once in the Scripting Reference. If the failure may already have written objects, query those objects once and stop.

## Rules & Environment Governance

### Model State and File Protection
- Generic Python variables expire after each execution turn, but Abaqus kernel state in `mdb` and `session` persists.
- Identify objects that already exist so the next script does not create duplicates. That is not permission to overwrite or delete them.
- Overwriting `.cae`, `.inp`, or `.odb`, deleting an existing object, or closing Abaqus requires the user to have asked for that action.
- If a new-object script may have written only part of its work, record the objects created in that same script and roll back only objects you can show belong to this run.

### Job Dispatch and Results Processing
- Before submit, run a read-only `scripts/model_reader.py --model MODEL` and compare repositories, materials, sections, steps, and set or surface entity counts with `analysis_spec`. Do not submit an empty region or a missing object.
- The submit milestone only calls `job.submit()` and returns `job_name`, `status`, and `odb_path`. Do not call `job.waitForCompletion()` and do not poll in a loop.
- A later milestone may call `scripts/model_reader.py --job JOB` once for status and `.sta`, `.msg`, `.dat`, and `.log`. If the job is not finished, report the status and stop.
- Open the ODB only when the status is `COMPLETED`. Add `--odb PATH` to the same inspector, list the real steps, frames, field outputs, components, invariants, and history outputs, and only then extract.
- A claim that a result is acceptable uses `references/result-evidence-gates.md`, writes `result_evidence`, and runs `scripts/evidence_check.py`. A `COMPLETED` job alone is not that claim.

`scripts/spec_check.py` calls `scripts/spec_shape.py` for the schema and CAE names, then `scripts/spec_rules.py` for the analysis-type rules. `scripts/evidence_check.py` uses that same review before it scores gates. `scripts/model_reader.py` sends `scripts/model_reader_kernel.py` into the Abaqus kernel as one read-only call. Run the kernel only through the reader. A bare `python` of each host script, with no arguments, is a self-check and exits 0.

### Consistent Physical Unit Systems
Abaqus does not convert physical units internally; all numerical inputs must be dimensionally consistent:
- A geometry-only task with no stated length unit is millimetres. Do not ask the user to choose N-mm or kN-mm for that task.
- An existing model keeps the unit convention already in the model.
- A new model that needs materials, density, loads, time, or result interpretation, and does not state a unit system, needs one consistent system from the user before those values are written.
- A common millimetre system is length in mm, force in N, mass in tonne, stress in MPa, steel density `7.85e-9` tonne/mm^3, and gravity `9800` mm/s^2. N-mm and kN-mm are project conventions, not Abaqus switches.
- State the unit convention in the reply.

### Reference Document Index
Read specific references on demand:
- Geometry and CAD import: `references/geometry.md`
- Materials & sections: `references/material.md`
- Boundary conditions & constraints: `references/bc.md`
- Loads & gravity fields: `references/load.md`
- Analysis steps & nonlinear controls: `references/step.md`
- Mesh controls & element types: `references/mesh.md`
- Static analysis: `references/static-analysis.md`
- Frequency extraction: `references/modal-analysis.md`
- Contact pairs, general contact, initial gaps, and contact output: `references/contact-analysis.md`
- Implicit or explicit dynamics, initial velocity, mass scaling, and energy: `references/dynamic-analysis.md`
- Steady or transient heat transfer: `references/thermal-analysis.md`
- Sequential and fully coupled temperature-displacement: `references/coupled-analysis.md`
- Field and history output requests: `references/output-requests.md`
- ODB step, frame, region, invariant, and evidence extraction: `references/odb-results.md`
- Read-only model, job, and ODB inspection: `references/inspectors.md`
- Troubleshooting: `references/troubleshooting.md`

---

## Official Documentation & Upstream API Sources

When looking up advanced nonlinear solver controls, complex material subroutines (UMAT/VUMAT), or fine-grained ODB field output parameters, refer to the official Dassault Systèmes SIMULIA documentation:

- **Dassault Systèmes User Assistance Portal**: [https://help.3ds.com/](https://help.3ds.com/)
  - Direct search queries: *Abaqus Scripting Reference Guide*, *Abaqus Python Development Guide*
- **SIMULIA Official Community & Documentation**: [https://www.3ds.com/support/documentation/](https://www.3ds.com/support/documentation/)
- **Installed product help**: run `abaqus doc` on a machine where Abaqus is installed. That command opens Dassault's product help. This skill package does not contain a copy of that help or a scripting lookup tool.

---

## Intellectual Property & Interoperability Notice

This skill provides open procedural automation workflows, interface scripts, and reference documentation for structural engineering and computational design. All third-party product names, software titles, registered trademarks, and logos referenced herein are the intellectual property of their respective owners. Mention of these systems is made solely for technical interoperability, compatibility identification, and execution routing. Use of this skill implies no affiliation, endorsement, sponsorship, or intellectual property rights claim.
