# 示例出处与溯源

本包是资料受限、待验证初版。示例主要用于说明 NX 系列共享的 JSON 形状，**全部未在真实 Gen NX 会话中发送，不能当作可执行的 Gen 请求。** 凡出处为 Civil NX 手册或官方 Civil NX Python 例的文件，必须先取得 Gen 接口正文或已验证导出结构并逐字段核对，才能执行写入；仅向用户声明来源并不足以允许执行。资料不足时只提供草案、缺口和验证步骤。路径字符串是手册占位符，必须换成用户指定路径。

| 文件 | 说明 | 出处与限制 |
| --- | --- | --- |
| `put_unit_official_postman.json` | PUT 单位系统 | 官方 Postman 教程（操作对象为 CIVIL NX）。单位字段属于 NX 共享约定，但仍非 Gen 专用页核验 |
| `put_unit_local_civil_handbook.json` | PUT 单位系统另一组取值 | 本地 Civil NX 手册；旁证，非 Gen 核验 |
| `official_python_civil_nx_unit.json` | 官方 Python 例中的单位（未含 HEAT/TEMPER） | 官方 Example: Python，文中运行于 CIVIL NX |
| `doc_new_empty.json` | 新建空文件 | 官方 DOC 约定与官方 Python 例（CIVIL NX） |
| `doc_open_handbook_placeholder.json` / `doc_saveas_handbook_placeholder.json` | 打开/另存路径 | 本地 Civil NX 手册占位路径 |
| `doc_anal_empty.json` | 执行分析 | 本地 Civil NX 手册；Gen NX 是否接受空 Body 须对照其接口页 |
| `doc_anal_pushover.json` | Pushover 分析参数 | 本地 Civil NX 手册；不要默认 Gen NX 使用相同 `TYPE` 值 |
| `post_node_local_civil_handbook.json` 等节点单元示例 | `Assign` + 坐标/单元拓扑 | 本地 Civil NX 手册 |
| `put_styp_example_*.json` | 结构类型 | 本地 Civil NX 手册的两套 example，不可擅自合并；Gen NX 是否字段相同未核验 |
| `post_table_beamforce_request.json` | `TABLE_TYPE` = BEAMFORCE | 本地 Civil NX 结果表页。官方 POST/TABLE 说明文也以 CIVIL NX 叙述为主 |
| `smart_report_table_name_only.json` | Smart Report 按表名导出 | 仅出自本地 Civil NX Smart Report 页，默认不当作 Gen NX 能力 |
| `official_python_civil_nx_*.json` | 材料、截面、支座、组合 | 官方 Python 简单梁例，明确运行于 CIVIL NX |

本包没有来自「已读取正文的 Gen 专用手册」的字段示例，因为该手册正文未能获取。


## 文件名清单（便于核验）

下列文件均已包含在本目录，出处见上表：

- `official_python_civil_nx_cons.json`
- `official_python_civil_nx_lcom_gen.json`
- `official_python_civil_nx_material.json`
- `official_python_civil_nx_section_sb.json`
- `official_python_civil_nx_unit.json`
- `post_elem_beam_local_civil_handbook.json`
- `post_elem_truss_local_civil_handbook.json`
- `post_node_local_civil_handbook.json`
- `put_styp_example_a_local_civil_handbook.json`
- `put_styp_example_b_local_civil_handbook.json`
- `put_unit_official_postman.json`
- `put_unit_local_civil_handbook.json`
- `doc_new_empty.json`
- `doc_open_handbook_placeholder.json`
- `doc_saveas_handbook_placeholder.json`
- `doc_anal_empty.json`
- `doc_anal_pushover.json`
- `post_table_beamforce_request.json`
- `smart_report_table_name_only.json`
