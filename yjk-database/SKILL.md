---
name: yjk-database
description: "Use this skill when working with YJK (盈建科) structural model SQLite databases (.ydb/.db), including schema analysis, sample validation, table relationship tracing, and read/write helper scripting."
---

# YJK Database Skill

## Overview

这个 skill 用于处理 YJK 结构模型输入库数据库，覆盖 4 类工作：

- 读取 `.ydb` / `.db` 数据库并查询结构模型数据
- 分析表结构、字段、附录枚举和表间关联
- 基于参考库校验目标库是否满足最小建模要求
- 编写或复用 Python 脚本完成读写、校验与批量分析

## Reference Files

- 参考数据库基线：`dtlmodel.db`
- 住宅样本数据库：`数据文件说明/8#楼住宅.ydb`
- 三层框架样本：`三层框架结构.ydb`
- 文档来源：`数据文件说明/dtlModel.docx`

## How To Use

### 1. 打开数据库

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".agents/skills/yjk-database/scripts").resolve()))
from yjk_db import YJKDatabase

db = YJKDatabase("数据文件说明/8#楼住宅.ydb")
```

### 2. 读取模型数据

```python
tables = db.get_tables()
floors = db.get_all_floors()
columns = db.get_all_columns()
beams = db.get_all_beams()
project_para = db.get_project_para()
```

### 3. 提取编号基线

```python
reference_db = YJKDatabase("dtlmodel.db")
baseline = reference_db.get_global_id_baseline()
print(baseline["min_id"], baseline["min_idnew"])
reference_db.close()
```

### 4. 校验目标数据库

```python
reference_db = YJKDatabase("dtlmodel.db")
report = reference_db.validate_target_database("三层框架结构.ydb")
reference_db.close()
```

### 5. 分配新编号并写入

```python
db = YJKDatabase("目标库.ydb")
allocation = db.allocate_global_ids(count=1)

row = db.insert_row(
    "tblStdFlr",
    {"No_": 2, "Height": 3000},
    auto_allocate_ids=True,
)
db.close()
```

### 6. 输出最小模型修复建议

```python
reference_db = YJKDatabase("dtlmodel.db")
repairs = reference_db.suggest_minimum_model_repairs("三层框架结构.ydb")
reference_db.close()
```

### 7. 基于空白模板新建模型

```bash
python create_frame_db.py
python .agents/skills/yjk-database/scripts/validate_yjk_db.py --reference ydbs/mini.ydb --target 三层框架结构.ydb --strict-minimum
```

当前 `create_frame_db.py` 的默认行为已经改为：

- 直接以 `ydbs/mini.ydb` 为模板生成新模型
- 所有新建模型都从这个完整空白模型出发，再向其中增量写入结构数据
- 梁和次梁统一通过 `tblBeamSeg` 建模；如需布置次梁，应补齐对应节点、轴线与网格，而不是写入 `tblSubBeam`
- 这样可以最大程度保持与 YJK 导出空白工程的一致性

### 8. 严格最小模型校验

```bash
python .agents/skills/yjk-database/scripts/validate_yjk_db.py --reference dtlmodel.db --target 三层框架结构.ydb --strict-minimum
```

说明：

- 默认校验是“最小可用模型”
- `--strict-minimum` 校验的是“是否严格匹配 dtlmodel.db 的最小模型轮廓”
- 如果要生成严格最小模板，请调用 `create_strict_minimum_database()`，而不是默认生成入口

或使用命令行：

```bash
python .agents/skills/yjk-database/scripts/validate_yjk_db.py --reference dtlmodel.db --target 三层框架结构.ydb
```

## Core Rules

### ID / idNew 基线

- 不要把 `ID` / `idNew` 起点写死到脚本里
- 一律从 `dtlmodel.db` 中动态提取最小值，作为建库与校验基线
- 当前仓库实测基线见 `references/database_baseline.md`

### 最小建模要求

- `dtlmodel.db` 被视为“最小必要数据集”的参考库
- 应优先关注参考库中“非空表”，这些表构成最小模型必需数据
- 当前样本实测最小建模表见 `references/database_baseline.md`

### 关系校验

- 优先检查 `StdFlrID`、`SectID`、`GridID`、`AxisID`、`JtID`、`Jt1ID`、`Jt2ID`、`SlabID`
- `tblProperty` 中的 `ID` / `idNew` 代表宿主构件引用，不能直接按“单表唯一主键”处理
- 对版本差异较大的表要允许例外规则，例如 `tblLoadSeg` 在部分样本中需要结合 `idDef -> tblLoadSect.idNew` 判断
- 遇到 BLOB 形式的 `idNew` 时，校验器应报告为“非标量编号字段”，而不是直接崩溃

### 写入规则

- 写新记录前，先调用 `allocate_global_ids()` 或 `insert_row(..., auto_allocate_ids=True)`
- 新增记录时只应写入目标表已存在的字段
- 修改最小模型库时，应先跑一次 `validate_target_database()`，再执行写入

## Reference Guide

- 字段与附录说明：`references/table_reference.md`
- 表间关系与主引用链：`references/table_relationships.md`
- 参考库基线、编号起点、最小建模表、样本校验结论：`references/database_baseline.md`

## Files

```text
.agents/skills/yjk-database/
├── SKILL.md
├── references/
│   ├── database_baseline.md
│   ├── table_reference.md
│   └── table_relationships.md
└── scripts/
    ├── validate_yjk_db.py
    └── yjk_db.py
```
