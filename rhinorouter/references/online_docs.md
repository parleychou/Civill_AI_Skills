# Rhino 官方网络文档与开发者参考指南

本技能封装了 McNeel 官方提供的公开标准 COM 自动化接口。在日常开发、复杂几何创建或排查接口行为时，可结合以下官方官方文档进行对照参考。

---

## 1. 核心官方入口

| 资源名称 | 官方 URL | 说明 |
|---|---|---|
| **Rhino 开发者主站** | https://developer.rhino3d.com/ | McNeel 官方开发者中心，包含所有语言的 API 与指南 |
| **RhinoScript 官方 API 文档** | https://developer.rhino3d.com/api/rhinoscript/ | 本技能 `rhinoscript_api.db` 的在线版，包含全量 1245 个函数详细手册 |
| **RhinoScript 外部 COM 自动化指南** | https://developer.rhino3d.com/guides/rhinoscript/external-access/ | 官方介绍如何通过 OLE/COM 从外部程序（C#、Python、VBA 等）控制 Rhino |
| **RhinoScriptSyntax (Python) API** | https://developer.rhino3d.com/api/RhinoScriptSyntax/ | Rhino 内嵌 Python 脚本库官方文档（适用于 `_-RunPythonScript`） |
| **Rhino 8 Python 脚本开发指南** | https://developer.rhino3d.com/guides/rhinopython/ | Rhino 8 全新内置 CPython 3 与 .NET 8 脚本引擎官方文档 |
| **Rhino Developer Samples (GitHub)** | https://github.com/mcneel/rhino-developer-samples | McNeel 官方开源的外部自动化与插件代码示例库 |
| **Rhino.Inside 架构介绍** | https://www.rhino3d.com/features/rhino-inside/ | 官方新一代进程内宿主技术 |

---

## 2. RhinoScript 29 个顶级模块在线直达速查表

在离线通过 `python scripts/get_function_detail.py <Module> <Func>` 检索的同时，若需查看官方网页版的图文演示或交互示例，可直接点击对应模块链接：

| 模块名 (Module) | 在线文档直达链接 | 核心用途 |
|---|---|---|
| **Curve_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/curve_methods/) | 曲线、圆、弧、样条、多段线创建与求交/编辑 |
| **Surface_and_Polysurface_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/surface_and_polysurface_methods/) | 曲面、多曲面、布尔运算、拉伸、放样与倒角 |
| **Mesh_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/mesh_methods/) | 三角网格、四边网格创建、顶点/面索引拓扑与网格布尔 |
| **Object_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/object_methods/) | 对象查询、名称、图层归属、几何变换、复制与删除 |
| **Selection_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/selection_methods/) | 对象选择状态、过滤选择、已选对象列表非阻塞查询 |
| **Layer_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/layer_methods/) | 层次化图层增删改查、颜色、线宽、可见性与锁定 |
| **Dimension_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/dimension_methods/) | 线性尺寸、角度尺寸、文字标注与引线 |
| **Geometry_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/geometry_methods/) | 点到物体距离、包围盒、法向量、切平面与剖切面计算 |
| **Light_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/light_methods/) | 点光源、平行光、聚光灯与矩形光参数配置 |
| **Material_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/material_methods/) | 渲染材质表维护、颜色、反光度、贴图通道分配 |
| **Block_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/block_methods/) | 块定义 (Block Definitions) 与块实例插入/分解 |
| **Group_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/group_methods/) | 几何体分组组织与解组 |
| **Hatch_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/hatch_methods/) | 剖面线填充图案与边界填充 |
| **Linetype_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/linetype_methods/) | 虚线、点划线等自定义线型管理 |
| **Line_and_Plane_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/line_and_plane_methods/) | 空间直线与平面（Plane 原点/X/Y/Z 轴）构造计算 |
| **Point_and_Vector_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/point_and_vector_methods/) | 3D 点与向量的点积、叉积、单位化与距离运算 |
| **Transformation_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/transformation_methods/) | 4×4 空间仿射变换矩阵（平移、旋转、缩放、镜像） |
| **View_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/view_methods/) | 视口视图切换（Top/Front/Right/Perspective）、无对话框高清截图 |
| **Document_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/document_methods/) | 文档单位、公差、无提示静默打开/保存/导出 |
| **Application_Methods** | [查看官方文档](https://developer.rhino3d.com/api/rhinoscript/application_methods/) | Rhino 主程序控制、无红绘模式 (`EnableRedraw`) 批量加速 |

---

## 3. Rhino COM 对象模型架构解析

```text
+-------------------------------------------------------------+
|                     Rhino.Application                       |
|           (IRhinoInterface / IRhinoApplication)             |
|   ProgID: "Rhino.Application.8" / "Rhino.Interface.8"       |
+-------------------------------------------------------------+
                              |
                     GetScriptObject()
                              |
                              v
+-------------------------------------------------------------+
|                       IRhinoScript                          |
|             (Plug-ins\RhinoScript.tlb / .rhp)               |
|            包含 Curve, Surface, Mesh 等 1245 个 API          |
+-------------------------------------------------------------+
```

- **外部进程调用时**：通过 `win32com.client.Dispatch("Rhino.Application.8")` 得到宿主对象，通过调用其 `GetScriptObject()` 方法即可获取完整的 `IRhinoScript` 接口。
- **参数数据格式**：底层采用标准 COM OLE `VARIANT`，本技能 `rhinorouter.variants` 提供了原生封装，彻底免除了手写 C++ SAFEARRAY 或复杂互操作代码的繁琐。
