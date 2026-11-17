# 端点索引（Gen NX 使用说明）

**本包为资料受限、待验证初版，不是完整 Gen API 成品。** 下表用于查找候选路由，不构成已在 Gen NX 实测或可直接执行的证据。Civil NX 示例在未逐字段核验前不得执行。


对照基准：官方 MIDAS API Online Manual（页面写明覆盖 CIVIL NX **与** GEN NX，Edited 2026-07-14）。

**没有** 一份已成功读取正文的 Gen / Gen NX 专用字段手册。用户本地手册是 Civil NX（抓取 2025-12-23）。因此本索引的含义与 Civil 技能不同：

- 「官方目录列出」≠「已在 GEN NX 实测」≠「经典 Gen 可用」
- 与本地 Civil NX 手册共有的路径，只说明该路径存在于 NX 系列资料中；字段示例若来自 Civil 手册或官方 Civil NX Python 例，必须在调用时标明来源
- 本地 Civil NX 手册未收录、但名称偏楼层/构件设计/建筑抗震抗风的路径，可列为「更可能与 Gen NX 建筑工作流相关的官方目录项」，仍须对照当前 GEN NX 接口页

## 1. 官方 NX 系列中与 Civil NX 手册共有的路径

这些路径同时出现在官方总目录和 Civil NX 本地手册，适合作为 **共享约定的路由清单**（DOC/DB 的 `Assign` 结构、单位、节点、单元、分析控制等）。**不要**把 Civil 手册里的移动荷载、钢束、桥梁专项字段直接套到 Gen NX。

条目数量：204。完整表见 Civil 技能包 `references/endpoint-index.md` 第 1 节（两包使用同一交叉表，避免各写各的造成漂移）。本包在同名文件中收录同一份共有表，供独立分发。

### DOC

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/doc/ANAL` | [Anal] Perform Analysis | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/CLOSE` | 关闭项目[CLOSE]Close Project | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/EXPORT` | 导出[EXPORT]Export to Json | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/EXPORTMXT` | 导出mct/mgt[EXPORTMXT]Export to mct/mgt | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/IMPORT` | 导入[IMPORT]Import to Json | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/IMPORTMXT` | 导入mct/mgt[IMPORTMXT]Import to mct/mgt | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/NEW` | 新项目[NEW]New Project | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/OPEN` | 打开项目[OPEN]Open Project... | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/SAVE` | 保存[SAVE]Save | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/doc/SAVEAS` | 另存为[SAVEAS]Save As... | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Analysis

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ACTL` | [ACTL]Main Control Data | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/BCCT` | [BCCT]Boundary Change Assignment | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/BUCK` | [BUCK]Buckling Analysis Control | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/EIGV` | [EIGV]Eigenvalue Analysis Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HHCT` | [HHCT]Heat of Hydration Analysis Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCT` | [MVCT]Moving Load Analysis Control(Eurocode) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCTbs` | [MVCTbs] Moving Load Analysis Control(BS) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCTch` | [MVCTch]Moving Load Analysis Control(China) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCTid` | [MVCTid]Moving Load Analysis Control(India) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCTtr` | [MVCTTR]Moving Load Analysis Control(Transverse) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NLCT` | [NLCT]Nonlinear Analysis Control Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PDEL` | [PDEL]P-Delta Analysis Control | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SMCT` | [SMCT]Settlement Analysis Control Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STCT` | [STCT]Construction Stage Analysis Control Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Analysis Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CLWP` | [CLWP]Plate Cutting Line Diagram | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CUTL` | [CUTL]Cutting Line | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-CONC` | 混凝土设计[LCOM-CONC]Load Combinations (Concrete Design) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-GEN` | 一般[LCOM-GEN]Load Combinations (General) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-SEISMIC` | 地震[LCOM-SEISMIC]Load Combinations (Seismic) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-SRC` | SRC设计[LCOM-SRC]Load Combinations (SRC Design) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-STEEL` | 钢结构设计[LCOM-STEEL]Load Combinations (Steel Design) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LCOM-STLCOMP` | 组合钢梁设计[LCOM-STLCOMP]Load Combinations (Composite Steel Girder Design) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Boundary

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CGLP` | 修改一般连接特性值[CGLP]Change General Link Properties | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CLDR` | 定义标签方向[CLDR]Define Constraints Label Direction | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CONS` | 一般支承[CONS]Define Supports | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/ELNK` | Elastic Link | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/FRLS` | 释放梁端约束[FRLS]Beam End Release | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GSPR` | 分配一般弹性支承[GSPR]Assign General Spring Supports | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GSTP` | 定义一般弹性支承[GSTP]Define General Spring Type | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MCON` | 线性约束[MCON]Linear Constraints | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MLFC` | 变形-内力函数[MLFC]Force-Deformation Function | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NLLP` | 一般连接特性值[NLLP]General Link Property | DELETE, GET | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NLNK` | 一般连接[NLNK]General Link | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NSPR` | 节点弹性支承[NSPR]Point Spring | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/OFFS` | 梁端刚域[OFFS]Beam End Offsets | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PRLS` | 释放板端约束[PRLS]Plate End Release | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PZEF` | 刚域效果[PZEF]Panel Zone Effects | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/RIGD` | 刚性连接[RIGD]Rigid Link | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDHY` | 滞回阻尼器(MSS)[SDHY]Hysteretic Isolator(MSS) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDIS` | 隔震器(MSS)[SDIS]Isolator(MSS) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDST` | 钢阻尼器[SDST]Steel Damper | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDVE` | 粘弹性阻尼器[SDVE]Viscoelastic Damper | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDVI` | 黏滞阻尼器/油阻尼器[SDVI]Viscous Damper/Oil Damper | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SSPS` | 面弹性支承[SSPS]Surface Spring | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Bridge Specialization Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CAMB` | [CAMB]FCM Camber Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GCMB` | [GCMB]General Camber Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GSBG` | [GSBG]Bridge Girder Diagrams | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/ULFC` | [ULFC]Cable Control/Unknown Load Factor Constraints | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Construction Stage Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CMCS` | [CMCS]Camber for Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CRPC` | [CRPC]Creep Coefficient for Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CSCS` | [CSCS]Composite Section for Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STAG` | [STAG]Define Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STBK` | [STBK]CS Loads : Set-Back Loads for Nonlinear Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TMLD` | [TMLD]CS-Loads : Time Loads for Construction Stage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Design

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DCON` | [DCON]RC Design Code | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MATD` | [MATD]Modify Concrete Materials | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/RCHK` | [RCHK] Rebar Input for Column Section | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Dynamic Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SPFC` | [SPFC]Response Spectrum Functions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SPLC` | [SPLC]Response Spectrum Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THFC` | [THFC]Time History Functions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THGA` | [THGA]Ground Acceleration | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THGC` | [THGC]Time History Global Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THIS` | [THIS]Time History Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THMS` | [THMS]Multiple Support Excitation | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THNL` | [THNL]Dynamic Nodal Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THSL` | [THSL]Time Varying Static Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Heat of Hydration Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CCFC` | [CCFC]Convection : Convection Coefficient Functions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/ETFC` | [ETFC]Ambient Temperature Functions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HAHS` | [HAHS]Heat Source/Assign Heat Source | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HECB` | [HECB]Convection/Element Convection Boundary | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HPCE` | [HPCE]Pipe Cooling | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HSFC` | [HSFC]Heat Source/Heat Source Functions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HSPT` | [HSPT]Prescribed Temperature | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/HSTG` | [HSTG]Define Construction Stage for Hydration | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Heat of Hydration Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/HHND` | [HHND]Heat of Hydaration Result Graph | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Miscellaneous Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EFCT` | [EFCT]Small Displacement/Initial Force Control Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IELC` | [IELC]Ignore Elements for Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IFGS` | [IFGS]Large Displacement/Initial Forces for Geometric Stiffness | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/INMF` | Initial Element Force | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LDSQ` | [LDSQ]Load Sequence for Nonlinear | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PLCB` | [PLCB]Pre-composite Section | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Moving Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CJFG` | [CJFG]Concurrent Joint Force Group | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CRGR` | [CRGR]Concurrent Reaction Group | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/DYFG` | [DYFG]Railway Dynamic Factor - EUROCODE | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/DYLA` | Dy | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/DYNF` | [DYNF]Railway Dynamic Factor by Element- EUROCODE | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IMPF` | [IMPF]Additional Impact Factor | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LLANch` | 交通车道线-China[LLANch]Traffic Line Lanes - China | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LLANop` | 移动荷载优化[LLANop]Traffic Line Lanes - Moving Load Optimizaion | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LLANtr` | 交通车道线-横向移动荷载[LLANtr]Traffic Line Lane - Transverse | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MLSP` | [MLSP] Lane Support - Negative Moments at Interior Piers | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MLSR` | Reactions | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVCD` | 移动荷载规范[MVCD]Moving Load Code | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVHC` | [MVHC]Vehicles Classes | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVHL` | [MVHL]Vehicles - AASHTO LRFD | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVHLtr` | 车辆-横向移动荷载[MVHLtr]Vehicles - Transverse | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLD` | [MVLD]Moving Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDbs` | [MVLDbs]Moving Load Cases(BS) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDch` | [MVLDch]Moving Load Cases(China) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDeu` | [MVLDeu]Moving Load Cases - EUROCODE | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDid` | [MVLDid]Moving Load Cases(India) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDpl` | [MVLDpl] Moving Load Cases(Plond) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MVLDtr` | [MVLDtr]Moving Load Case(Transverse) | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SINF` | [SINF]Plate Element for Influence Surface | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SLANch` | 交通车道面-China[SLANch]Traffic Surface Lanes - China | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Node/Element

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DOEL` | 区域-单元[DOEL]Domain-Element | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/ELEM` | 单元[ELEM]Element | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MADO` | 定义区域[MADO]Define Domain | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NODE` | 节点[NODE]Node | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SBDO` | 定义子区域[SBDO]Define Sub-Domain | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SKEW` | 节点局部坐标轴[SKEW]Node Local Axis | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Prestress Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EXLD` | 体外力类型荷载[EXLD]External Type Load Case for Pretension | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PRST` | 梁单元预应力荷载[PRST]Prestress Beam Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PTNS` | 初拉力[PTNS]Pretension Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDCS` | 组合截面钢束的位置[TDCS]Tendon Location for Composite Section | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDNA` | Tendon Profile | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDNT` | Tendon Property | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDPL` | 钢束预应力[TDPL]Tendon Prestress | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Project

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BNGR` | 边界组[BNGR]Boundary Group | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GRUP` | 结构组[GRUP]Structure Group | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LDGR` | 荷载组[LDGR]Define Load Group | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PJCF` | 项目信息[PJCF]Project Information | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STYP` | 结构类型[STYP]Structure Type | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDGR` | Tendon Group | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/UNIT` | 单位系统[UNIT]Unit System | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Properties

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EDMP` | 修改特性[EDMP]Change Property | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/EPMT` | 塑性材料[EPMT]Plastic Material | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/EWSF` | 有效宽度系数[EWSF]Effective Width Scale Factor | GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/FIBR` | 纤维截面分割[FIBR]Fiber Division of Section | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/FIMP` | 非线性材料特性[FIMP]Inelastic Material Properties | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GRDP` | 组阻尼[GRDP]Group Damping | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IEHC` | 非弹性特性控制数据[IEHC]Inealstic Hinge Control Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IEHG` | 分配非弹性铰特性值[IEHG]Assign Inelastic Hinge Properties | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/IMFM` | 纤维模型的弹塑性材料特性[IMFM]Inelastic Material Properties for Fiber Model | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/MATL` | 材料特性值[MATL]Material Data | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PSSF` | 板刚度修改系数[PSSF]Plate Stiffness Scale Factor | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/RPSC` | 钢筋[RPSC]Reinforcements | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SECF` | 刚度[SECF]Stiffness | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SECT` | PSC设计截面[SECT]PSC | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STRPSSM` | 应力点[STRPSSM]Stress Points | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDME` | 抗压强度[TDME]Comp. Strength | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDMF` | 用户定义[TDMF]User Define | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TDMT` | 徐变/收缩[TDMT]Creep/Shrinkage | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THIK` | 加劲肋板 - 数据库[THIK]Thickness-Stiffened DB | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TMAT` | 时间依存性材料连接[TMAT]Time Dependent Material Link | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/TSGR` | 变截面组[TSGR]Tapered Group | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/VBEM` | 合力截面 - 定义虚梁[VBEM]Section for Resultant Forces - Define Virtual Beam | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/VSEC` | 合力截面 - 定义虚拟截面[VSEC]Section for Resultant Forces - Define Virtual Section | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Pushover

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/IEPI` | 忽略非线性分析初始荷载的单元[IEPI]Ignore Elements for NL. Analysis Intial Load | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PHGE` | 分配Pushover铰特性[PHGE]Assign Pushover Hinge Properties | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/POGD` | 整体控制[POGD]Global Control | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/POLC` | Pushover荷载工况[POLC]Pushover Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Settlement Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SMLC` | [SMLC]Settlement Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SMPT` | [SMPT]Settlement Group | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Static Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BMLD` | 梁荷载(单元）[BMLD]Beam Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/BODF` | 自重[BODF]Self Weight | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CNLD` | 节点荷载[CNLD]Nodal Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/FBLA` | 分配楼面荷载[FBLA]Assign Floor Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/FBLD` | 定义楼面荷载类型[FBLD]Define Floor Load Type | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/LTOM` | 荷载转换为质量[LTOM]Loads to Masses | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NBOF` | 节点体力[NBOF]Nodal Body Force | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NMAS` | 节点质量[NMAS]Nodal Masses | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PNLA` | 分配平面荷载[PNLA]Assign Plane Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PNLD` | 定义平面荷载类型[PNLD]Define Plane Load Type | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PRES` | 指定压力荷载[PRES]Assign Pressure Loads | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/PSLT` | 定义压力荷载类型[PSLT]Define Pressure Load Type | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/SDSP` | Displacement | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STLD` | 静力荷载工况[STLD]Static Load Cases | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Structure

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SPAN` | 跨度信息[SPAN]Span Information | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Temperature Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BTMP` | 梁截面温度[BTMP]Beam Section Temp. | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/ETMP` | 单元温度[ETMP]Element Temp. | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/GTMP` | 温度梯度[GTMP]Temperature Gradient | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NTMP` | 节点温度[NTMP]Nodal Temp. | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/STMP` | 系统温度[STMP]System Temp. | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / Time History Analysis Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/THRG` | [THRG]General Link Result | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THRI` | [THRI]Inelastic Hinge | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/THRS` | [THRS]Seismic Control Devices | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### DB / View

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CO_F` | [CO_F]Floor Load Color | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CO_M` | [CO_M]Material Color | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CO_S` | [CO_S]Section Color | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/CO_T` | [CO_T]Thickness Color | GET, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/db/NPLN` | 命名的平面[NPLN]Named Plane | DELETE, GET, POST, PUT | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### OPE

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/ope/AUTOMESH` | 自动网格[AUTOMESH] Auto-Mesh Planar Area | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/ope/DIVIDEELEM` | 分割单元[DIVIDEELEM] Divide Elements | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/ope/LINEBMLD` | 梁荷载(连续)[LINEBMLD] Line Beam Load | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/ope/PROJECTSTATUS` | 项目状态[PROJECTSTATUS]Project Status | GET | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/ope/SECTPROP` | 获取截面特性值˙[SECTPROP]Show Calculation Results | GET | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/ope/USLC` | 使用荷载组合[USLC]Using Load Combinations | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### VIEW

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/view/ACTIVE` | 激活[ACTIVE]Active | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/view/ANGLE` | 视点[ANGLE]View Point | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/view/CAPTURE` | 截图[CAPTURE]Capture | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/view/RESULTGRAPHIC` | [RESULTGRAPHIC]Buckling Mode Shapes | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |
| `/view/SELECT` | 选择[SELECT] Select | GET | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

### POST / Design

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/post/PM` | [PM] P-M Interaction Diagram (General Section) | POST | 官方 NX 目录；字段旁证来自 Civil NX 手册时必须标明 |

## 2. 更可能与 Gen NX / 建筑结构工作流相关、但未经 Gen 手册核验的官方目录项

这些路径出现在官方 NX 总目录，**未**出现在本地 Civil NX 手册，名称涉及楼层、墙、钢/SRC/冷弯设计、建筑规范地震与风、层间参数等。将它们列为「优先在 Gen NX 接口页中核对」的候选，**不是**已验证的 Gen NX 字段清单，更不是经典 Gen 的能力。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DCTL` | Definition of Frame | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/DRLS` | Diaphragm Disconnect | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/DSTL` | Steel Design Code | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/EPSE` | Seismic Earth Pressure | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/EPST` | Static Earth Pressure | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/LENG` | Unbraced Length | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/LTSR` | Limiting Slenderness Ratio | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/MBTP` | Modify Member Type | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/MEMB` | Member Assignment | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/POSL` | Parameter of Seismic Loads | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/POSP` | Parameter of Soil Properties | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/SSEIS` | Static Seismic Load - KDS(41-17-00:2019)  Static Seismic Load - User Type | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/STOR` | Story Data | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/SWIND` | Static Wind Load - KDS(41-12:2022)  Static Wind Load - User Type | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/THRE` | Time History Graph - Element Force Smart Graph | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/db/WMAK` | Modify Wall Mark Design | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/GUSTFACTOR` | Gust Factor Calculator | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/LCOM-CONC` | Load Combination (Concrete) - KDS 41 20 : 2022 | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/LCOM-SRC` | Load Combination (SRC) - KDS 41 SRC : 2022  Load Combination (SRC) - AIK-SRC2K | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/LCOM-STEEL` | Load Combination (Steel) - KDS 41 30 : 2022 | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/MEMB` | Member Assignment | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/STOR` | Story Calculation | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/STORPROP` | Story Properties | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/STORY_IRR_PARAM` | Story Irregularity Check Parameter | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/ope/STORY_PARAM` | Story Check Parameter | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/BRACEDESIGNFORCES` | Concrete Design - Brace Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/COLDFORMEDSTEELMEMBERDESIGNFORCES` | Cold Formed Design - Cold Formed Steel Member Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/SRCBEAMDESIGNFORCES` | SRC Design - SRC Beam Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/SRCCOLUMNDESIGNFORCES SRC` | SRC Design - SRC Column Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/STEELMEMBERDESIGNFORCES` | Steel Design - Steel Member Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |
| `/post/WALLDESIGNFORCES` | Concrete Design - Wall Design Forces | — | 仅官方 NX 目录；无 Gen 专用手册交叉核验 |

相关的官方结果表（预处理 Story 表、Analysis Story Table、墙/SRC/冷弯设计力等）见下节。仍需 `TABLE_TYPE` 以官方表页为准。

## 3. 不要当作 Gen NX 默认能力的官方标记项

### 3.1 Hyper-S solver only

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ACTL-M1` | Main Control Data | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/BCGA-M1` | Assign Boundary Combination | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/BCGD-M1` | Assign Boundary Combination | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/EIGV-M1` | Eigenvalue Analysis Control | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/EPMT-M1` | Plastic Material | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/HHCT-M1` | Heat of Hydration Analysis Control | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/IEHG-BEAM-M1` | Assign Inelastic Hinges - Beam | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/IEHG-GL-M1` | Assign Inelastic Hinges - General Link | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/IEHG-PSS-M1` | Assign Inelastic Hinges - Point Spring Support | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/IEHG-TRUSS-M1` | Assign Inelastic Hinges - Truss | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/IMFM-M1` | Inelastic Material Link for Auto Generation | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/MATL-M1` | Material Properties | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/NLCT-M1` | Nonlinear Analysis Control | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/NLNK-M1` | General Link | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/POGD-M1` | Pushover Global Control | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/POLC-M1` | Pushover Load Case | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/STCT-M1` | Construction Stage Analysis Control Data | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/STYP-M1` | Structure Type | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/THGC-M1` | Time History Global Control | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/THIS-M1` | Time History Load Cases | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |
| `/db/THOO-M1` | Time History Output Option | — | 仅官方目录；Hyper-S；限制：Hyper-S solver only |

### 3.2 官方标注为 MIDAS CIVIL NX JP Version only

即使写在同一份 NX 手册里，也不要当成 Gen NX 或通用 Gen 能力。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/GALD` | Grid Analysis Load | — | 官方限制：CIVIL NX 日本版；限制：CIVIL NX JP Version only |

### 3.3 更偏桥梁 / 移动荷载、且仅在官方目录出现的项

在 Gen NX 中调用前必须先确认当前产品接口页确实提供；默认视为 Civil 向能力。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/LLAN` | Traffic Line Lanes | — | 仅官方目录；偏桥梁/移动荷载 |
| `/db/LLANid` | Traffic Line Lanes - India | — | 仅官方目录；偏桥梁/移动荷载 |
| `/db/SLAN` | Traffic Surface Lanes | — | 仅官方目录；偏桥梁/移动荷载 |
| `/db/SLANop` | Traffic Surface Lanes - Moving Load Optimization | — | 仅官方目录；偏桥梁/移动荷载 |
| `/db/WVLD` | Wave Loads | — | 仅官方目录；偏桥梁/移动荷载 |
| `/doc/STAGAS` | Save Current Stage As | — | 仅官方目录；偏桥梁/移动荷载 |
| `/ope/GSBG` | Bridge Girder Diagrams | — | 仅官方目录；偏桥梁/移动荷载 |

### 3.4 其他仅官方目录路径

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ESSF` | Element Stiffness Scale Factor | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/db/FMLD` | Finishing Material Loads | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/db/ULCT` | Underground Load Combination Type | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/ope/EDMP` | Change Property | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/ope/LCOM-GEN` | Load Combination (General) - KDS : 2022  Load Combination (General) - AIK-SRC2K | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/ope/SSPS` | Surface Spring | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/post/BEAMDESIGNFORCES` | Concrete Design - Beam Design Force | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/post/COLUMNDESIGNFORCES` | Concrete Design - Column Design Forces | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/post/STEELCODECHECK` | Steel Code Check | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/view/DISPLAY` | Display | — | 仅官方目录；产品归属未在手册中单独标明 |
| `/view/PRECAPTURE` | Dialog Capture | — | 仅官方目录；产品归属未在手册中单独标明 |

## 4. 仅出现在本地 Civil NX 手册的路径

下列路径不应默认搬到 Gen NX 技能的「可用清单」中（例如 Wave Loads、Named UCS、Smart Report 用户表）。若用户在 GEN NX 接口页上看到相同路径，再按该页使用。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/NUCS` | 定义用户坐标系[NUCS]Named UCS | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册；默认不列入 Gen NX 已支持范围 |
| `/db/UFTR` | [UFTR] Define Header and Footer | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册；默认不列入 Gen NX 已支持范围 |
| `/db/UTBL` | [UTBL] User Defined Table | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册；默认不列入 Gen NX 已支持范围 |
| `/db/wvld` | [WVLD]Wave Loads | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册；默认不列入 Gen NX 已支持范围 |
| `/post/TABLE` | [TABLE]Get Result Table from Smart Report Table | POST | 仅本地 Civil NX 手册；默认不列入 Gen NX 已支持范围 |

## 5. 官方结果表类型

官方用单一 `post/TABLE` + `TABLE_TYPE`。下表抄自官方总目录。其中 Story 表、部分设计力表更偏建筑工作流，但仍 **未** 在 Gen 专用手册中逐表核验。该官方 POST/TABLE 说明文本身以 CIVIL NX 叙述为主。

### Pre-Process Table

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Element Weight | Element Weight Table | — |
| Nodal Body Force | Nodal Body Force Table | — |
| Mass Summary | Mass Summary Table | — |
| Load Summary | Load Summary Table | — |
| Material | Material Table | — |
| Section | Section Table | — |
| Restraint Supports | Restraint Support Table | — |
| Story Mass Summary | Story Mass Summary Table | — |
| Story Load Summary | Story Load Summary Table | — |
| Story Weight | Story Weight Table | — |
### Analysis Result Table

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Reaction-Local Reaction-Global Reaction-Local-Surface Spring | Reaction - Analysis Result Table | — |
| Displacement-Local Displacement-Global | Displacements - Analysis Result Table | — |
| Truss Force | Truss Force - Analysis Result Table | — |
| Cable Force | Cable Force - Analysis Result Table | — |
| Beam Force Beam Force-View by Max Value Item | Beam Force - Analysis Result Table | — |
| Plate Force-Local | Plate Force (Local) - Analysis Result Table | — |
| Plane Stress Force-Local | Plane Force (Local) - Analysis Result Table | — |
| Plane Strain Force-Local | Plane Strain Force (Local) - Analysis Result Table | — |
| Axisymmetric Force-Local | Axisymmetric Force (Local) - Analysis Result Table | — |
| Solid Force-Local | Solid Force (Local) - Analysis Result Table | — |
| Elastic Link View by Max Value Item | Elastic Link - Analysis Result Table | — |
| General Link Force General Link Force-View by Max Value Item General Link Deformation | General Link - Analysis Result Table | — |
| Resultant Force Resultant Force-View by Max Value Item | Resultant Forces - Analysis Result Table | — |
| Vibartion Mode-Eigenvalue Vibartion Mode-Participation Vector | Vibration Mode Shape - Analysis Result Table | — |
| Buckling Mode | Buckling Mode Shape - Analysis Result Table | — |
| Effective Span Length-Truss Effective Span Length-Beam Effective Span Length-Plate | Effective Span Length - Analysis Result Table | — |
| Nodal Results of RS-Inertia Force Nodal Results of RS-Acceleration | Nodal Results of RS - Analysis Result Table | — |
| Tendon Coordinates | Tendon Coordinates - Analysis Result Table | — |
| Composite Section for C.S. Force Composite Section for C.S. Stress | Composite Section for C.S. (Force and Stress) - Analysis Result Table | — |
| Element Properties at Each Stage | Element Properties at Each Stage - Analysis Result Table | — |
| Lack of Fit Force-Truss | Lack of Fit Force (Truss) - Analysis Result Table | — |
| Equilibrium Element Nodal Force | Equilibrium Element Nodal Force - Analysis Result Table | — |
| Initial Element Force | Initial Element Force - Analysis Result Table | — |
| Wall Force/Moment | Wall Force/Moment - Analysis Result Table | — |
| Concurrent Joint Force Table | Concurrent Joint Force Table | — |
### Analysis Story Table

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Story Drift (X,Y,Combined) | Story Drift - Analysis Story Table | — |
| Story Displacement (X,Y,Combined) | Story Displacement - Analysis Story Table | — |
| Story Shear(R.S Analysis) - Story Shear(for R.S) Story Shear(R.S.Analysis) - Story Shear Force Coefficient | Story Shear(R.S Analysis) - Analysis Story Table Story Shear Force Coefficient(R.S.Analysis) - Story Result Table | — |
| Story Mode Shape | Story Mode Shape - Analysis Story Table | — |
| Story Shear Force Ratio | Story Shear Force Ratio - Analysis Story Table | — |
| Story Eccentricity | Story Eccentricity - Analysis Story Table | — |
| Overturning Moment | Overturning Moment - Analysis Story Table | — |
| Story Axial Force Sum | Story Axial Force Sum - Analysis Story Table | — |
| Story Stability Coefficient | Story Stability Coefficient - Analysis Story Table | — |
| Torsional Irregularity Check | Torsional Irregularity Check - Analysis Story Table | — |
| Torsional Amplification Factor | Torsional Amplification Factor - Analysis Story Table | — |
| Stiffness Irregularity Check (Soft Story) | Stiffness Irregularity Check (Soft Story) - Analysis Story Table | — |
| Capacity Irregularity Check(Weak Story) | Capacity Irregularity Check(Weak Story) - Analysis Story Table | — |
| Criteria for Regularity in Plan | Criteria for Regularity in Plan - Analysis Story Table | — |
| Ultimate Story Shear For Check | Ultimate Story Shear For Check - Analysis Story Table | — |
| Weight Irregularity Check - Story Result Table | Weight Irregularity Check - Analysis Story Table | — |
### Time History Result Table

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Displacement Velocity Absolute Acceleration Relative Acceleration | Displacement/Velocity/Acceleration - TH Result Table | — |
| Beam Force | Beam Force - TH Result Table | — |
| Truss Force | Truss Force - TH Result Table | — |
| General Link Force Deformation | General Link - TH Result Table | — |
| Event Time-Lumped Event Time-Distributed Event Time-Wall Event Time-Truss Event Time-Spring | Inelastic Hinge Event Time - TH Result Table | — |
| Beam Summary-DX Beam Summary-DY Beam Summary-DZ Beam Summary-RY Beam Summary-RZ | Inelastic Hinge Beam Summary - TH Result Table | — |
| Truss Summary-DX | Inelastic Hinge Truss Summary - TH Result Table | — |
| General Link Summary-DX General Link Summary-DY General Link Summary-DZ General Link Summary-RX General Link Summary-RY General Link Summary-RZ | Inelastic Hinge General Link Summary - TH Result Table | — |
| Force-Lumped Force-Distributed Force-Wall Force-Truss Force-Spring | Inelastic Hinge Force - TH Result Table | — |
| Deformation-Lumped Deformation-Distributed Deformation-Wall Deformation-Truss Deformation-Spring | Inelastic Hinge Deformation - TH Result Table | — |
| Element Rotation-Beam Element Rotation-Wall | Inelastic Hinge Element Rotation - TH Result Table | — |
| Ductility Factor(D/D1)-Lumped Ductility Factor(D/D1)-Distributed Ductility Factor(D/D1)-Wall Ductility Factor(D/D1)-Truss Ductility Factor(D/D1)-Spring | Inelastic Hinge Ductility Factor(D/D1) - TH Result Table | — |
| Ductility Factor(D/D2)-Lumped Ductility Factor(D/D2)-Distributed Ductility Factor(D/D2)-Wall Ductility Factor(D/D2)-Truss Ductility Factor(D/D2)-Spring | Inelastic Hinge Ductility Factor(D/D2) - TH Result Table | — |
| Estimate Yield Strength | Fiber Section Estimate Yield Strength - TH Result Table | — |
| Elastic Modulus Retention Rate | Fiber Section Elastic Modulus Retention Rate - TH Result Table | CIVIL NX JP Version only |
| Maximum Strain of The Cell | Fiber Section Maximum Strain of The Cell - TH Result Table | CIVIL NX JP Version only |
| Event Step | Fiber Section Event Step - TH Result Table | CIVIL NX JP Version only |
| Average Compression Strain | Fiber Section Average Compression Strain - TH Result Table | CIVIL NX JP Version only |
### Heat of Hydration Result Table

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Stress-Local Stress-Global | Stress - HY Result Table | — |
| Temperature | Temperature - HY Result Table | — |
| Displacement | Displacement - HY Result Table | — |
| Tensile Stress | Tensile Stress - HY Result Table | — |
| Pipe Cooling Nodal Temperature | Pipe Cooling Nodal Temperature - HY Result Table | — |
### Time History Text

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Node Results | Time History Text - Node Results | — |
| Element Result(Truss, Beam, Plane Stress/Strain, Solid) | Time History Text - Element Result(Truss, Beam, Plane Stress/Strain, Solid) | — |
| Element Result(Plate) | Time History Text - Element Result(Plate) | — |
| Element Result(Wall) | Time History Text - Element Result(Wall) | — |
| General Link Result | Time History Text - General Link Result | — |
### Pushover Text

| 表类型或名称（官方目录，多数无独立路径） | 说明 | 限制 |
| --- | --- | --- |
| Displacement Result | Pushover Text - Displacement Result | — |
| Element Result(Beam, Truss) | Pushover Text - Element Result(Beam, Truss) | — |
| Element Result(Wall) | Pushover Text - Element Result(Wall) | — |
| General Link Result | Pushover Text - General Link Result | — |
| Elastic Link Result | Pushover Text - Elastic Link Result | — |
