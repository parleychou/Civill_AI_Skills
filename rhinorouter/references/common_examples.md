# Rhino Python COM 高频操作示例 (已校验)

本文件列举了使用 `rhinorouter` 进行自动化 3D 建模的高频最小可用示例。
写代码前先查阅；涉及创建复杂几何体或不确定的参数，先通过 `python scripts/get_function_detail.py <Module> <Func>` 查询。

所有示例默认已执行以下连接初始化代码：

```python
from rhinorouter import (
    get_rhino,
    to_nested_variant_r8,
    to_nested_variant_i4,
    to_flat_variant_r8,
    to_flat_variant_i4,
    rgb,
)

# 连接到已打开的 Rhino 或唤起新实例
rhino, script, version = get_rhino()
rs = script
```

---

## 1. 基础几何图元 (标量/单点参数，直接传 Python 原生类型)

```python
# 点与线段
pt_id = rs.AddPoint([0, 0, 0])
line_id = rs.AddLine([0, 0, 0], [100, 0, 0])

# 圆 (圆心 + 半径，默认在 WorldXY 平面)
circle_id = rs.AddCircle([0, 0, 0], 50)

# 球体与圆柱体
sphere_id = rs.AddSphere([0, 0, 0], 50)
cyl_id = rs.AddCylinder([0, 0, 0], [0, 0, 100], 25)   # 底面圆心、顶面圆心、半径
cone_id = rs.AddCone([0, 0, 0], [0, 0, 100], 25)       # 底面圆心、顶点、底半径
```

---

## 2. 长方体 (8 个角点，逆时针顺序：先底面后顶面)

```python
# 必须使用 to_nested_variant_r8 包装点数组
box_id = rs.AddBox(to_nested_variant_r8(
    (0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0),    # 底面 4 个角点
    (0, 0, 5), (10, 0, 5), (10, 10, 5), (0, 10, 5),    # 顶面 4 个角点
))
```

---

## 3. 多段线 / 插值曲线 / NURBS 曲线

```python
points = [(0, 0, 0), (50, 50, 0), (100, 0, 0), (150, 50, 0)]

# 折线
poly_id = rs.AddPolyline(to_nested_variant_r8(points))

# 空间插值光滑曲线
curve_id = rs.AddInterpCurve(to_nested_variant_r8(points))          # 默认 3 次样条
curve5_id = rs.AddInterpCurve(to_nested_variant_r8(points), 5)      # 5 次样条

# NURBS 曲线 (控制点用 to_nested_variant_r8，节点矢量 knots 用 to_flat_variant_r8)
knots = [0, 0, 0, 0.5, 1, 1, 1]  # 节点数量 = 控制点数量 + 次数 - 1
nurbs_id = rs.AddNurbsCurve(to_nested_variant_r8(points), to_flat_variant_r8(knots), 3)
```

---

## 4. 网格建模 (AddMesh — 嵌套数组数据)

```python
# 4 个顶点
verts = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]

# 2 个三角面拓扑 (三角面最后两个索引重复；四边面为 4 个互异索引)
faces = [[0, 1, 2, 2], [0, 2, 3, 3]]

mesh_id = rs.AddMesh(
    to_nested_variant_r8(verts),   # arrVertices: 浮点坐标嵌套数组
    to_nested_variant_i4(faces),   # arrFaceVertices: 整数面索引嵌套数组
)
```

---

## 5. 空间平面与椭圆/矩形 (arrPlane 包装)

RhinoScript 中平面 `arrPlane` 结构为 4 个三维向量：`[原点, X轴, Y轴, Z轴]`。必须使用 `to_nested_variant_r8` 包装：

```python
import math

rad = math.radians(30)
plane = to_nested_variant_r8(
    (0, 0, 50),                         # 原点
    (math.cos(rad), math.sin(rad), 0),  # X 轴方向
    (-math.sin(rad), math.cos(rad), 0), # Y 轴方向
    (0, 0, 1),                          # Z 轴方向
)

# 传入平面与长半轴/短半轴
ellipse_id = rs.AddEllipse(plane, 100, 60)
```

---

## 6. 图层管理与颜色设定

```python
# 添加图层并指定 RGB 颜色
layer_name = "Structure::Columns"
if not rs.IsLayer(layer_name):
    rs.AddLayer(layer_name, rgb(255, 128, 0))  # 颜色必须用 rgb() 函数生成 32 位整型

# 将对象分配给图层
rs.ObjectLayer(box_id, layer_name)
```

---

## 7. 批量创建性能加速 (EnableRedraw 保护模板)

批量创建数千个图元时，关闭重绘可提速上百倍。必须使用 `try...finally` 结构，防止异常导致 Rhino 界面永久冻结：

```python
rs.EnableRedraw(False)  # 冻结视图更新
try:
    for x in range(0, 1000, 100):
        for y in range(0, 1000, 100):
            rs.AddPoint([x, y, 0])
finally:
    rs.EnableRedraw(True)   # 保证无论是否报错均能解冻
    rs.Redraw()             # 主动触发一次刷新
```

---

## 8. 无交互静默导出与视图截图

自动化流水线中严禁弹出文件对话框或模态窗口：

```python
import os

output_dir = os.path.abspath("./output")
os.makedirs(output_dir, exist_ok=True)

# 1. 无弹窗保存当前文档
save_file = os.path.join(output_dir, "model_output.3dm")
rs.DocumentModified(False)  # 重置修改标记，避免保存提示
rs.Command(f'_-SaveAs "{save_file}" _Enter', False)

# 2. 静默渲染/捕获当前视口视图为 PNG 图片
img_file = os.path.join(output_dir, "viewport_view.png")
rs.Command(f'_-ViewCaptureToFile "{img_file}" _Width=1920 _Height=1080 _Enter', False)
```
