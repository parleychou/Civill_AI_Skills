# 示例出处与溯源

所有 JSON 均可被标准解析器解析。路径字符串来自手册占位符，**不是**用户环境路径，使用前必须替换。本包示例 **未** 在真实 Civil NX 会话中发送。

| 文件 | HTTP 方法与路径（资料中的写法） | 可溯源字段 | 出处 |
| --- | --- | --- | --- |
| `put_unit_official_postman.json` | PUT `{base url} + /db/UNIT`（教程从 API Settings 复制 Base URL 后再追加） | `Assign` / `"1"` / `FORCE` `DIST` `HEAT` `TEMPER` | 官方 Postman 教程，查阅 2026-11-18；示例把 Force 改为 KN、温度改为 F |
| `put_unit_local_civil_handbook.json` | PUT `{base url} + db/UNIT` | 同上，取值为 KIPS/FT/BTU/C | 本地 Civil NX 手册「单位系统[UNIT]」，抓取 2025-12-23 |
| `official_python_civil_nx_unit.json` | PUT `/db/unit` | `DIST` `FORCE`（该示例未写 HEAT/TEMPER） | 官方 Example: Python（Edited 2024-10-28），文中写明运行于 CIVIL NX |
| `doc_new_empty.json` | POST `/doc/new` 或 `/doc/NEW` | 空对象 `{}`，符合官方「Argument 为空可用 `{}`」 | 本地「新项目[NEW]」示例与官方 Python 例、官方 DOC 说明 |
| `doc_open_handbook_placeholder.json` | POST `doc/open` | `Argument` 为路径字符串 | 本地「打开项目[OPEN]」；路径为手册占位 |
| `doc_saveas_handbook_placeholder.json` | POST `doc/saveas` | `Argument` 为路径字符串 | 本地「另存为[SAVEAS]」；路径为手册占位 |
| `doc_anal_empty.json` | POST `doc/Anal` | `{}` | 本地「[Anal] Perform Analysis」普通分析示例 |
| `doc_anal_pushover.json` | POST `doc/Anal` | `Argument.TYPE` = `"Pushover"` | 同上页的 Push Over 示例 |
| `post_node_local_civil_handbook.json` | POST `db/NODE` | `Assign` / 节点号 / `X` `Y` `Z` | 本地「节点[NODE]」Input Data Example |
| `post_elem_beam_local_civil_handbook.json` | POST `db/ELEM` | `TYPE` `MATL` `SECT` `NODE` `ANGLE` `STYPE` | 本地「单元[ELEM]」BEAM 示例 |
| `post_elem_truss_local_civil_handbook.json` | POST `db/ELEM` | `TYPE` `MATL` `SECT` `NODE` `ANGLE` | 本地「单元[ELEM]」TRUSS 示例 |
| `put_styp_example_a_local_civil_handbook.json` | PUT `db/STYP` | 该套 example 出现的字段 | 本地「结构类型[STYP]」示例之一；不要与 B 套擅自合并 |
| `put_styp_example_b_local_civil_handbook.json` | PUT `db/STYP` | 含 `SMASS`、`bSELFWEIGHT` 等 | 同上页另一套示例 |
| `post_table_beamforce_request.json` | POST `post/TABLE`（官方） | 必要 `TABLE_TYPE`=`BEAMFORCE`，以及该页列出的可选键 | 本地「内力Beam Force」结果表页。`EXPORT_PATH` 为手册占位 |
| `smart_report_table_name_only.json` | POST `POST/TABLE`（本地 Smart Report 页写法） | `TABLE_NAME` 为用户表名，无 `TABLE_TYPE` | 本地 Smart Report「Get Result Table」页。不可与上一行混用 |
| `official_python_civil_nx_material.json` | POST `/db/matl` | `TYPE` `NAME` `PARAM` | 官方 Example: Python，CIVIL NX |
| `official_python_civil_nx_section_sb.json` | POST `/db/sect` | `SECTTYPE` `SECT_NAME` `SECT_BEFORE` | 同上；`vSIZE` 取自该例的 height=1.0、width=0.8 |
| `official_python_civil_nx_cons.json` | POST `/db/cons` | `ITEMS` / `CONSTRAINT` | 同上；节点 1 与 21 对应该例 start=1、20 等分后的梁端 |
| `official_python_civil_nx_lcom_gen.json` | POST `/db/lcom-gen` | `NAME` `ACTIVE` `iTYPE` `vCOMB` | 同上 |

GET `/db/UNIT`（以及多数 GET/DELETE）在官方 Postman 教程中不需要 Body，故未另放请求 JSON。
