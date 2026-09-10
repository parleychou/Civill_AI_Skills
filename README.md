# Civill_AI_Skills

<p align="center">
  <strong>Standardized AI Skills Library for Civil & Structural Engineers</strong><br>
  <em>Turn Claude Code, Cursor, and Antigravity into Senior Structural Engineers</em>
</p>

<p align="center">
  <a href="https://ai.venchy.online/skills/">🌐 Official Online Skills Portal</a> •
  <a href="#quick-start">🚀 Quick Start</a> •
  <a href="#core-capabilities">🛠️ Core Capabilities</a> •
  <a href="#skills-catalog">📦 Skills Catalog</a> •
  <a href="README_zh.md">🇨🇳 中文文档</a>
</p>

---

## 📖 Overview

**Civill_AI_Skills** is a specialized, open-source AI Agent skill repository tailored for civil and structural engineering workflows.

While general-purpose LLMs excel at generic programming, they struggle with civil engineering tasks due to:
1. **Lack of Industrial Software APIs**: Proprietary or legacy COM/ActiveX interfaces (AutoCAD, Rhino 8/7, SAP2000 OAPI, YJK SQLite `.ydb`) are rarely covered in general pretraining data.
2. **Missing Engineering Drafting Rules**: Standard conventions (such as drawing bending moment diagrams strictly on the tension side, preserving DWG layer hierarchies, preventing duplicate translation tags) require explicit domain constraints.
3. **Rigorous Mechanics Accuracy**: Finite element algorithms and stiffness matrix assembly demand exact mathematical formulation and benchmark verification.

`Civill_AI_Skills` bridges this gap. By loading these standardized `SKILL.md` packages into your project's `./skills/` directory, AI Agents like **Claude Code**, **Cursor**, and **Antigravity** instantly gain native engineering capabilities.

> ⚡ **Continuously Expanding Ecosystem**: This repository is actively maintained. Additional skills covering geotechnical engineering, foundation analysis, reinforced concrete detailing, and code-checking automation are continuously being added.

---

## 🛠️ Core Capabilities

### 1. CAD & Drafting Automation
* **`pyautocad`**: Native AutoCAD ActiveX/COM Python automation for batch entity extraction, layer management, and geometric drafting.
* **`autocad-structural-translation`**: Production-grade Chinese-to-English DWG drawing translation engine that preserves layers, alignments, and text formatting while avoiding duplicate translations.
* **`autocad-floor-layout-to-yjk`**: Intelligent CAD architectural/structural floor plan recognition and automatic conversion into structural analytical models.
* **`multi-floor-dwg-to-ydb-model`**: Multi-story drawing batch parsing, column grid alignment, and upper-lower floor model merging.

### 2. 3D Parametric & BIM Visualization
* **`rhinorouter`**: Production-grade skill for Rhinoceros (Rhino 8 / 7 / 6) via Python and RhinoScript COM automation. Features an offline database of 1,245 official APIs across 29 modules, multi-version connection discovery, robust VARIANT data marshaling, and parametric curve/surface modeling.
* **`ifc-threejs-viewer.skill`**: One-click IFC model to interactive Three.js 3D web viewer with public deployment. Automatically parses IFC geometry, extracts floor levels and structural types (columns, beams, slabs, walls), generates GLB models + manifests, and outputs interactive web viewers with floor/type toggles.

### 3. Structural Database & Analysis Interfaces
* **`yjk-database`**: Direct SQLite underlying read/write access to YJK (`.ydb`) structural databases, component geometry queries, and sectional property extraction.
* **`sap2000-python`**: SAP2000 OAPI modeling, load case definitions, load combinations, and member internal force extraction.
* **`structural-plan-layout-workflow`**: Structural framing layout design, column grid synthesis, and preliminary beam/column member dimensioning.

### 4. Finite Element Mechanics & Standardization
* **`matrix-stiffness-2d`**: High-performance 2D Direct Stiffness Method (DSM) plane frame finite element solver kernel with precise joint displacement and force computation.
* **`mechanics-diagram-renderer`**: Canvas and SVG rendering engine enforcing strict civil engineering drafting standards (tension-side bending moments, shear, and axial force diagrams).
* **`structure-benchmark-verifier`**: Classical structural mechanics benchmark regression suite for rigorous calculation validation.
* **`docker-electron-delivery`**: Lightweight containerization and desktop packaging templates for civil engineering solver deployment.

### 5. AI Agent Optimization & Cost Delegation
* **`cheap-agent`**: Delegate bounded software-engineering work (repo exploration, first-pass code review/analysis, test generation, and bounded implementation) to Antigravity CLI with Gemini Flash in an isolated git worktree, significantly reducing primary model token costs.

---

## 🚀 Quick Start

### Method 1: Use via Local Repository (Recommended)

1. **Clone this repository**:
   ```bash
   git clone https://github.com/parleychou/Civill_AI_Skills.git
   ```

2. **Copy the desired skills into your project**:
   Copy the skill folders you need into your project's `./skills/` directory:
   ```text
   your-engineering-project/
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

3. **Prompt Claude Code / Cursor**:
   Launch your agent in the project folder. The AI automatically detects the `SKILL.md` rules and executes according to civil engineering standards:
   ```bash
   # Example Claude Code command:
   >_ claude "Inspect the DWG file in current directory and translate structural annotations into English"
   ```

### Method 2: Web Portal Download
Visit our official web repository to browse, preview, and download individual skill packages:  
🌐 **[https://ai.venchy.online/skills/](https://ai.venchy.online/skills/)**

---

## 📦 Skills Catalog

| Skill Directory | Target Software / Domain | Description | Key Assets Included |
| :--- | :--- | :--- | :--- |
| **`autocad-structural-translation`** | AutoCAD / Global Projects | Intelligent Chinese-to-English DWG drawing translation | Translation engine, glossary, evals |
| **`pyautocad`** | AutoCAD / Python COM | Batch CAD entity extraction and geometric manipulation | ActiveX wrappers, drafting utilities |
| **`rhinorouter`** | Rhino 8/7 / Grasshopper | Parametric 3D modeling with 1,245 official COM APIs | SQLite API database, connection manager |
| **`ifc-threejs-viewer.skill`** | BIM / WebGL / Three.js | One-click IFC model to interactive Three.js web viewer with floor & type toggles | `ifc_to_web.py`, `viewer.html`, `SKILL.md` |
| **`yjk-database`** | YJK (盈建科) | Direct SQLite read/write access to YJK `.ydb` models | Database baseline, validation scripts |
| **`sap2000-python`** | CSI SAP2000 | OAPI structural modeling, loading, and force extraction | OAPI reference, extraction scripts |
| **`matrix-stiffness-2d`** | Structural Mechanics / FEA | 2D Direct Stiffness Method finite element solver kernel | Stiffness solver, internal force engine |
| **`mechanics-diagram-renderer`** | Structural Mechanics | Tension-side bending moment diagram renderer | Canvas/SVG renderers, viewport templates |
| **`structure-benchmark-verifier`** | Benchmark Verification | Automated regression test suite against classic problems | 100+ benchmark cases, runner scripts |
| **`autocad-floor-layout-to-yjk`** | AutoCAD + YJK | Floor plan recognition to structural analysis model | Layout parsing rules, mapping schema |
| **`multi-floor-dwg-to-ydb-model`** | Multi-story Buildings | Multi-floor drawing batch parsing and vertical alignment | Alignment pipeline, merge workflow |
| **`structural-plan-layout-workflow`** | Structural Scheme Design | Column grid generation and preliminary sizing | Member estimation tables, rules |
| **`docker-electron-delivery`** | Private Deployment | Solver containerization and cross-platform desktop UI | Dockerfile, Electron main templates |

---

## 🌟 Roadmap & Continuous Expansion

- [x] AutoCAD drafting automation and DWG structural drawing translation
- [x] Rhino 8/7 parametric COM API router with offline knowledge base
- [x] YJK (`.ydb`) and SAP2000 structural database integration
- [x] 2D Direct Stiffness Method solver and tension-side diagram rendering
- [ ] 3D space frame & truss Direct Stiffness Method solver
- [ ] Foundation & soil-structure interaction analysis skills
- [ ] Reinforced concrete & structural steel automated connection detailing
- [ ] Code compliance checking (GB 50010, GB 50011, ACI 318, Eurocode)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free and open-source for personal and commercial engineering applications.
