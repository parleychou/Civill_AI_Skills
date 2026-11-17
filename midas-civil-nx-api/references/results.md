# 结果读取

## 推荐：`post/TABLE` + `TABLE_TYPE`

官方《Designing with Intent: The Vision Behind POST/TABLE》（Edited 2026-07-30）说明：大量前后处理表共用 **一个** 端点 `post/TABLE`，用必要键 `TABLE_TYPE` 选择表格。该文叙述以 CIVIL NX 为主。可选键包括：

- `TABLE_NAME`：可选，用于响应标题
- `EXPORT_PATH`：可选，保存 JSON 的路径（手册示例形如 `C:\\MIDAS\\Result\\Elements.json`，须换成用户指定路径）
- `UNIT`：可选；结构与 `/db/UNIT` 类似，但温度键在该文中写作 `TEMP`（注意与单位系统页的 `TEMPER` 不同）
- `STYLES`（`FORMAT`、`PLACE`）、`COMPONENTS`、`NODE_ELEMS`（`KEYS` / `TO` / `STRUCTURE_GROUP_NAME` 三选一）
- 部分表还有 `PARTS`、`LOAD_CASE_NAMES`、施工阶段相关键等
- `FIBER_CELL_MINMAX`、`SECT_POSITION`、`OUTPUT_STEP` 等被该文写明仅用于日本版纤维截面时程结果

本地 Civil NX「梁单元内力 Beam Force」页给出 `TABLE_TYPE` 为 `"BEAMFORCE"` 的请求与响应示例，已收入 `examples/post_table_beamforce_request.json`。该页字段说明把 `TABLE_TYPE` 标为必要。

官方目录中的表类型名称见 `endpoint-index.md` 第 4 节（Civil 包）或第 5 节（Gen 包）。表类型名称本身不是 REST 路径。

## 不要与 Smart Report 混用

本地「[TABLE]Get Result Table from Smart Report Table」页的 Input URI 写作 `{{base url}} + POST/TABLE`，方法 POST，示例用 **用户定义的** `TABLE_NAME`（如 `"Beam Force"`）和可选 `EXPORT_PATH`，没有把 `TABLE_TYPE` 写成必要键。这是 Smart Report 已有表格的导出，与官方 `TABLE_TYPE` 枚举不是同一套说明。调用前必须分清用户要的是「官方结果表类型」还是「Smart Report 中已命名的表」。

## 视图图形

`/view/RESULTGRAPHIC` 等用于结果图形显示，本地手册中大量结果图形页共享该路径。需要具体图形类型时打开对应本地页或官方视图说明，不要只靠路径猜测 Body。

## 设计结果

官方另有 `/post/PM`、`/post/STEELCODECHECK` 以及各类 Design Forces。墙、SRC、冷弯等更偏建筑/Gen 工作流，Civil 技能不把未出现在本地手册的设计力表列为已核验。
