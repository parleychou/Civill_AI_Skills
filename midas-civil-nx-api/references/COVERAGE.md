# 离线字段目录覆盖说明（Civil NX）

整理于 2026-11-18（America/Los_Angeles 为 2026-11-17 晚；Asia/Shanghai 已是 18 日）。本目录从用户提供的 Civil NX JSON 手册只读抽取接口、方法和字段，**不是** 430 篇手册原文的再发布。

## 抽取统计

- 解析页面：428（已排除类型生成说明页）
- 解析到 Input URI：412；解析到方法：412
- 含字段表的页面：390；字段行：3768（打包后有效字段行约 3768）
- 解析到 JSON Schema 属性的页面：62（多数页面以字段表为准；schema 未能解析的页面不编造属性）
- 含短示例的页面：413
- 唯一 Input URI 数：209（大量结果表页共享 `/post/TABLE`，以 `TABLE_TYPE` 区分）
- 打包记录数：428

## 版权与范围

- 手册版权属于 MIDAS Information Technology Co., Ltd.。本包只收录独立整理的接口/字段事实、枚举与必要短例，并保留来源 URL 与抓取日期。
- 不包含手册插图、版式全文或 430 篇 Markdown 原件。完整接口页请查阅官方手册或用户持有的手册副本。
- 公开在线手册入口：https://support.midasuser.com/hc/en-us/articles/33016922742937-MIDAS-API-Online-Manual（作为在线更新兜底）。个别已成功读取的官方字段页收录在 `official-shared.jsonl`。
- wolai 入口此前未能读到正文，不能填补未抽取到的段落。

## 已知资料冲突与限制

- `/db/UNIT`：官方 Unit System 页把 FORCE/DIST/HEAT/TEMPER 列为 Optional；本地 Civil NX 手册列为 Required。检索结果会同时保留两处表述，不得擅自统一。
- 官方 Element / Material / Section 页末尾有 “MIDAS CIVIL NX only / MIDAS GEN NX only” 脚注，转换后的公开页未能绑定到具体行，本包不强行推测。
- 尚未在真实 Civil NX 会话中实测。`SAVE` 不是备份，`SAVEAS` 会切换当前文件。

## 检索

```bash
python3 scripts/search_index.py NODE
python3 scripts/search_index.py UNIT TEMPER
python3 scripts/search_index.py 材料
python3 scripts/search_index.py 截面 SECTTYPE
python3 scripts/search_index.py BEAMFORCE TABLE_TYPE
```
