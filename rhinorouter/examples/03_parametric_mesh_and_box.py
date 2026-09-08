"""03_parametric_mesh_and_box.py
示例 3：高级参数化几何建模与 VARIANT 数据封送转换机制。

核心攻关要点：
1. RhinoScript COM 源于 Windows OLE Automation (VBScript)，不能直接向 COM 方法传递 Python 原生嵌套列表。
2. 点数组/平面封送：使用 to_nested_variant_r8(...) 构造 VT_ARRAY | VT_VARIANT (内部嵌套 VT_R8)。
3. 面拓扑索引封送：使用 to_nested_variant_i4(...) 构造 VT_ARRAY | VT_VARIANT (内部嵌套 VT_I4)。
4. 纯数值浮点数组：使用 to_flat_variant_r8(...) 构造 VT_ARRAY | VT_R8。
5. 颜色值封装：使用 rgb(r, g, b) 构造 32 位整型 (COLORREF)。
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from rhinorouter import (
    find_rhino_process,
    get_rhino,
    rgb,
    to_flat_variant_i4,
    to_flat_variant_r8,
    to_nested_variant_i4,
    to_nested_variant_r8,
)


def verify_marshaling_types():
    print("=== 1. 本地 OLE VARIANT 数据封送格式校验 ===")

    # 1.1 嵌套浮点点坐标 (用于 AddBox, AddPolyline, AddMesh vertices)
    pts = [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)]
    v_pts = to_nested_variant_r8(pts)
    print(f"  [点坐标嵌套封送] 类型: {type(v_pts)}, 元素数: {len(v_pts.value)}, 首项内部类型: {type(v_pts.value[0])}")

    # 1.2 嵌套整数面索引 (用于 AddMesh arrFaceVertices)
    # 三角面后两项重复 [0, 1, 2, 2]，四边面为互异四项 [0, 1, 2, 3]
    faces = [[0, 1, 2, 2], [0, 2, 3, 3]]
    v_faces = to_nested_variant_i4(faces)
    print(f"  [网格面拓扑封送] 类型: {type(v_faces)}, 面数: {len(v_faces.value)}, 拓扑结构: {v_faces.value[0].value}")

    # 1.3 节点向量 (用于 NURBS knots)
    knots = [0, 0, 0, 0.5, 1, 1, 1]
    v_knots = to_flat_variant_r8(knots)
    print(f"  [节点向量平铺封送] 类型: {type(v_knots)}, 数值列表: {v_knots.value}")

    # 1.4 RGB 颜色封送
    col = rgb(255, 128, 0)
    print(f"  [RGB 颜色整型编码] RGB(255, 128, 0) -> {col} (0x{col:06X})\n")


def build_parametric_model():
    print("=== 2. Rhino COM 实际建模与实体生成 ===")

    pid, _, _, _ = find_rhino_process()
    if not pid:
        print("  [提示] 当前无运行中的 Rhino 进程。若需在 Rhino 画布中生成实体，请先启动 Rhino 软件，然后重新运行本脚本。")
        return

    result = get_rhino(auto_spawn=False)
    if isinstance(result, str):
        print(f"  [连接跳过] {result}")
        return

    rhino, rs, version = result
    print(f"  [连接成功] 正在 Rhino {version} (PID={pid}) 中执行参数化建模...")

    try:
        rs.EnableRedraw(False)

        # 2.1 准备图层
        layer = "Parametric_Models"
        if not rs.IsLayer(layer):
            rs.AddLayer(layer, rgb(255, 100, 50))
        rs.CurrentLayer(layer)

        # 2.2 实体长方体 (8 个角点，先底面逆时针，再顶面逆时针)
        box_pts = (
            (0, 0, 0), (200, 0, 0), (200, 200, 0), (0, 200, 0),
            (0, 0, 100), (200, 0, 100), (200, 200, 100), (0, 200, 100),
        )
        box_id = rs.AddBox(to_nested_variant_r8(box_pts))
        print(f"  - 长方体已生成: Box ID={box_id}")

        # 2.3 空间光滑样条曲线 (AddInterpCurve)
        curve_pts = [(0, 0, 150), (100, 50, 200), (200, 0, 150), (300, 100, 250)]
        curve_id = rs.AddInterpCurve(to_nested_variant_r8(curve_pts), 3)
        print(f"  - 3 次空间样条已生成: Curve ID={curve_id}")

        # 2.4 网格曲面构造 (AddMesh)
        mesh_verts = [
            (300, 0, 0), (400, 0, 50), (400, 100, 50), (300, 100, 0),
            (400, 0, 50), (500, 0, 0), (500, 100, 0), (400, 100, 50)
        ]
        mesh_faces = [
            [0, 1, 2, 3],  # 四边面
            [4, 5, 6, 7],  # 四边面
        ]
        mesh_id = rs.AddMesh(
            to_nested_variant_r8(mesh_verts),
            to_nested_variant_i4(mesh_faces),
        )
        print(f"  - 参数化网格已生成: Mesh ID={mesh_id}")

    finally:
        rs.EnableRedraw(True)
        print("  - 渲染已刷新完成！")


def main():
    verify_marshaling_types()
    build_parametric_model()


if __name__ == "__main__":
    main()
