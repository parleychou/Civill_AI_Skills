# Civill_AI_Skills (中文说明)

<p align="center">
  <strong>面向土木与结构工程师的标准化 AI Skills 技能库</strong><br>
  <em>让 Claude Code、Cursor、Antigravity 成为精通工程规则的资深结构工程师</em>
</p>

<p align="center">
  <a href="https://ai.venchy.online/skills/">🌐 官方在线技能库入口</a> •
  <a href="#快速上手">🚀 快速上手</a> •
  <a href="#核心功能模块">🛠️ 核心功能</a> •
  <a href="#技能包清单">📦 技能清单</a> •
  <a href="README.md">🇺🇸 English Version</a>
</p>

---

## 📖 项目简介

`Civill_AI_Skills` 是专为土木工程、结构设计从业者打造的工程级 AI Agent 技能扩展库。

通用大模型虽然擅长编写通用代码，但在土木与结构工程场景中常常面临三大痛点：
1. **工业软件专属 API 盲区**：工业级软件（AutoCAD、Rhino、盈建科 YJK、SAP2000）的底层 COM、ActiveX 及 SQLite 数据库接口在通用预训练语料中极少覆盖。
2. **缺乏严苛行业规范**：土木工程具有特殊的出图标准（例如弯矩图强制画在受拉侧、图纸图层排版不可打乱、汉译英不可重复翻译等），缺乏规范约束时 AI 极易生成废图。
3. **力学计算严谨度不足**：有限元刚度装配与位移解算要求极高精度，需要严格的基准算例回归验证。

`Civill_AI_Skills` 解决了这一难题。只需将本仓库中标准化的 `SKILL.md` 规则库放入项目 `./skills/` 目录，**Claude Code**、**Cursor** 及 **Antigravity** 即可秒级装载工程实战能力。

> ⚡ **持续扩充更新**：本仓库长期维护，后续将陆续上线地基基础、结构抗震验算、构件自动配筋及各类工业软件专属能力包，永久免费开源！

---

## 🛠️ 核心功能模块

### 1. CAD & 施工图自动化
* **`pyautocad`**: 基于 AutoCAD ActiveX/COM 的 Python 批处理驱动，支持图元提取、图层控制与几何绘制。
* **`autocad-structural-translation`**: 生产级 DWG 施工图纸智能汉译英引擎，精准保持原图层、对齐与文字排版，自动过滤已有翻译防重译。
* **`autocad-floor-layout-to-yjk`**: 建筑/结构 CAD 平面图智能识别并转换为 YJK 结构计算模型。
* **`multi-floor-dwg-to-ydb-model`**: 多层施工图批量解析与上下层柱网轴网对齐合并。

### 2. 三维参数化与 BIM 轻量化浏览
* **`rhinorouter`**: 面向 Rhino 8/7/6 的工业级 Python COM 自动化技能包，内置 29 个模块、1245 个官方 API 离线知识库，支持跨版本探测、VARIANT 数据类型转换与空间参数化曲面造型。
* **`ifc-threejs-viewer.skill`**: IFC 一键转 Web 查看器（含公网部署）。输入单个 .ifc 模型，一键提取几何与楼层构件（柱/梁/板/墙），自动导出轻量化 GLB 与动态 Manifest，生成基于 Three.js 的 3D 浏览器，支持按层/构件类型动态开关与公网免装专业软件分享。

### 3. 结构数据库与模型接口
* **`yjk-database`**: 盈建科 YJK (`.ydb`) SQLite 底层构件批量读写、几何截面查询与模型修改。
* **`sap2000-python`**: SAP2000 OAPI 建模、工况组合、荷载定义与构件内力结果自动化提取。
* **`structural-plan-layout-workflow`**: 结构方案规划、柱网拓扑生成与梁柱构件截面初选。

### 4. 有限元力学求解与出图
* **`matrix-stiffness-2d`**: 2D 平面直接刚度法有限元计算内核，节点受力与位移精确求解。
* **`mechanics-diagram-renderer`**: 受拉侧内力图规范渲染引擎，严格遵循土木结构出图标准（弯矩画在受拉侧）。
* **`structure-benchmark-verifier`**: 经典结构力学题库回归验证与基准解自动化比对套件。
* **`docker-electron-delivery`**: 求解器极简容器私有化部署与跨平台客户端交付模板。

### 5. 多智能体协同与工头分流系统
* **`agent-foreman`**: 多智能体工头协同与分流治理系统（v2.0，原 cheap-agent 升级版）。支持任何主导 Agent（Codex、Claude Code、Pi、通用 Coding Agent 或 Antigravity）将调研、代码审查、通用任务及封闭实现委托给基于 Gemini 的工作者，支持递归分发、Git Worktree 隔离运行、人工/主导者 Verdict 审核卡口与受控合并交付。

---

## 🚀 快速上手

### 方式 1：本地仓库克隆使用（推荐）
1. **克隆本仓库**：
   ```bash
   git clone https://github.com/parleychou/Civill_AI_Skills.git
   ```
2. **复制到项目中的 `./skills/` 目录**：
   ```text
   your-project/
   ├── skills/
   │   ├── pyautocad/
   │   │   └── SKILL.md
   │   ├── autocad-structural-translation/
   │   │   └── SKILL.md
   │   ├── rhinorouter/
   │   │   └── SKILL.md
   │   ├── yjk-database/
   │   │   └── SKILL.md
   │   └── matrix-stiffness-2d/
   │       └── SKILL.md
   └── main.py
   ```
3. **在 Claude Code / Cursor 中直接提问**：
   ```bash
   >_ claude "读取当前目录下的 DWG 施工图，并将文字和标注汉译英"
   ```

### 方式 2：官方网页直接下载
访问官方在线技能库直接下载各个技能包：  
🌐 **[https://ai.venchy.online/skills/](https://ai.venchy.online/skills/)**

---

## 📦 技能包清单

| 技能目录 | 适用软件 / 领域 | 说明 | 包含文件 |
| :--- | :--- | :--- | :--- |
| **`autocad-structural-translation`** | AutoCAD / 海外工程 | DWG 施工图纸智能汉译英 | 翻译引擎、词汇库、测试集 |
| **`pyautocad`** | AutoCAD | AutoCAD Python 图元批量提取与绘制 | ActiveX 封装、出图脚本 |
| **`rhinorouter`** | Rhino / Grasshopper | Rhino 8/7 参数化建模与 1245 个官方 API | SQLite API 库、连接器、算例 |
| **`ifc-threejs-viewer.skill`** | BIM / WebGL / Three.js | IFC 一键转 Three.js 网页查看器（含分层/构件开关与公网发布） | `ifc_to_web.py`、`viewer.html`、`SKILL.md` |
| **`yjk-database`** | 盈建科 YJK | YJK 结构数据库 SQLite 底层构件读写 | YDB 读取脚本、基准数据库 |
| **`sap2000-python`** | SAP2000 | SAP2000 OAPI 建模与内力提取 | OAPI 文档、内力提取脚本 |
| **`matrix-stiffness-2d`** | 结构力学 / 有限元 | 2D 直接刚度法平面有限元求解内核 | 刚度矩阵装配、求解器代码 |
| **`mechanics-diagram-renderer`** | 结构力学 | 受拉侧内力图出图规范渲染 | Canvas/SVG 渲染器、视口模板 |
| **`structure-benchmark-verifier`** | 结构力学基准 | 经典力学题库基准回归验证 | 经典算例库、回归测试脚本 |
| **`autocad-floor-layout-to-yjk`** | AutoCAD + YJK | CAD 平面布置转 YJK 结构模型 | 构件识别、模型映射规则 |
| **`multi-floor-dwg-to-ydb-model`** | AutoCAD + YJK | 多层图纸批量解析对齐合并 | 上下层对齐工作流与规范 |
| **`structural-plan-layout-workflow`** | 方案前期 | 结构方案规划与柱网构件截面初选 | 构件估算表、规则指引 |
| **`docker-electron-delivery`** | 交付部署 | 求解器容器与客户端交付 | Dockerfile 与 Electron 模板 |

---

## 🌟 持续扩充路线 (Roadmap)

- [x] AutoCAD 基础自动化与 DWG 施工图智能汉译英
- [x] Rhino 8/7 参数化 COM API 路由与三维几何交互
- [x] 盈建科 YJK 与 SAP2000 结构数据库接口对接
- [x] 2D 平面直接刚度法求解内核与受拉侧出图规范
- [ ] 空间桁架与 3D 空间结构直接刚度法求解器
- [ ] 地基基础与桩土相互作用分析模块
- [ ] 现浇混凝土与钢结构节点深化与构件自动配筋技能

---

## 📄 开源许可 (License)

本项目采用 [MIT License](LICENSE)，永久开源免费。
