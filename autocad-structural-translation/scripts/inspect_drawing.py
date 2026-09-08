"""Read-only AutoCAD inventory via pyautocad. Never executes drawing commands."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


TEXT_PROPS = (
    "TextString", "TextOverride", "TextPrefix", "TextSuffix",
    "AltTextPrefix", "AltTextSuffix", "MTextAttributeContent", "TagString",
    "PromptString", "HyperlinkDescription",
)
BASE = ("Handle", "ObjectName", "ObjectID", "OwnerID", "Layer", "Color",
        "Visible", "Linetype", "Lineweight", "EntityTransparency")
TEXT_FORMAT = (
    "StyleName", "TextStyle", "TextStyleName", "Height", "TextHeight", "Width",
    "ScaleFactor", "Rotation", "TextRotation", "ObliqueAngle", "Alignment",
    "AttachmentPoint", "InsertionPoint", "TextAlignmentPoint", "TextPosition",
    "Normal", "Backward", "UpsideDown", "TextGenerationFlag", "DrawingDirection",
    "LineSpacingFactor", "LineSpacingStyle", "BackgroundFill", "Invisible",
    "MTextAttribute", "Constant", "Measurement", "UnitsFormat", "PrimaryUnitsPrecision",
)
BLOCK_PROPS = ("Name", "EffectiveName", "InsertionPoint", "Rotation", "Normal",
               "XScaleFactor", "YScaleFactor", "ZScaleFactor", "IsDynamicBlock",
               "HasAttributes", "Path", "Rows", "Columns", "RowSpacing", "ColumnSpacing")
GEOMETRY = ("StartPoint", "EndPoint", "Coordinates", "Center", "Radius", "Closed",
            "StartAngle", "EndAngle", "Elevation", "Thickness", "Normal")
TEXT_FAMILIES = ("Text", "Attribute", "Dimension", "MLeader", "Tolerance", "Table", "GeoPosition")


def prepare_comtypes():
    """Host-tested fix for missing SAFEARRAY dispatch mappings; process local only."""
    import ctypes
    import comtypes
    import comtypes.automation as automation
    patched = []
    for vt, typ in ((automation.VT_DISPATCH, ctypes.POINTER(automation.IDispatch)),
                    (automation.VT_UNKNOWN, ctypes.POINTER(comtypes.IUnknown))):
        if vt not in automation._vartype_to_ctype:
            automation._vartype_to_ctype[vt] = typ
            patched.append(vt)
    return patched


def serial(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return [serial(x) for x in value]
    return str(value)


class Scanner:
    def __init__(self, acad):
        self.acad = acad
        self.errors = []
        self.unsupported = Counter()

    def call(self, fn):
        for attempt in range(6):
            try:
                return fn()
            except Exception as exc:
                hr = getattr(exc, "hresult", None)
                if hr not in (-2147418111, -2147417846) or attempt == 5:
                    raise
                time.sleep(0.2 * (attempt + 1))

    def get(self, obj, name, required=False, context=""):
        try:
            return serial(self.call(lambda: getattr(obj, name)))
        except Exception as exc:
            if required:
                self.errors.append({"context": context, "operation": name, "error": str(exc)})
            else:
                self.unsupported[name] += 1
            return None

    def props(self, obj, names, context=""):
        result = {}
        for name in names:
            value = self.get(obj, name, context=context)
            if value is not None:
                result[name] = value
        return result

    def cast(self, obj):
        return self.call(lambda: self.acad.best_interface(obj))

    def entity(self, raw, container, selected, include_attributes=True):
        obj = self.cast(raw)
        rec = self.props(obj, BASE)
        handle = rec.get("Handle", "?")
        kind = rec.get("ObjectName", "unknown")
        rec.update(container=container, selected=handle in selected)
        try:
            rec["bbox"] = serial(self.call(obj.GetBoundingBox))
        except Exception as exc:
            rec["bbox_error"] = str(exc)
        try:
            rec["true_color"] = self.props(obj.TrueColor, ("ColorMethod", "ColorIndex", "Red", "Green", "Blue", "ColorName", "BookName"))
        except Exception:
            pass
        # Probe text properties even for unfamiliar/proxy objects. Optional probing
        # is not proof that those objects contain no text (see coverage report).
        rec["text"] = self.props(obj, TEXT_PROPS)
        if any(x in kind for x in ("Text", "Attribute", "Tolerance")) and "TextString" not in rec["text"]:
            self.get(obj, "TextString", True, handle)
        if rec["text"] or any(x in kind for x in TEXT_FAMILIES):
            rec.update(self.props(obj, TEXT_FORMAT))
            if any("%<" in str(v) for v in rec["text"].values()):
                rec["coverage_gap"] = "Field expression detected: preserve code and verify evaluated visible text separately."
        known = ("AcDbText", "AcDbMText", "AcDbAttribute", "AcDbAttributeDefinition",
                 "AcDbBlockReference", "AcDbMInsertBlock", "AcDbExternalReference",
                 "AcDbLeader", "AcDbMLeader", "AcDbTable", "AcDbFcf", "AcDbTolerance",
                 "AcDbLine", "AcDbPolyline", "AcDb2dPolyline", "AcDb3dPolyline",
                 "AcDbCircle", "AcDbArc", "AcDbEllipse", "AcDbSpline", "AcDbHatch",
                 "AcDbPoint", "AcDbSolid", "AcDbTrace", "AcDbFace")
        if kind not in known and "Dimension" not in kind:
            rec["coverage_gap"] = "Unclassified object family: inspect rendered text and supported ActiveX properties explicitly."
        if "Dimension" in kind:
            rec.update(self.props(obj, ("TextColor", "TextFill", "TextFillColor", "TextGap", "TextMovement", "TextInside", "TextInsideAlign", "TextOutsideAlign", "DimConstrDesc", "DimConstrExpression")))
            for prop in ("TextOverride", "TextPrefix", "TextSuffix"):
                if prop not in rec["text"]:
                    self.get(obj, prop, True, handle)
        if "BlockReference" in kind or "MInsertBlock" in kind or "ExternalReference" in kind:
            rec.update(self.props(obj, BLOCK_PROPS))
            if include_attributes:
                for method in ("GetAttributes", "GetConstantAttributes"):
                    try:
                        attrs = self.call(lambda: getattr(obj, method)())
                        rec[method] = [self.entity(a, container + "/insert:" + handle,
                                                  selected, False) for a in attrs]
                    except Exception as exc:
                        self.errors.append({"context": handle, "operation": method, "error": str(exc)})
        if kind == "AcDbLeader":
            rec.update(self.props(obj, ("Coordinates", "Type", "Annotation")))
            try:
                rec["annotation_handle"] = self.get(obj.Annotation, "Handle")
            except Exception:
                pass
        if kind == "AcDbMLeader":
            rec.update(self.props(obj, ("ContentType", "ContentBlockName", "TextHeight", "TextWidth", "TextRotation", "TextStyleName", "TextLineSpacingFactor", "ScaleFactor")))
            if rec.get("ContentType") == 1:
                rec["coverage_gap"] = "Block-content MLeader: inspect content block and per-instance GetBlockAttributeValue values."
        if kind == "AcDbTable":
            rec.update(self.props(obj, ("Rows", "Columns", "InsertionPoint", "Direction")))
            rec["cells"] = []
            for row in range(int(rec.get("Rows", 0))):
                for col in range(int(rec.get("Columns", 0))):
                    cell = {"row": row, "column": col}
                    for method in ("GetText", "GetFormula", "GetCellType", "GetCellTextHeight", "GetCellTextStyle"):
                        try:
                            cell[method] = serial(self.call(lambda m=method: getattr(obj, m)(row, col)))
                        except Exception as exc:
                            if method == "GetText":
                                self.errors.append({"context": f"{handle}[{row},{col}]", "operation": method, "error": str(exc)})
                    rec["cells"].append(cell)
            rec["coverage_gap"] = "Inspect multi-content cells, fields, merged cells and cell blocks before declaring table coverage complete."
        if any(x in kind for x in ("Line", "Circle", "Arc", "Polyline", "Spline", "Ellipse", "Hatch")):
            rec["geometry"] = self.props(obj, GEOMETRY)
            if kind == "AcDbPolyline":
                n = len(rec["geometry"].get("Coordinates", [])) // 2
                try:
                    rec["geometry"]["bulges"] = [obj.GetBulge(i) for i in range(n)]
                except Exception as exc:
                    rec["geometry"]["bulge_error"] = str(exc)
        try:
            rec["hyperlinks"] = [self.props(link, ("URL", "URLDescription", "URLNamedLocation")) for link in obj.Hyperlinks]
        except Exception:
            pass
        return rec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-name", required=True)
    parser.add_argument("--expect-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    from pyautocad import Autocad
    patched_types = prepare_comtypes()
    acad = Autocad(create_if_not_exists=False)
    scan = Scanner(acad)
    doc = acad.doc
    name, full_name = doc.Name, doc.FullName
    if name.casefold() != args.expect_name.casefold():
        raise SystemExit(f"Active document mismatch: {full_name}")
    if args.expect_path and Path(full_name).resolve() != Path(args.expect_path).resolve():
        raise SystemExit(f"Active path mismatch: {full_name}")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    selected = [str(obj.Handle) for obj in doc.PickfirstSelectionSet]
    selection_file = output / "selection.json"
    # Do not overwrite a prior capture: the original exemplar set is valuable.
    if selection_file.exists() or (output / "inventory.json").exists():
        raise SystemExit("Output already contains a capture; choose a fresh --output directory.")
    selection_file.write_text(json.dumps({"drawing": full_name, "handles": selected}, ensure_ascii=False, indent=2), encoding="utf-8")
    selected_set = set(selected)
    data = {"schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(),
            "drawing": full_name, "name": name, "selected_handles": selected,
            "application_version": acad.app.Version,
            "document_before": scan.props(doc, ("Saved", "ReadOnly", "ActiveSpace")),
            "layouts": [], "blocks": [], "layers": [], "text_styles": [], "dim_styles": []}
    data["comtypes_process_local_mappings_added"] = patched_types
    data["variables"] = {}
    for var in ("INSUNITS", "LUNITS", "LUPREC", "DIMSCALE", "CANNOSCALE", "TILEMODE", "CTAB", "DBMOD"):
        try:
            data["variables"][var] = serial(doc.GetVariable(var))
        except Exception as exc:
            scan.errors.append({"context": "document", "operation": var, "error": str(exc)})
    print(f"Connected: {full_name}; selected={len(selected)}", flush=True)
    for collection, key, names in (
        (doc.Layers, "layers", ("Name", "Color", "LayerOn", "Freeze", "Lock", "Linetype", "Lineweight", "Plottable")),
        (doc.TextStyles, "text_styles", ("Name", "FontFile", "BigFontFile", "Height", "Width", "ObliqueAngle", "TextGenerationFlag")),
        (doc.DimStyles, "dim_styles", ("Name",)),
    ):
        for obj in collection:
            obj = scan.cast(obj)
            rec = scan.props(obj, names)
            if key == "text_styles":
                try:
                    rec["font"] = serial(obj.GetFont())
                except Exception as exc:
                    rec["font_error"] = str(exc)
            if key == "layers":
                try:
                    rec["true_color"] = scan.props(obj.TrueColor, ("ColorMethod", "ColorIndex", "Red", "Green", "Blue"))
                except Exception:
                    pass
            data[key].append(rec)
    count = 0
    for block in doc.Blocks:
        meta = scan.props(block, ("Name", "Handle", "IsLayout", "IsXRef", "Origin", "Path", "Count"))
        container = "block:" + str(meta.get("Name", "?"))
        if meta.get("IsLayout"):
            try:
                meta["layout_name"] = block.Layout.Name
                container = "layout:" + meta["layout_name"]
            except Exception as exc:
                scan.errors.append({"context": container, "operation": "Layout", "error": str(exc)})
        records = []
        try:
            n = int(block.Count)
            for i in range(n):
                try:
                    records.append(scan.entity(block.Item(i), container, selected_set))
                except Exception as exc:
                    scan.errors.append({"context": f"{container}[{i}]", "operation": "entity", "error": str(exc)})
                count += 1
                if count % 250 == 0:
                    print(f"Inspected {count} objects", flush=True)
        except Exception as exc:
            scan.errors.append({"context": container, "operation": "block", "error": str(exc)})
        meta["entities"] = records
        data["layouts" if meta.get("IsLayout") else "blocks"].append(meta)
    data["errors"] = scan.errors
    data["unsupported_property_probe_counts"] = dict(scan.unsupported)
    data["document_after"] = scan.props(doc, ("Saved", "ReadOnly", "ActiveSpace"))
    data["selection_after"] = [str(obj.Handle) for obj in doc.PickfirstSelectionSet]
    data["dbmod_after"] = doc.GetVariable("DBMOD")
    data["active_document_after"] = acad.doc.FullName
    kinds = Counter(e.get("ObjectName") for b in data["layouts"] + data["blocks"] for e in b["entities"])
    data["summary"] = {"enumerated_entities": count, "selected": len(selected), "types": dict(kinds),
                       "errors": len(scan.errors), "layouts": len(data["layouts"]), "blocks": len(data["blocks"])}
    (output / "inventory.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
