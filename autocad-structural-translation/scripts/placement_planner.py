"""Offline spatial rehearsal for individual and aligned-column English overlays."""
import argparse
import json
import math
from pathlib import Path

from translation_rules import rectangle_overlap, segment_hits_box


class SpatialIndex:
    def __init__(self, cell_size=4000.0):
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")
        self.cell_size = float(cell_size)
        self.cells = {}

    def _cells(self, box):
        for x in range(math.floor(box[0] / self.cell_size), math.floor(box[2] / self.cell_size) + 1):
            for y in range(math.floor(box[1] / self.cell_size), math.floor(box[3] / self.cell_size) + 1):
                yield x, y

    def add(self, key, box, payload=None):
        item = {"key": str(key), "box": list(map(float, box)), "payload": payload}
        for cell in self._cells(item["box"]):
            self.cells.setdefault(cell, []).append(item)

    def query(self, box):
        found = {}
        for cell in self._cells(box):
            for item in self.cells.get(cell, ()):
                if item["key"] not in found and rectangle_overlap(box, item["box"]):
                    found[item["key"]] = item
        return [found[k] for k in sorted(found)]


def _point(matrix, point):
    a, b, c, d, tx, ty = matrix
    return [a * point[0] + c * point[1] + tx,
            b * point[0] + d * point[1] + ty]


def build_obstacle_index(entities, cell_size=4000.0):
    """Index visible obstacles and report objects whose bounds remain unknown."""
    index, gaps = SpatialIndex(cell_size), []
    for entity in entities:
        if not entity.get("effective_visible", True):
            continue
        kind = entity.get("ObjectName")
        if kind in {"AcDbPoint", "AcDbBlockReference", "AcDbAttributeDefinition"}:
            continue
        if entity.get("effective_layer") == "DEFPOINTS":
            continue
        box = entity.get("bbox_xy")
        raw = "".join(str(v) for v in entity.get("text", {}).values()).strip()
        if box is None and kind in {"AcDbText", "AcDbAttribute", "AcDbAttributeReference"} and not raw:
            continue
        if box is None:
            gaps.append({"id": entity.get("instance_id"), "reason": "visible obstacle has no bounds"})
            continue
        geometry = entity.get("geometry", {})
        matrix = entity.get("matrix_xy", [1, 0, 0, 1, 0, 0])
        segments = []
        if kind == "AcDbLine" and "StartPoint" in geometry and "EndPoint" in geometry:
            segments = [(_point(matrix, geometry["StartPoint"]),
                         _point(matrix, geometry["EndPoint"]))]
        elif kind == "AcDbPolyline" and not any(geometry.get("bulges", [1])):
            coords = geometry.get("Coordinates", [])
            vertices = [_point(matrix, [coords[i], coords[i + 1], 0])
                        for i in range(0, len(coords) - 1, 2)]
            segments = list(zip(vertices, vertices[1:]))
            if geometry.get("Closed") and vertices:
                segments.append((vertices[-1], vertices[0]))
        elif kind == "AcDbLeader":
            coords = entity.get("Coordinates", geometry.get("Coordinates", []))
            vertices = [_point(matrix, coords[i:i + 3]) for i in range(0, len(coords) - 2, 3)]
            segments = list(zip(vertices, vertices[1:]))
        index.add(entity.get("instance_id", entity.get("Handle", "?")), box,
                  {"kind": kind, "segments": segments})
    return index, gaps


def collision_keys(box, index, clearance=0.0, ignore=()):
    expanded = _expanded(box, clearance)
    ignored, hits = {str(x) for x in ignore}, []
    for item in index.query(expanded):
        if item["key"] in ignored:
            continue
        segments = (item.get("payload") or {}).get("segments", [])
        if segments and not any(segment_hits_box(a, b, expanded) for a, b in segments):
            continue
        hits.append(item["key"])
    return sorted(set(hits))


def estimate_text_box(text, height, width_factor=0.7, glyph_factor=0.50, max_width=3000.0):
    if height <= 0 or width_factor <= 0 or glyph_factor <= 0 or max_width <= 0:
        raise ValueError("text metrics must be positive")
    single = max(height, len(str(text)) * height * width_factor * glyph_factor + 140.0)
    width = min(single, max_width)
    lines = max(1, math.ceil(single / max_width))
    return {"width": width, "height": height * lines * 1.2, "estimated": True, "lines": lines}


def _edge_distance(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def _compatible(a, b, x_tolerance, spacing_ratio):
    if a.get("layout") != b.get("layout") or a.get("container") != b.get("container"):
        return False
    ah, bh = float(a.get("height_xy", 0)), float(b.get("height_xy", 0))
    if min(ah, bh) <= 0 or max(ah, bh) / min(ah, bh) > 1.5:
        return False
    return abs(a["bbox_xy"][0] - b["bbox_xy"][0]) <= x_tolerance * max(ah, bh)


def group_columns(sources, minimum_rows=3, x_tolerance=1.5, spacing_ratio=6.0):
    buckets = {}
    for source in sources:
        buckets.setdefault((source.get("layout"), source.get("container")), []).append(source)
    groups = []
    for key, rows in buckets.items():
        remaining = sorted(rows, key=lambda r: (-r["bbox_xy"][3], r["bbox_xy"][0]))
        current = []
        for source in remaining:
            if not current or _compatible(current[-1], source, x_tolerance, spacing_ratio):
                if current:
                    vertical_gap = current[-1]["bbox_xy"][1] - source["bbox_xy"][3]
                    if vertical_gap > spacing_ratio * max(current[-1]["height_xy"], source["height_xy"]):
                        if len(current) >= minimum_rows:
                            groups.append(current)
                        current = []
                current.append(source)
            else:
                if len(current) >= minimum_rows:
                    groups.append(current)
                current = [source]
        if len(current) >= minimum_rows:
            groups.append(current)
    return groups


def _expanded(box, clearance):
    return [box[0] - clearance, box[1] - clearance, box[2] + clearance, box[3] + clearance]


def plan_column(group, index, options=None):
    if len(group) < 3:
        return {"status": "blocked", "reason": "column mode requires at least three aligned rows"}
    options = options or {}
    clearance = float(options.get("clearance", 60.0))
    max_distance = float(options.get("max_distance", 1750.0))
    max_width = float(options.get("max_width", 3000.0))
    left = min(r["bbox_xy"][0] for r in group)
    right = max(r["bbox_xy"][2] for r in group)
    metrics = [estimate_text_box(r["english"], float(r["height_xy"]), max_width=max_width) for r in group]
    column_width = max(m["width"] for m in metrics)
    diagnostics = []
    for side in ("right", "left"):
        for gap in options.get("gaps", (90.0, 175.0, 350.0, 700.0)):
            x = right + gap if side == "right" else left - gap - column_width
            placements, hits, too_far = [], set(), []
            for source, metric in zip(group, metrics):
                top = source["bbox_xy"][3]
                box = [x, top - metric["height"], x + metric["width"], top]
                hits.update(collision_keys(box, index, clearance))
                distance = _edge_distance(box, source["bbox_xy"])
                if distance > max_distance:
                    too_far.append(source["source_key"])
                if any(rectangle_overlap(_expanded(box, clearance), old["box"])
                       for old in placements):
                    hits.add("same-column-row-overlap")
                placements.append({"source_key": source["source_key"], "anchor": [x, top],
                                   "box": box, "distance": distance, "estimated": True})
            diagnostics.append({"side": side, "gap": gap, "hits": sorted(hits), "too_far": too_far})
            if not hits and not too_far:
                return {"status": "placed", "mode": "column", "side": side,
                        "placements": placements, "diagnostics": diagnostics,
                        "atomic": True}
    return {"status": "blocked", "mode": "column", "atomic": True,
            "reason": "No collision-free, unambiguous column fits the configured distance",
            "diagnostics": diagnostics}


def plan_individual(source, english, index, options=None):
    options = options or {}
    clearance = float(options.get("clearance", 60.0))
    max_distance = float(options.get("max_distance", 1750.0))
    metric = estimate_text_box(english, float(source["height_xy"]),
                               max_width=float(options.get("max_width", 3000.0)))
    l, b, r, t = source["bbox_xy"]
    rejected = []
    for gap in options.get("gaps", (90.0, 175.0, 350.0, 700.0, 1050.0, 1400.0)):
        anchors = ((l, b-gap), (l, t+gap+metric["height"]),
                   (r+gap, t), (l-gap-metric["width"], t))
        for x, y in anchors:
            box = [x, y-metric["height"], x+metric["width"], y]
            hits = [h["key"] for h in index.query(_expanded(box, clearance))]
            distance = _edge_distance(box, source["bbox_xy"])
            if not hits and distance <= max_distance:
                return {"status": "placed", "mode": "individual", "anchor": [x, y],
                        "box": box, "distance": distance, "estimated": True,
                        "rejected": rejected}
            rejected.append({"anchor": [x, y], "hits": hits, "distance": distance})
    return {"status": "blocked", "mode": "individual",
            "reason": "No candidate passes clearance and distance", "rejected": rejected}


def plan_manifest(occurrences, scope, manifest, options=None):
    """Plan only scoped needs_translation decisions, with explicit column groups."""
    options = options or {}
    entities = {e["instance_id"]: e for e in occurrences.get("entities", [])}
    index, gaps = build_obstacle_index(occurrences.get("entities", []),
                                       float(options.get("grid_size", 4000.0)))
    scoped = set(scope.get("source_keys", []))
    candidates, blocked = {}, []
    for decision in manifest.get("decisions", []):
        key = decision.get("source_key")
        if key not in scoped or decision.get("status") != "needs_translation":
            continue
        ident = key.split("::", 1)[0]
        source = entities.get(ident)
        if source is None or source.get("bbox_xy") is None:
            blocked.append({"source_key": key, "status": "blocked",
                            "reason": "Source occurrence has no resolved bounds"})
            continue
        item = dict(source)
        item.update(source_key=key, english=decision.get("new_english", ""),
                    height_xy=float(decision.get("placement_style", {}).get(
                        "height", source.get("height_xy", 0) or 0)),
                    placement_group=decision.get("placement_group"))
        if not item["english"] or item["height_xy"] <= 0:
            blocked.append({"source_key": key, "status": "blocked",
                            "reason": "Reviewed English or positive text height is missing"})
            continue
        candidates[key] = item

    plan, consumed = [], set()
    groups = {}
    for key, source in candidates.items():
        if source.get("placement_group"):
            groups.setdefault(str(source["placement_group"]), []).append(source)
    for group_id in sorted(groups):
        rows = sorted(groups[group_id], key=lambda r: (-r["bbox_xy"][3], r["bbox_xy"][0]))
        compatible = group_columns(rows)
        if len(compatible) != 1 or len(compatible[0]) != len(rows):
            result = {"status": "blocked", "mode": "column", "atomic": True,
                      "reason": "Explicit column group is not one compatible aligned sequence",
                      "source_keys": [r["source_key"] for r in rows]}
        else:
            result = plan_column(rows, index, options)
            result["source_keys"] = [r["source_key"] for r in rows]
        result["group_id"] = group_id
        plan.append(result)
        consumed.update(result["source_keys"])
        if result["status"] == "placed":
            for placement in result["placements"]:
                index.add("planned:" + placement["source_key"], placement["box"],
                          {"kind": "AcDbMText", "segments": []})

    for key in sorted(set(candidates) - consumed):
        result = plan_individual(candidates[key], candidates[key]["english"], index, options)
        result["source_key"] = key
        plan.append(result)
        if result["status"] == "placed":
            index.add("planned:" + key, result["box"],
                      {"kind": "AcDbMText", "segments": []})
    plan.extend(blocked)
    placed_groups = [p for p in plan if p.get("status") == "placed"]
    placed_sources = sum(len(p.get("placements", [])) if p.get("mode") == "column" else 1
                         for p in placed_groups)
    return {"scope_mode": scope.get("mode"), "plan": plan,
            "obstacle_gaps": gaps,
            "summary": {"placed_groups": len(placed_groups),
                        "placed_sources": placed_sources,
                        "blocked_items": sum(p.get("status") == "blocked" for p in plan)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("occurrences")
    parser.add_argument("scope")
    parser.add_argument("manifest")
    parser.add_argument("--options", help="optional reviewed placement-policy JSON")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    options = load(args.options) if args.options else {}
    result = plan_manifest(load(args.occurrences), load(args.scope),
                           load(args.manifest), options)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
