"""Reconcile a translation result offline; optional live checks are kept separate."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import time

from translation_rules import protected_tokens
from apply_translations import fingerprint_object
from placement_planner import build_obstacle_index, collision_keys


def fingerprint_mismatches(expected, current, tolerance=1e-6):
    """Return changed source properties, ignoring run-identification metadata."""
    ignored = {"source_key", "handle"}
    mismatches = []
    for name, wanted in expected.items():
        if name in ignored:
            continue
        actual = current.get(name)
        if isinstance(wanted, (int, float)) and not isinstance(wanted, bool):
            try:
                if abs(float(actual) - float(wanted)) > tolerance:
                    mismatches.append(name)
            except (TypeError, ValueError):
                mismatches.append(name)
        elif actual != wanted:
            mismatches.append(name)
    return mismatches


def _find_open_document(app, expected_path):
    expected = Path(expected_path).resolve()
    for candidate in app.Documents:
        try:
            if Path(candidate.FullName).resolve() == expected:
                return candidate
        except Exception:
            continue
    return None


def _save_document_with_state(doc):
    try:
        doc.Save()
    except Exception:
        try:
            if bool(doc.Saved):
                return
        except Exception:
            pass
        raise


def _close_document_with_state(app, doc, expected_path, timeout=15.0):
    try:
        doc.Close(False)
    except Exception:
        if _find_open_document(app, expected_path) is not None:
            raise
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _find_open_document(app, expected_path) is None:
            return
        time.sleep(0.25)
    raise RuntimeError("Output drawing remained open after Close")


def _open_document_with_state(app, expected_path):
    existing = _find_open_document(app, expected_path)
    if existing is not None:
        return existing
    try:
        return app.Documents.Open(str(Path(expected_path).resolve()))
    except Exception:
        existing = _find_open_document(app, expected_path)
        if existing is not None:
            return existing
        raise


def _entities_by_handle(final_occurrences):
    return {str(e.get("Handle", "")).upper(): e
            for e in final_occurrences.get("entities", []) if e.get("Handle")}


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def reconcile(scope, decisions, journal, final_occurrences):
    errors = []
    source_keys = set(scope.get("source_keys", []))
    rows = decisions.get("decisions", [])
    by_source = {}
    for row in rows:
        key = row.get("source_key")
        if key in by_source:
            errors.append("Duplicate decision: " + str(key))
        by_source[key] = row
    for key in source_keys - set(by_source):
        errors.append("Missing scoped decision: " + key)
    actionable = {"needs_translation", "translated"}
    for key, row in by_source.items():
        if key not in source_keys and row.get("status") in actionable:
            errors.append("Actionable decision outside scope: " + str(key))
    operations = journal.get("operations", journal.get("created", []))
    latest_operations = {}
    for operation in operations:
        if operation.get("source_key"):
            latest_operations[operation["source_key"]] = operation
    placed = {}
    handles = []
    for op in latest_operations.values():
        if op.get("status") != "placed":
            continue
        key = op.get("source_key")
        if key not in source_keys:
            errors.append("Placed operation outside scope: " + str(key))
        if key in placed:
            errors.append("Multiple placed operations for source: " + str(key))
        placed[key] = op
        if op.get("handle"):
            handles.append(str(op["handle"]).upper())
    for handle, count in Counter(handles).items():
        if count > 1:
            errors.append("Created handle reused: " + handle)
    entities = _entities_by_handle(final_occurrences)
    occurrence_ids = {e.get("instance_id"): e for e in final_occurrences.get("entities", [])}
    for key, row in by_source.items():
        status = row.get("status")
        if status == "already_translated" and not row.get("existing_english_ids"):
            errors.append("Existing translation lacks provenance: " + str(key))
        if status == "already_translated":
            for target_id in row.get("existing_english_ids", []):
                target = occurrence_ids.get(target_id)
                if target is None:
                    errors.append("Existing English missing from final inventory: " + str(target_id))
                elif not target.get("effective_visible", False):
                    errors.append("Existing English is not visible: " + str(target_id))
                elif not any(any(ch.isascii() and ch.isalpha() for ch in str(v))
                             for v in target.get("text", {}).values()):
                    errors.append("Existing counterpart contains no English: " + str(target_id))
        if status in actionable:
            op = placed.get(key)
            if op is None:
                errors.append("Translation has no placed journal operation: " + str(key))
                continue
            handle = str(op.get("handle", "")).upper()
            if handle and handle not in entities:
                errors.append("Created handle missing from final inventory: " + handle)
            raw = str(row.get("source_raw", ""))
            english = str(op.get("english", row.get("new_english", "")))
            required = protected_tokens(raw)
            actual = protected_tokens(english)
            missing = required - actual
            if missing:
                errors.append("Protected tokens changed for %s: %s" % (key, dict(missing)))
    repeat = final_occurrences.get("repeat_additions")
    if repeat is None:
        errors.append("Final verification did not record second-run additions")
    elif repeat:
        errors.append("Second run proposes additions: " + ", ".join(map(str, repeat)))
    counts = Counter(str(r.get("status")) for r in rows if r.get("source_key") in source_keys)
    return {"passed": not errors, "errors": errors, "scope_count": len(source_keys),
            "decision_counts": dict(counts), "placed_count": len(placed)}


def live_verify(output_dwg, source_dwg, expected_source_sha256, journal,
                final_occurrences=None, clearance=60.0, save_reopen=False):
    """Verify journaled objects in the live output; optionally save/reopen it."""
    from inspect_drawing import prepare_comtypes
    prepare_comtypes()
    from pyautocad import Autocad
    acad = Autocad(create_if_not_exists=False)
    doc = acad.doc
    output = Path(output_dwg).resolve()
    source = Path(source_dwg).resolve()
    errors, objects = [], []
    if Path(doc.FullName).resolve() != output:
        errors.append("Wrong active output drawing: " + str(doc.FullName))
        return {"passed": False, "errors": errors, "objects": objects}
    if _sha256(source) != expected_source_sha256:
        errors.append("Source disk SHA-256 does not match the pre-write value")
    latest = {}
    for operation in journal.get("operations", []):
        if operation.get("source_key"):
            latest[operation["source_key"]] = operation
    created_handles = {str(operation.get("handle", "")).upper()
                       for operation in latest.values()
                       if operation.get("status") == "placed" and operation.get("handle")}
    obstacle_index = None
    obstacle_gaps = []
    if final_occurrences is not None:
        obstacle_entities = [row for row in final_occurrences.get("entities", [])
                             if str(row.get("Handle", "")).upper() not in created_handles]
        obstacle_index, obstacle_gaps = build_obstacle_index(obstacle_entities)
    for key, operation in latest.items():
        if operation.get("status") != "placed":
            continue
        try:
            obj = acad.best_interface(doc.HandleToObject(operation["handle"]))
            text = str(obj.TextString)
            if text != str(operation["english"]):
                errors.append("Live English differs for " + key)
            style = operation.get("style", {})
            checks = {
                "StyleName": style.get("text_style"), "Layer": style.get("layer"),
                "Color": style.get("aci_color"), "Height": style.get("height"),
                "Rotation": style.get("rotation", 0.0),
            }
            mismatches = []
            for prop, expected in checks.items():
                if expected is None:
                    continue
                actual = getattr(obj, prop)
                if isinstance(expected, (int, float)):
                    if abs(float(actual) - float(expected)) > 1e-6:
                        mismatches.append(prop)
                elif str(actual) != str(expected):
                    mismatches.append(prop)
            low, high = obj.GetBoundingBox()
            objects.append({"source_key": key, "handle": operation["handle"],
                            "text": text, "bbox_xy": [low[0], low[1], high[0], high[1]],
                            "mismatches": mismatches})
            if mismatches:
                errors.append("Live style mismatch for %s: %s" % (key, ", ".join(mismatches)))
            if obstacle_index is not None:
                box = [float(low[0]), float(low[1]), float(high[0]), float(high[1])]
                hits = collision_keys(box, obstacle_index, float(clearance))
                if hits:
                    errors.append("Live English collision for %s: %s" %
                                  (key, ", ".join(hits[:20])))
                obstacle_index.add("verified-new:" + str(operation["handle"]), box,
                                   {"kind": "AcDbMText", "segments": []})
        except Exception as exc:
            errors.append("Cannot read created object for %s: %s" % (key, exc))
    for key, expected in journal.get("source_fingerprints", {}).items():
        try:
            source_obj = acad.best_interface(doc.HandleToObject(expected["handle"]))
            current = fingerprint_object(source_obj, expected["property"])
            mismatches = fingerprint_mismatches(expected, current)
            if mismatches:
                errors.append("Original source properties changed for %s: %s" %
                              (key, ", ".join(mismatches)))
        except Exception as exc:
            errors.append("Cannot verify original source for %s: %s" % (key, exc))
    if save_reopen and not errors:
        # Document-level calls can execute despite RPC rejection. Check actual state
        # before retrying to avoid duplicate opens or saves.
        _save_document_with_state(doc)
        _close_document_with_state(acad.app, doc, output)
        reopened = _open_document_with_state(acad.app, output)
        reopened.Activate()
        time.sleep(1.0)
        if Path(acad.doc.FullName).resolve() != output:
            errors.append("Save/reopen did not return to the expected output")
    return {"passed": not errors, "errors": errors, "objects": objects,
            "source_sha256": _sha256(source), "obstacle_gaps": obstacle_gaps}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope")
    parser.add_argument("decisions")
    parser.add_argument("journal")
    parser.add_argument("final_occurrences")
    parser.add_argument("--output")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output-dwg")
    parser.add_argument("--source-dwg")
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--save-reopen", action="store_true")
    args = parser.parse_args()
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    final_occurrences = load(args.final_occurrences)
    journal = load(args.journal)
    result = reconcile(load(args.scope), load(args.decisions), journal,
                       final_occurrences)
    if args.live:
        required = (args.output_dwg, args.source_dwg, args.expected_source_sha256)
        if not all(required):
            raise SystemExit("--live requires --output-dwg, --source-dwg and --expected-source-sha256")
        result["live"] = live_verify(args.output_dwg, args.source_dwg,
                                     args.expected_source_sha256, journal,
                                     final_occurrences, save_reopen=args.save_reopen)
        result["passed"] = result["passed"] and result["live"]["passed"]
        result["errors"].extend(result["live"]["errors"])
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(not result["passed"])


if __name__ == "__main__":
    main()
