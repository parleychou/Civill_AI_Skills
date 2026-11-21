# python_executor: timeout=300
"""
PlantS corridor truss generator.

Run this script inside cadagent's python_executor after PlantS is running.
It creates a sloped rectangular corridor made from four planar trusses:
- two side trusses
- top-plane X bracing
- bottom-plane X bracing
It also creates support columns and independent foundations at configured
stations by default.

Coordinates:
- X: corridor length
- Y: corridor width
- Z: elevation
"""

import math

# 导入工业结构自动化通信模块


# ============================================================
# 1. Parameters
# ============================================================

PARAMS = {
    # Geometry, unit: mm
    "origin": [0.0, 0.0, 6000.0],
    "total_length": None,
    # num_bays is derived from total_length and the target bay_length when total_length is set.
    "num_bays": 12,
    "bay_length": 3500.0,
    "width": 3000.0,
    "truss_height": 3800.0,
    "slope_angle_deg": 14.0,

    # Side-truss diagonal pattern.
    # "bottom": middle diagonals form a V with the apex on the bottom chord.
    # "top": middle diagonals form an inverted V with the apex on the top chord.
    "side_v_apex": "bottom",
    "reverse_end_diagonals": True,

    # Plane bracing
    "create_top_x_bracing": True,
    "create_bottom_x_bracing": True,
    "create_transverse_frames": True,

    # Support columns from bottom chord down to ground_z.
    # None means automatic support stations by support_span_m; [] disables supports.
    "support_indices": None,
    "support_span_m": 30.0,
    "max_support_span_m": 60.0,
    "ground_z": 0.0,

    # Independent foundations below support columns.
    "create_foundations": True,
    "foundation_type": "StepCast",
    "foundation_steps": [
        {"width": 2200.0, "height": 2200.0, "step_height": 500},
        {"width": 1400.0, "height": 1400.0, "step_height": 400},
    ],
    "foundation_angle_deg": 0.0,

    # Sections. Change these to available PlantS steel section names.
    "steel_standard": "国标热轧H型钢",
    "chord_section": "HM294X200",
    "web_section": "HN150X75",
    "cross_brace_section": "HN150X75",
    "support_section": "HM294X200",

    # Material. If unavailable in PlantS enum, script will skip material assignment.
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


def _uniform_bay_layout(total_length, target_bay_length):
    total_length = float(total_length)
    target_bay_length = float(target_bay_length)
    if total_length <= 0:
        raise ValueError("total_length must be positive.")
    if target_bay_length <= 0:
        raise ValueError("bay_length must be positive.")

    bay_count = max(1, int(math.floor(total_length / target_bay_length + 0.5)))
    adjusted_bay_length = total_length / bay_count
    return bay_count, adjusted_bay_length


def _apply_param_overrides():
    overrides = {}
    for name in ("INDUSTRY_CORRIDOR_PARAMS", "CORRIDOR_PARAMS"):
        value = globals().get(name)
        if isinstance(value, dict):
            overrides.update(value)

    if not overrides:
        return

    normalized = {}
    for key, value in overrides.items():
        normalized[PARAM_ALIASES.get(key, key)] = value

    explicit_num_bays = "num_bays" in normalized
    unknown = sorted(key for key in normalized if key not in PARAMS)
    for key in unknown:
        print(f"[WARN] Unknown IndustryCorridor parameter ignored: {key}")

    PARAMS.update({key: value for key, value in normalized.items() if key in PARAMS})

    if PARAMS["total_length"] is not None:
        total_length = float(PARAMS["total_length"])
        n, bay = _uniform_bay_layout(total_length, PARAMS["bay_length"])
        PARAMS["total_length"] = total_length
        PARAMS["bay_length"] = bay
        PARAMS["num_bays"] = n
        if explicit_num_bays:
            print("[WARN] num_bays is derived from total_length and bay_length; supplied num_bays ignored.")


_apply_param_overrides()


# ============================================================
# 2. Small utilities
# ============================================================

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

stats = {
    "created": 0,
    "modified": 0,
    "failed": 0,
    "warnings": [],
}


def _warn(message):
    stats["warnings"].append(message)
    print("[WARN]", message)


def _point(x, y, z):
    return [round(float(x), 3), round(float(y), 3), round(float(z), 3)]


def _same_point(a, b, tol=1e-6):
    return all(abs(float(a[i]) - float(b[i])) <= tol for i in range(3))


def _valid_material_or_none(material):
    material = (material or "").strip()
    if not material:
        return None
    try:
        allowed = GetMaterialTypes()
    except Exception as exc:
        _warn(f"GetMaterialTypes failed, material will be skipped: {exc}")
        return None
    if material in allowed:
        return material
    _warn(f"Material '{material}' is not in GetMaterialTypes(); material will be skipped.")
    _warn(f"Available materials: {allowed}")
    return None


def _make_sections():
    std = PARAMS["steel_standard"]

    chord_data = Generate_BarSectionData_StandardSteel(
        StandardName=std,
        SectName=PARAMS["chord_section"],
    )
    web_data = Generate_BarSectionData_StandardSteel(
        StandardName=std,
        SectName=PARAMS["web_section"],
    )
    cross_data = Generate_BarSectionData_StandardSteel(
        StandardName=std,
        SectName=PARAMS["cross_brace_section"],
    )
    support_data = Generate_BarSectionData_StandardSteel(
        StandardName=std,
        SectName=PARAMS["support_section"],
    )

    return {
        "chord_beam": Find_Or_Add_BeamSection(section=chord_data),
        "web_column": Find_Or_Add_ColumnSection(section=web_data),
        "web_brace": Find_Or_Add_BraceSection(section=web_data),
        "cross_brace": Find_Or_Add_BraceSection(section=cross_data),
        "support_column": Find_Or_Add_ColumnSection(section=support_data),
    }


def _support_span_m():
    span = float(PARAMS["support_span_m"])
    max_span = float(PARAMS["max_support_span_m"])

    if span <= 0:
        fallback = 30.0
        _warn(f"support_span_m must be positive; using {fallback}m.")
        span = fallback

    if max_span <= 0:
        fallback = 60.0
        _warn(f"max_support_span_m must be positive; using {fallback}m.")
        max_span = fallback

    if span > max_span:
        _warn(f"support_span_m={span}m exceeds max {max_span}m; clamped to {max_span}m.")
        span = max_span

    if span < 20.0 or span > 36.0:
        _warn("Recommended support_span_m is 20-36m; continuing with the configured value.")

    PARAMS["support_span_m"] = span
    PARAMS["max_support_span_m"] = max_span
    return span


def _bay_lengths():
    n = int(PARAMS["num_bays"])
    bay = float(PARAMS["bay_length"])
    if n <= 0:
        raise ValueError("num_bays must be positive.")
    if bay <= 0:
        raise ValueError("bay_length must be positive.")

    total_length = PARAMS.get("total_length")
    if total_length is None:
        return [bay] * n

    total_length = float(total_length)
    n, bay = _uniform_bay_layout(total_length, bay)
    PARAMS["num_bays"] = n
    PARAMS["bay_length"] = bay
    return [bay] * n


def _node_offsets():
    offsets = [0.0]
    for length in _bay_lengths():
        offsets.append(offsets[-1] + length)
    return offsets


def _auto_support_indices(num_bays):
    offsets = _node_offsets()
    num_bays = len(offsets) - 1
    if num_bays <= 0:
        return [0]

    span_mm = _support_span_m() * 1000.0
    max_span_mm = float(PARAMS["max_support_span_m"]) * 1000.0
    total_length = offsets[-1]
    span_count = max(1, int(round(total_length / span_mm)))
    min_span_count = max(1, int(math.ceil(total_length / max_span_mm)))
    span_count = min(num_bays, max(span_count, min_span_count))

    def nearest_node_index(target):
        return min(range(len(offsets)), key=lambda index: (abs(offsets[index] - target), index))

    def indices_for_count(count):
        return sorted(set(nearest_node_index(i * total_length / count) for i in range(count + 1)))

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
    return sorted(set(int(i) for i in indices))


def _valid_support_indices(num_bays):
    indices = []
    for i in _support_indices(num_bays):
        if i < 0 or i > num_bays:
            _warn(f"Support index out of range and skipped: {i}")
            continue
        indices.append(i)
    return indices


def _diagonal_spans(num_bays, support_indices):
    if not support_indices:
        return [(0, num_bays)]

    boundaries = sorted(set([0, num_bays] + support_indices))
    return [
        (start, end)
        for start, end in zip(boundaries, boundaries[1:])
        if end > start
    ]


def _reverse_diagonal_bays(diagonal_spans, support_indices):
    if not PARAMS["reverse_end_diagonals"]:
        return set()
    if not support_indices:
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
            raise ValueError(f"foundation_steps[{index}] must contain positive dimensions.")

        specs.append(
            {
                "width": width,
                "height": height,
                "step_height": step_height,
            }
        )
    return specs


def _make_foundation_section():
    if not PARAMS["create_foundations"]:
        return None, 0.0

    try:
        steps = []
        total_height = 0.0
        for spec in _foundation_step_specs():
            shape = Generate_ShapeDefData_Rectangle(
                width=spec["width"],
                height=spec["height"],
            )
            step = Generate_IsoFoundationStepData(
                height=spec["step_height"],
                shape=shape,
            )
            steps.append(step)
            total_height += spec["step_height"]

        section = Generate_IsoFoundationSectData(
            foundation_type=PARAMS["foundation_type"],
            steps=steps,
        )
        return Find_Or_Add_IsoFoundationSection(section=section), total_height
    except Exception as exc:
        stats["failed"] += 1
        _warn(f"Prepare independent foundation section failed; foundations will be skipped: {exc}")
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
        raise ValueError(f"Unknown member kind: {kind}")

    if result.get("success"):
        stats["modified"] += 1
        return True

    stats["failed"] += 1
    _warn(f"Modify {kind} failed: key={key}, result={result}")
    return False


def _create_member(kind, start, end, section_key=None, material=None, role="members"):
    if _same_point(start, end):
        _warn(f"Skip zero-length {kind}: {start} -> {end}")
        return None

    if kind == "beam":
        result = CreateBeam(start_point=start, end_point=end)
        key_name = "beam_key"
    elif kind == "column":
        result = CreateColumn(start_point=start, end_point=end)
        key_name = "column_key"
    elif kind == "brace":
        result = CreateBrace(start_point=start, end_point=end)
        key_name = "brace_key"
    else:
        raise ValueError(f"Unknown member kind: {kind}")

    if not result.get("success"):
        stats["failed"] += 1
        _warn(f"Create {kind} failed: {start} -> {end}, result={result}")
        return None

    key = result[key_name]
    stats["created"] += 1
    _modify_member(kind, key, section_key=section_key, material=material)
    created.setdefault(role, []).append(key)
    return key


def _modify_foundation(key, top_ele, bot_ele, angle_deg):
    result = ModifyIsoFoundationProperties(
        foundation_key=key,
        properties={
            "TopEle": top_ele,
            "BotEle": bot_ele,
            "Angle": angle_deg,
        },
    )

    if result.get("success"):
        stats["modified"] += 1
        return True

    stats["failed"] += 1
    _warn(f"Modify independent foundation failed: key={key}, result={result}")
    return False


def _create_foundation(place_point, section_key, total_height, angle_deg):
    if section_key is None:
        return None

    result = CreateIsoFoundation(sect_key=section_key, place_point=place_point)
    if not result.get("success"):
        stats["failed"] += 1
        _warn(f"Create independent foundation failed: point={place_point}, result={result}")
        return None

    key = result["foundation_key"]
    stats["created"] += 1
    created.setdefault("foundations", []).append(key)
    top_ele = float(place_point[2])
    _modify_foundation(
        key,
        top_ele=top_ele,
        bot_ele=top_ele - float(total_height),
        angle_deg=angle_deg,
    )
    return key


# ============================================================
# 3. Geometry
# ============================================================

def build_nodes():
    ox, oy, oz = PARAMS["origin"]
    offsets = _node_offsets()
    PARAMS["num_bays"] = len(offsets) - 1
    width = float(PARAMS["width"])
    height = float(PARAMS["truss_height"])
    slope = math.tan(math.radians(float(PARAMS["slope_angle_deg"])))

    left_bottom = []
    right_bottom = []
    left_top = []
    right_top = []

    for offset in offsets:
        x = ox + offset
        z_bottom = oz + offset * slope
        z_top = z_bottom + height

        left_bottom.append(_point(x, oy, z_bottom))
        right_bottom.append(_point(x, oy + width, z_bottom))
        left_top.append(_point(x, oy, z_top))
        right_top.append(_point(x, oy + width, z_top))

    return {
        "LB": left_bottom,
        "RB": right_bottom,
        "LT": left_top,
        "RT": right_top,
    }


def side_diagonal_pair(bottom_nodes, top_nodes, bay_index, diagonal_spans, reverse_bays):
    span_start = 0
    span_end = int(PARAMS["num_bays"])
    for start, end in diagonal_spans:
        if start <= bay_index < end:
            span_start = start
            span_end = end
            break

    mid = (span_start + span_end) / 2.0
    apex = PARAMS["side_v_apex"].lower()

    if apex == "bottom":
        # Left half of the current support span: top[i] -> bottom[i+1].
        # Right half of the current support span: bottom[i] -> top[i+1].
        start_top_to_bottom = bay_index < mid
    elif apex == "top":
        # Left half of the current support span: bottom[i] -> top[i+1].
        # Right half of the current support span: top[i] -> bottom[i+1].
        start_top_to_bottom = bay_index >= mid
    else:
        raise ValueError("side_v_apex must be 'bottom' or 'top'")

    if bay_index in reverse_bays:
        start_top_to_bottom = not start_top_to_bottom

    if start_top_to_bottom:
        return top_nodes[bay_index], bottom_nodes[bay_index + 1]
    return bottom_nodes[bay_index], top_nodes[bay_index + 1]


# ============================================================
# 4. Create corridor
# ============================================================

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
        raise RuntimeError(f"Failed to connect plantsmcp: {connect_result}")

    material = _valid_material_or_none(PARAMS["material"])
    sections = _make_sections()
    nodes = build_nodes()

    LB = nodes["LB"]
    RB = nodes["RB"]
    LT = nodes["LT"]
    RT = nodes["RT"]
    n = int(PARAMS["num_bays"])
    support_indices = _valid_support_indices(n)
    diagonal_spans = _diagonal_spans(n, support_indices)
    reverse_bays = _reverse_diagonal_bays(diagonal_spans, support_indices)

    # Side trusses: left and right planes
    for side_name, bottom, top in (("left", LB, LT), ("right", RB, RT)):
        for i in range(n):
            _create_member(
                "beam", top[i], top[i + 1],
                section_key=sections["chord_beam"],
                material=material,
                role="side_chords",
            )
            _create_member(
                "beam", bottom[i], bottom[i + 1],
                section_key=sections["chord_beam"],
                material=material,
                role="side_chords",
            )

        for i in range(n + 1):
            _create_member(
                "column", bottom[i], top[i],
                section_key=sections["web_column"],
                material=material,
                role="side_verticals",
            )

        for i in range(n):
            start, end = side_diagonal_pair(bottom, top, i, diagonal_spans, reverse_bays)
            _create_member(
                "brace", start, end,
                section_key=sections["web_brace"],
                material=material,
                role="side_diagonals",
            )

    # Transverse frames at every station
    if PARAMS["create_transverse_frames"]:
        for i in range(n + 1):
            _create_member(
                "beam", LT[i], RT[i],
                section_key=sections["chord_beam"],
                material=material,
                role="top_transverse",
            )
            _create_member(
                "beam", LB[i], RB[i],
                section_key=sections["chord_beam"],
                material=material,
                role="bottom_transverse",
            )

    # Top and bottom X bracing
    if PARAMS["create_top_x_bracing"]:
        for i in range(n):
            _create_member(
                "brace", LT[i], RT[i + 1],
                section_key=sections["cross_brace"],
                material=material,
                role="top_x_braces",
            )
            _create_member(
                "brace", RT[i], LT[i + 1],
                section_key=sections["cross_brace"],
                material=material,
                role="top_x_braces",
            )

    if PARAMS["create_bottom_x_bracing"]:
        for i in range(n):
            _create_member(
                "brace", LB[i], RB[i + 1],
                section_key=sections["cross_brace"],
                material=material,
                role="bottom_x_braces",
            )
            _create_member(
                "brace", RB[i], LB[i + 1],
                section_key=sections["cross_brace"],
                material=material,
                role="bottom_x_braces",
            )

    # Support columns and independent foundations
    ground_z = float(PARAMS["ground_z"])
    foundation_section = None
    foundation_total_height = 0.0
    if support_indices:
        foundation_section, foundation_total_height = _make_foundation_section()
    foundation_angle = float(PARAMS["foundation_angle_deg"])
    for i in support_indices:
        left_base = _point(LB[i][0], LB[i][1], ground_z)
        right_base = _point(RB[i][0], RB[i][1], ground_z)

        left_column = _create_member(
            "column", left_base, LB[i],
            section_key=sections["support_column"],
            material=material,
            role="supports",
        )
        if left_column is not None:
            _create_foundation(
                left_base,
                section_key=foundation_section,
                total_height=foundation_total_height,
                angle_deg=foundation_angle,
            )

        right_column = _create_member(
            "column", right_base, RB[i],
            section_key=sections["support_column"],
            material=material,
            role="supports",
        )
        if right_column is not None:
            _create_foundation(
                right_base,
                section_key=foundation_section,
                total_height=foundation_total_height,
                angle_deg=foundation_angle,
            )

    print("\n=== PlantS 通廊空间桁架创建完成 ===")
    print("参数:", PARAMS)
    print("构件统计:")
    for role, keys in created.items():
        print(f"  {role}: {len(keys)}")
    print(f"created={stats['created']}, modified={stats['modified']}, failed={stats['failed']}")
    if stats["warnings"]:
        print("\n警告:")
        for msg in stats["warnings"]:
            print(" -", msg)

    return {
        "params": PARAMS,
        "nodes": nodes,
        "created": created,
        "stats": stats,
    }


result = create_corridor()
