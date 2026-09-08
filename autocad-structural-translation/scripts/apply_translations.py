"""Apply a reviewed translation manifest to an explicit DWG copy through pyautocad.

The default is a no-CAD dry run. Pass --apply to permit creating English MTEXT in
the output copy. This helper never uses AutoLISP, SendCommand, or a second CAD API.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

from scope_manifest import validate_scope
from translation_rules import validate_decisions
from placement_planner import build_obstacle_index, collision_keys


TRANSIENT_HRESULTS = ("-2147418111", "-2147417846", "RPC_E_CALL_REJECTED")
FINGERPRINT_PROPERTIES = ("ObjectName", "Layer", "Color", "Visible", "StyleName",
                          "Height", "Rotation", "ScaleFactor", "TextStyle",
                          "TextHeight")


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def call_retry(fn, tries=7, base=0.25):
    last = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as exc:  # COM errors vary by generated interface
            last = exc
            if not any(code.lower() in str(exc).lower() for code in TRANSIENT_HRESULTS):
                raise
            if attempt + 1 < tries:
                time.sleep(base * (2 ** attempt))
    raise last


def fingerprint_object(obj, text_property):
    """Capture source text and stable presentation properties before any write."""
    snapshot = {"property": str(text_property),
                "value": str(getattr(obj, text_property))}
    for name in FINGERPRINT_PROPERTIES:
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            snapshot[name] = value
        else:
            snapshot[name] = str(value)
    return snapshot


def capture_source_fingerprints(doc, scan, occurrences, scope):
    entities = {row["instance_id"]: row for row in occurrences.get("entities", [])}
    snapshots = {}
    for key in scope.get("source_keys", []):
        instance_id, text_property = key.split("::", 1)
        source = entities.get(instance_id)
        if source is None:
            raise RuntimeError("Cannot fingerprint missing source occurrence: " + key)
        obj = _source_object(doc, scan, source)
        snapshot = fingerprint_object(obj, text_property)
        snapshot.update({"source_key": key, "handle": str(source["Handle"]).upper()})
        snapshots[key] = snapshot
    return snapshots


def _plan_rows(plan):
    rows = {}
    groups = {}
    for item in plan.get("plan", plan.get("placements", [])):
        if item.get("status") == "blocked":
            continue
        if item.get("placements"):
            gid = item.get("group_id", "column-" + str(len(groups) + 1))
            groups[gid] = item["placements"]
            for row in item["placements"]:
                rows[row["source_key"]] = dict(row, group_id=gid)
        elif item.get("source_key"):
            rows[item["source_key"]] = item
    return rows, groups


def execution_batches(plan_rows):
    """Return deterministic all-or-none column batches plus individual batches."""
    grouped, singles = {}, []
    for key, row in plan_rows.items():
        group_id = row.get("group_id")
        if group_id:
            grouped.setdefault(str(group_id), []).append(key)
        else:
            singles.append(key)
    batches = [sorted(grouped[group_id]) for group_id in sorted(grouped)]
    batches.extend([[key] for key in sorted(singles)])
    return batches


def latest_operation_map(journal):
    latest = {}
    for operation in journal.get("operations", []):
        if operation.get("source_key"):
            latest[operation["source_key"]] = operation
    return latest


def completed_sources(journal, plan_rows):
    """Count a column complete only when every planned member is placed."""
    latest = latest_operation_map(journal)
    completed = {key for key, row in plan_rows.items()
                 if not row.get("group_id") and latest.get(key, {}).get("status") == "placed"}
    groups = {}
    for key, row in plan_rows.items():
        if row.get("group_id"):
            groups.setdefault(str(row["group_id"]), set()).add(key)
    for members in groups.values():
        if all(latest.get(key, {}).get("status") == "placed" for key in members):
            completed.update(members)
    return completed


def validate_resume_journal(journal, source_path, output_path, scope, source_hash):
    errors = []
    if Path(journal.get("source_dwg", "")).resolve() != Path(source_path).resolve():
        errors.append("Journal source DWG does not match this run")
    if Path(journal.get("output_dwg", "")).resolve() != Path(output_path).resolve():
        errors.append("Journal output DWG does not match this run")
    if journal.get("source_sha256") != source_hash:
        errors.append("Journal source SHA-256 does not match the current source disk")
    if journal.get("scope") != scope:
        errors.append("Journal scope does not match the frozen scope")
    return errors


def validate_run_inputs(occurrences, scope, manifest, plan):
    errors = validate_scope(scope, occurrences)
    checked = dict(manifest)
    checked["scope"] = scope
    errors.extend(validate_decisions(occurrences, checked))
    rows, _groups = _plan_rows(plan)
    decisions = {d.get("source_key"): d for d in manifest.get("decisions", [])}
    for key in scope.get("source_keys", []):
        decision = decisions.get(key)
        if not decision:
            continue
        if decision.get("status") == "uncertain_existing":
            errors.append("Uncertain counterpart must be reviewed before writing: " + key)
        if decision.get("status") == "needs_translation":
            if not decision.get("new_english"):
                errors.append("Missing reviewed English: " + key)
            if key not in rows:
                errors.append("Missing placement for translatable source: " + key)
    for key in set(rows) - set(scope.get("source_keys", [])):
        errors.append("Placement outside scope: " + key)
    return errors


def _source_object(doc, scan, source_record):
    return scan.cast(call_retry(lambda: doc.HandleToObject(source_record["Handle"])))


def _collection_for_layout(doc, layout_name):
    for block in doc.Blocks:
        if bool(block.IsLayout) and str(block.Layout.Name) == str(layout_name):
            return block
    raise RuntimeError("Layout not found: " + str(layout_name))


def _style(decision, manifest):
    style = dict(manifest.get("default_style", {}))
    style.update(decision.get("placement_style", {}))
    required = ("text_style", "height", "layer", "aci_color")
    missing = [name for name in required if name not in style]
    if missing:
        raise RuntimeError("Missing reviewed style fields: " + ", ".join(missing))
    return style


def _set_mtext(mt, style, width):
    mt.StyleName = style["text_style"]
    mt.Height = float(style["height"])
    mt.Width = float(width)
    mt.AttachmentPoint = int(style.get("attachment", 1))
    mt.Rotation = float(style.get("rotation", 0.0))
    mt.Layer = style["layer"]
    mt.Color = int(style["aci_color"])
    mt.LineSpacingFactor = float(style.get("line_spacing_factor", 1.0))
    mt.LineSpacingStyle = int(style.get("line_spacing_style", 1))
    mt.BackgroundFill = bool(style.get("background_fill", False))
    mt.Update()


def _measure_width(collection, scan, APoint, text, style, maximum):
    probe = scan.cast(call_retry(lambda: collection.AddText(text, APoint(0, 0, 0), float(style["height"]))))
    try:
        probe.StyleName = style["text_style"]
        probe.Height = float(style["height"])
        if "width_factor" in style:
            probe.ScaleFactor = float(style["width_factor"])
        probe.Update()
        low, high = call_retry(probe.GetBoundingBox)
        return min(float(maximum), float(high[0] - low[0] + style.get("width_margin", 140.0)))
    finally:
        call_retry(probe.Delete)


def _journal_transition(journal_path, journal, operation):
    journal.setdefault("operations", []).append(operation)
    write_json(journal_path, journal)


def apply_one(doc, scan, APoint, source, decision, placement, manifest,
              journal, journal_path, obstacle_index):
    key = decision["source_key"]
    prop = key.split("::", 1)[1]
    live = _source_object(doc, scan, source)
    if str(call_retry(lambda: getattr(live, prop))) != str(decision["source_raw"]):
        raise RuntimeError("Source changed before insertion: " + key)
    if not decision.get("existing_check", {}).get("completed"):
        raise RuntimeError("Existing-English check is stale or absent: " + key)
    collection = _collection_for_layout(doc, source["layout"])
    style = _style(decision, manifest)
    text = decision["new_english"]
    _journal_transition(journal_path, journal,
                        {"source_key": key, "status": "intent", "english": text})
    maximum = float(style.get("max_width", placement.get("width", 3000.0)))
    width = _measure_width(collection, scan, APoint, text, style, maximum)
    anchor = placement["anchor"]
    mt = scan.cast(call_retry(lambda: collection.AddMText(APoint(anchor[0], anchor[1], 0), width, text)))
    created = {"source_key": key, "status": "created_unplaced", "handle": str(mt.Handle),
               "english": text, "style": style, "group_id": placement.get("group_id")}
    _journal_transition(journal_path, journal, created)
    try:
        _set_mtext(mt, style, width)
        low, high = call_retry(mt.GetBoundingBox)
        box = [float(low[0]), float(low[1]), float(high[0]), float(high[1])]
        clearance = float(manifest.get("placement_policy", {}).get("clearance", 60.0))
        hits = collision_keys(box, obstacle_index, clearance)
        if hits:
            raise RuntimeError("Measured English box collides with: " + ", ".join(hits[:20]))
        placed = dict(created, status="placed", anchor=list(anchor), bbox_xy=box, width=width)
        _journal_transition(journal_path, journal, placed)
        obstacle_index.add("new:" + str(mt.Handle), box,
                           {"kind": "AcDbMText", "segments": []})
        return mt, placed
    except Exception:
        call_retry(mt.Delete)
        _journal_transition(journal_path, journal, dict(created, status="deleted_error"))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--occurrences", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--source-dwg", required=True)
    parser.add_argument("--output-dwg", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--expect-active", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--apply", action="store_true", help="permit writes to the explicit output copy")
    parser.add_argument("--dry-run", action="store_true", help="explicit alias for the safe default")
    args = parser.parse_args()

    source_path, output_path = Path(args.source_dwg).resolve(), Path(args.output_dwg).resolve()
    if source_path == output_path:
        raise SystemExit("Source and output DWG must differ")
    load_json(args.inventory)  # prove the declared inventory is readable JSON
    occurrences, scope = load_json(args.occurrences), load_json(args.scope)
    expected_occurrences_hash = scope.get("occurrences_sha256")
    if expected_occurrences_hash and sha256(args.occurrences) != expected_occurrences_hash:
        raise SystemExit("Occurrences file does not match the frozen scope hash")
    manifest, plan = load_json(args.manifest), load_json(args.plan)
    errors = validate_run_inputs(occurrences, scope, manifest, plan)
    if errors:
        raise SystemExit("\n".join(errors))
    plan_rows, groups = _plan_rows(plan)
    summary = {"mode": scope["mode"], "sources": len(scope["source_keys"]),
               "translations": sum(d.get("status") == "needs_translation" for d in manifest["decisions"]),
               "planned": len(plan_rows), "column_groups": len(groups)}
    if not args.apply:
        print("DRY RUN — no AutoCAD connection and no DWG writes")
        print(json.dumps(summary, ensure_ascii=False))
        return
    if not source_path.exists():
        raise SystemExit("Source DWG not found")
    if output_path.exists() and not args.resume:
        raise SystemExit("Refusing existing output without --resume")

    from inspect_drawing import Scanner, prepare_comtypes
    prepare_comtypes()
    from pyautocad import Autocad, APoint
    acad = Autocad(create_if_not_exists=False)
    doc = acad.doc
    scan = Scanner(acad)
    if Path(doc.FullName).resolve() != Path(args.expect_active).resolve():
        raise SystemExit("Wrong active drawing: " + doc.FullName)
    if not args.resume and Path(doc.FullName).resolve() != source_path:
        raise SystemExit("Fresh apply must start from the source drawing")
    if args.resume and Path(doc.FullName).resolve() != output_path:
        raise SystemExit("Resume must start from the output drawing")
    if scope["mode"] == "selected" and not args.resume:
        live_selection = [str(obj.Handle).upper() for obj in doc.PickfirstSelectionSet]
        selection_errors = validate_scope(scope, occurrences, live_selection)
        if selection_errors:
            raise SystemExit("\n".join(selection_errors))

    source_hash = sha256(source_path)
    journal_path = Path(args.journal)
    if args.resume:
        journal = load_json(journal_path)
        journal_errors = validate_resume_journal(journal, source_path, output_path,
                                                 scope, source_hash)
        if journal_errors:
            raise SystemExit("\n".join(journal_errors))
    else:
        source_fingerprints = capture_source_fingerprints(doc, scan, occurrences, scope)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        recovery = output_path.with_name(output_path.stem + ".before-translation.dwg")
        if recovery.exists():
            raise SystemExit("Recovery path already exists")
        doc.SaveAs(str(output_path))
        shutil.copy2(output_path, recovery)
        journal = {"run_version": 2, "source_dwg": str(source_path),
                   "output_dwg": str(output_path), "source_sha256": source_hash,
                   "scope": scope, "source_fingerprints": source_fingerprints,
                   "operations": []}
        write_json(journal_path, journal)

    # Resume never trusts an incomplete object. Delete only a logged object whose
    # live text and handle still identify this run, then retry that source.
    latest = latest_operation_map(journal)
    completed = completed_sources(journal, plan_rows)
    # A stopped column is not partially complete. Remove only live objects whose
    # latest journal state, handle and text prove ownership by this run.
    incomplete_group_keys = {key for key, row in plan_rows.items()
                             if row.get("group_id") and key not in completed}
    for key in sorted(incomplete_group_keys):
        op = latest.get(key, {})
        if op.get("status") not in {"placed", "created_unplaced"} or not op.get("handle"):
            continue
        try:
            partial = scan.cast(doc.HandleToObject(op["handle"]))
            if str(partial.TextString) != str(op.get("english")):
                raise RuntimeError("Incomplete group handle text does not match journal: " + key)
            call_retry(partial.Delete)
            _journal_transition(journal_path, journal,
                                dict(op, status="rolled_back_incomplete_group"))
        except RuntimeError:
            raise
        except Exception:
            _journal_transition(journal_path, journal,
                                dict(op, status="incomplete_group_handle_not_found"))
    latest = latest_operation_map(journal)
    completed = completed_sources(journal, plan_rows)
    for op in list(journal.get("operations", [])):
        if op.get("status") != "created_unplaced" or op["source_key"] in completed:
            continue
        try:
            orphan = scan.cast(doc.HandleToObject(op["handle"]))
            if str(orphan.TextString) == str(op["english"]):
                call_retry(orphan.Delete)
                _journal_transition(journal_path, journal, dict(op, status="deleted_orphan_on_resume"))
        except Exception:
            _journal_transition(journal_path, journal, dict(op, status="orphan_not_found_on_resume"))

    obstacle_index, obstacle_gaps = build_obstacle_index(
        occurrences["entities"],
        float(manifest.get("placement_policy", {}).get("grid_size", 4000.0)))
    if obstacle_gaps and manifest.get("claims_collision_complete", False):
        raise RuntimeError("Cannot claim complete collision coverage with unbounded obstacles")
    for key in completed:
        op = latest[key]
        if op.get("bbox_xy"):
            obstacle_index.add("existing-run:" + str(op.get("handle", key)), op["bbox_xy"],
                               {"kind": "AcDbMText", "segments": []})

    entities = {e["instance_id"]: e for e in occurrences["entities"]}
    decisions = {d["source_key"]: d for d in manifest["decisions"]}
    pending_rows = {key: row for key, row in plan_rows.items()
                    if decisions[key].get("status") == "needs_translation" and key not in completed}
    for batch in execution_batches(pending_rows):
        created_batch = []
        try:
            for key in batch:
                decision = decisions[key]
                source = entities[key.split("::", 1)[0]]
                mt, placed = apply_one(doc, scan, APoint, source, decision,
                                       pending_rows[key], manifest, journal,
                                       journal_path, obstacle_index)
                created_batch.append((key, mt, placed))
        except Exception:
            if len(batch) > 1:
                for key, mt, placed in reversed(created_batch):
                    try:
                        call_retry(mt.Delete)
                        _journal_transition(journal_path, journal,
                                            dict(placed, status="rolled_back_group"))
                    except Exception as cleanup_error:
                        _journal_transition(journal_path, journal,
                                            dict(placed, status="rollback_failed",
                                                 cleanup_error=str(cleanup_error)))
            raise
        if not created_batch:
            continue
        call_retry(doc.Save)
    if sha256(source_path) != source_hash:
        raise RuntimeError("Source disk hash changed during output-copy write")
    print(json.dumps(summary | {"status": "saved", "output": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
