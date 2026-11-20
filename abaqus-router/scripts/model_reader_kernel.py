# -*- coding: utf-8 -*-
"""Read-only model, job, and ODB inventory for the Abaqus/CAE kernel.

The host prefixes ``inspection_request`` and sends this source in one call.
Keep the file free of host-package imports. Repository proxies do not share
one exception type across releases, so each read is guarded.
io.open and str.format stay compatible with older CAE Python.
"""

import io
import os


def _attr(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _length(value):
    try:
        return len(value)
    except Exception:
        return 0


def _keys(repo):
    try:
        return sorted([str(key) for key in repo.keys()])
    except Exception:
        return []


def _window(values, maximum):
    items = list(values)
    return {
        "count": len(items),
        "items": items[:maximum],
        "truncated": len(items) > maximum,
    }


def _type_name(value):
    try:
        return value.__class__.__name__
    except Exception:
        return type(value).__name__


_ENTITY_NAMES = (
    "vertices",
    "edges",
    "faces",
    "cells",
    "nodes",
    "elements",
    "referencePoints",
)


def _entity_counts(region):
    return dict((name, _length(_attr(region, name, ()))) for name in _ENTITY_NAMES)


def _region_index(repo, maximum):
    output = {}
    names = _keys(repo)
    for name in names[:maximum]:
        try:
            output[name] = _entity_counts(repo[name])
        except Exception as error:
            output[name] = {"error": str(error)}
    return {
        "count": len(names),
        "items": output,
        "truncated": len(names) > maximum,
    }


def _typed_index(repo, maximum):
    output = []
    names = _keys(repo)
    for name in names[:maximum]:
        try:
            item = repo[name]
            output.append(
                {
                    "name": name,
                    "type": _type_name(item),
                    "create_step": str(_attr(item, "createStepName", "")),
                }
            )
        except Exception as error:
            output.append({"name": name, "error": str(error)})
    return {
        "count": len(names),
        "items": output,
        "truncated": len(names) > maximum,
    }


def _element_types(part, maximum):
    elements = _attr(part, "elements", ())
    total = _length(elements)
    scan_limit = max(10000, maximum * 1000)
    counts = {}
    scanned = 0
    error_text = ""
    try:
        for element in elements:
            if scanned >= scan_limit:
                break
            element_type = str(_attr(element, "type", "")) or "UNKNOWN"
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


def _mesh_controls(part, maximum):
    get_mesh_control = _attr(part, "getMeshControl")
    if not callable(get_mesh_control):
        return {"status": "UNAVAILABLE"}
    try:
        from abaqusConstants import ALGORITHM, ELEM_SHAPE, MIN_TRANSITION, TECHNIQUE
    except Exception as error:
        return {"status": "UNAVAILABLE", "error": str(error)}

    cells = _attr(part, "cells", ())
    faces = _attr(part, "faces", ())
    if _length(cells):
        region_kind = "CELL"
        regions = cells
    elif _length(faces):
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
            key = tuple(values[name] for name, _attribute in attributes)
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
        "region_count": _length(regions),
        "inspected_regions": inspected,
        "items": items,
        "truncated": inspected < _length(regions),
    }
    if errors:
        report["errors"] = errors[:maximum]
    return report


def _mesh_stats(part):
    get_mesh_stats = _attr(part, "getMeshStats")
    if not callable(get_mesh_stats):
        return {"status": "UNAVAILABLE"}
    cells = _attr(part, "cells", ())
    faces = _attr(part, "faces", ())
    if _length(cells):
        region_kind = "CELL"
        regions = cells
    elif _length(faces):
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
        value = _attr(stats, name)
        if value is not None:
            report[name] = value
    return report


def _mesh_report(part, maximum):
    return {
        "element_types": _element_types(part, maximum),
        "controls": _mesh_controls(part, maximum),
        "stats": _mesh_stats(part),
    }


def _part_report(part, maximum):
    section_assignments = []
    for assignment in list(_attr(part, "sectionAssignments", ()) or ())[:maximum]:
        region = _attr(assignment, "region")
        section_assignments.append(
            {
                "section_name": str(_attr(assignment, "sectionName", "")),
                "region_name": str(_attr(region, "name", "")),
            }
        )
    return {
        "type": _type_name(part),
        "dimensionality": str(_attr(part, "dimensionality", "")),
        "body_type": str(_attr(part, "type", "")),
        "counts": _entity_counts(part),
        "sets": _region_index(_attr(part, "sets", {}), maximum),
        "surfaces": _region_index(_attr(part, "surfaces", {}), maximum),
        "section_assignments": section_assignments,
        "mesh": _mesh_report(part, maximum),
    }


def _instance_report(instance, maximum):
    return {
        "type": _type_name(instance),
        "part_name": str(_attr(instance, "partName", "")),
        "dependent": str(_attr(instance, "dependent", "")),
        "counts": _entity_counts(instance),
        "sets": _region_index(_attr(instance, "sets", {}), maximum),
        "surfaces": _region_index(_attr(instance, "surfaces", {}), maximum),
    }


_MODEL_REPOSITORIES = (
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
)


def read_model(mdb, model_name, maximum):
    model_names = _keys(_attr(mdb, "models", {}))
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
    for name in _MODEL_REPOSITORIES:
        repositories[name] = _typed_index(_attr(model, name, {}), maximum)
    parts = {}
    part_names = _keys(_attr(model, "parts", {}))
    for name in part_names[:maximum]:
        parts[name] = _part_report(model.parts[name], maximum)
    assembly = _attr(model, "rootAssembly")
    instances = {}
    instance_names = _keys(_attr(assembly, "instances", {}))
    for name in instance_names[:maximum]:
        instances[name] = _instance_report(assembly.instances[name], maximum)
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
            "root_assembly": {
                "instances": {
                    "count": len(instance_names),
                    "items": instances,
                    "truncated": len(instance_names) > maximum,
                },
                "sets": _region_index(_attr(assembly, "sets", {}), maximum),
                "surfaces": _region_index(_attr(assembly, "surfaces", {}), maximum),
            },
        }
    )
    return report


def _decode_tail(data):
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return data.decode(encoding)
        except Exception:
            pass
    return data.decode("latin-1", "replace")


def _log_tail(path, maximum_lines):
    if not os.path.isfile(path):
        return {"exists": False, "path": os.path.abspath(path)}
    size = os.path.getsize(path)
    with io.open(path, "rb") as stream:
        if size > 262144:
            stream.seek(size - 262144)
        text = _decode_tail(stream.read())
    lines = text.splitlines()
    markers = ("ERROR", "WARNING", "FATAL", "ABORT", "TERMINAT")
    diagnostic = [line for line in lines if any(word in line.upper() for word in markers)]
    return {
        "exists": True,
        "path": os.path.abspath(path),
        "size_bytes": size,
        "tail": lines[-maximum_lines:],
        "diagnostic_lines": diagnostic[-maximum_lines:],
        "truncated": len(lines) > maximum_lines,
    }


def _job_messages(job, maximum):
    messages = []
    try:
        raw_messages = list(job.messages)
    except Exception:
        raw_messages = []
    for message in raw_messages[-maximum:]:
        messages.append(
            {
                "type": str(_attr(message, "type", "")),
                "text": str(_attr(message, "data", _attr(message, "message", message))),
            }
        )
    return messages


def read_job(mdb, job_name, workspace_dir, maximum_lines):
    job_names = _keys(_attr(mdb, "jobs", {}))
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
        files[extension] = _log_tail(
            os.path.join(work_dir, job_name + "." + extension), maximum_lines
        )
    report.update(
        {
            "status": "OK",
            "selected_job": job_name,
            "job_status": str(_attr(job, "status", "UNKNOWN")),
            "model": str(_attr(job, "model", "")),
            "type": _type_name(job),
            "num_cpus": _attr(job, "numCpus"),
            "memory": _attr(job, "memory"),
            "memory_units": str(_attr(job, "memoryUnits", "")),
            "messages": _job_messages(job, maximum_lines),
            "diagnostic_files": files,
        }
    )
    return report


def _frame_meta(frame, index):
    return {
        "index": index,
        "frame_id": _attr(frame, "frameId"),
        "increment_number": _attr(frame, "incrementNumber"),
        "frame_value": _attr(frame, "frameValue"),
        "mode": _attr(frame, "mode"),
        "frequency": _attr(frame, "frequency"),
        "description": str(_attr(frame, "description", "")),
    }


def _field_index(frames, maximum):
    catalog = {}
    for frame_index, frame in enumerate(frames):
        field_outputs = _attr(frame, "fieldOutputs", {})
        for name in _keys(field_outputs):
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
            entry["types"].add(str(_attr(field, "type", "")))
            for label in list(_attr(field, "componentLabels", ()) or ()):
                entry["component_labels"].add(str(label))
            for invariant in list(_attr(field, "validInvariants", ()) or ()):
                entry["valid_invariants"].add(str(invariant))
            for location in list(_attr(field, "locations", ()) or ()):
                entry["positions"].add(str(_attr(location, "position", "")))
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


def _history_index(step, maximum):
    regions = []
    names = _keys(_attr(step, "historyRegions", {}))
    for name in names[:maximum]:
        region = step.historyRegions[name]
        outputs = _keys(_attr(region, "historyOutputs", {}))
        regions.append(
            {
                "name": name,
                "description": str(_attr(region, "description", "")),
                "position": str(_attr(region, "position", "")),
                "outputs": _window(outputs, maximum),
            }
        )
    return {"count": len(names), "items": regions, "truncated": len(names) > maximum}


def _odb_regions(assembly, maximum):
    instances = []
    names = _keys(_attr(assembly, "instances", {}))
    for name in names[:maximum]:
        instance = assembly.instances[name]
        instances.append(
            {
                "name": name,
                "nodes": _length(_attr(instance, "nodes", ())),
                "elements": _length(_attr(instance, "elements", ())),
                "node_sets": _window(_keys(_attr(instance, "nodeSets", {})), maximum),
                "element_sets": _window(_keys(_attr(instance, "elementSets", {})), maximum),
                "surfaces": _window(_keys(_attr(instance, "surfaces", {})), maximum),
            }
        )
    return {
        "instances": {"count": len(names), "items": instances, "truncated": len(names) > maximum},
        "node_sets": _window(_keys(_attr(assembly, "nodeSets", {})), maximum),
        "element_sets": _window(_keys(_attr(assembly, "elementSets", {})), maximum),
        "surfaces": _window(_keys(_attr(assembly, "surfaces", {})), maximum),
    }


def read_odb(odb_path, open_odb, maximum):
    absolute_path = os.path.abspath(odb_path)
    if not os.path.isfile(absolute_path):
        return {"status": "NOT_FOUND", "path": absolute_path, "error": "ODB file does not exist"}
    odb = open_odb(path=absolute_path, readOnly=True)
    try:
        steps = []
        step_names = _keys(_attr(odb, "steps", {}))
        for name in step_names[:maximum]:
            step = odb.steps[name]
            frames = list(_attr(step, "frames", ()) or ())
            frame_samples = []
            if frames:
                frame_samples.append(_frame_meta(frames[0], 0))
                if len(frames) > 1:
                    frame_samples.append(_frame_meta(frames[-1], len(frames) - 1))
            steps.append(
                {
                    "name": name,
                    "procedure": str(_attr(step, "procedure", "")),
                    "domain": str(_attr(step, "domain", "")),
                    "time_period": _attr(step, "timePeriod"),
                    "frame_count": len(frames),
                    "frame_samples": frame_samples,
                    "field_outputs": _field_index(frames, maximum),
                    "history_regions": _history_index(step, maximum),
                }
            )
        diagnostic = _attr(odb, "diagnosticData")
        diagnostic_data = {}
        for name in (
            "jobStatus",
            "analysisErrors",
            "analysisWarnings",
            "numberOfAnalysisErrors",
            "numberOfAnalysisWarnings",
        ):
            value = _attr(diagnostic, name)
            if value is not None:
                diagnostic_data[name] = str(value)
        return {
            "status": "OK",
            "path": absolute_path,
            "name": str(_attr(odb, "name", "")),
            "analysis_title": str(_attr(odb, "analysisTitle", "")),
            "description": str(_attr(odb, "description", "")),
            "diagnostic_data": diagnostic_data,
            "root_assembly": _odb_regions(odb.rootAssembly, maximum),
            "steps": {
                "count": len(step_names),
                "items": steps,
                "truncated": len(step_names) > maximum,
            },
        }
    finally:
        odb.close()


def read_session(request):
    from abaqus import mdb

    maximum = max(1, min(int(request.get("max_items", 200)), 1000))
    maximum_lines = max(1, min(int(request.get("max_log_lines", 40)), 200))
    report = {
        "read_only": True,
        "model": read_model(mdb, request.get("model"), maximum),
        "job": read_job(mdb, request.get("job"), request.get("workspace_dir"), maximum_lines),
        "odb": {"status": "NOT_REQUESTED"},
    }
    if request.get("odb_path"):
        from odbAccess import openOdb

        report["odb"] = read_odb(request["odb_path"], openOdb, maximum)
    statuses = [report[name]["status"] for name in ("model", "job", "odb")]
    report["status"] = "PARTIAL" if "NOT_FOUND" in statuses else "OK"
    return report


if "inspection_request" in globals():
    result = read_session(globals()["inspection_request"])
