---
name: tekla
version: 1.0.5
display_name: Tekla
display_name_en: Tekla
description_zh: 实现对活动状态下 Tekla Structures 实例的编程控制与模型交互，支持结构构件建模、节点细部连接及工程出图。
description_en: Provides programmatic control and model interaction with active Tekla Structures instances, supporting structural modeling, steel detailing, and automated drawings.
license: Apache-2.0
---
# Tekla Structures Automation Guide (Tekla Router)

## Automated Execution Workflow

```
Attach to Running Tekla Instance -> Detect Active Release Year -> Consult Verified Code Patterns
  -> Construct Strongly-Typed CLR Invocations -> Execute Modeling/Detailing -> Validate Results
```

1. **Verified Code Patterns**:
   - For general structural modeling (beams, columns, slabs, contour plates): read `references/common_examples.md`.
   - For steel detailing, connections, macros, and custom components: read `references/component_workflow.md`.
2. **API Specification Verification**:
   - For specialized methods, events, or overload signatures, refer directly to the [Tekla Developer Center Open API Reference](https://developer.tekla.com/tekla-structures/api-reference).

## 1. Connecting to the Tekla Process

Communication with the Tekla process is established within the execution environment (`python_executor`). The worker process persists across calls within the same session; loaded CLR runtimes, referenced assemblies, and connection handles remain valid for subsequent calls.

```python
from Agent.software_link_kit.tekla import connect_tekla

tekla = connect_tekla()
model = tekla.model
print({
    "connected": model.GetConnectionStatus(),
    "version": tekla.program_version,
    "api_year": tekla.api_year
})
```

**Connection Management Guidelines**:
- **Attach to Running Instances Only**: The system connects exclusively to an already running Tekla process with an open model; it does not launch new software instances automatically.
- **Isolated Assembly Loading**: `connect_tekla()` automatically detects the release year of the active instance, loads assemblies using absolute program paths, and verifies version integrity. Do not call `clr.AddReference(...)` manually in workspace scripts to prevent assembly version mismatches. Once connected, import target types directly via `from Tekla... import ...`.
- **Handle Reuse**: Check `model.GetConnectionStatus()` prior to executing subsequent scripts. When it returns `True`, reuse the existing handle without reinitializing the CLR; if `False`, retry `connect_tekla()` once. If connection fails again, abort and notify the user rather than entering an infinite retry loop.

## 2. Version Alignment and Runtime Constraints

- **Supported Releases**: Tekla Structures 2020 through 2026. Do not write calls while `api_year` is unknown. Outside that range, stop and tell the user. With explicit permission, an adjacent release's documentation may be read as a hint. It is not permission to insert, modify, or delete, because members and overloads differ.
- **Lookup**: Confirm a type, member, and overload at https://developer.tekla.com/tekla-structures/api-reference and in the XML documentation installed with that Tekla release. Do not infer a member from a similar name. Examples in this skill only show call order.
- **Useful symbols to confirm before use**: `ModelObjectSelector.GetAllObjects`, `ModelObject.GetReportProperty`, `ModelObject.GetUserProperty`, and `Part.Name`. Report and user properties are not the same call.

## 3. Reliable Execution Lifecycle

### 3.1 Define Operational Boundaries and Success Criteria
Determine whether the task is read-only or mutative. Read-only tasks must never call `Insert()`, `Modify()`, `Delete()`, or `CommitChanges()`. For mutative modeling tasks, adhere to catalog selection, commit transactions, resource disposal, and metric unit rules in `references/common_examples.md`.

### 3.2 Validate API Contracts
Rely on verified signatures from `references/common_examples.md` and the official developer reference. Verify declaring types, argument types, return values, exceptions, and preconditions. Never guess interfaces from similar names or intuition.

### 3.3 Construct Strongly-Typed CLR Invocations
- Pass genuine .NET enum instances rather than raw integers;
- Differentiate between Python `type` and .NET `System.Type`;
- Correctly initialize strongly-typed arrays, coordinate points, and related CLR objects.

### 3.4 Incremental Verification Before Batch Execution
For complex or bulk operations, validate end-to-end connectivity, return types, and observable changes on a single object or minimal test region first. Never run untested batch scripts directly against the full model. Record object IDs and stack traces on partial failures.

### 3.5 Verify Outcomes
Script completion without exceptions means the script finished. It does not mean the task succeeded. Check the boolean returns, object counts, and a query of the objects you changed.
An empty result, a zero, or a count that is far too small is not proof that the model has no data. Check the connection, the selector, filters, and whether the model has been committed. Do not hide a failure with `except Exception: pass`, an empty string, or zero unless that API documents the value as optional.
A conclusion covers only the objects you actually checked. A partial failure stays in the report. A guess is not an API fact.

---

## 4. Local scripts

`scripts/find_install.py` locates the bin directory of a running Tekla, then the registry, then common install folders. With no arguments and no Tekla install it prints a self-check and exits 0. `--require`, `--path`, and `--force` still exit 2 when the install cannot be resolved. `scripts/session.py` loads the assemblies for that bin and exposes `connect_tekla()`. The normal connection from a task remains `Agent.software_link_kit.tekla.connect_tekla`. `scripts/read_probe.py` prints the read-only symbol list and the empty-result rule. Pass `--run` only when a model is already open. It counts objects and does not insert, modify, or delete.

## Official Documentation & Upstream API Sources

When requiring deeper API context, architectural release notes, or when looking up specialized interfaces, refer to the official Trimble Tekla documentation sources:

- **Tekla Developer Center (Open API Reference)**: [https://developer.tekla.com/tekla-structures/api-reference](https://developer.tekla.com/tekla-structures/api-reference)
- **Tekla Open API Documentation & Guides**: [https://developer.tekla.com/tekla-structures/documentation](https://developer.tekla.com/tekla-structures/documentation)
- **Trimble Solutions Corporation GitHub Samples**: [https://github.com/TrimbleSolutionsCorporation](https://github.com/TrimbleSolutionsCorporation)
- **Local Installed Primary Material**: Assembly XML documentation files shipped within the Tekla Structures installation directory:
  - `<TEKLA_DIR>\bin\Tekla.Structures.Model.xml`
  - `<TEKLA_DIR>\bin\Tekla.Structures.Drawing.xml`

---

## Intellectual Property & Interoperability Notice

This skill provides open procedural automation workflows, interface scripts, and reference documentation for structural engineering and computational design. All third-party product names, software titles, registered trademarks, and logos referenced herein are the intellectual property of their respective owners. Mention of these systems is made solely for technical interoperability, compatibility identification, and execution routing. Use of this skill implies no affiliation, endorsement, sponsorship, or intellectual property rights claim.
