# 未验证的跨产品对照（Civil NX 资料）

**默认检索不会包含本文件。** 只有在用户明确要求对照，并运行 `python scripts/search_index.py <关键词> --include-cross-product` 时才应打开。

这些内容来自 Civil NX 手册或官方以 CIVIL NX 为主的示例，**不是 Gen NX 已验证的可执行契约**。未取得当前 Gen NX 接口正文或已验证导出结构并逐字段核对前，不得按下列字段执行写入。

---

## 原 modeling 摘录（Civil 来源）

# 建模：项目设置、节点单元、特性、边界与荷载

## 项目设置

本地 Civil NX 手册（同时出现在官方目录）：

- `/db/UNIT`：GET、PUT。字段 `FORCE`、`DIST`、`HEAT`、`TEMPER` 为必填字符串。力的取值包括 `"N"` `"KN"` `"KGF"` `"TONF"` `"LBF"` `"KIPS"`；长度 `"M"` `"CM"` `"MM"` `"FT"` `"IN"`；热量 `"CAL"` `"KCAL"` `"J"` `"KJ"` `"BTU"`；温度 `"C"` `"F"`。POST/PUT 包在 `Assign` / `"1"` 中。
- `/db/STYP`：GET、PUT。本地手册有多组示例（质量定义、自重转换、刚域等字段不同时出现）。若页中有多套 example，只按用户目标选用对应那一套，不要自行合并字段。
- 结构组、边界组、荷载组、钢束组、项目信息与项目状态：见端点索引中 Project 一节。钢束组更偏桥梁/Civil，在 Gen 技能中不要默认支持。

官方 Python 简单梁例（文中写明结果出现在 CIVIL NX）还演示了：

- `/db/MATL` 材料（`TYPE`/`NAME`/`PARAM`）
- `/db/SECT` 截面（`SECTTYPE`/`SECT_NAME`/`SECT_BEFORE`）
- `/db/NODE`、`/db/ELEM`
- `/db/CONS` 支座约束（`CONSTRAINT` 用 0/1 字符串）
- `/db/STLD` 荷载工况、`/db/BODF` 自重、`/db/BMLD` 梁荷载
- `/db/LCOM-GEN` 荷载组合

这些字段示例已收入 `examples/`，并在 `PROVENANCE.md` 标明是官方 Civil NX Python 例或本地 Civil NX 手册。它们 **不是已验证的 Gen NX 用法**。必须先取得 Gen 文档或已验证导出结构并逐字段核对，才能执行对应写入；仅声明来源不够。资料不足时只提供草案、缺口和验证步骤，不调用该写接口。

## 节点与单元

本地 Civil NX 手册：

- `/db/NODE`：GET/POST/PUT/DELETE。创建示例用 `Assign`，键为节点号，值为 `X` `Y` `Z`（Real，默认 0）。
- `/db/ELEM`：GET/POST/PUT/DELETE。梁示例：`TYPE` 为 `"BEAM"`，含 `MATL`、`SECT`、`NODE` 数组、`ANGLE`、`STYPE`。另有 TRUSS 等示例。`NODE` 在 schema 中最多 8 个整数。
- 另有节点局部轴、区域/子区域、自动网格、分割单元等，见索引。

## 特性、边界、荷载

本地 Civil NX 手册按主题收录材料、截面、厚度、时间依存、非弹性铰、约束与弹性连接、静力/温度/预应力/移动/动力/施工阶段/水化热等荷载，详见 `endpoint-index.md`。

Civil 技能可以把这些当作已交叉核验的 **路由**（字段仍看对应页）。Gen 技能不得把移动荷载、钢束、波浪荷载、桥梁专项等默认列为已支持。


---

## 原 results 摘录（含以 CIVIL NX 为主的 POST/TABLE 叙述）

# 结果读取

## 推荐：`post/TABLE` + `TABLE_TYPE`

官方《Designing with Intent: The Vision Behind POST/TABLE》（Edited 2026-07-30）说明：大量前后处理表共用 **一个** 端点 `post/TABLE`，用必要键 `TABLE_TYPE` 选择表格。该文叙述以 CIVIL NX 为主。可选键包括：

- `TABLE_NAME`：可选，用于响应标题
- `EXPORT_PATH`：可选，保存 JSON 的路径（手册示例形如 `C:\\MIDAS\\Result\\Elements.json`，须换成用户指定路径）
- `UNIT`：可选；结构与 `/db/UNIT` 类似，但温度键在该文中写作 `TEMP`（注意与单位系统页的 `TEMPER` 不同）
- `STYLES`（`FORMAT`、`PLACE`）、`COMPONENTS`、`NODE_ELEMS`（`KEYS` / `TO` / `STRUCTURE_GROUP_NAME` 三选一）
- 部分表还有 `PARTS`、`LOAD_CASE_NAMES`、施工阶段相关键等
- `FIBER_CELL_MINMAX`、`SECT_POSITION`、`OUTPUT_STEP` 等被该文写明仅用于日本版纤维截面时程结果

本地 Civil NX「梁单元内力 Beam Force」页给出 `TABLE_TYPE` 为 `"BEAMFORCE"` 的请求与响应示例，已收入 `examples/post_table_beamforce_request.json`。该页字段说明把 `TABLE_TYPE` 标为必要。该示例尚未在 Gen NX 核验，未核对前不要直接发送。

官方目录中的表类型名称见 `endpoint-index.md` 第 4 节（Civil 包）或第 5 节（Gen 包）。表类型名称本身不是 REST 路径。

## 不要与 Smart Report 混用

本地「[TABLE]Get Result Table from Smart Report Table」页的 Input URI 写作 `{{base url}} + POST/TABLE`，方法 POST，示例用 **用户定义的** `TABLE_NAME`（如 `"Beam Force"`）和可选 `EXPORT_PATH`，没有把 `TABLE_TYPE` 写成必要键。这是 Smart Report 已有表格的导出，与官方 `TABLE_TYPE` 枚举不是同一套说明。调用前必须分清用户要的是「官方结果表类型」还是「Smart Report 中已命名的表」。

## 视图图形

`/view/RESULTGRAPHIC` 等用于结果图形显示，本地手册中大量结果图形页共享该路径。需要具体图形类型时打开对应本地页或官方视图说明，不要只靠路径猜测 Body。

## 设计结果

官方另有 `/post/PM`、`/post/STEELCODECHECK` 以及各类 Design Forces。墙、SRC、冷弯等更偏建筑/Gen 工作流，Civil 技能不把未出现在本地手册的设计力表列为已核验。

