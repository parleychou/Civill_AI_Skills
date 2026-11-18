# 结果读取（Gen NX，资料受限）

推荐先查阅官方共享说明：`post/TABLE` + 必要键 `TABLE_TYPE`。相关公开页：

- https://support.midasuser.com/hc/en-us/articles/45171987915929-Designing-with-Intent-The-Vision-Behind-POST-TABLE （叙述以 CIVIL NX 为主，只能当共享约定）
- https://support.midasuser.com/hc/en-us/articles/43835398107801-Section-Table （`TABLE_TYPE` 如 `SECTIONALL` 等）

可用 `python3 scripts/search_index.py 结果 TABLE_TYPE` 查看本包已收录的共享字段。注意：该官方文章里 `UNIT` 的温度键是 `TEMP`，与 `/db/UNIT` 的 `TEMPER` 不同。

## 缺口

- 没有已读取的 Gen 专用结果表字段手册。
- Civil 手册中的 `BEAMFORCE` 等具体表类型，默认不作为 Gen 已证实能力。若用户要对照，必须加 `--include-cross-product`，并在当前 Gen NX 接口页核验后再说能否使用。
- 不要把 Smart Report 的 `TABLE_NAME` 当成官方 `TABLE_TYPE`。
- 墙、SRC、冷弯等设计结果表，未在 Gen 专用手册核验前不得当成已支持。

工程结论必须人工复核。
