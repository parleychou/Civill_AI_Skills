# 建模（Gen NX，资料受限）

本包**没有**已读取正文的 Gen 专用节点/单元/材料/截面字段手册。默认只使用已证实的连接方法，以及官方 NX 系列 JSON Manual 中已成功读取的共享字段页。

检索：

```bash
python3 scripts/search_index.py NODE
python3 scripts/search_index.py UNIT
python3 scripts/search_index.py 材料
python3 scripts/search_index.py 截面
```

这些命中若来自 `official-shared.jsonl`，证据级别是 **shared**，不是 Gen 实机验证。官方 Material / Element / Section 页末尾有未绑定到具体行的 “CIVIL NX only / GEN NX only” 脚注，不得猜测哪些键属于 Gen。

## 已能引用的共享字段（仍须在当前 Gen NX 页确认）

- `/db/UNIT`：FORCE、DIST、HEAT、TEMPER。官方页列为 Optional；Civil 手册列为 Required。不要擅自统一。
- `/db/NODE`：X、Y、Z。
- `/db/ELEM`：TYPE、MATL、SECT、NODE 等，见官方 Element 页。
- `/db/MATL`：TYPE、NAME、PARAM 等，见官方 Material Properties 页。
- `/db/SECT`：目前只收录了官方 *Section Properties - Common* 的共享键（SECTTYPE、SECT_NAME、SECT_BEFORE 等）。Value / DB-User / PSC 等分页面没有全部摄入，缺少的形状专用键要标为缺口。

## 明确缺口

- 无 Gen 专用完整字段手册（wolai《midas Gen API 使用手册》正文未读到）。
- 包内 `examples/` 里的节点、梁、单位等 JSON 来自 Civil NX，默认检索不会列出；即使用 `--include-cross-product` 看到，也不得直接写入 Gen。
- 钢束组、移动荷载、波浪荷载、桥梁专项默认不属于本技能。

需要 Civil 对照时，先声明“不是 Gen 可执行契约”，再查阅 `references/unverified-cross-product.md`。
