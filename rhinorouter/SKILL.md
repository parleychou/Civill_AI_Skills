---
name: rhinorouter
version: 1.0.0
display_name: Rhino三维建模与参数化路由
display_name_en: Rhino 3D Modeling & Script Automation
description: Use when automating Rhinoceros (Rhino 8 / 7 / 6) via Python and RhinoScript COM to create 3D geometry, curves, surfaces, meshes, boolean operations, manage layers, or query the built-in offline 1245 official API database.
description_zh: 基于 Python 与 Rhino 官方 COM/RhinoScript 的 Rhino 3D 参数化建模与自动化路由技能库。内置 29 个模块、1245 个官方 API 离线知识库，支持跨版本自动连接探测、VARIANT 数据封送转换、曲线/曲面/实体/网格生成、图层材质控制与自动化批量绘图。
description_en: Production-grade skill for automating Rhinoceros (Rhino 8/7/6) via Python and RhinoScript COM automation. Features an offline database of 1245 official APIs across 29 modules, multi-version connection discovery, robust VARIANT data marshaling, curve/surface/mesh parametric modeling, layer control, and headless batch script execution.
---

# Rhino 3D 自动化建模路由技能 (RhinoRouter)

## Overview

**RhinoRouter** 是一套专为 AI Coding Agent 及工程自动化工作流打造的 **Rhino 官方 COM 自动化连接与 3D 建模开发套件**。

### 核心能力与技术基石
1. **官方原生与零入侵**：
   - 基于标准 Windows COM (`Rhino.Application` 与 `IRhinoScript`) 接口，完全通过跨进程通信驱动。
   - **无需在 Rhino 内部安装任何第三方插件**，开箱即用支持本地已安装的 Rhino 8、Rhino 7、Rhino 6 原生环境。
2. **防幻觉渐进式知识库**：
   - 随包内置 1.43 MB 标准 SQLite 知识库 ([references/rhinoscript_api.db](./references/rhinoscript_api.db))，收录官方 **29 个模块、1245 个完整 API** 签名与示例。
   - 编写代码前可动态“按需查询、查准再写”，从根源上杜绝大模型对 API 签名和参数顺序的虚构。
3. **开箱即用的 VARIANT 数据封送**：
   - 彻底攻克了 `win32com` 无法向 OLE Automation 传递复杂嵌套点数组的业界难题。
   - 提供 `to_nested_variant_r8`、`to_nested_variant_i4`、`to_flat_variant_r8`、`to_flat_variant_i4`、`rgb` 等 5 个经过生产环境严格校验的数据封送转换函数。
4. **完备的进程与安全守护**：
   - 自动扫描注册表排查无效或已卸载幽灵键；
   - 智能识别后台运行的 Rhino 进程，支持安全附着或独立拉起；
   - 严格的模态弹窗拦截规范与视口重绘解冻守护。

---

## Directory Structure

本 Skill 严格遵循**两级目录结构**（根目录 / 二级目录 / 文件），所有子目录下禁止创建嵌套子目录或残留 `__pycache__` 字节码文件，解压总大小严格控制在 3MB 以内（当前解压总大小仅约 1.43 MB）：

```text
.agents/skills/rhinorouter/
├── SKILL.md                          # 技能主说明书与运行手册（本文件）
├── LICENSE                           # MIT 开源许可证
├── requirements.txt                  # Python 依赖清单 (pywin32, psutil)
├── rhinorouter/                      # 核心纯 Python 包（二级目录）
│   ├── __init__.py                   # 模块顶层快捷导出
│   ├── connector.py                  # Rhino COM 自动化、生命周期管理与 TypeLib 动态绑定
│   ├── variants.py                   # OLE Automation VARIANT / SAFEARRAY 数据封送器
│   └── api_docs.py                   # 本地 1245 个官方 API 知识库查询引擎
├── scripts/                          # 渐进式检索与验证工具（二级目录）
│   ├── list_top_modules.py           # 列出 29 个顶级模块
│   ├── list_module_functions.py      # 列出指定模块函数列表
│   ├── get_function_detail.py        # 查询函数签名、参数、返回值与官方示例
│   └── test_rhinorouter.py           # 自动化单元测试 (封送、数据库检索、系统检测)
├── references/                       # 离线与权威参考文档（二级目录）
│   ├── common_examples.md            # 已校验的 3D 几何/网格/图层 Python 高频示例
│   ├── online_docs.md                # 权威官方网络文档与在线 API 模块索引
│   └── rhinoscript_api.db            # 纯净 SQLite 3 官方全量 1245 个 API 数据库 (1.43 MB)
└── examples/                         # 独立可执行示例脚本（二级目录）
    ├── 01_query_api_database.py      # 示例 1：离线查询 29 个模块与 1245 个 API 知识库
    ├── 02_connect_and_basic_shapes.py # 示例 2：环境探测与基础几何图元创建
    └── 03_parametric_mesh_and_box.py # 示例 3：高级参数化长方体、样条与网格封送建模
```

> [!IMPORTANT]
> 执行 Python 脚本或校验测试时，务必使用 `python -B`，禁止生成 `__pycache__` 目录，确保维持二级目录规范。

---

## Core Engineering Rules

### 1. 跨进程 VARIANT 数据封送规则 (强制遵循)

RhinoScript COM 底层基于 Windows OLE Automation (VBScript 规范)，**严禁向 COM 方法直接传递 Python 嵌套列表 (如 `[[0,0,0], [10,0,0]]`)**。必须按几何类型使用对应的转换函数：

| 参数几何类型 | 官方典型结构 (VBScript) | Python 封送转换函数 | 典型适用 API |
|---|---|---|---|
| **单点 / 单向量** | `Array(x, y, z)` | 直接传原生列表 `[x, y, z]` | `AddPoint`, `AddSphere` 圆心, `MoveObject` |
| **点数组 / 向量数组** | `Array(Array(x,y,z), ...)` | **`to_nested_variant_r8(...)`** | `AddBox`, `AddPolyline`, `AddMesh` 顶点 |
| **参考平面 (Plane)** | `Array(原点, X轴, Y轴, Z轴)` | **`to_nested_variant_r8(...)`** | `AddEllipse`, `AddCircle` 平面定向 |
| **网格面索引数组** | `Array(Array(i0,i1,i2,i3), ...)`| **`to_nested_variant_i4(...)`** | `AddMesh` 的 `arrFaceVertices` |
| **纯数字平铺向量** | `Array(k0, k1, k2, ...)` | **`to_flat_variant_r8(...)`** | `AddNurbsCurve` 的 `knots` / `weights` |
| **颜色值 (Color)** | `RGB(r, g, b)` | **`rgb(r, g, b)`** | `AddLayer`, `ObjectColor` (返回 32 位整型) |

### 2. 关键避坑与安全规范

1. **绝对禁止调用阻塞型用户交互函数**：
   - 严禁调用 `User_Interface_Methods` 模块中的输入等待函数（如 `GetPoint`, `GetString`, `GetBox`, `MessageBox`）；
   - 严禁调用 `Selection_Methods` 中带 "Prompts the user" 的函数（如 `GetObject`, `GetObjects`）；
   - 若需读取用户已选对象，必须使用非阻塞的 `script.SelectedObjects()`。
2. **批量建模重绘保护**：
   - 创建大量图元时，使用 `script.EnableRedraw(False)` 加速；
   - **必须**将 `script.EnableRedraw(True)` 放置在 `try...finally` 的 `finally` 块中，杜绝因异常导致 Rhino 界面永久假死。
3. **文件路径一律使用绝对路径**：
   - 调用 `Command()` 执行 SaveAs / Export 或导出截图时，务必使用 `os.path.abspath(...)` 构建绝对路径，Rhino 独立进程不共享调用方的相对路径。
4. **返回值类型辨析**：
   - 数组返回值均为 Python `tuple`（如需修改请用 `list(ret)`）；
   - 多数 `AddXxx` 函数在失败时静默返回 `None`（而不是抛出异常）。若返回 `None`，优先检查是否使用了正确的 `to_nested_variant_r8` 包装。

---

## Standard Operating Procedures (SOP)

### SOP 1: API 渐进式检索链 (查准后再写代码)

在编写任何几何建模代码前，通过配套脚本查询真实签名：

```bash
# Step 1: 确定功能所属模块
python -B .agents/skills/rhinorouter/scripts/list_top_modules.py

# Step 2: 列出模块内的函数清单
python -B .agents/skills/rhinorouter/scripts/list_module_functions.py Curve_Methods --limit 20
python -B .agents/skills/rhinorouter/scripts/list_module_functions.py Surface_and_Polysurface_Methods --limit 20

# Step 3: 查看函数精确签名、参数说明与官方示例
python -B .agents/skills/rhinorouter/scripts/get_function_detail.py Surface_and_Polysurface_Methods AddBox

# 支持全局模糊搜索：
python -B .agents/skills/rhinorouter/scripts/get_function_detail.py --search BoundingBox
```

### SOP 2: 建立连接并创建基础图元

```python
import sys
from pathlib import Path

# 添加技能根目录以导入 rhinorouter
sys.path.insert(0, str(Path(".agents/skills/rhinorouter").resolve()))
from rhinorouter import get_rhino, rgb

# 建立连接 (优先复用活跃实例；auto_spawn=True 可在后台未运行时自动拉起)
result = get_rhino(auto_spawn=False)
if isinstance(result, str):
    print("连接提示:", result)
else:
    rhino, rs, version = result
    print(f"成功连接到 Rhino {version}")

    try:
        rs.EnableRedraw(False)

        # 1. 管理图层
        if not rs.IsLayer("MyLayer"):
            rs.AddLayer("MyLayer", rgb(0, 120, 215))
        rs.CurrentLayer("MyLayer")

        # 2. 创建基础几何
        pt_id = rs.AddPoint([0, 0, 0])
        line_id = rs.AddLine([0, 0, 0], [100, 0, 0])
        circle_id = rs.AddCircle([0, 0, 0], 50)
        sphere_id = rs.AddSphere([0, 0, 50], 30)

    finally:
        rs.EnableRedraw(True)
```

### SOP 3: 复杂实体与网格参数化建模 (封送转换)

```python
from rhinorouter import (
    get_rhino,
    to_nested_variant_r8,
    to_nested_variant_i4,
    to_flat_variant_r8,
    rgb,
)

rhino, rs, version = get_rhino()
try:
    rs.EnableRedraw(False)

    # 1. 实体长方体 (8 个角点，必须用 to_nested_variant_r8 包装)
    box_id = rs.AddBox(to_nested_variant_r8(
        (0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0),
        (0, 0, 50), (100, 0, 50), (100, 100, 50), (0, 100, 50),
    ))

    # 2. 空间插值曲线
    pts = [(0, 0, 100), (50, 50, 150), (100, 0, 100), (150, 50, 150)]
    curve_id = rs.AddInterpCurve(to_nested_variant_r8(pts), 3)

    # 3. 空间网格构造 (AddMesh)
    mesh_verts = [(0, 0, 0), (50, 0, 20), (50, 50, 20), (0, 50, 0)]
    mesh_faces = [[0, 1, 2, 2], [0, 2, 3, 3]]  # 三角面索引拓扑
    mesh_id = rs.AddMesh(
        to_nested_variant_r8(mesh_verts),
        to_nested_variant_i4(mesh_faces),
    )
finally:
    rs.EnableRedraw(True)
```

---

## Technical Reference Manuals

- [common_examples.md](./references/common_examples.md):
  - 基础点线面高频示例
  - 长方体 8 点坐标拓扑顺序规范
  - 多段线、插值曲线、NURBS 样条曲线
  - 网格面索引数据构造
  - 空间倾斜参考平面与椭圆/圆环构造
- [online_docs.md](./references/online_docs.md):
  - McNeel 官方开发者中心与在线手册链接
  - 29 个顶级模块官方在线 URL 对应表
  - Rhino COM 架构及 ProgID 解析机制
- [rhinoscript_api.db](./references/rhinoscript_api.db):
  - SQLite 3 官方全量知识库，包含 `modules` 表与 `functions` 表（1245 个函数详细记录）

---

## Standalone Examples Walkthrough

- **[01_query_api_database.py](./examples/01_query_api_database.py)**：离线查询 29 个顶级模块、模块内函数列表与函数详细签名参数，杜绝 API 幻觉。
- **[02_connect_and_basic_shapes.py](./examples/02_connect_and_basic_shapes.py)**：自动扫描本地已安装 Rhino 版本、检查活跃进程、安全附着并生成基础点、线、圆、球等标量图元。
- **[03_parametric_mesh_and_box.py](./examples/03_parametric_mesh_and_box.py)**：高级参数化几何生成，全面演练长方体、空间样条与网格拓扑的 VARIANT 数据封送机制。
