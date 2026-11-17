# 端点索引（Civil NX 交叉核验）

对照基准：

- 官方 MIDAS API Online Manual（NX 系列目录，页面标注 Edited 2026-07-14）
- 本地 midas Civil NX API 用户手册（抓取 2025-12-23），已解析到 URI 的页面 412 个

路径已做前缀大小写归一（`/doc` `/db` `/ope` `/view` `/post`）。文档级路径另将最后一段统一为大写以便对照（如本地 `doc/save` 与官方 `/doc/SAVE` 视为同一条）。**实际请求的大小写以当前接口页或实测响应为准。**

统计：双方共有路径 **204**；仅本地手册（归一后仍无法与官方路径对齐）**5**；仅官方目录 **71**；官方结果表类条目（目录未给独立路径、通常走 `post/TABLE`）**84**。

## 1. 双方共有（可作为 Civil NX 已交叉核验的端点清单）

出现在官方 NX 目录，并且本地 Civil NX 手册也有对应 URI。字段仍以各接口页为准，本表只做路由。

### DOC

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/doc/ANAL` | [Anal] Perform Analysis | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/CLOSE` | 关闭项目[CLOSE]Close Project | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/EXPORT` | 导出[EXPORT]Export to Json | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/EXPORTMXT` | 导出mct/mgt[EXPORTMXT]Export to mct/mgt | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/IMPORT` | 导入[IMPORT]Import to Json | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/IMPORTMXT` | 导入mct/mgt[IMPORTMXT]Import to mct/mgt | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/NEW` | 新项目[NEW]New Project | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/OPEN` | 打开项目[OPEN]Open Project... | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/SAVE` | 保存[SAVE]Save | POST | 官方目录 + 本地 Civil NX 手册 |
| `/doc/SAVEAS` | 另存为[SAVEAS]Save As... | POST | 官方目录 + 本地 Civil NX 手册 |
### DB / Analysis

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ACTL` | [ACTL]Main Control Data | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/BCCT` | [BCCT]Boundary Change Assignment | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/BUCK` | [BUCK]Buckling Analysis Control | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/EIGV` | [EIGV]Eigenvalue Analysis Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HHCT` | [HHCT]Heat of Hydration Analysis Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCT` | [MVCT]Moving Load Analysis Control(Eurocode) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCTbs` | [MVCTbs] Moving Load Analysis Control(BS) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCTch` | [MVCTch]Moving Load Analysis Control(China) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCTid` | [MVCTid]Moving Load Analysis Control(India) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCTtr` | [MVCTTR]Moving Load Analysis Control(Transverse) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NLCT` | [NLCT]Nonlinear Analysis Control Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PDEL` | [PDEL]P-Delta Analysis Control | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SMCT` | [SMCT]Settlement Analysis Control Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STCT` | [STCT]Construction Stage Analysis Control Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Analysis Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CLWP` | [CLWP]Plate Cutting Line Diagram | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CUTL` | [CUTL]Cutting Line | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-CONC` | 混凝土设计[LCOM-CONC]Load Combinations (Concrete Design) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-GEN` | 一般[LCOM-GEN]Load Combinations (General) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-SEISMIC` | 地震[LCOM-SEISMIC]Load Combinations (Seismic) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-SRC` | SRC设计[LCOM-SRC]Load Combinations (SRC Design) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-STEEL` | 钢结构设计[LCOM-STEEL]Load Combinations (Steel Design) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LCOM-STLCOMP` | 组合钢梁设计[LCOM-STLCOMP]Load Combinations (Composite Steel Girder Design) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Boundary

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CGLP` | 修改一般连接特性值[CGLP]Change General Link Properties | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CLDR` | 定义标签方向[CLDR]Define Constraints Label Direction | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CONS` | 一般支承[CONS]Define Supports | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/ELNK` | Elastic Link | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/FRLS` | 释放梁端约束[FRLS]Beam End Release | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GSPR` | 分配一般弹性支承[GSPR]Assign General Spring Supports | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GSTP` | 定义一般弹性支承[GSTP]Define General Spring Type | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MCON` | 线性约束[MCON]Linear Constraints | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MLFC` | 变形-内力函数[MLFC]Force-Deformation Function | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NLLP` | 一般连接特性值[NLLP]General Link Property | DELETE, GET | 官方目录 + 本地 Civil NX 手册 |
| `/db/NLNK` | 一般连接[NLNK]General Link | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NSPR` | 节点弹性支承[NSPR]Point Spring | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/OFFS` | 梁端刚域[OFFS]Beam End Offsets | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PRLS` | 释放板端约束[PRLS]Plate End Release | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PZEF` | 刚域效果[PZEF]Panel Zone Effects | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/RIGD` | 刚性连接[RIGD]Rigid Link | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDHY` | 滞回阻尼器(MSS)[SDHY]Hysteretic Isolator(MSS) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDIS` | 隔震器(MSS)[SDIS]Isolator(MSS) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDST` | 钢阻尼器[SDST]Steel Damper | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDVE` | 粘弹性阻尼器[SDVE]Viscoelastic Damper | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDVI` | 黏滞阻尼器/油阻尼器[SDVI]Viscous Damper/Oil Damper | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SSPS` | 面弹性支承[SSPS]Surface Spring | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Bridge Specialization Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CAMB` | [CAMB]FCM Camber Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GCMB` | [GCMB]General Camber Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GSBG` | [GSBG]Bridge Girder Diagrams | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/ULFC` | [ULFC]Cable Control/Unknown Load Factor Constraints | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Construction Stage Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CMCS` | [CMCS]Camber for Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CRPC` | [CRPC]Creep Coefficient for Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CSCS` | [CSCS]Composite Section for Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STAG` | [STAG]Define Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STBK` | [STBK]CS Loads : Set-Back Loads for Nonlinear Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TMLD` | [TMLD]CS-Loads : Time Loads for Construction Stage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Design

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DCON` | [DCON]RC Design Code | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MATD` | [MATD]Modify Concrete Materials | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/RCHK` | [RCHK] Rebar Input for Column Section | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Dynamic Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SPFC` | [SPFC]Response Spectrum Functions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SPLC` | [SPLC]Response Spectrum Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THFC` | [THFC]Time History Functions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THGA` | [THGA]Ground Acceleration | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THGC` | [THGC]Time History Global Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THIS` | [THIS]Time History Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THMS` | [THMS]Multiple Support Excitation | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THNL` | [THNL]Dynamic Nodal Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THSL` | [THSL]Time Varying Static Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Heat of Hydration Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CCFC` | [CCFC]Convection : Convection Coefficient Functions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/ETFC` | [ETFC]Ambient Temperature Functions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HAHS` | [HAHS]Heat Source/Assign Heat Source | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HECB` | [HECB]Convection/Element Convection Boundary | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HPCE` | [HPCE]Pipe Cooling | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HSFC` | [HSFC]Heat Source/Heat Source Functions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HSPT` | [HSPT]Prescribed Temperature | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/HSTG` | [HSTG]Define Construction Stage for Hydration | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Heat of Hydration Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/HHND` | [HHND]Heat of Hydaration Result Graph | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Miscellaneous Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EFCT` | [EFCT]Small Displacement/Initial Force Control Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IELC` | [IELC]Ignore Elements for Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IFGS` | [IFGS]Large Displacement/Initial Forces for Geometric Stiffness | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/INMF` | Initial Element Force | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LDSQ` | [LDSQ]Load Sequence for Nonlinear | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PLCB` | [PLCB]Pre-composite Section | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Moving Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CJFG` | [CJFG]Concurrent Joint Force Group | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CRGR` | [CRGR]Concurrent Reaction Group | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/DYFG` | [DYFG]Railway Dynamic Factor - EUROCODE | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/DYLA` | Dy | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/DYNF` | [DYNF]Railway Dynamic Factor by Element- EUROCODE | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IMPF` | [IMPF]Additional Impact Factor | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LLANch` | 交通车道线-China[LLANch]Traffic Line Lanes - China | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LLANop` | 移动荷载优化[LLANop]Traffic Line Lanes - Moving Load Optimizaion | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LLANtr` | 交通车道线-横向移动荷载[LLANtr]Traffic Line Lane - Transverse | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MLSP` | [MLSP] Lane Support - Negative Moments at Interior Piers | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MLSR` | Reactions | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVCD` | 移动荷载规范[MVCD]Moving Load Code | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVHC` | [MVHC]Vehicles Classes | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVHL` | [MVHL]Vehicles - AASHTO LRFD | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVHLtr` | 车辆-横向移动荷载[MVHLtr]Vehicles - Transverse | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLD` | [MVLD]Moving Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDbs` | [MVLDbs]Moving Load Cases(BS) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDch` | [MVLDch]Moving Load Cases(China) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDeu` | [MVLDeu]Moving Load Cases - EUROCODE | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDid` | [MVLDid]Moving Load Cases(India) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDpl` | [MVLDpl] Moving Load Cases(Plond) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MVLDtr` | [MVLDtr]Moving Load Case(Transverse) | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SINF` | [SINF]Plate Element for Influence Surface | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SLANch` | 交通车道面-China[SLANch]Traffic Surface Lanes - China | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Node/Element

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DOEL` | 区域-单元[DOEL]Domain-Element | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/ELEM` | 单元[ELEM]Element | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MADO` | 定义区域[MADO]Define Domain | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NODE` | 节点[NODE]Node | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SBDO` | 定义子区域[SBDO]Define Sub-Domain | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SKEW` | 节点局部坐标轴[SKEW]Node Local Axis | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Prestress Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EXLD` | 体外力类型荷载[EXLD]External Type Load Case for Pretension | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PRST` | 梁单元预应力荷载[PRST]Prestress Beam Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PTNS` | 初拉力[PTNS]Pretension Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDCS` | 组合截面钢束的位置[TDCS]Tendon Location for Composite Section | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDNA` | Tendon Profile | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDNT` | Tendon Property | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDPL` | 钢束预应力[TDPL]Tendon Prestress | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Project

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BNGR` | 边界组[BNGR]Boundary Group | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GRUP` | 结构组[GRUP]Structure Group | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LDGR` | 荷载组[LDGR]Define Load Group | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PJCF` | 项目信息[PJCF]Project Information | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STYP` | 结构类型[STYP]Structure Type | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDGR` | Tendon Group | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/UNIT` | 单位系统[UNIT]Unit System | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Properties

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/EDMP` | 修改特性[EDMP]Change Property | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/EPMT` | 塑性材料[EPMT]Plastic Material | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/EWSF` | 有效宽度系数[EWSF]Effective Width Scale Factor | GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/FIBR` | 纤维截面分割[FIBR]Fiber Division of Section | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/FIMP` | 非线性材料特性[FIMP]Inelastic Material Properties | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GRDP` | 组阻尼[GRDP]Group Damping | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IEHC` | 非弹性特性控制数据[IEHC]Inealstic Hinge Control Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IEHG` | 分配非弹性铰特性值[IEHG]Assign Inelastic Hinge Properties | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/IMFM` | 纤维模型的弹塑性材料特性[IMFM]Inelastic Material Properties for Fiber Model | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/MATL` | 材料特性值[MATL]Material Data | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PSSF` | 板刚度修改系数[PSSF]Plate Stiffness Scale Factor | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/RPSC` | 钢筋[RPSC]Reinforcements | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SECF` | 刚度[SECF]Stiffness | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SECT` | PSC设计截面[SECT]PSC | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STRPSSM` | 应力点[STRPSSM]Stress Points | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDME` | 抗压强度[TDME]Comp. Strength | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDMF` | 用户定义[TDMF]User Define | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TDMT` | 徐变/收缩[TDMT]Creep/Shrinkage | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THIK` | 加劲肋板 - 数据库[THIK]Thickness-Stiffened DB | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TMAT` | 时间依存性材料连接[TMAT]Time Dependent Material Link | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/TSGR` | 变截面组[TSGR]Tapered Group | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/VBEM` | 合力截面 - 定义虚梁[VBEM]Section for Resultant Forces - Define Virtual Beam | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/VSEC` | 合力截面 - 定义虚拟截面[VSEC]Section for Resultant Forces - Define Virtual Section | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Pushover

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/IEPI` | 忽略非线性分析初始荷载的单元[IEPI]Ignore Elements for NL. Analysis Intial Load | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PHGE` | 分配Pushover铰特性[PHGE]Assign Pushover Hinge Properties | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/POGD` | 整体控制[POGD]Global Control | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/POLC` | Pushover荷载工况[POLC]Pushover Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Settlement Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SMLC` | [SMLC]Settlement Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SMPT` | [SMPT]Settlement Group | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Static Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BMLD` | 梁荷载(单元）[BMLD]Beam Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/BODF` | 自重[BODF]Self Weight | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CNLD` | 节点荷载[CNLD]Nodal Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/FBLA` | 分配楼面荷载[FBLA]Assign Floor Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/FBLD` | 定义楼面荷载类型[FBLD]Define Floor Load Type | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/LTOM` | 荷载转换为质量[LTOM]Loads to Masses | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NBOF` | 节点体力[NBOF]Nodal Body Force | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NMAS` | 节点质量[NMAS]Nodal Masses | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PNLA` | 分配平面荷载[PNLA]Assign Plane Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PNLD` | 定义平面荷载类型[PNLD]Define Plane Load Type | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PRES` | 指定压力荷载[PRES]Assign Pressure Loads | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/PSLT` | 定义压力荷载类型[PSLT]Define Pressure Load Type | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/SDSP` | Displacement | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STLD` | 静力荷载工况[STLD]Static Load Cases | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Structure

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/SPAN` | 跨度信息[SPAN]Span Information | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Temperature Loads

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/BTMP` | 梁截面温度[BTMP]Beam Section Temp. | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/ETMP` | 单元温度[ETMP]Element Temp. | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/GTMP` | 温度梯度[GTMP]Temperature Gradient | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NTMP` | 节点温度[NTMP]Nodal Temp. | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/STMP` | 系统温度[STMP]System Temp. | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / Time History Analysis Results

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/THRG` | [THRG]General Link Result | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THRI` | [THRI]Inelastic Hinge | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/THRS` | [THRS]Seismic Control Devices | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### DB / View

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/CO_F` | [CO_F]Floor Load Color | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CO_M` | [CO_M]Material Color | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CO_S` | [CO_S]Section Color | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/CO_T` | [CO_T]Thickness Color | GET, PUT | 官方目录 + 本地 Civil NX 手册 |
| `/db/NPLN` | 命名的平面[NPLN]Named Plane | DELETE, GET, POST, PUT | 官方目录 + 本地 Civil NX 手册 |
### OPE

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/ope/AUTOMESH` | 自动网格[AUTOMESH] Auto-Mesh Planar Area | POST | 官方目录 + 本地 Civil NX 手册 |
| `/ope/DIVIDEELEM` | 分割单元[DIVIDEELEM] Divide Elements | POST | 官方目录 + 本地 Civil NX 手册 |
| `/ope/LINEBMLD` | 梁荷载(连续)[LINEBMLD] Line Beam Load | POST | 官方目录 + 本地 Civil NX 手册 |
| `/ope/PROJECTSTATUS` | 项目状态[PROJECTSTATUS]Project Status | GET | 官方目录 + 本地 Civil NX 手册 |
| `/ope/SECTPROP` | 获取截面特性值˙[SECTPROP]Show Calculation Results | GET | 官方目录 + 本地 Civil NX 手册 |
| `/ope/USLC` | 使用荷载组合[USLC]Using Load Combinations | POST | 官方目录 + 本地 Civil NX 手册 |
### VIEW

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/view/ACTIVE` | 激活[ACTIVE]Active | POST | 官方目录 + 本地 Civil NX 手册 |
| `/view/ANGLE` | 视点[ANGLE]View Point | POST | 官方目录 + 本地 Civil NX 手册 |
| `/view/CAPTURE` | 截图[CAPTURE]Capture | POST | 官方目录 + 本地 Civil NX 手册 |
| `/view/RESULTGRAPHIC` | [RESULTGRAPHIC]Buckling Mode Shapes | POST | 官方目录 + 本地 Civil NX 手册 |
| `/view/SELECT` | 选择[SELECT] Select | GET | 官方目录 + 本地 Civil NX 手册 |
### POST / Design

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/post/PM` | [PM] P-M Interaction Diagram (General Section) | POST | 官方目录 + 本地 Civil NX 手册 |

## 2. 仅出现在本地 Civil NX 手册

这些路径在归一后仍无法与官方目录中的路径一一对应。其中部分可能是写法差异、Smart Report 专用，或官方目录未单列。不要把它们写成「官方目录已列出的标准路径」，但可以在 Civil NX 场景按本地手册使用，并注明来源。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/NUCS` | 定义用户坐标系[NUCS]Named UCS | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册 |
| `/db/UFTR` | [UFTR] Define Header and Footer | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册 |
| `/db/UTBL` | [UTBL] User Defined Table | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册 |
| `/db/wvld` | [WVLD]Wave Loads | DELETE, GET, POST, PUT | 仅本地 Civil NX 手册 |
| `/post/TABLE` | [TABLE]Get Result Table from Smart Report Table | POST | 仅本地 Civil NX 手册 |

说明：

- `/db/NUCS`、`/db/UFTR`、`/db/UTBL`、`/db/wvld` 等为本地手册收录、官方总目录未单列的路径。
- 本地 Smart Report 页使用 `{base url} + POST/TABLE`，与官方结果表的 `post/TABLE` + `TABLE_TYPE` 不是同一套说明，见 `results.md`。

## 3. 仅出现在官方 NX 目录（默认不当作 Civil NX 已交叉核验）

### 3.1 官方标为 Hyper-S solver only（`-M1`）

本地 Civil NX 手册未收录。除非用户环境与对应接口页明确支持 Hyper-S，否则不要调用，更不要当作常规 Civil NX 能力。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ACTL-M1` | Main Control Data | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/BCGA-M1` | Assign Boundary Combination | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/BCGD-M1` | Assign Boundary Combination | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/EIGV-M1` | Eigenvalue Analysis Control | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/EPMT-M1` | Plastic Material | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/HHCT-M1` | Heat of Hydration Analysis Control | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/IEHG-BEAM-M1` | Assign Inelastic Hinges - Beam | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/IEHG-GL-M1` | Assign Inelastic Hinges - General Link | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/IEHG-PSS-M1` | Assign Inelastic Hinges - Point Spring Support | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/IEHG-TRUSS-M1` | Assign Inelastic Hinges - Truss | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/IMFM-M1` | Inelastic Material Link for Auto Generation | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/MATL-M1` | Material Properties | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/NLCT-M1` | Nonlinear Analysis Control | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/NLNK-M1` | General Link | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/POGD-M1` | Pushover Global Control | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/POLC-M1` | Pushover Load Case | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/STCT-M1` | Construction Stage Analysis Control Data | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/STYP-M1` | Structure Type | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/THGC-M1` | Time History Global Control | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/THIS-M1` | Time History Load Cases | — | 仅官方目录；限制：Hyper-S solver only |
| `/db/THOO-M1` | Time History Output Option | — | 仅官方目录；限制：Hyper-S solver only |

### 3.2 官方标为 MIDAS CIVIL NX JP Version only

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/GALD` | Grid Analysis Load | — | 仅官方目录；CIVIL NX 日本版；限制：CIVIL NX JP Version only |

### 3.3 更偏建筑 / 楼层 / 设计（官方目录有，本地 Civil NX 手册无）

这些条目常与楼层、墙、钢/SRC 设计或建筑规范地震风荷载相关。它们出现在「CIVIL NX 与 GEN NX 共用」的官方总目录中，但 **未** 出现在本地 Civil NX 手册。本 Civil 技能 **不把它们列为已核验的 Civil NX 能力**，也不把它们写入 Gen 技能时改称为「已在 Gen NX 实测」。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/DCTL` | Definition of Frame | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/DRLS` | Diaphragm Disconnect | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/DSTL` | Steel Design Code | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/EPSE` | Seismic Earth Pressure | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/EPST` | Static Earth Pressure | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/LENG` | Unbraced Length | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/LTSR` | Limiting Slenderness Ratio | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/MBTP` | Modify Member Type | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/MEMB` | Member Assignment | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/POSL` | Parameter of Seismic Loads | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/POSP` | Parameter of Soil Properties | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/SSEIS` | Static Seismic Load - KDS(41-17-00:2019)  Static Seismic Load - User Type | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/STOR` | Story Data | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/SWIND` | Static Wind Load - KDS(41-12:2022)  Static Wind Load - User Type | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/THRE` | Time History Graph - Element Force Smart Graph | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/db/WMAK` | Modify Wall Mark Design | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/GUSTFACTOR` | Gust Factor Calculator | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/LCOM-CONC` | Load Combination (Concrete) - KDS 41 20 : 2022 | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/LCOM-SRC` | Load Combination (SRC) - KDS 41 SRC : 2022  Load Combination (SRC) - AIK-SRC2K | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/LCOM-STEEL` | Load Combination (Steel) - KDS 41 30 : 2022 | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/MEMB` | Member Assignment | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/STOR` | Story Calculation | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/STORPROP` | Story Properties | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/STORY_IRR_PARAM` | Story Irregularity Check Parameter | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/ope/STORY_PARAM` | Story Check Parameter | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/BRACEDESIGNFORCES` | Concrete Design - Brace Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/COLDFORMEDSTEELMEMBERDESIGNFORCES` | Cold Formed Design - Cold Formed Steel Member Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/SRCBEAMDESIGNFORCES` | SRC Design - SRC Beam Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/SRCCOLUMNDESIGNFORCES SRC` | SRC Design - SRC Column Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/STEELMEMBERDESIGNFORCES` | Steel Design - Steel Member Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |
| `/post/WALLDESIGNFORCES` | Concrete Design - Wall Design Forces | — | 仅官方 NX 目录；本地 Civil NX 手册未收录 |

### 3.4 更偏桥梁 / 移动荷载 / 施工阶段等（官方有，本地 Civil NX 手册未见）

可能是目录更新（官方编辑于 2026-07-14，本地抓取于 2025-12-23）或命名差异。使用前必须打开官方接口页，不能仅凭本表调用。

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/LLAN` | Traffic Line Lanes | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/LLANid` | Traffic Line Lanes - India | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/SLAN` | Traffic Surface Lanes | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/SLANop` | Traffic Surface Lanes - Moving Load Optimization | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/WVLD` | Wave Loads | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/doc/STAGAS` | Save Current Stage As | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/ope/GSBG` | Bridge Girder Diagrams | — | 仅官方目录；本地 Civil NX 手册未收录 |

### 3.5 其他仅官方目录路径

| 端点 | 说明 | 本地手册方法 | 标注 |
| --- | --- | --- | --- |
| `/db/ESSF` | Element Stiffness Scale Factor | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/FMLD` | Finishing Material Loads | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/db/ULCT` | Underground Load Combination Type | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/ope/EDMP` | Change Property | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/ope/LCOM-GEN` | Load Combination (General) - KDS : 2022  Load Combination (General) - AIK-SRC2K | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/ope/SSPS` | Surface Spring | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/post/BEAMDESIGNFORCES` | Concrete Design - Beam Design Force | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/post/COLUMNDESIGNFORCES` | Concrete Design - Column Design Forces | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/post/STEELCODECHECK` | Steel Code Check | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/view/DISPLAY` | Display | — | 仅官方目录；本地 Civil NX 手册未收录 |
| `/view/PRECAPTURE` | Dialog Capture | — | 仅官方目录；本地 Civil NX 手册未收录 |

## 4. 官方结果表类型（多数没有独立 URI）

官方说明：前后处理表格主要通过 **一个** `post/TABLE` 端点提取，用 `TABLE_TYPE` 选择表格。下表是官方总目录中的表类型名称，不是独立 REST 路径。完整字段见官方《Designing with Intent: The Vision Behind POST/TABLE》与各表页面。部分表类型可能偏建筑/楼层，不自动等于 Civil NX 已核验。

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
