"""Flatten supported DWG occurrences and export an auditable text inventory offline."""
import argparse
from collections import Counter
import csv
import itertools
import json
import math
from pathlib import Path
import re

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]")
IDENTITY = (1., 0., 0., 1., 0., 0.)


def plain_text(raw):
    # Comparison text only. Never write this lossy normalization back to CAD.
    value = re.sub(r"\\U\+([0-9a-fA-F]{4})", lambda m: chr(int(m[1], 16)), raw)
    value = re.sub(r"\\[Pp]", "\n", value)
    value = value.replace(r"\~", " ")
    value = re.sub(r"\\[ACcFfHhQqTtWw][^;]*;", "", value)
    value = re.sub(r"\\[LlOoKk]", "", value)
    return value.replace("{", "").replace("}", "").strip()


def normalize(raw):
    return " ".join(plain_text(raw).split()).casefold()


def point(matrix, p):
    a, b, c, d, tx, ty = matrix
    return [a*p[0]+c*p[1]+tx, b*p[0]+d*p[1]+ty, p[2] if len(p)>2 else 0.]


def compose(parent, child):
    a,b,c,d,x,y = parent
    e,f,g,h,u,v = child
    return (a*e+c*f, b*e+d*f, a*g+c*h, b*g+d*h, a*u+c*v+x, b*u+d*v+y)


def insert_matrix(insert, origin):
    rot = insert.get("Rotation", 0.)
    sx,sy = insert.get("XScaleFactor",1.),insert.get("YScaleFactor",1.)
    a,b,c,d = math.cos(rot)*sx, math.sin(rot)*sx, -math.sin(rot)*sy, math.cos(rot)*sy
    p = insert["InsertionPoint"]
    return (a,b,c,d,p[0]-a*origin[0]-c*origin[1],p[1]-b*origin[0]-d*origin[1])


def bounds(matrix, box):
    points = [point(matrix, (x,y,0)) for x,y in itertools.product(
        (box[0][0],box[1][0]), (box[0][1],box[1][1]))]
    return [min(p[0] for p in points),min(p[1] for p in points),
            max(p[0] for p in points),max(p[1] for p in points)]


def flatten(data):
    blocks = {b["Name"]:b for b in data["blocks"]}
    layers = {l["Name"]:l for l in data["layers"]}
    output, gaps = [], []
    selected = set(data["selected_handles"])

    def walk(entities, matrix, layout, prefix, ancestry, inherited_layer="0", inherited_color=7, selected_parent=False, parent_visible=True):
        for e in entities:
            key = prefix + [e["Handle"]]
            instance_id = layout + "/" + "/".join(key)
            normal = e.get("Normal", e.get("geometry",{}).get("Normal", [0,0,1]))
            if any(abs(normal[i]-[0,0,1][i])>1e-8 for i in range(3)):
                gaps.append({"id":instance_id,"reason":"Non-+Z OCS requires full 3D/viewport projection."})
                continue
            own_layer = e.get("Layer","0")
            layer = inherited_layer if own_layer=="0" and prefix else own_layer
            layer_rec = layers.get(layer,{})
            col = e.get("Color",256)
            effective_color = inherited_color if col==0 else layer_rec.get("Color",7) if col==256 else col
            kind = e.get("ObjectName","")
            selected_here = selected_parent or e["Handle"] in selected
            record = dict(e, instance_id=instance_id, occurrence_path=key, layout=layout,
                          selected_occurrence=selected_here, effective_layer=layer,
                          effective_aci=effective_color, matrix_xy=list(matrix),
                          effective_visible=parent_visible and e.get("Visible",True) and not e.get("Invisible",False)
                              and layer_rec.get("LayerOn",True) and not layer_rec.get("Freeze",False))
            if e.get("bbox"):
                record["bbox_xy"] = bounds(matrix,e["bbox"])
            anchor = e.get("InsertionPoint",e.get("TextPosition"))
            if anchor:
                record["anchor_xy"] = point(matrix,anchor)[:2]
            rotation = e.get("TextRotation",e.get("Rotation",0.))
            ux,uy = math.cos(rotation),math.sin(rotation)
            a,b,c,d,_,_ = matrix
            record["rotation_xy"] = math.atan2(b*ux+d*uy,a*ux+c*uy)
            record["height_xy"] = e.get("Height",e.get("TextHeight",0.))*math.hypot(-a*uy+c*ux,-b*uy+d*ux)
            output.append(record)
            if e.get("coverage_gap"):
                gaps.append({"id":instance_id,"reason":e["coverage_gap"]})
            for name in ("GetAttributes","GetConstantAttributes"):
                # Attribute refs already use their owner's containing coordinate
                # system. Applying the insert matrix again would move them twice.
                walk(e.get(name,[]),matrix,layout,key,ancestry,layer,effective_color,selected_here,record["effective_visible"])
            if "BlockReference" in kind or "MInsertBlock" in kind or "ExternalReference" in kind:
                block_name = e.get("Name")
                block = blocks.get(block_name)
                if not block or block_name in ancestry:
                    gaps.append({"id":instance_id,"reason":"Missing block or cyclic reference", "block":block_name})
                    continue
                if block.get("IsXRef"):
                    gaps.append({"id":instance_id,"reason":"External reference: inspect host-visible clipping/overrides and referenced document separately."})
                if kind=="AcDbMInsertBlock":
                    gaps.append({"id":instance_id,"reason":"MINSERT grid requires each row/column occurrence; not flattened by this helper."})
                    continue
                if e.get("IsDynamicBlock"):
                    gaps.append({"id":instance_id,"reason":"Dynamic instance: actual Name traversed; verify visibility state and clipping."})
                transform = compose(matrix,insert_matrix(e,block.get("Origin",[0,0,0])))
                walk(block["entities"],transform,layout,key,ancestry+[block_name],layer,effective_color,selected_here,record["effective_visible"])

    for layout in data["layouts"]:
        walk(layout["entities"], IDENTITY,layout["layout_name"],[],[])
    return output,gaps


def text_rows(records):
    for e in records:
        for prop,raw in e.get("text",{}).items():
            if not isinstance(raw,str) or not raw:
                continue
            plain = plain_text(raw)
            yield dict(instance_id=e["instance_id"], handle=e["Handle"], property=prop,
                       raw=raw, plain=plain, chinese=bool(CJK.search(plain)),
                       display_candidate=prop not in ("TagString","PromptString","HyperlinkDescription"),
                       selected=e["selected_occurrence"], layout=e["layout"],
                       layer=e["effective_layer"],visible=e["effective_visible"],
                       anchor=e.get("anchor_xy"),height=e.get("height_xy"),rotation=e.get("rotation_xy"))
        for cell in e.get("cells",[]):
            raw = cell.get("GetText","")
            if raw:
                yield dict(instance_id=e["instance_id"],handle=e["Handle"],
                           property=f"cell[{cell['row']},{cell['column']}]",raw=raw,
                           plain=plain_text(raw),chinese=bool(CJK.search(plain_text(raw))),
                           display_candidate=True,selected=e["selected_occurrence"],
                           layout=e["layout"],layer=e["effective_layer"],visible=e["effective_visible"])


def local_offset(source, target):
    sx,sy = source["anchor_xy"]
    ex,ey = target["anchor_xy"]
    r = source["rotation_xy"]
    dx,dy = ex-sx,ey-sy
    h = source["height_xy"]
    return {"dx":dx,"dy":dy,"along_h":(dx*math.cos(r)+dy*math.sin(r))/h,
            "above_h":(-dx*math.sin(r)+dy*math.cos(r))/h,
            "english_height_ratio":target["height_xy"]/h,
            "rotation_delta_deg":math.degrees(target["rotation_xy"]-r)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory")
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    data=json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    records,gaps=flatten(data)
    rows=list(text_rows(records))
    summary={"occurrences":len(records),"text_fields":len(rows),
             "chinese_display_fields":sum(r["chinese"] and r["display_candidate"] for r in rows),
             "selected_chinese_display_fields":sum(r["chinese"] and r["display_candidate"] and r["selected"] for r in rows),
             "extraction_errors":len(data["errors"]),"flattening_gaps":len(gaps)}
    (out/"occurrences.json").write_text(json.dumps({"summary":summary,"gaps":gaps,"entities":records,"texts":rows},ensure_ascii=False,indent=2),encoding="utf-8")
    with (out/"texts.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        fields=("instance_id","handle","property","raw","plain","chinese","display_candidate","selected","layout","layer","visible","anchor","height","rotation")
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary,ensure_ascii=False))


if __name__=="__main__":
    main()
