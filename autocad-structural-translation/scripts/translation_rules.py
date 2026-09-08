"""Pure, conservative checks used by translation planning. No CAD dependencies."""
import math
import re
from collections import Counter


def protected_tokens(raw):
    """Partial token safety check; domain review still required for symbol meaning."""
    fields = re.findall(r"%<.*?>%",raw,re.S)
    without_fields = re.sub(r"%<.*?>%","",raw,flags=re.S)
    return Counter(fields+re.findall(r"<>|\[\]|%%[a-zA-Z]|\\U\+[0-9A-Fa-f]{4}|[A-Za-z]+\d*(?:\.\d+)?|\d+(?:\.\d+)?|[≤≥±ØΦφ∅@=:/×+−-]",without_fields))


def rectangle_overlap(a,b,clearance=0.):
    return not (a[2]+clearance < b[0] or b[2]+clearance < a[0]
                or a[3]+clearance < b[1] or b[3]+clearance < a[1])


def segment_hits_box(p,q,box):
    """Liang–Barsky clipping; detects a line crossing the label, not just endpoints."""
    dx,dy=q[0]-p[0],q[1]-p[1]
    low,high=0.,1.
    for den,num in ((-dx,p[0]-box[0]),(dx,box[2]-p[0]),(-dy,p[1]-box[1]),(dy,box[3]-p[1])):
        if abs(den)<1e-12:
            if num<0:
                return False
            continue
        t=num/den
        if den<0:
            low=max(low,t)
        else:
            high=min(high,t)
        if low>high:
            return False
    return True


def candidate_anchors(anchor,rotation,height,preferred=(0.,-1.2)):
    """Search order is a starting default, not a learned universal placement law."""
    if height<=0:
        raise ValueError("Positive visible text height required")
    offsets=[preferred,(0.,1.2),(1.,-1.2),(-1.,-1.2),(0.,-2.),(0.,2.),(2.,0.),(-2.,0.)]
    for u,v in offsets:
        yield [anchor[0]+height*(u*math.cos(rotation)-v*math.sin(rotation)),
               anchor[1]+height*(u*math.sin(rotation)+v*math.cos(rotation))]


def source_key(row):
    return row["instance_id"]+"::"+row["property"]


def validate_decisions(occurrences,manifest):
    """Enforce inventory accounting and skip-before-translate; not semantic proof."""
    all_sources={source_key(r):r for r in occurrences["texts"] if r["chinese"] and r["display_candidate"]}
    scope=manifest.get("scope")
    if scope:
        scoped=set(scope.get("source_keys",[]))
        sources={k:v for k,v in all_sources.items() if k in scoped}
    else:
        scoped=set(all_sources)
        sources=all_sources
    targets={e["instance_id"]:e for e in occurrences["entities"]}
    errors=[]
    decisions={}
    for item in manifest.get("decisions",[]):
        key=item.get("source_key")
        if key in decisions:
            errors.append(f"Duplicate source decision: {key}")
        decisions[key]=item
    for key,row in sources.items():
        item=decisions.get(key)
        if item is None:
            errors.append(f"Missing disposition: {key}")
            continue
        if item.get("source_raw")!=row["raw"]:
            errors.append(f"Stale source text: {key}")
        status=item.get("status")
        if status not in ("already_translated","needs_translation","uncertain_existing","excluded","blocked"):
            errors.append(f"Unknown disposition: {key}")
        if not item.get("existing_check",{}).get("completed"):
            errors.append(f"Existing-translation check not completed: {key}")
        if not item.get("reason"):
            errors.append(f"Missing reason: {key}")
        if status=="already_translated":
            linked=item.get("existing_english_ids",[])
            if not linked:
                errors.append(f"Skip has no English provenance: {key}")
            for ident in linked:
                target=targets.get(ident)
                if target is None or target.get("layout")!=row["layout"]:
                    errors.append(f"Invalid/mismatched English occurrence: {ident}")
                elif not target.get("effective_visible",False):
                    errors.append(f"English is not visible: {ident}")
                elif not any(re.search(r"[A-Za-z]",str(v)) for v in target.get("text",{}).values()):
                    errors.append(f"Linked occurrence has no English text field: {ident}")
            if item.get("new_english") or item.get("placement"):
                errors.append(f"Already-translated source must not receive new text: {key}")
        elif status=="needs_translation":
            if item.get("existing_english_ids"):
                errors.append(f"Existing counterpart conflicts with needs_translation: {key}")
        elif item.get("new_english") or item.get("placement"):
            errors.append(f"Non-actionable source has a proposed write: {key}")
    for key in decisions.keys()-sources.keys():
        item=decisions[key]
        if key not in all_sources:
            errors.append(f"Decision refers to unknown source: {key}")
        elif item.get("status") in ("needs_translation","translated") or item.get("new_english") or item.get("placement"):
            errors.append(f"Actionable decision outside scope: {key}")
    if occurrences.get("gaps") and manifest.get("claims_complete"):
        errors.append("Cannot claim complete coverage with unresolved occurrence gaps")
    if occurrences.get("summary",{}).get("extraction_errors",0) and manifest.get("claims_complete"):
        errors.append("Cannot claim complete coverage with extraction errors")
    return errors


def main():
    import argparse
    import json
    from pathlib import Path
    p=argparse.ArgumentParser(description="Validate occurrence dispositions; does not approve translation meaning or collision-free placement.")
    p.add_argument("occurrences")
    p.add_argument("manifest")
    p.add_argument("--scope",help="optional scope.json; required for strict selected-mode validation")
    args=p.parse_args()
    manifest=json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    if args.scope:
        manifest["scope"]=json.loads(Path(args.scope).read_text(encoding="utf-8"))
    errors=validate_decisions(json.loads(Path(args.occurrences).read_text(encoding="utf-8")),manifest)
    print(json.dumps({"passed":not errors,"errors":errors},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))


if __name__=="__main__":
    main()
