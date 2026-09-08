"""Build and validate strict selected- or drawing-scope translation manifests."""
import argparse
import hashlib
import json
from pathlib import Path

from translation_rules import source_key


def _chinese_rows(occurrences):
    return [r for r in occurrences.get("texts", [])
            if r.get("chinese") and r.get("display_candidate")]


def _path_has_handle(instance_id, handles):
    return any(part.upper() in handles for part in str(instance_id).split("/"))


def read_selection_handles(capture):
    """Read inspect_drawing.py output and tolerate older list-shaped captures."""
    if isinstance(capture, list):
        selected = capture
    else:
        selected = capture.get("handles", capture.get("selected", capture.get("selection", [])))
    return [str(x.get("Handle", x) if isinstance(x, dict) else x).upper()
            for x in selected]


def build_scope(occurrences, mode, selected_handles=()):
    """Return the immutable source-key boundary for one translation run.

    Selection is occurrence based. Selecting insert A includes Model/A/... but not
    another insertion of the same block definition at Model/B/....
    """
    if mode not in {"selected", "drawing"}:
        raise ValueError("mode must be selected or drawing")
    selected = {str(h).upper() for h in selected_handles}
    if mode == "selected" and not selected:
        raise ValueError("selected mode requires captured Pickfirst handles")
    rows = _chinese_rows(occurrences)
    if mode == "drawing":
        keys = [source_key(r) for r in rows]
    else:
        keys = [source_key(r) for r in rows
                if _path_has_handle(r.get("instance_id", ""), selected)]
    keys = sorted(set(keys))
    return {
        "mode": mode,
        "selected_handles": sorted(selected),
        "source_keys": keys,
        "source_count": len(keys),
        "inventory_chinese_count": len(rows),
        "selection_rule": "selected entity or descendant of selected insert occurrence",
    }


def validate_scope(scope, occurrences, live_selected_handles=None):
    errors = []
    mode = scope.get("mode")
    if mode not in {"selected", "drawing"}:
        errors.append("Invalid scope mode")
    keys = list(scope.get("source_keys", []))
    if len(keys) != len(set(keys)):
        errors.append("Duplicate source key in scope")
    known = {source_key(r) for r in _chinese_rows(occurrences)}
    for key in set(keys) - known:
        errors.append("Unknown scoped source: " + key)
    if scope.get("source_count") != len(keys):
        errors.append("Scope source_count does not match source_keys")
    if mode == "drawing" and set(keys) != known:
        errors.append("Drawing scope does not account for every Chinese display field")
    if mode == "selected":
        frozen = {str(h).upper() for h in scope.get("selected_handles", [])}
        if not frozen:
            errors.append("Selected scope has no frozen Pickfirst handles")
        if not keys:
            errors.append("Selected scope contains no Chinese display fields")
        if live_selected_handles is not None:
            live = {str(h).upper() for h in live_selected_handles}
            if live != frozen:
                errors.append("Pickfirst selection changed after scope capture")
        for key in keys:
            ident = key.split("::", 1)[0]
            if not _path_has_handle(ident, frozen):
                errors.append("Selected scope leaked outside frozen selection: " + key)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("occurrences")
    parser.add_argument("--mode", choices=("selected", "drawing"), required=True)
    parser.add_argument("--selection", help="selection.json from inspect_drawing.py")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    occurrence_path = Path(args.occurrences)
    occurrences = json.loads(occurrence_path.read_text(encoding="utf-8"))
    handles = []
    if args.selection:
        capture = json.loads(Path(args.selection).read_text(encoding="utf-8"))
        handles = read_selection_handles(capture)
    scope = build_scope(occurrences, args.mode, handles)
    scope["occurrences_sha256"] = hashlib.sha256(occurrence_path.read_bytes()).hexdigest()
    errors = validate_scope(scope, occurrences)
    if errors:
        raise SystemExit("; ".join(errors))
    Path(args.output).write_text(json.dumps(scope, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mode": args.mode, "sources": scope["source_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
