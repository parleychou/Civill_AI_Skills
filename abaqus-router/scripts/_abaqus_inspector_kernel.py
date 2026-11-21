# -*- coding: utf-8 -*-
"""Read-only inspectors executed inside the Abaqus Python kernel.

Keep this file compatible with the Abaqus interpreter. The agent-side wrapper
prefixes ``inspection_request`` and sends the complete source in one execution.
"""

# Abaqus repositories are opaque proxy objects whose attribute/iteration
# failures are not exposed as one stable exception class across releases.
# io.open and str.format keep this injected kernel compatible with older CAE Python.
# ruff: noqa: BLE001, C402, S110, SIM118, UP020, UP030, UP032

import io
import os


def _safe_attr(obj, name, default=None):
    """安全读取 Abaqus 代理对象属性，访问失败时返回默认值。"""
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _safe_len(value):
    """安全取得代理集合长度，无法读取时按零处理。"""
    try:
        return len(value)
    except Exception:
        return 0


def _repo_keys(repo):
    """安全读取并排序 Abaqus repository 的字符串键。"""
    try:
        return sorted([str(key) for key in repo.keys()])
    except Exception:
        return []


def _limited(values, maximum):
    """生成带总数和截断标记的限量列表。"""
    items = list(values)
    return {
        "count": len(items),
        "items": items[:maximum],
        "truncated": len(items) > maximum,
    }


def _class_name(value):
    """返回代理对象的运行时类名，并兼容属性访问异常。"""
    try:
        return value.__class__.__name__
    except Exception:
        return type(value).__name__


def _region_counts(region):
    """统计区域中的几何实体、节点和单元数量。"""
    names = (
        "vertices",
        "edges",
        "faces",
        "cells",
        "nodes",
        "elements",
        "referencePoints",
    )
    return dict((name, _safe_len(_safe_attr(region, name, ()))) for name in names)


def _region_repo(repo, maximum):
    """汇总 Set 或 Surface repository 中各区域的实体数量。"""
    output = {}
    names = _repo_keys(repo)
    for name in names[:maximum]:
        try:
            output[name] = _region_counts(repo[name])
        except Exception as error:
            output[name] = {"error": str(error)}
    return {
        "count": len(names),
        "items": output,
        "truncated": len(names) > maximum,
    }


def _typed_repo(repo, maximum):
    """列出 repository 对象的名称、类型及关联区域。"""
    output = []
    names = _repo_keys(repo)
    for name in names[:maximum]:
        try:
            item = repo[name]
            output.append(
                {
                    "name": name,
                    "type": _class_name(item),
                    "create_step": str(_safe_attr(item, "createStepName", "")),
                }
            )
        except Exception as error:
            output.append({"name": name, "error": str(error)})
    return {
        "count": len(names),
        "items": output,
        "truncated": len(names) > maximum,
    }


def _element_type_inventory(part, maximum):
    """扫描 Part 已生成单元并统计实际单元类型。"""
    elements = _safe_attr(part, "elements", ())
    total = _safe_len(elements)
    scan_limit = max(10000, maximum * 1000)
    counts = {}
    scanned = 0
    error_text = ""
    try:
        for element in elements:
            if scanned >= scan_limit:
                break
            element_type = str(_safe_attr(element, "type", "")) or "UNKNOWN"
            counts[element_type] = counts.get(element_type, 0) + 1
            scanned += 1
    except Exception as error:
        error_text = str(error)
    report = {
        "total_elements": total,
        "scanned_elements": scanned,
        "items": [{"type": name, "count": counts[name]} for name in sorted(counts)],
        "truncated": scanned < total,
    }
    if error_text:
        report["error"] = error_text
    return report


def _mesh_control_inventory(part, maximum):
    """读取 Part 各 Cell 或 Face 的网格控制参数。"""
    get_mesh_control = _safe_attr(part, "getMeshControl")
    if not callable(get_mesh_control):
        return {"status": "UNAVAILABLE"}
    try:
        from abaqusConstants import ALGORITHM, ELEM_SHAPE, MIN_TRANSITION, TECHNIQUE
    except Exception as error:
        return {"status": "UNAVAILABLE", "error": str(error)}

    cells = _safe_attr(part, "cells", ())
    faces = _safe_attr(part, "faces", ())
    if _safe_len(cells):
        region_kind = "CELL"
        regions = cells
    elif _safe_len(faces):
        region_kind = "FACE"
        regions = faces
    else:
        return {"status": "EMPTY", "region_kind": "NONE", "region_count": 0}

    attributes = (
        ("elem_shape", ELEM_SHAPE),
        ("technique", TECHNIQUE),
        ("algorithm", ALGORITHM),
        ("min_transition", MIN_TRANSITION),
    )
    combinations = {}
    errors = []
    inspected = 0
    for index, region in enumerate(regions):
        if inspected >= maximum:
            break
        values = {}
        try:
            for name, attribute in attributes:
                values[name] = str(get_mesh_control(region=region, attribute=attribute))
            key = tuple(values[name] for name, _ in attributes)
            combinations[key] = combinations.get(key, 0) + 1
        except Exception as error:
            errors.append({"region_index": index, "error": str(error)})
        inspected += 1

    items = []
    for key in sorted(combinations):
        item = dict((attributes[index][0], value) for index, value in enumerate(key))
        item["region_count"] = combinations[key]
        items.append(item)
    report = {
        "status": "OK" if not errors else "PARTIAL",
        "region_kind": region_kind,
        "region_count": _safe_len(regions),
        "inspected_regions": inspected,
        "items": items,
        "truncated": inspected < _safe_len(regions),
    }
    if errors:
        report["errors"] = errors[:maximum]
    return report


def _mesh_stats_inventory(part):
    """调用 ``getMeshStats`` 返回 Part 的实际网格统计。"""
    get_mesh_stats = _safe_attr(part, "getMeshStats")
    if not callable(get_mesh_stats):
        return {"status": "UNAVAILABLE"}
    cells = _safe_attr(part, "cells", ())
    faces = _safe_attr(part, "faces", ())
    if _safe_len(cells):
        region_kind = "CELL"
        regions = cells
    elif _safe_len(faces):
        region_kind = "FACE"
        regions = faces
    else:
        return {"status": "EMPTY", "region_kind": "NONE"}
    try:
        stats = get_mesh_stats(regions=(regions,))
    except Exception as error:
        return {"status": "ERROR", "region_kind": region_kind, "error": str(error)}

    report = {"status": "OK", "region_kind": region_kind}
    for name in (
        "numNodes",
        "numHexElems",
        "numWedgeElems",
        "numPyramidElems",
        "numTetElems",
        "numQuadElems",
        "numTriElems",
        "numMeshedRegions",
    ):
        value = _safe_attr(stats, name)
        if value is not None:
            report[name] = value
    return report


def _mesh_inventory(part, maximum):
    """组合单元类型、网格控制和网格统计三类证据。"""
    return {
        "element_types": _element_type_inventory(part, maximum),
        "controls": _mesh_control_inventory(part, maximum),
        "stats": _mesh_stats_inventory(part),
    }


def _part_inventory(part, maximum):
    """汇总一个 Part 的实体数量、截面指派、集合和网格状态。"""
    section_assignments = []
    for assignment in list(_safe_attr(part, "sectionAssignments", ()) or ())[:maximum]:
        region = _safe_attr(assignment, "region")
        section_assignments.append(
            {
                "section_name": str(_safe_attr(assignment, "sectionName", "")),
                "region_name": str(_safe_attr(region, "name", "")),
            }
        )
    return {
        "type": _class_name(part),
        "dimensionality": str(_safe_attr(part, "dimensionality", "")),
        "body_type": str(_safe_attr(part, "type", "")),
        "counts": _region_counts(part),
        "sets": _region_repo(_safe_attr(part, "sets", {}), maximum),
        "surfaces": _region_repo(_safe_attr(part, "surfaces", {}), maximum),
        "section_assignments": section_assignments,
        "mesh": _mesh_inventory(part, maximum),
    }


def _instance_inventory(instance, maximum):
    """汇总一个 Assembly Instance 的依赖关系、实体数量和集合。"""
    return {
        "type": _class_name(instance),
        "part_name": str(_safe_attr(instance, "partName", "")),
        "dependent": str(_safe_attr(instance, "dependent", "")),
        "counts": _region_counts(instance),
        "sets": _region_repo(_safe_attr(instance, "sets", {}), maximum),
        "surfaces": _region_repo(_safe_attr(instance, "surfaces", {}), maximum),
    }


def inspect_model(mdb, model_name, maximum):
    """列出模型或检查指定模型的仓库、Part、Instance 和分析对象。"""
    model_names = _repo_keys(_safe_attr(mdb, "models", {}))
    report = {"available_models": model_names, "selected_model": None}
    if not model_name:
        report["status"] = "LISTED"
        return report
    if model_name not in model_names:
        report["status"] = "NOT_FOUND"
        report["error"] = "model does not exist: {0}".format(model_name)
        return report

    model = mdb.models[model_name]
    repositories = {}
    for name in (
        "materials",
        "sections",
        "steps",
        "boundaryConditions",
        "loads",
        "interactions",
        "interactionProperties",
        "constraints",
        "fieldOutputRequests",
        "historyOutputRequests",
        "amplitudes",
    ):
        repositories[name] = _typed_repo(_safe_attr(model, name, {}), maximum)

    parts = {}
    part_names = _repo_keys(_safe_attr(model, "parts", {}))
    for name in part_names[:maximum]:
        parts[name] = _part_inventory(model.parts[name], maximum)

    assembly = _safe_attr(model, "rootAssembly")
    instances = {}
    instance_names = _repo_keys(_safe_attr(assembly, "instances", {}))
    for name in instance_names[:maximum]:
        instances[name] = _instance_inventory(assembly.instances[name], maximum)
    assembly_report = {
        "instances": {
            "count": len(instance_names),
            "items": instances,
            "truncated": len(instance_names) > maximum,
        },
        "sets": _region_repo(_safe_attr(assembly, "sets", {}), maximum),
        "surfaces": _region_repo(_safe_attr(assembly, "surfaces", {}), maximum),
    }
    report.update(
        {
            "status": "OK",
            "selected_model": model_name,
            "repositories": repositories,
            "parts": {
                "count": len(part_names),
                "items": parts,
                "truncated": len(part_names) > maximum,
            },
            "root_assembly": assembly_report,
        }
    )
    return report


def _decode_tail(data):
    """依次尝试常见编码，将日志尾部字节转换为文本。"""
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(encoding)
        except Exception:
            pass
    return data.decode("latin-1", "replace")


def _log_diagnostic(path, maximum_lines):
    """读取求解日志尾部，并返回文件状态和限量行内容。"""
    if not os.path.isfile(path):
        return {"exists": False, "path": os.path.abspath(path)}
    size = os.path.getsize(path)
    with io.open(path, "rb") as stream:
        if size > 262144:
            stream.seek(size - 262144)
        text = _decode_tail(stream.read())
    lines = text.splitlines()
    diagnostic = [
        line
        for line in lines
        if any(word in line.upper() for word in ("ERROR", "WARNING", "FATAL", "ABORT", "TERMINAT"))
    ]
    return {
        "exists": True,
        "path": os.path.abspath(path),
        "size_bytes": size,
        "tail": lines[-maximum_lines:],
        "diagnostic_lines": diagnostic[-maximum_lines:],
        "truncated": len(lines) > maximum_lines,
    }


def _job_messages(job, maximum):
    """提取 Abaqus Job 对象最近的消息记录。"""
    messages = []
    try:
        raw_messages = list(job.messages)
    except Exception:
        raw_messages = []
    for message in raw_messages[-maximum:]:
        messages.append(
            {
                "type": str(_safe_attr(message, "type", "")),
                "text": str(_safe_attr(message, "data", _safe_attr(message, "message", message))),
            }
        )
    return messages


def inspect_job(mdb, job_name, workspace_dir, maximum_lines):
    """列出 Job 或检查指定 Job 的状态、消息和诊断文件。"""
    job_names = _repo_keys(_safe_attr(mdb, "jobs", {}))
    report = {"available_jobs": job_names, "selected_job": None}
    if not job_name:
        report["status"] = "LISTED"
        return report
    if job_name not in job_names:
        report["status"] = "NOT_FOUND"
        report["error"] = "job does not exist: {0}".format(job_name)
        return report

    job = mdb.jobs[job_name]
    work_dir = os.path.abspath(workspace_dir or os.getcwd())
    files = {}
    for extension in ("sta", "msg", "dat", "log"):
        files[extension] = _log_diagnostic(
            os.path.join(work_dir, job_name + "." + extension), maximum_lines
        )
    report.update(
        {
            "status": "OK",
            "selected_job": job_name,
            "job_status": str(_safe_attr(job, "status", "UNKNOWN")),
            "model": str(_safe_attr(job, "model", "")),
            "type": _class_name(job),
            "num_cpus": _safe_attr(job, "numCpus"),
            "memory": _safe_attr(job, "memory"),
            "memory_units": str(_safe_attr(job, "memoryUnits", "")),
            "messages": _job_messages(job, maximum_lines),
            "diagnostic_files": files,
        }
    )
    return report


def _frame_metadata(frame, index):
    """提取一个 ODB Frame 的索引、增量和值等基本元数据。"""
    return {
        "index": index,
        "frame_id": _safe_attr(frame, "frameId"),
        "increment_number": _safe_attr(frame, "incrementNumber"),
        "frame_value": _safe_attr(frame, "frameValue"),
        "mode": _safe_attr(frame, "mode"),
        "frequency": _safe_attr(frame, "frequency"),
        "description": str(_safe_attr(frame, "description", "")),
    }


def _field_catalog(frames, maximum):
    """跨 Frame 汇总 Field Output、分量和有效不变量。"""
    catalog = {}
    for frame_index, frame in enumerate(frames):
        field_outputs = _safe_attr(frame, "fieldOutputs", {})
        for name in _repo_keys(field_outputs):
            field = field_outputs[name]
            entry = catalog.setdefault(
                name,
                {
                    "frame_count": 0,
                    "first_frame": frame_index,
                    "last_frame": frame_index,
                    "types": set(),
                    "component_labels": set(),
                    "valid_invariants": set(),
                    "positions": set(),
                },
            )
            entry["frame_count"] += 1
            entry["last_frame"] = frame_index
            entry["types"].add(str(_safe_attr(field, "type", "")))
            for label in list(_safe_attr(field, "componentLabels", ()) or ()):
                entry["component_labels"].add(str(label))
            for invariant in list(_safe_attr(field, "validInvariants", ()) or ()):
                entry["valid_invariants"].add(str(invariant))
            for location in list(_safe_attr(field, "locations", ()) or ()):
                entry["positions"].add(str(_safe_attr(location, "position", "")))
    output = []
    names = sorted(catalog)
    for name in names[:maximum]:
        entry = catalog[name]
        output.append(
            {
                "name": name,
                "frame_count": entry["frame_count"],
                "first_frame": entry["first_frame"],
                "last_frame": entry["last_frame"],
                "types": sorted(entry["types"]),
                "component_labels": sorted(entry["component_labels"]),
                "valid_invariants": sorted(entry["valid_invariants"]),
                "positions": sorted(entry["positions"]),
            }
        )
    return {"count": len(names), "items": output, "truncated": len(names) > maximum}


def _history_catalog(step, maximum):
    """汇总一个 ODB Step 中的 History Region 和输出变量。"""
    regions = []
    names = _repo_keys(_safe_attr(step, "historyRegions", {}))
    for name in names[:maximum]:
        region = step.historyRegions[name]
        outputs = _repo_keys(_safe_attr(region, "historyOutputs", {}))
        regions.append(
            {
                "name": name,
                "description": str(_safe_attr(region, "description", "")),
                "position": str(_safe_attr(region, "position", "")),
                "outputs": _limited(outputs, maximum),
            }
        )
    return {"count": len(names), "items": regions, "truncated": len(names) > maximum}


def _odb_region_inventory(assembly, maximum):
    """汇总 ODB 根装配中的 Instance、Set 和 Surface 区域。"""
    instances = []
    names = _repo_keys(_safe_attr(assembly, "instances", {}))
    for name in names[:maximum]:
        instance = assembly.instances[name]
        instances.append(
            {
                "name": name,
                "nodes": _safe_len(_safe_attr(instance, "nodes", ())),
                "elements": _safe_len(_safe_attr(instance, "elements", ())),
                "node_sets": _limited(_repo_keys(_safe_attr(instance, "nodeSets", {})), maximum),
                "element_sets": _limited(
                    _repo_keys(_safe_attr(instance, "elementSets", {})), maximum
                ),
                "surfaces": _limited(_repo_keys(_safe_attr(instance, "surfaces", {})), maximum),
            }
        )
    return {
        "instances": {"count": len(names), "items": instances, "truncated": len(names) > maximum},
        "node_sets": _limited(_repo_keys(_safe_attr(assembly, "nodeSets", {})), maximum),
        "element_sets": _limited(_repo_keys(_safe_attr(assembly, "elementSets", {})), maximum),
        "surfaces": _limited(_repo_keys(_safe_attr(assembly, "surfaces", {})), maximum),
    }


def inspect_odb(odb_path, open_odb, maximum):
    """只读打开 ODB，列出 Step、Frame、输出字段和区域清单。"""
    absolute_path = os.path.abspath(odb_path)
    if not os.path.isfile(absolute_path):
        return {"status": "NOT_FOUND", "path": absolute_path, "error": "ODB file does not exist"}
    odb = open_odb(path=absolute_path, readOnly=True)
    try:
        steps = []
        step_names = _repo_keys(_safe_attr(odb, "steps", {}))
        for name in step_names[:maximum]:
            step = odb.steps[name]
            frames = list(_safe_attr(step, "frames", ()) or ())
            frame_samples = []
            if frames:
                frame_samples.append(_frame_metadata(frames[0], 0))
                if len(frames) > 1:
                    frame_samples.append(_frame_metadata(frames[-1], len(frames) - 1))
            steps.append(
                {
                    "name": name,
                    "procedure": str(_safe_attr(step, "procedure", "")),
                    "domain": str(_safe_attr(step, "domain", "")),
                    "time_period": _safe_attr(step, "timePeriod"),
                    "frame_count": len(frames),
                    "frame_samples": frame_samples,
                    "field_outputs": _field_catalog(frames, maximum),
                    "history_regions": _history_catalog(step, maximum),
                }
            )
        diagnostic = _safe_attr(odb, "diagnosticData")
        diagnostic_data = {}
        for name in (
            "jobStatus",
            "analysisErrors",
            "analysisWarnings",
            "numberOfAnalysisErrors",
            "numberOfAnalysisWarnings",
        ):
            value = _safe_attr(diagnostic, name)
            if value is not None:
                diagnostic_data[name] = str(value)
        return {
            "status": "OK",
            "path": absolute_path,
            "name": str(_safe_attr(odb, "name", "")),
            "analysis_title": str(_safe_attr(odb, "analysisTitle", "")),
            "description": str(_safe_attr(odb, "description", "")),
            "diagnostic_data": diagnostic_data,
            "root_assembly": _odb_region_inventory(odb.rootAssembly, maximum),
            "steps": {
                "count": len(step_names),
                "items": steps,
                "truncated": len(step_names) > maximum,
            },
        }
    finally:
        odb.close()


def inspect_abaqus(request):
    """根据统一请求依次执行模型、Job 和 ODB 检查。"""
    from abaqus import mdb

    maximum = max(1, min(int(request.get("max_items", 200)), 1000))
    maximum_lines = max(1, min(int(request.get("max_log_lines", 40)), 200))
    report = {
        "read_only": True,
        "model": inspect_model(mdb, request.get("model"), maximum),
        "job": inspect_job(
            mdb,
            request.get("job"),
            request.get("workspace_dir"),
            maximum_lines,
        ),
        "odb": {"status": "NOT_REQUESTED"},
    }
    if request.get("odb_path"):
        from odbAccess import openOdb

        report["odb"] = inspect_odb(request["odb_path"], openOdb, maximum)
    statuses = [report[name]["status"] for name in ("model", "job", "odb")]
    if "NOT_FOUND" in statuses:
        report["status"] = "PARTIAL"
    else:
        report["status"] = "OK"
    return report


if "inspection_request" in globals():
    result = inspect_abaqus(globals()["inspection_request"])
