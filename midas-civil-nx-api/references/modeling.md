# 建模：项目设置、节点单元、特性、边界与荷载

完整字段请先运行 `python scripts/search_index.py <关键词>` 或打开 `references/civil-field-catalog.jsonl`。下面只保留常用接口的提要。

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

这些字段示例已收入 `examples/`，并在 `PROVENANCE.md` 标明出处。它们只是模板，不是可无条件执行的模型。用于 Civil NX 时仍须按当前产品接口页核对字段与编号，并先读后改。不得把它们搬到 Gen NX 当作已验证用法。

## 节点与单元

本地 Civil NX 手册：

- `/db/NODE`：GET/POST/PUT/DELETE。创建示例用 `Assign`，键为节点号，值为 `X` `Y` `Z`（Real，默认 0）。
- `/db/ELEM`：GET/POST/PUT/DELETE。梁示例：`TYPE` 为 `"BEAM"`，含 `MATL`、`SECT`、`NODE` 数组、`ANGLE`、`STYPE`。另有 TRUSS 等示例。`NODE` 在 schema 中最多 8 个整数。
- 另有节点局部轴、区域/子区域、自动网格、分割单元等，见索引。

## 特性、边界、荷载

本地 Civil NX 手册按主题收录材料、截面、厚度、时间依存、非弹性铰、约束与弹性连接、静力/温度/预应力/移动/动力/施工阶段/水化热等荷载，详见 `endpoint-index.md`。

Civil 技能可以把这些当作已交叉核验的 **路由**（字段仍看对应页）。Gen 技能不得把移动荷载、钢束、波浪荷载、桥梁专项等默认列为已支持。
