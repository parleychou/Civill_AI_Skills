# YJK 数据库基线与最小建模规则

本文档记录 `dtlmodel.db` 的实测基线，并作为后续生成、修改、校验 YJK 数据库的依据。

## 1. 参考库

- 基线参考库：`dtlmodel.db`
- 默认建模模板：`ydbs/mini.ydb`
- 对照样本库：
  - `数据文件说明/8#楼住宅.ydb`
  - `8#楼住宅.db`
  - `三层框架结构.ydb`

## 2. ID / idNew 起始值

起始值不采用硬编码，而是从参考库中所有含对应字段的表内取最小值。

### 全局最小值

| 字段 | 实测最小值 | 说明 |
|------|-----------:|------|
| `ID` | 0 | 来自 `tblProjectPara.ID` |
| `idNew` | 1 | 来自 `tblProperty.idNew` |

### 关键业务表最小值

| 表名 | 最小 `ID` | 最小 `idNew` |
|------|----------:|-------------:|
| `tblStdFlr` | 1001 | 2 |
| `tblFloor` | 1002 | 3 |
| `tblJoint` | 1003 | 4 |
| `tblGrid` | 1007 | 8 |
| `tblColSect` | 1011 | 12 |
| `tblColSeg` | 1012 | 13 |
| `tblBeamSect` | 1016 | 17 |
| `tblBeamSeg` | 1017 | 18 |
| `tblAxis` | 1022 | 22 |
| `tblProperty` | 999 | 1 |

## 3. 最小建模必需表

以下表在 `dtlmodel.db` 中非空，可视为当前仓库下“最小可建模”数据集合：

| 表名 | 作用 |
|------|------|
| `tblStdFlr` | 标准层主表 |
| `tblStdFlrPara` | 标准层参数 |
| `tblFloor` | 自然层 |
| `tblJoint` | 节点 |
| `tblGrid` | 网格 |
| `tblAxis` | 轴线 |
| `tblColSect` | 柱截面定义 |
| `tblColSeg` | 柱布置 |
| `tblBeamSect` | 梁截面定义 |
| `tblBeamSeg` | 梁布置 |
| `tblProjectPara` | 工程参数 |
| `tblProperty` | 构件扩展属性 |

说明：

- 上述列表是根据参考库“非空表”自动提取的结果
- 某些表即使存在于 schema 中，但在参考库为空，当前不应被当作最小模型强制表
- `tblProperty` 虽然属于最小集合，但其 `ID` / `idNew` 表达的是宿主构件引用，不应直接按“本表主键唯一”理解

## 3.0 新建模型策略

新建模型应采用两级策略：

1. 默认模板：`ydbs/mini.ydb`
   - 这是从 YJK 导出的完整空白模型
   - 所有新建工程应先复制这个文件，再增量写入结构数据
   - 这样能保留 YJK 原生空白工程中的完整表结构和初始化状态

2. 严格最小模板：`dtlmodel.db`
   - 用于定义“最小数据范围”的理论基线
   - 用于严格校验，不作为默认新建模板

## 3.1 严格最小模型轮廓

如果目标是“严格匹配 `dtlmodel.db` 的最小模板”，就不能只看表是否存在，还要看关键非空表的记录数是否一致。

`dtlmodel.db` 的严格最小轮廓如下：

| 表名 | 严格记录数 |
|------|-----------:|
| `tblStdFlr` | 1 |
| `tblStdFlrPara` | 26 |
| `tblFloor` | 1 |
| `tblJoint` | 4 |
| `tblGrid` | 4 |
| `tblAxis` | 4 |
| `tblColSect` | 1 |
| `tblColSeg` | 4 |
| `tblBeamSect` | 1 |
| `tblBeamSeg` | 4 |
| `tblProjectPara` | 1264 |
| `tblProperty` | 2 |

补充说明：

- `tblMaterialDef` 在 `dtlmodel.db` 中为 0 行，因此它不是严格最小模板中的必需非空表
- `create_frame_db.py` 当前默认复制 `ydbs/mini.ydb`
- 如需严格最小模板，可调用 `create_strict_minimum_database()` 复制 `dtlmodel.db`
- 需要严格对齐时，应使用 `validate_yjk_db.py --strict-minimum`

## 4. 样本库校验结论

### `数据文件说明/8#楼住宅.ydb`

- 缺少的 schema 表：`tblGuardRail`、`tblGuardRailSect`
- 最小建模表缺失：无
- `ID` / `idNew` 低于参考起点：无
- 主要引用异常：未发现

### `8#楼住宅.db`

- 与 `数据文件说明/8#楼住宅.ydb` 结论一致
- 命令行输出中若出现路径乱码，属于 Windows 控制台显示问题，不影响数据库内容本身

### `三层框架结构.ydb`

- 仅包含 12 张表，明显小于参考库完整 schema
- 最小建模表缺失：`tblProperty`
- 引用异常：`tblGrid.AxisID -> tblAxis.ID` 存在 120 条无法匹配记录

### `ydbs/01.ydb`、`ydbs/02.ydb`、`ydbs/03.ydb`

- 3 个样本库均具备完整 79 张参考表
- `tblGroup.idNew` 在样本库中表现为 `BLOB`，不能按普通整数编号字段处理
- `ydbs/01.ydb`、`ydbs/02.ydb` 中 `tblStdFlr.ID = -1` 表示 YJK 的“空间层”记录，校验时不应作为“低于基线”的错误
- `ydbs/02.ydb` 的荷载表版本与参考文档不同：
  - `tblLoadSeg` 使用 `No`、`Type`、`ElementID`
  - `tblLoadSect` 使用 `No`
  - 荷载关系是双分支的：
    - `tblLoadSeg.SectID -> tblLoadSect.ID` 或 `tblSkinLoadSect.ID`
    - `tblLoadSeg.idDef -> tblLoadSect.idNew` 或 `tblSkinLoadSect.idNew`
- `ydbs/02.ydb` 在当前规则下已可被正确识别，不再视为引用异常

## 5. 建库与校验准则

1. 建新库前，先读取参考库编号基线，不要写死起始号。
2. 至少保证最小建模表全部存在。
3. 校验时区分：
   - 完整 schema 缺失
   - 最小建模缺失
   - 编号越界
   - 关联引用断裂
4. `tblProperty` 需要按“宿主对象属性表”处理，而不是普通主数据表。
5. `tblStdFlr.ID = -1` 在 YJK 中表示“空间层”，属于合法业务语义。
6. 负数 `ID` / `idNew` 在部分场景下承载特殊语义，基线下限比较应仅针对非负编号。

## 6. 写入建议

### 编号分配

- 使用 `allocate_global_ids(count)` 计算下一段可用的 `ID` / `idNew`
- 当前实现按“库内所有相关表的最大值 + 1”分配
- 如果数据库为空，则回退到参考库最小值

### 自动写入

- 使用 `insert_row(table_name, row_data, auto_allocate_ids=True)` 可在目标表包含 `ID` / `idNew` 时自动补号
- 自动补号只处理当前目标表存在的字段，不会盲写不存在的列

## 7. 最小模型修复建议

对于不满足最小建模条件的数据库，可调用：

```python
reference_db.suggest_minimum_model_repairs("三层框架结构.ydb")
```

当前 `三层框架结构.ydb` 的实测修复重点：

1. 补建 `tblProperty`
2. 修复 `tblGrid.AxisID -> tblAxis.ID` 的 120 条失配记录
