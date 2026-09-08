# Civill_AI_Skills

> **面向土木与结构工程师的标准化 AI Skills 技能库**  
> 官方在线技能库: [https://ai.venchy.online/skills/](https://ai.venchy.online/skills/)  
> 适配 Claude Code / Cursor / Antigravity 等 AI Agent 即插即用

---

## 📖 项目简介 (Introduction)

Civill_AI_Skills 是专为土木工程、结构设计从业者打造的工程级 AI Agent 技能扩展库。  
本项目深度整合工业软件（AutoCAD、Rhino、盈建科 YJK、SAP2000）原生 API 与有限元力学计算内核，赋予 AI 严苛的行业制图规范、数据接口读写与计算验算能力。

本仓库技能**持续扩充更新中，永久开源免费！**

---

## 🛠️ 核心功能模块 (Core Capabilities)

### 1. CAD & 施工图自动化
- **pyautocad**: AutoCAD 图元批量提取、图层控制与几何对象自动化绘制。
- **utocad-structural-translation**: DWG 施工图纸智能汉译英，保持原图层与文字排版防重译。
- **utocad-floor-layout-to-yjk**: 建筑/结构 CAD 平面图智能识别并转换为 YJK 结构模型。
- **multi-floor-dwg-to-ydb-model**: 多层图纸批量解析与上下层柱网轴网对齐合并。

### 2. 三维参数化与几何建模
- **
hinorouter**: Rhino 8/7 原生 COM API 驱动、1245 个官方 API 全覆盖、参数化几何形体生成与数据交互。

### 3. 结构数据库与模型接口
- **yjk-database**: 盈建科 YJK 结构数据库 (.ydb) SQLite 底层构件批量读写与截面参数查询。
- **sap2000-python**: SAP2000 OAPI 建模、工况组合、荷载定义与构件内力结果提取。
- **structural-plan-layout-workflow**: 结构方案规划、柱网生成与梁柱构件截面初选。

### 4. 有限元力学求解与出图
- **matrix-stiffness-2d**: 2D 直接刚度法平面有限元计算内核，节点自由度受力与位移精确求解。
- **mechanics-diagram-renderer**: 受拉侧内力图规范渲染，强制遵循土木结构出图标准（弯矩画在受拉侧）。
- **structure-benchmark-verifier**: 经典结构力学题库回归验证与基准解比对。
- **docker-electron-delivery**: 求解器极简容器私有化部署与客户端打包交付。

---

## 🚀 快速上手 (Quick Start)

### 步骤 1：克隆仓库
`ash
git clone https://github.com/parleychou/Civill_AI_Skills.git
`

### 步骤 2：直接复制到项目中使用
将需要的技能文件夹复制到您当前项目的 ./skills/ 目录中：
`	ext
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
│   └── ...
`

### 步骤 3：AI 自动装载运行
在项目目录下启动 **Claude Code** 或 **Cursor**，AI 将自动识别 ./skills/*/SKILL.md 规范并遵循土木工程规则执行任务！

---

## 📦 技能包清单

| 技能目录 | 说明 | 适用软件 / 领域 |
| :--- | :--- | :--- |
| utocad-structural-translation | DWG 施工图纸智能汉译英 | AutoCAD / 海外工程 |
| pyautocad | AutoCAD Python 图元批量提取与绘制 | AutoCAD |
| 
hinorouter | Rhino 8/7 参数化建模与 1245 个官方 API | Rhino / Grasshopper |
| yjk-database | YJK 结构数据库 SQLite 底层构件读写 | 盈建科 YJK |
| sap2000-python | SAP2000 OAPI 建模与内力提取 | SAP2000 |
| matrix-stiffness-2d | 2D 直接刚度法平面有限元内核 | 结构力学 / 有限元 |
| mechanics-diagram-renderer | 受拉侧内力图出图规范渲染 | 结构力学 |
| structure-benchmark-verifier| 经典力学题库基准回归验证 | 结构力学 |
| utocad-floor-layout-to-yjk | CAD 平面布置转 YJK 结构模型 | AutoCAD / YJK |
| multi-floor-dwg-to-ydb-model| 多层图纸批量解析对齐合并 | AutoCAD / YJK |
| structural-plan-layout-workflow | 结构方案与柱网生成 | 结构设计前期 |
| docker-electron-delivery | 求解器容器与客户端交付 | 交付与部署 |

---

## 🌟 持续扩充路线 (Roadmap)

- [x] AutoCAD 基础自动化与 DWG 施工图智能汉译英
- [x] Rhino 8/7 参数化 COM API 路由与几何交互
- [x] 盈建科 YJK 与 SAP2000 结构数据库接口对接
- [x] 2D 平面直接刚度法求解内核与受拉侧出图规范
- [ ] 空间桁架与 3D 空间结构直接刚度法求解器
- [ ] 地基基础与桩土相互作用分析模块
- [ ] 现浇混凝土与钢结构节点深化与构件自动配筋技能

---

## 📄 开源许可 (License)

本项目采用 MIT 许可证，永久免费开源。
