# Abaqus troubleshooting

Confirm method names, argument counts, and types in the installed Abaqus Scripting Reference. Open it with `abaqus doc`, or search the Abaqus Scripting Reference on https://help.3ds.com/. This skill does not include a scripting lookup script or a versioned API file.

## Connection errors

| Error | Cause | Action |
|------|------|------|
| Abaqus installation was not found | Abaqus is not installed or is not on `PATH` | Install Abaqus, or set the `ABAQUS_COMMAND` environment variable |
| Abaqus failed to start or connect | Installation, license, or process state | Keep the original error. Do not start Abaqus again until the cause is fixed |
| More than one Abaqus/CAE process is running | The session cannot choose an instance | Close the extra Abaqus/CAE processes and retry |
| "request did not complete" | The request timed out | Record `request_id`, inspect the model, and do not replay the write blindly |

## Python API errors

### KeyError — missing key

```
KeyError: 'badKey'
```

Use the available keys and close matches reported with the error. Do not invent a repository name.

### AttributeError — missing attribute or method

```
AttributeError: 'Material' object has no attribute 'Elestic'
```

Read `error.recovery` on the `abaqus.execute` response for the real object type and `possible_members`. Then open the Scripting Reference page for that type and choose a member that the page actually lists. A misspelled name such as `Elestic` is not repaired by trying nearby spellings.

### NameError — missing import

```
NameError: name 'THREE_D' is not defined
```

Add `from abaqusConstants import *` in the Abaqus script.

### TypeError — wrong arguments

```
TypeError: unexpected keyword argument 'E'
```

Stop guessing keywords. Read `callable_signature` and `possible_keywords` from `error.recovery` when that response includes them. If the overload is still incomplete, open the Scripting Reference page for `Receiver.method` and use only the arguments listed there.

## Convergence

| Symptom | Likely cause | Action |
|------|----------|------|
| Too many increment attempts | Increment is too large, or the nonlinearity is strong | Reduce `initialInc` and raise `maxNumInc` |
| Rigid-body motion (numerical singularity) | Constraints are incomplete | Add the missing constraints and check for disconnected parts |
| Negative eigenvalues | Local instability or incomplete constraints | Add stabilization only with a recorded reason, and check contact |
| Excessive local plastic strain | Mesh is too coarse, or the load is too large | Refine the mesh and apply the load in steps |

## Modeling mistakes

| Mistake | Correction |
|------|------|
| Section was never assigned | `part.SectionAssignment(region=..., sectionName=...)` |
| Modal analysis material has no density | `mat.Density(table=((7.85e-9,),))` in a consistent unit system |
| Job submitted before it exists | Create `mdb.Job(name=..., model=...)` first |
| ODB has no result frames after submit | The job is still `SUBMITTED` or `RUNNING`, or it `ABORTED` / `TERMINATED`. Read `job.status` once. Open the ODB only when the status is `COMPLETED`. On failure, read `.dat`, `.msg`, and `.sta` |
| Mixed unit systems | Abaqus has no unit switch. Keep one consistent system from the first material, load, and time value |
| Hard-coded coordinates | Prefer `part.sets['MySet']` over `findAt((x, y, z))` when a set already exists |

## Debugging rules

1. An exception is not the Scripting Reference. Use it to locate the failure, then confirm the symbol in `abaqus doc` or on https://help.3ds.com/.
2. Build the model in milestones. Query an existing model with a separate read-only script before editing it.
3. Reference notes do not prove that a region, geometric selection, or solver path is correct. Split a complex task into milestones that can be observed.
4. On `KeyError`, `AttributeError`, or `TypeError`, use the runtime evidence once, then check the Scripting Reference once. Do not repeat the same call with guessed names.
