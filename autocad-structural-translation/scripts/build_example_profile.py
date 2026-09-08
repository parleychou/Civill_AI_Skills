"""Build THIS exemplar's measured profile from the saved inventory, without CAD writes."""
import argparse
import hashlib
import json
from pathlib import Path
from analyze_inventory import flatten, local_offset, text_rows

# Reviewed associations for the 2026-09-07 exemplar ONLY. Never reuse these handles
# as mappings on a different drawing. The containing insert 916 is part of the key.
PAIRS = [
    ("8E5","91B","WL与钢梁搭接详图","Detailed Drawing of WL and Steel Beam Lapping","full"),
    ("75A","91C","中间跨","Middle Span","full"),
    ("801","91D","钢梁","Steel Beam","full"),
    ("6E4","91E","檩托详图","Purlin Bracket","abbreviated title; retains component but omits 'detail'"),
    ("75B","91F","边跨","Side Span","full"),
    ("8C5","920","钢梁","Steel Beam","full"),
    ("8D5","921","外挑尺寸","Overhang Dimension","full; dimension override"),
    ("824","922","钢梁","Steel Beam","full; English horizontal beside 5-degree Chinese"),
]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    blob=Path(args.inventory).read_bytes()
    data=json.loads(blob)
    entities,gaps=flatten(data)
    by_id={e["instance_id"]:e for e in entities}
    pairs=[]
    for ch,en,zh,english,quality in PAIRS:
        source=by_id["Model/"+ch]
        target=by_id["Model/916/"+en]
        prop="TextOverride" if "Dimension" in source["ObjectName"] else "TextString"
        if source["text"][prop]!=zh or target["text"]["TextString"]!=english:
            raise SystemExit("This is not the learned exemplar; do not reuse its handle mappings.")
        pairs.append({"source_id":source["instance_id"],"source_property":prop,
                      "source_raw":zh,"english_id":target["instance_id"],"english_raw":english,
                      "status":"already_translated","quality_note":quality,
                      "association_basis":"Reviewed semantic match and spatial position within the selected detail; individual repeated occurrences paired separately.",
                      "offset":local_offset(source,target),"source":source,"english":target})
    used={x["source_id"] for x in pairs}
    rows=list(text_rows(entities))
    remaining=[r for r in rows if r["chinese"] and r["display_candidate"] and r["instance_id"] not in used]
    profile={"drawing":data["drawing"],"captured_at":data["captured_at"],
             "inventory_sha256":hashlib.sha256(blob).hexdigest(),
             "application_version":data["application_version"],"pairs":pairs,
             "remaining_chinese_fields":remaining,"scope_note":"Only existing English examples are learned; candidate future wording is not drawing evidence.",
             "summary":{"confirmed_existing_pairs":len(pairs),"unique_observed_english":len({x[3] for x in PAIRS}),
                        "chinese_fields":sum(r["chinese"] and r["display_candidate"] for r in rows),
                        "remaining_chinese_fields":len(remaining),
                        "remaining_selected_chinese_fields":sum(r["selected"] for r in remaining),
                        "flattening_gaps":len(gaps)},
             "text_styles":data["text_styles"],
             "layer_facts":[l for l in data["layers"] if l["Name"] in ("EN","S-BEAM_CON","0","TEXT","DIM")],
             "integrity":{"selection_preserved":data["selected_handles"]==data["selection_after"],
                          "dbmod_before":data["variables"]["DBMOD"],"dbmod_after":data["dbmod_after"],
                          "extraction_errors":data["errors"]}}
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    (out/"learned-profile.json").write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding="utf-8")
    terms=[]
    for zh in dict.fromkeys(x[2] for x in PAIRS):
        examples=[x for x in pairs if x["source_raw"]==zh]
        terms.append({"chinese":zh,"observed_english":examples[0]["english_raw"],
                      "evidence":[x["source_id"]+" -> "+x["english_id"] for x in examples],
                      "quality_note":examples[0]["quality_note"]})
    (out/"observed-glossary.json").write_text(json.dumps({"drawing":data["drawing"],"terms":terms},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(profile["summary"],ensure_ascii=False))
    for x in pairs:
        print(x["source_id"],x["english_raw"],json.dumps(x["offset"]))


if __name__=="__main__":
    main()
