# -*- coding: utf-8 -*-
"""
ifc_to_web.py — 单个 IFC 模型 → 可公网访问的 three.js 查看器（一键流程）

用法:
    python ifc_to_web.py <模型.ifc> [--name "模型名"] [--out <输出目录>]
                         [--public-url https://...] [--icon-emoji 🏢]

功能:
    1. 解析 IFC：楼层 IfcBuildingStorey + 构件(柱/梁/板/墙/其他) 数量与三角网格
    2. 按 (楼层, 构件类型) 分组、去重合并顶点，导出单个 model.glb + manifest.json
    3. 从模板渲染 index.html（three.js 查看器）与 link.html（分享落地页）
    4. 全程只依赖 ifcopenshell + numpy（前端 three.js 走 CDN，无需本地构建）

产物结构（--out 目录）:
    model.glb        三角形网格 + 材质（按 F{楼层}_{类型} 命名 mesh 节点）
    manifest.json    楼层/类型/统计等元数据（页面 UI 据此动态生成）
    index.html       three.js 查看器（楼层开关 / 构件类型开关 / 视角切换）
    link.html        分享落地页（"打开模型"入口，可放公网链接）

坐标与单位约定（实测 YJK → IFC 导出）:
    - ifcopenshell 几何默认已转成"米"（除非文件单位本就非 mm），顶点为世界坐标。
    - IFC 是 Z-up，glTF/three.js 是 Y-up，导出时做 (x,y,z) → (x,z,-y)。
    - 模型会平移到包围盒中心，保证相机好取景。
"""
import argparse
import json
import os
import struct
import sys
import time

import numpy as np

# 默认处理的构件类型。KEY 会写进 mesh 节点名与 manifest；颜色为 RGB 0~1。
TYPE_DEFS = [
    ("COLUMN", "IfcColumn", "柱",  [0.90, 0.22, 0.21]),
    ("BEAM",   "IfcBeam",   "梁",  [0.12, 0.53, 0.90]),
    ("SLAB",   "IfcSlab",   "板",  [0.26, 0.63, 0.28]),
    ("WALL",   "IfcWall",   "墙",  [0.98, 0.55, 0.00]),
]
# 可选补充类型（若 IFC 中存在则纳入，避免漏构件）。默认不启用，需要时用 --extra-types。
EXTRA_TYPE_DEFS = [
    ("MEMBER", "IfcMember",        "斜撑", [0.55, 0.45, 0.90]),
    ("PLATE",  "IfcPlate",         "板件", [0.85, 0.75, 0.30]),
    ("FOOTING","IfcFooting",       "基础", [0.40, 0.40, 0.40]),
    ("STAIR",  "IfcStair",         "楼梯", [0.70, 0.55, 0.30]),
    ("RAMP",   "IfcRamp",          "坡道", [0.60, 0.60, 0.50]),
    ("CURTAINWALL", "IfcCurtainWall", "幕墙", [0.30, 0.75, 0.80]),
]

VIEWER_TEMPLATE = None  # 由运行时从模板文件加载（--template-dir 或脚本同目录 assets/viewer.html）


# ---------- GLB 序列化 ----------
def write_glb(meshes, materials, out_path):
    """meshes: [{name, verts(f32 Nx3), faces(u32 Mx3), material_idx}], 所有坐标已世界化/居中。"""
    buf = bytearray()
    bufferViews = []
    accessors = []
    nodes = []
    mesh_defs = []

    for mi, mesh in enumerate(meshes):
        verts = mesh["verts"]
        faces = mesh["faces"]
        pos_bytes = verts.tobytes()
        idx_bytes = faces.tobytes()

        pos_off = len(buf)
        buf += pos_bytes
        idx_off = len(buf)
        buf += idx_bytes

        bv_pos = len(bufferViews)
        bufferViews.append({"buffer": 0, "byteOffset": pos_off, "byteLength": len(pos_bytes), "target": 34962})
        bv_idx = len(bufferViews)
        bufferViews.append({"buffer": 0, "byteOffset": idx_off, "byteLength": len(idx_bytes), "target": 34963})

        acc_pos = len(accessors)
        accessors.append({"bufferView": bv_pos, "componentType": 5126, "count": int(len(verts)),
                          "type": "VEC3",
                          "min": [float(x) for x in verts.min(axis=0)],
                          "max": [float(x) for x in verts.max(axis=0)]})
        acc_idx = len(accessors)
        accessors.append({"bufferView": bv_idx, "componentType": 5125, "count": int(len(faces) * 3),
                          "type": "SCALAR"})

        prim = {"attributes": {"POSITION": acc_pos}, "indices": acc_idx,
                "material": mesh["material_idx"], "mode": 4}
        mesh_defs.append({"primitives": [prim], "name": mesh["name"]})
        nodes.append({"mesh": mi, "name": mesh["name"]})

    gltf = {
        "asset": {"version": "2.0", "generator": "ifc_to_web"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": mesh_defs,
        "materials": materials,
        "buffers": [{"byteLength": len(buf)}],
        "bufferViews": bufferViews,
        "accessors": accessors,
    }
    json_str = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    while len(json_str) % 4 != 0:
        json_str += b" "
    while len(buf) % 4 != 0:
        buf += b"\x00"
    total = 12 + 8 + len(json_str) + 8 + len(buf)
    with open(out_path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(json_str), 0x4E4F534A))
        f.write(json_str)
        f.write(struct.pack("<II", len(buf), 0x004E4942))
        f.write(buf)


# ---------- IFC 解析与几何提取 ----------
def build_type_defs(extra=False):
    t = [list(x) for x in TYPE_DEFS]
    if extra:
        # 把 EXTRA 中在文件里真实存在的类型也加进来，避免 UI 出现空类型
        for e in EXTRA_TYPE_DEFS:
            if not any(x[0] == e[0] for x in t):
                t.append(list(e))
    return t


def extract_ifc(ifc_path, extra_types=False):
    """返回 (floors, type_defs, type_count, meta, glb_meshes)"""
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element

    t0 = time.time()
    m = ifcopenshell.open(ifc_path)

    # 楼层按标高升序；若 IFC 没有 IfcBuildingStorey，则归为单一「整体」层，避免漏构件
    storeys = sorted(m.by_type("IfcBuildingStorey"), key=lambda s: s.Elevation)
    fallback_single_floor = len(storeys) == 0
    floor_idx_of = {s.id(): i for i, s in enumerate(storeys)}
    floors = []
    if fallback_single_floor:
        floors.append({"index": 0, "num": 1, "name": "整体", "label": "整体", "elevation": 0.0})
    for i, s in enumerate(storeys):
        elev = float(s.Elevation) if s.Elevation is not None else 0.0
        # ifcopenshell 的 IfcBuildingStorey.Elevation 通常是原单位(mm)，这里转 m 展示
        if abs(elev) > 200:  # 启发式：超过 200 判定为 mm 表示
            elev = elev / 1000.0
        floors.append({
            "index": i,
            "num": i + 1,  # 楼层显示序号（从 1 起），mesh 节点名 F{num}_{KEY} 与前端开关均用它
            "name": str(s.Name),
            "label": f"{s.Name}层",
            "elevation": round(elev, 2),
        })

    type_defs = build_type_defs(extra_types)

    # 先探查各类构件实际数量，筛掉为 0 的类型（避免空 checkbox）
    present = []
    for t in type_defs:
        try:
            n = len(m.by_type(t[1]))
        except Exception:
            n = 0
        if n > 0:
            present.append(t)
    if not present:
        present = type_defs
    type_defs = present

    # 构件 → (floor_idx, type_key)；无楼层时全部归入 0
    products, id_map, type_count = [], {}, {t[0]: 0 for t in type_defs}
    for key, tname, *_ in type_defs:
        for e in m.by_type(tname):
            c = ifcopenshell.util.element.get_container(e)
            if fallback_single_floor:
                products.append(e)
                id_map[e.id()] = (0, key)
                type_count[key] += 1
                continue
            if c is None:
                continue
            fi = floor_idx_of.get(c.id())
            if fi is None:
                continue
            products.append(e)
            id_map[e.id()] = (fi, key)
            type_count[key] += 1

    print(f"楼层 {len(storeys)} | 待提取构件 {len(products)} | 类型: { {t[0]: type_count[t[0]] for t in type_defs} }",
          flush=True)

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.WELD_VERTICES, True)

    groups, offsets, failures = {}, {}, 0
    processed = 0
    it = ifcopenshell.geom.iterator(settings, m, 1, include=products)
    if it.initialize():
        while True:
            shp = it.get()
            processed += 1
            k = id_map.get(shp.id) or id_map.get(getattr(shp, "guid", None))
            if k is None:
                failures += 1
            else:
                try:
                    verts = np.array(shp.geometry.verts, dtype=np.float32).reshape(-1, 3)
                    faces = np.array(shp.geometry.faces, dtype=np.uint32).reshape(-1, 3)
                    if len(faces):
                        g = groups.setdefault(k, {"verts": [], "faces": []})
                        off = offsets.get(k, 0)
                        g["verts"].append(verts)
                        g["faces"].append(faces + off)
                        offsets[k] = off + len(verts)
                except Exception:
                    failures += 1
            if processed % 1000 == 0:
                print(f"  已处理 {processed} 构件…", flush=True)
            if not it.next():
                break
    print(f"几何提取完成：{processed} 个，失败 {failures}，用时 {time.time()-t0:.1f}s", flush=True)

    if not groups:
        raise RuntimeError("没有任何可渲染构件：请检查 IFC 是否含 IfcBuildingStorey 层级，或尝试 --extra-types")

    concat_verts, final_groups = [], {}
    for k, g in groups.items():
        v = np.concatenate(g["verts"], axis=0)
        f = np.concatenate(g["faces"], axis=0)
        concat_verts.append(v)
        final_groups[k] = (v, f)

    allv = np.concatenate(concat_verts, axis=0)
    vmin, vmax = allv.min(axis=0), allv.max(axis=0)
    center = (vmin + vmax) / 2.0
    scale = 1.0  # ifcopenshell 几何已为米
    size = (vmax - vmin) * scale
    print(f"模型尺寸(米) W={size[0]:.1f} D={size[1]:.1f} H={size[2]:.1f}，中心已平移到原点", flush=True)

    # Z-up → Y-up 并居中
    meshes = []
    type_mat_idx = {t[0]: i for i, t in enumerate(type_defs)}
    for k in sorted(final_groups.keys()):
        fi, key = k
        v, f = final_groups[k]
        v = (v - center) / scale
        x, y, z = v[:, 0], v[:, 1], v[:, 2]
        v = np.stack([x, z, -y], axis=1).astype(np.float32)
        meshes.append({
            "name": f"F{fi+1}_{key}",
            "verts": v,
            "faces": f,
            "material_idx": type_mat_idx[key],
        })

    return floors, type_defs, type_count, {
        "elements": len(products),
        "failures": failures,
    }, meshes


# ---------- manifest / 模板渲染 ----------

def build_link_html(model_name, floors, type_defs, public_url, glb_mb, elements, icon="🏢"):
    n_floors = len(floors)
    labels = " / ".join(t[2] for t in type_defs)
    url = public_url or "index.html"
    link_attr = 'class="open" href="index.html"' if not public_url else 'class="open" target="_blank" rel="noopener" href="%s"' % public_url
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{model_name} · 在线查看</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ height:100%; }}
  body {{ background:#0f1216; color:#e8edf2;
    font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
    display:flex; align-items:center; justify-content:center; padding:24px; }}
  .card {{ width:min(720px,100%); background:#171b21; border:1px solid #2b333d;
    border-radius:16px; padding:34px 32px 30px; }}
  .tag {{ font-size:12px; color:#7d8894; letter-spacing:.14em; margin-bottom:14px; }}
  h1 {{ font-size:23px; font-weight:600; line-height:1.45; margin-bottom:8px; }}
  .meta {{ font-size:13.5px; color:#7d8894; margin-bottom:22px; }}
  .linkbox {{ background:#0f1216; border:1px solid #2b333d; border-radius:10px;
    padding:14px 16px; margin-bottom:22px; font-family:Consolas,"SF Mono",monospace;
    font-size:12.5px; line-height:1.7; color:#6fb0ff; word-break:break-all; }}
  a.open {{ display:inline-block; background:#1e6fd9; color:#fff; text-decoration:none;
    font-size:15px; padding:11px 30px; border-radius:9px; font-weight:500; }}
  a.open:hover {{ background:#2a7ce8; }}
  .hint {{ margin-top:16px; font-size:12.5px; color:#5f6a76; }}
  @media (max-width:640px) {{
    .card {{ padding:26px 20px 24px; }} h1 {{ font-size:19px; }}
    .linkbox {{ font-size:11px; padding:12px 13px; }}
    a.open {{ display:block; text-align:center; padding:13px 0; }}
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="tag">模型分享 · {icon}</div>
    <h1>{model_name}</h1>
    <div class="meta">{n_floors} 层 · {elements} 个构件 · {labels} 可分层查看　|　手机电脑都能打开，无需安装软件</div>
    <div class="linkbox">{public_url or "本地预览地址（部署后填写公网链接）"}</div>
    <a {link_attr}>打开模型</a>
    <div class="hint">点击后等待 2–5 秒加载，模型约 {glb_mb:.1f} MB</div>
  </div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="IFC 结构模型 → three.js 网页查看器（一键生成 model.glb + index.html + link.html）")
    ap.add_argument("ifc", help="输入的 .ifc 文件路径")
    ap.add_argument("--name", default=None, help="模型显示名（默认取 IFC 文件名）")
    ap.add_argument("--out", default=None, help="输出目录（默认 <ifc所在目录>/web_ifc）")
    ap.add_argument("--public-url", default=None, help="公网 URL（用于 link.html 展示与跳转）")
    ap.add_argument("--icon", default="🏢", help="分享页图标 emoji")
    ap.add_argument("--extra-types", action="store_true", help="尝试包含 IfcMember/IfcPlate 等更多类型")
    ap.add_argument("--template-dir", default=None, help="含 viewer.html 模板的目录（默认脚本同目录 assets/）")
    args = ap.parse_args()

    if not os.path.isfile(args.ifc):
        sys.exit(f"找不到 IFC 文件: {args.ifc}")

    model_name = args.name or os.path.splitext(os.path.basename(args.ifc))[0]
    out_dir = args.out or os.path.join(os.path.dirname(os.path.abspath(args.ifc)), "web_ifc")
    os.makedirs(out_dir, exist_ok=True)

    # 模板目录：--template-dir 优先，其次脚本同目录 assets/，再次脚本同目录
    tpl_dir = args.template_dir
    if not tpl_dir:
        here = os.path.dirname(os.path.abspath(__file__))
        cand = [os.path.join(here, "assets"), here]
        for c in cand:
            if os.path.isfile(os.path.join(c, "viewer.html")):
                tpl_dir = c
                break
    if not tpl_dir:
        sys.exit("缺少 viewer.html 模板：请用 --template-dir 指定，或把模板放在脚本旁 assets/ 下")
    with open(os.path.join(tpl_dir, "viewer.html"), encoding="utf-8") as f:
        viewer_tpl = f.read()

    # 1. 提取
    floors, type_defs, type_count, meta, meshes = extract_ifc(args.ifc, extra_types=args.extra_types)
    total_tris = sum(len(m["faces"]) for m in meshes)

    # 2. GLB
    glb_path = os.path.join(out_dir, "model.glb")
    materials = [{"name": t[0],
                  "pbrMetallicRoughness": {"baseColorFactor": t[3] + [1.0],
                                           "metallicFactor": 0.0, "roughnessFactor": 0.9},
                  "doubleSided": True} for t in type_defs]
    write_glb(meshes, materials, glb_path)
    glb_mb = os.path.getsize(glb_path) / 1024 / 1024
    print(f"GLB: {glb_path} ({glb_mb:.2f} MB, {total_tris} 三角面)", flush=True)

    # 3. manifest
    node_names = [m["name"] for m in meshes]
    manifest = {
        "generator": "ifc_to_web / ifcopenshell -> GLB",
        "modelName": model_name,
        "floors": floors,
        "types": [{"key": t[0], "label": t[2], "count": type_count.get(t[0], 0),
                   "color": "#%02x%02x%02x" % (int(t[3][0]*255), int(t[3][1]*255), int(t[3][2]*255))}
                  for t in type_defs],
        "nodes": node_names,
        "stats": {
            "elements": meta["elements"],
            "triangles": total_tris,
            "glb_bytes": os.path.getsize(glb_path),
        },
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 4. 渲染 index.html 模板（替换占位符）
    logo_short = model_name[:2] if model_name else "BIM"
    html = (viewer_tpl
            .replace("{{MODEL_NAME}}", model_name)
            .replace("{{LOGO_SHORT}}", logo_short)
            .replace("{{TOTAL_ELEMENTS}}", str(meta["elements"]))
            .replace("{{TOTAL_FLOORS}}", str(len(floors))))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    # 5. link.html 分享落地页
    link_html = build_link_html(model_name, floors, type_defs, args.public_url,
                                glb_mb, meta["elements"], icon=args.icon)
    with open(os.path.join(out_dir, "link.html"), "w", encoding="utf-8") as f:
        f.write(link_html)

    print(f"\n完成！输出目录: {out_dir}")
    print(f"  - model.glb    ({glb_mb:.2f} MB)")
    print(f"  - manifest.json")
    print(f"  - index.html   查看器（本地验证: python -m http.server 8765 --bind 127.0.0.1 -d {out_dir}）")
    if args.public_url:
        print(f"  - link.html    分享页 (公网: {args.public_url})")
    else:
        print(f"  - link.html    分享页（部署后可用 --public-url 重新生成）")
    print("\n下一步：把输出目录通过 WorkBuddy「发布为应用」部署即可获得公网链接。")


if __name__ == "__main__":
    main()
