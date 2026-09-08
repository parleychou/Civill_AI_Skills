---
name: ifc-threejs-viewer
title: "IFC 一键转 Web 查看器（含公网部署）"
description: "输入一个 .ifc 模型，一键生成 three.js 网页查看器（按楼层/构件类型开关显示）并可发布为公网链接。全程只需一个 IFC 文件。"
summary: "输入一个 .ifc 模型 → 一键生成 three.js 网页查看器（楼层/构件类型开关）→ 通过 WorkBuddy 发布为公网链接。全程只需一个 IFC 文件。"
trigger:
  - "ifc 转网页"
  - "ifc 网页查看器"
  - "ifc three.js"
  - "ifc 在线预览"
  - "ifc 发布链接"
  - "把模型做成网页"
  - "bim 模型网页展示"
  - "ifc 公网访问"
agent_created: true
---

# IFC 一键转 Web 查看器（含公网部署）

**核心承诺**：只要用户能提供一个 `.ifc` 文件（YJK / Revit / Tekla / Rhino 等均可导出），就把它变成一个可交互、可公网访问的 three.js 网页查看器——支持按楼层、按构件类型（柱/梁/板/墙）开关显示。

## 适用场景
- 结构 / 建筑 / 机电模型要给别人"在线看"，不要对方装专业软件。
- 手机、电脑浏览器都能打开，无需登录。
- 需要分层、分构件查看（例如"只看第 5 层的梁"）。

## 本 skill 已内置（assets/ 目录）
| 文件 | 作用 |
|---|---|
| `assets/ifc_to_web.py` | **一键主脚本**：解析 IFC → 提取几何 → 按(楼层,类型)分组 → 导出 `model.glb` + `manifest.json` → 渲染 `index.html` 与 `link.html` |
| `assets/viewer.html` | 查看器前端模板（three.js，加载 manifest 动态生成 UI，自适应任何楼层数/类型数/模型尺寸） |

脚本与模板均已参数化、可复现，**不需要复制粘贴任何工作区文件**。

## 端到端流程（4 步）

### 第 1 步：准备 Python 环境（一次性）
```bash
# 建议用独立 venv，避免污染系统 Python
python -m venv ifc_env
ifc_env/Scripts/python -m pip install ifcopenshell numpy
```

### 第 2 步：一键生成网页（核心）
```bash
python <skill>/assets/ifc_to_web.py "E:\path\to\模型.ifc" --name "项目名" --out "E:\path\to\web输出目录"
```
常用参数：
| 参数 | 说明 | 默认 |
|---|---|---|
| `模型.ifc`（位置参数） | 输入 IFC，必填 | — |
| `--name` | 网页显示的模型名 | IFC 文件名 |
| `--out` | 输出目录 | IFC 同目录下 `web_ifc/` |
| `--public-url` | 公网链接（部署后再生成 link.html 用） | 无 |
| `--extra-types` | 额外构件类型（斜撑/板件/楼梯/幕墙等） | 关 |
| `--icon` | link.html 图标 emoji | 🏢 |

产物 4 个文件：`model.glb`、`manifest.json`、`index.html`、`link.html`。
命令行会打印楼层数、各类型构件数、模型尺寸、GLB 大小、三角面数，**应核对与源模型一致**（若发现构件数为 0，用 `--extra-types` 重试，或提醒用户该 IFC 的构件类型不在默认清单）。

### 第 3 步：本地冒烟验证（可选但强烈建议）
```bash
python -m http.server 8765 --bind 127.0.0.1 -d <输出目录>
```
浏览器打开 `http://127.0.0.1:8765/index.html`，确认：
- 模型显示、不横躺、颜色区分构件类型；
- 楼层/类型开关、全选/反选正常；
- 无控制台报错。

自动化验证可用浏览器工具加载后检查 `window.__app`（模板已内置调试接口：
`{state, camera, scene, controls, manifest}`），例如断言
`window.__app.state.meshes.length > 0`。

### 第 4 步：发布公网链接
用部署工具把**输出目录**发布为静态站点：
```json
{
  "action": "deploy",
  "directory": "<绝对路径>/web输出目录",
  "language": "static",
  "appName": "IFC结构模型查看器",
  "userAskedToPublish": true
}
```
拿到公网 URL 后，**重新跑一次**主脚本补上 `--public-url <链接>`（或直接改 link.html 中 `.linkbox` 文本与 `a.open` 的 href），link.html 即成为带"打开模型"按钮的分享落地页。

最终交付给用户：
- 公网链接（优先给 link.html 的链接，或 index.html 直链）；
- 产物目录路径与文件说明。

## 架构与关键实现（排查时看这里）

### 数据链路
```
IFC ──ifcopenshell──> 构件 (楼层, 类型, 三角网格)
   ──按 (楼层,类型) 分组合并──> 102 个左右网格（示例 33 层 8347 构件 → 102 mesh）
   ──手写 GLB──> model.glb（2 MB 级）
   ──> index.html 加载 model.glb + manifest.json
```
- 前端**不按构件**逐个体渲染，而是按 `F{楼层序号}_{类型}`（如 `F5_BEAM`）合并为一个 mesh，节点名即开关的键，见 viewer.html 中 `name.match(/^F(\d+)_(.+)$/)`。
- UI 完全由 `manifest.json` 动态生成（楼层数、类型数、颜色、数量都不写死），所以**任何 IFC 都能用同一套模板**。

### 单位与坐标系（实测结论）
- ifcopenshell 几何输出默认是**米**（除非 IFC 显式用非 mm 单位），不要额外 `/1000`。
- IFC `IfcBuildingStorey.Elevation` 字段**可能仍是毫米**，脚本用启发式 `|elev|>200 → /1000` 转米（仅用于 UI 展示标高）。
- IFC 是 **Z-up**，three.js/glTF 是 **Y-up**：导出时做 `(x,y,z)→(x,z,-y)`，否则模型横躺。
- 模型平移到包围盒中心，前端 `fitCamera()` 自动取景；地面网格跟随可见模型贴地/缩放。

### manifest.json 楼层键
- 每个楼层含 `num`（从 1 起，mesh 节点名 `F{num}_…` 与前端开关都用它）、`name`（原始楼层名，仅用于显示）、`elevation`。
- 楼层 key 用 `num` 而不用 `name`：兼容楼层名为"第5层"/"屋顶"/"B1"等非纯数字命名。

## 常见坑与对策
1. **单位搞错**：几何已是米，别再除以 1000（缩成 1mm 的小点）。核实方法：命令行打印的模型尺寸应为几十米级。
2. **模型横躺**：漏做 Z-up→Y-up。脚本已内置，若自行改动脚本注意保留。
3. **构件数为 0 / 页面空**：该 IFC 可能无 `IfcBuildingStorey`（脚本已自动归为单层"整体"）或构件类型不在默认 4 类（加 `--extra-types`）。
4. **4–33 层无柱**（剪力墙住宅等）：正常，脚本已自动筛掉实际数量为 0 的类型，UI 不会出现空开关。
5. **楼层开关无效**：检查前端所有 `state.floorVis` 读写都使用 `f.num`（曾经发生过 `f.name`/`f.num` 混用导致 Map key 不一致）。
6. **超大型模型**：十万级三角面流畅；百万级建议提醒用户可接受加载时间，或后续扩展按层拆 GLB。
7. **部署后页面白屏**：确认输出目录里 `model.glb`/`manifest.json` 与 `index.html` 同级且文件名正确；用 curl 检查资源 HTTP 200。

## 端到端验证清单（发布前过一遍）
- [ ] 命令行输出：楼层数、构件数与源模型对得上
- [ ] 本地打开：模型竖直、四类颜色区分
- [ ] 只勾某层 + 重置视角：镜头聚焦该层
- [ ] 类型开关：墙/板关闭后可见内部梁柱
- [ ] 手机视口：单指旋转、双指缩放可用（模板已设 `touch-action:none` 与 OrbitControls 单指旋转）
- [ ] 公网链接：HTML/manifest/glb 均 200，真机可开

## 参考（本工作流首个实例）
- 源 IFC：`E:\2026\20260903_01让AI用网页展示你的模型\结构模型.ifc`（33 层住宅，8347 构件，38 MB）
- 产出目录：`E:\2026\20260903_01让AI用网页展示你的模型\web\`
- 公网示例：`https://a1a7dc771a744d099d19fa979c6b70c4.app.workbuddy.link`
