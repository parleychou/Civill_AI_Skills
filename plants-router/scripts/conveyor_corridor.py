# python_executor: timeout=300
"""Parametric conveyor corridor for an open PlantS session.

The corridor is a sloped rectangle of two side trusses plus top and bottom
X bracing, with support columns and independent foundations at selected
stations. Coordinates are millimetres: X along the corridor, Y across the
width, Z vertical.

Run with no arguments for a geometry self-check. Inside python_executor,
set INDUSTRY_CORRIDOR_PARAMS and execute the file after connect_to_plants
has injected CreateBeam and CreateColumn.
"""

from __future__ import annotations

import json
import math

try:
    from Agent.software_link_kit.plants import connect_to_plants
except ImportError:
    def connect_to_plants(**kwargs):
        raise RuntimeError(
            "PlantS is not available in this interpreter. "
            "Connect with Agent.software_link_kit.plants.connect_to_plants inside python_executor, "
            "then execute this script."
        )


PARAMS = {
    "origin": [0.0, 0.0, 6000.0],
    "total_length": None,
    "num_bays": 12,
    "bay_length": 3500.0,
    "width": 3000.0,
    "truss_height": 3800.0,
    "slope_angle_deg": 14.0,
    "side_v_apex": "bottom",
    "reverse_end_diagonals": True,
    "create_top_x_bracing": True,
    "create_bottom_x_bracing": True,
    "create_transverse_frames": True,
    "support_indices": None,
    "support_span_m": 30.0,
    "max_support_span_m": 60.0,
    "ground_z": 0.0,
    "create_foundations": True,
    "foundation_type": "StepCast",
    "foundation_steps": [
        {"width": 2200.0, "height": 2200.0, "step_height": 500},
        {"width": 1400.0, "height": 1400.0, "step_height": 400},
    ],
    "foundation_angle_deg": 0.0,
    "steel_standard": "国标热轧H型钢",
    "chord_section": "HM294X200",
    "web_section": "HN150X75",
    "cross_brace_section": "HN150X75",
    "support_section": "HM294X200",
    "material": "Q345B",
}

PARAM_ALIASES = {
    "length": "total_length",
    "total_len": "total_length",
    "bay_count": "num_bays",
    "panel_count": "num_bays",
    "bay_spacing": "bay_length",
    "panel_length": "bay_length",
    "height": "truss_height",
    "slope": "slope_angle_deg",
    "slope_deg": "slope_angle_deg",
    "support_span": "support_span_m",
    "support_spacing": "support_span_m",
    "support_interval": "support_span_m",
    "corridor_span": "support_span_m",
}

created = {
    "side_chords": [],
    "side_verticals": [],
    "side_diagonals": [],
    "top_transverse": [],
    "bottom_transverse": [],
    "top_x_braces": [],
    "bottom_x_braces": [],
    "supports": [],
    "foundations": [],
}
stats = {"created": 0, "modified": 0, "failed": 0, "warnings": []}


def _warn(message: str) -> None:
    stats["warnings"].append(message)
    print("[WARN]", message)


def uniform_bay_layout(total_length, target_bay_length):
    total_length = float(total_length)
    target_bay_length = float(target_bay_length)
    if total_length <= 0:
        raise ValueError("total_length must be positive.")
    if target_bay_length <= 0:
        raise ValueError("bay_length must be positive.")
    bay_count = max(1, int(math.floor(total_length / target_bay_length + 0.5)))
    return bay_count, total_length / bay_count


def apply_param_overrides() -> None:
    overrides = {}
    for name in ("INDUSTRY_CORRIDOR_PARAMS", "CORRIDOR_PARAMS"):
        value = globals().get(name)
        if isinstance(value, dict):
            overrides.update(value)
    if not overrides:
        return
    normalized = {PARAM_ALIASES.get(key, key): value for key, value in overrides.items()}
    explicit_num_bays = "num_bays" in normalized
    for key in sorted(key for key in normalized if key not in PARAMS):
        print("[WARN] Unknown corridor parameter ignored: {0}".format(key))
    PARAMS.update({key: value for key, value in normalized.items() if key in PARAMS})
    if PARAMS["total_length"] is None:
        return
    total_length = float(PARAMS["total_length"])
    bay_count, bay_length = uniform_bay_layout(total_length, PARAMS["bay_length"])
    PARAMS["total_length"] = total_length
    PARAMS["bay_length"] = bay_length
    PARAMS["num_bays"] = bay_count
    if explicit_num_bays:
        print("[WARN] num_bays is derived from total_length and bay_length; supplied num_bays ignored.")


apply_param_overrides()


def _point(x, y, z):
    return [round(float(x), 3), round(float(y), 3), round(float(z), 3)]


def _same_point(left, right, tol=1e-6):
    return all(abs(float(left[index]) - float(right[index])) <= tol for index in range(3))


def _valid_material_or_none(material):
    material = (material or "").strip()
    if not material:
        return None
    try:
        allowed = GetMaterialTypes()
    except Exception as exc:
        _warn("GetMaterialTypes failed, material will be skipped: {0}".format(exc))
        return None
    if material in allowed:
        return material
    _warn("Material '{0}' is not in GetMaterialTypes(); material will be skipped.".format(material))
    _warn("Available materials: {0}".format(allowed))
    return None


def _make_sections():
    standard = PARAMS["steel_standard"]
    chord = Generate_BarSectionData_StandardSteel(StandardName=standard, SectName=PARAMS["chord_section"])
    web = Generate_BarSectionData_StandardSteel(StandardName=standard, SectName=PARAMS["web_section"])
    cross = Generate_BarSectionData_StandardSteel(StandardName=standard, SectName=PARAMS["cross_brace_section"])
    support = Generate_BarSectionData_StandardSteel(StandardName=standard, SectName=PARAMS["support_section"])
    return {
        "chord_beam": Find_Or_Add_BeamSection(section=chord),
        "web_column": Find_Or_Add_ColumnSection(section=web),
        "web_brace": Find_Or_Add_BraceSection(section=web),
        "cross_brace": Find_Or_Add_BraceSection(section=cross),
        "support_column": Find_Or_Add_ColumnSection(section=support),
    }


def _support_span_m():
    span = float(PARAMS["support_span_m"])
    max_span = float(PARAMS["max_support_span_m"])
    if span <= 0:
        span = 30.0
        _warn("support_span_m must be positive; using {0}m.".format(span))
    if max_span <= 0:
        max_span = 60.0
        _warn("max_support_span_m must be positive; using {0}m.".format(max_span))
    if span > max_span:
        _warn("support_span_m={0}m exceeds max {1}m; clamped to {1}m.".format(span, max_span))
        span = max_span
    if span < 20.0 or span > 36.0:
        _warn("Recommended support_span_m is 20-36m; continuing with the configured value.")
    PARAMS["support_span_m"] = span
    PARAMS["max_support_span_m"] = max_span
    return span


def _bay_lengths():
    bay_count = int(PARAMS["num_bays"])
    bay_length = float(PARAMS["bay_length"])
    if bay_count <= 0:
        raise ValueError("num_bays must be positive.")
    if bay_length <= 0:
        raise ValueError("bay_length must be positive.")
    total_length = PARAMS.get("total_length")
    if total_length is None:
        return [bay_length] * bay_count
    bay_count, bay_length = uniform_bay_layout(float(total_length), bay_length)
    PARAMS["num_bays"] = bay_count
    PARAMS["bay_length"] = bay_length
    return [bay_length] * bay_count


def _node_offsets():
    offsets = [0.0]
    for length in _bay_lengths():
        offsets.append(offsets[-1] + length)
    return offsets


def _nearest_station(offsets, target):
    return min(range(len(offsets)), key=lambda index: (abs(offsets[index] - target), index))


def _auto_support_indices(num_bays):
    offsets = _node_offsets()
    num_bays = len(offsets) - 1
    if num_bays <= 0:
        return [0]
    span_mm = _support_span_m() * 1000.0
    max_span_mm = float(PARAMS["max_support_span_m"]) * 1000.0
    total_length = offsets[-1]

    def indices_for_count(count):
        return sorted({_nearest_station(offsets, i * total_length / count) for i in range(count + 1)})

    span_count = max(1, int(round(total_length / span_mm)))
    min_span_count = max(1, int(math.ceil(total_length / max_span_mm)))
    span_count = min(num_bays, max(span_count, min_span_count))
    indices = indices_for_count(span_count)
    while span_count < num_bays:
        max_gap = max(offsets[indices[i + 1]] - offsets[indices[i]] for i in range(len(indices) - 1))
        if max_gap <= max_span_mm:
            break
        span_count += 1
        indices = indices_for_count(span_count)
    max_gap = max(offsets[indices[i + 1]] - offsets[indices[i]] for i in range(len(indices) - 1))
    if max_gap > max_span_mm:
        _warn("A single bay is longer than max_support_span_m; support span limit cannot be satisfied.")
    if indices[0] != 0:
        indices.insert(0, 0)
    if indices[-1] != num_bays:
        indices.append(num_bays)
    return indices


def _support_indices(num_bays):
    indices = PARAMS["support_indices"]
    if indices is None:
        return _auto_support_indices(num_bays)
    return sorted({int(index) for index in indices})


def _valid_support_indices(num_bays):
    kept = []
    for index in _support_indices(num_bays):
        if index < 0 or index > num_bays:
            _warn("Support index out of range and skipped: {0}".format(index))
            continue
        kept.append(index)
    return kept


def _diagonal_spans(num_bays, support_indices):
    if not support_indices:
        return [(0, num_bays)]
    boundaries = sorted(set([0, num_bays] + list(support_indices)))
    return [(start, end) for start, end in zip(boundaries, boundaries[1:]) if end > start]


def _reverse_diagonal_bays(diagonal_spans, support_indices):
    if not PARAMS["reverse_end_diagonals"] or not support_indices:
        return set()
    reverse_bays = set()
    for start, end in diagonal_spans:
        reverse_bays.add(start)
        reverse_bays.add(end - 1)
    return reverse_bays


def _foundation_step_specs():
    specs = []
    for index, item in enumerate(PARAMS["foundation_steps"], start=1):
        if isinstance(item, dict):
            width = float(item["width"])
            height = float(item["height"])
            step_height = int(round(float(item["step_height"])))
        else:
            width, height, step_height = item
            width = float(width)
            height = float(height)
            step_height = int(round(float(step_height)))
        if width <= 0 or height <= 0 or step_height <= 0:
            raise ValueError("foundation_steps[{0}] must contain positive dimensions.".format(index))
        specs.append({"width": width, "height": height, "step_height": step_height})
    return specs


def _make_foundation_section():
    if not PARAMS["create_foundations"]:
        return None, 0.0
    try:
        steps = []
        total_height = 0.0
        for spec in _foundation_step_specs():
            shape = Generate_ShapeDefData_Rectangle(width=spec["width"], height=spec["height"])
            steps.append(Generate_IsoFoundationStepData(height=spec["step_height"], shape=shape))
            total_height += spec["step_height"]
        section = Generate_IsoFoundationSectData(foundation_type=PARAMS["foundation_type"], steps=steps)
        return Find_Or_Add_IsoFoundationSection(section=section), total_height
    except Exception as exc:
        stats["failed"] += 1
        _warn("Prepare independent foundation section failed; foundations will be skipped: {0}".format(exc))
        return None, 0.0


def _modify_member(kind, key, section_key=None, material=None):
    props = {}
    if section_key is not None:
        props["截面"] = section_key
    if material:
        props["材料"] = material
    if not props:
        return True
    if kind == "beam":
        result = ModifyBeamProperties(beam_key=key, properties=props)
    elif kind == "column":
        result = ModifyColumnProperties(column_key=key, properties=props)
    elif kind == "brace":
        result = ModifyBraceProperties(brace_key=key, properties=props)
    else:
        raise ValueError("Unknown member kind: {0}".format(kind))
    if result.get("success"):
        stats["modified"] += 1
        return True
    stats["failed"] += 1
    _warn("Modify {0} failed: key={1}, result={2}".format(kind, key, result))
    return False


def _create_member(kind, start, end, section_key=None, material=None, role="members"):
    if _same_point(start, end):
        _warn("Skip zero-length {0}: {1} -> {2}".format(kind, start, end))
        return None
    creators = {
        "beam": (CreateBeam, "beam_key"),
        "column": (CreateColumn, "column_key"),
        "brace": (CreateBrace, "brace_key"),
    }
    if kind not in creators:
        raise ValueError("Unknown member kind: {0}".format(kind))
    create, key_name = creators[kind]
    result = create(start_point=start, end_point=end)
    if not result.get("success"):
        stats["failed"] += 1
        _warn("Create {0} failed: {1} -> {2}, result={3}".format(kind, start, end, result))
        return None
    key = result[key_name]
    stats["created"] += 1
    _modify_member(kind, key, section_key=section_key, material=material)
    created.setdefault(role, []).append(key)
    return key


def _modify_foundation(key, top_ele, bot_ele, angle_deg):
    result = ModifyIsoFoundationProperties(
        foundation_key=key,
        properties={"TopEle": top_ele, "BotEle": bot_ele, "Angle": angle_deg},
    )
    if result.get("success"):
        stats["modified"] += 1
        return True
    stats["failed"] += 1
    _warn("Modify independent foundation failed: key={0}, result={1}".format(key, result))
    return False


def _create_foundation(place_point, section_key, total_height, angle_deg):
    if section_key is None:
        return None
    result = CreateIsoFoundation(sect_key=section_key, place_point=place_point)
    if not result.get("success"):
        stats["failed"] += 1
        _warn("Create independent foundation failed: point={0}, result={1}".format(place_point, result))
        return None
    key = result["foundation_key"]
    stats["created"] += 1
    created.setdefault("foundations", []).append(key)
    top_ele = float(place_point[2])
    _modify_foundation(key, top_ele=top_ele, bot_ele=top_ele - float(total_height), angle_deg=angle_deg)
    return key


def build_nodes():
    origin_x, origin_y, origin_z = PARAMS["origin"]
    offsets = _node_offsets()
    PARAMS["num_bays"] = len(offsets) - 1
    width = float(PARAMS["width"])
    height = float(PARAMS["truss_height"])
    slope = math.tan(math.radians(float(PARAMS["slope_angle_deg"])))
    left_bottom, right_bottom, left_top, right_top = [], [], [], []
    for offset in offsets:
        x = origin_x + offset
        z_bottom = origin_z + offset * slope
        z_top = z_bottom + height
        left_bottom.append(_point(x, origin_y, z_bottom))
        right_bottom.append(_point(x, origin_y + width, z_bottom))
        left_top.append(_point(x, origin_y, z_top))
        right_top.append(_point(x, origin_y + width, z_top))
    return {"LB": left_bottom, "RB": right_bottom, "LT": left_top, "RT": right_top}


def side_diagonal_pair(bottom_nodes, top_nodes, bay_index, diagonal_spans, reverse_bays):
    span_start = 0
    span_end = int(PARAMS["num_bays"])
    for start, end in diagonal_spans:
        if start <= bay_index < end:
            span_start = start
            span_end = end
            break
    mid = (span_start + span_end) / 2.0
    apex = str(PARAMS["side_v_apex"]).lower()
    if apex == "bottom":
        start_top_to_bottom = bay_index < mid
    elif apex == "top":
        start_top_to_bottom = bay_index >= mid
    else:
        raise ValueError("side_v_apex must be 'bottom' or 'top'")
    if bay_index in reverse_bays:
        start_top_to_bottom = not start_top_to_bottom
    if start_top_to_bottom:
        return top_nodes[bay_index], bottom_nodes[bay_index + 1]
    return bottom_nodes[bay_index], top_nodes[bay_index + 1]


def _member_run(kind, pairs, section_key, material, role):
    for start, end in pairs:
        _create_member(kind, start, end, section_key=section_key, material=material, role=role)


def create_corridor():
    print("Connecting PlantS MCP...")
    connect_kwargs = {}
    exe_path = globals().get("INDUSTRY_CORRIDOR_EXE_PATH") or globals().get("PLANTS_EXE_PATH")
    project_path = globals().get("INDUSTRY_CORRIDOR_PROJECT_PATH") or globals().get("PLANTS_PROJECT_PATH")
    if exe_path:
        connect_kwargs["exe_path"] = exe_path
    if project_path:
        connect_kwargs["project_path"] = project_path
    connect_result = connect_to_plants(**connect_kwargs)
    print("connect_to_plants:", connect_result)
    if connect_result is not True:
        raise RuntimeError("Failed to connect plantsmcp: {0}".format(connect_result))

    material = _valid_material_or_none(PARAMS["material"])
    sections = _make_sections()
    nodes = build_nodes()
    left_bottom, right_bottom = nodes["LB"], nodes["RB"]
    left_top, right_top = nodes["LT"], nodes["RT"]
    bay_count = int(PARAMS["num_bays"])
    support_indices = _valid_support_indices(bay_count)
    diagonal_spans = _diagonal_spans(bay_count, support_indices)
    reverse_bays = _reverse_diagonal_bays(diagonal_spans, support_indices)

    for _side, bottom, top in (("left", left_bottom, left_top), ("right", right_bottom, right_top)):
        _member_run(
            "beam",
            [(top[i], top[i + 1]) for i in range(bay_count)] + [(bottom[i], bottom[i + 1]) for i in range(bay_count)],
            sections["chord_beam"],
            material,
            "side_chords",
        )
        _member_run(
            "column",
            [(bottom[i], top[i]) for i in range(bay_count + 1)],
            sections["web_column"],
            material,
            "side_verticals",
        )
        diagonals = [
            side_diagonal_pair(bottom, top, i, diagonal_spans, reverse_bays) for i in range(bay_count)
        ]
        _member_run("brace", diagonals, sections["web_brace"], material, "side_diagonals")

    if PARAMS["create_transverse_frames"]:
        _member_run(
            "beam",
            [(left_top[i], right_top[i]) for i in range(bay_count + 1)],
            sections["chord_beam"],
            material,
            "top_transverse",
        )
        _member_run(
            "beam",
            [(left_bottom[i], right_bottom[i]) for i in range(bay_count + 1)],
            sections["chord_beam"],
            material,
            "bottom_transverse",
        )
    if PARAMS["create_top_x_bracing"]:
        _member_run(
            "brace",
            [(left_top[i], right_top[i + 1]) for i in range(bay_count)]
            + [(right_top[i], left_top[i + 1]) for i in range(bay_count)],
            sections["cross_brace"],
            material,
            "top_x_braces",
        )
    if PARAMS["create_bottom_x_bracing"]:
        _member_run(
            "brace",
            [(left_bottom[i], right_bottom[i + 1]) for i in range(bay_count)]
            + [(right_bottom[i], left_bottom[i + 1]) for i in range(bay_count)],
            sections["cross_brace"],
            material,
            "bottom_x_braces",
        )

    ground_z = float(PARAMS["ground_z"])
    foundation_section, foundation_height = (None, 0.0)
    if support_indices:
        foundation_section, foundation_height = _make_foundation_section()
    foundation_angle = float(PARAMS["foundation_angle_deg"])
    for index in support_indices:
        for chord in (left_bottom[index], right_bottom[index]):
            base = _point(chord[0], chord[1], ground_z)
            column = _create_member(
                "column",
                base,
                chord,
                section_key=sections["support_column"],
                material=material,
                role="supports",
            )
            if column is not None:
                _create_foundation(base, foundation_section, foundation_height, foundation_angle)

    print("\n=== PlantS corridor truss created ===")
    print("params:", PARAMS)
    print("members:")
    for role, keys in created.items():
        print("  {0}: {1}".format(role, len(keys)))
    print(
        "created={0}, modified={1}, failed={2}".format(
            stats["created"], stats["modified"], stats["failed"]
        )
    )
    if stats["warnings"]:
        print("\nwarnings:")
        for message in stats["warnings"]:
            print(" -", message)
    return {"params": PARAMS, "nodes": nodes, "created": created, "stats": stats}


def _modeling_api_ready() -> bool:
    return callable(globals().get("CreateBeam")) and callable(globals().get("CreateColumn"))


def self_check() -> dict:
    nodes = build_nodes()
    return {
        "status": "ok",
        "self_check": True,
        "bays": PARAMS["num_bays"],
        "stations": len(nodes["LB"]),
        "width": PARAMS["width"],
    }


_build_requested = any(
    isinstance(globals().get(name), dict) for name in ("INDUSTRY_CORRIDOR_PARAMS", "CORRIDOR_PARAMS")
) or any(
    globals().get(name)
    for name in (
        "INDUSTRY_CORRIDOR_EXE_PATH",
        "INDUSTRY_CORRIDOR_PROJECT_PATH",
        "PLANTS_EXE_PATH",
        "PLANTS_PROJECT_PATH",
    )
)

if _modeling_api_ready():
    result = create_corridor()
elif _build_requested:
    raise RuntimeError(
        "PlantS modeling functions are not in this interpreter. "
        "Call connect_to_plants() before executing the corridor script."
    )
elif __name__ == "__main__":
    print(json.dumps(self_check(), ensure_ascii=False))
    result = None
else:
    result = None
