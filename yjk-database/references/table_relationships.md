# YJK 表关系与主引用链

本文档用于描述 YJK 结构模型输入库中的主表关系、核心索引字段，以及附录枚举如何落到业务表字段。

## 1. 主数据链

```text
tblStdFlr
  -> tblStdFlrPara
  -> tblFloor
      -> tblAxis
      -> tblJoint
      -> tblGrid
          -> 构件布置表
```

## 2. 分层关系

| 来源表 | 字段 | 目标表 | 含义 |
|--------|------|--------|------|
| `tblStdFlrPara` | `StdFlrID` | `tblStdFlr.ID` | 标准层参数从属标准层 |
| `tblFloor` | `StdFlrID` | `tblStdFlr.ID` | 自然层映射标准层 |
| `tblAxis` | `StdFlrID` | `tblStdFlr.ID` | 轴线属于标准层 |
| `tblJoint` | `StdFlrID` | `tblStdFlr.ID` | 节点属于标准层 |
| `tblGrid` | `StdFlrID` | `tblStdFlr.ID` | 网格属于标准层 |
| `tblColSeg` | `StdFlrID` | `tblStdFlr.ID` | 柱属于标准层 |
| `tblBeamSeg` | `StdFlrID` | `tblStdFlr.ID` | 梁属于标准层 |
| `tblWallSeg` | `StdFlrID` | `tblStdFlr.ID` | 墙属于标准层 |
| `tblSlab` | `StdFlrID` | `tblStdFlr.ID` | 板属于标准层 |

补充：

- `tblStdFlr.ID = -1` 表示 YJK 的“空间层”概念，不应按普通标准层编号解释

## 3. 几何关系

| 来源表 | 字段 | 目标表 | 说明 |
|--------|------|--------|------|
| `tblAxis` | `Jt1ID`, `Jt2ID` | `tblJoint.ID` | 轴线由两个节点确定；负值可能表示特殊语义 |
| `tblGrid` | `Jt1ID`, `Jt2ID` | `tblJoint.ID` | 网格边界节点 |
| `tblGrid` | `AxisID` | `tblAxis.ID` | 网格落在轴线之上 |
| `tblColSeg` | `JtID` | `tblJoint.ID` | 柱定位节点 |
| `tblBraceSeg` | `Jt1ID`, `Jt2ID` | `tblJoint.ID` | 支撑端点 |
| `tblSlabHole` | `JtID` | `tblJoint.ID` | 板洞形心定位点 |

## 4. 构件定义与布置关系

| 布置表 | 类型字段 | 类型定义表 |
|--------|----------|------------|
| `tblColSeg` | `SectID` | `tblColSect` |
| `tblBeamSeg` | `SectID` | `tblBeamSect` |
| `tblWallSeg` | `SectID` | `tblWallSect` |
| `tblBraceSeg` | `SectID` | `tblBraceSect` |
| `tblWallHole` | `SectID` | `tblWallHoleDef` |
| `tblSlabHole` | `SectID` | `tblSlabHoleDef` |
| `tblCantiSlab` | `SectID` | `tblCantiSlabDef` |
| `tblLoadSeg` | `SectID` | `tblLoadSect` |
| `tblStairSeg` | `SectionID` | `tblStairDef` |

注：

- 在 `ydbs/02.ydb` 这类版本中，`tblLoadSeg` 还存在 `idDef -> tblLoadSect.idNew` 的定义关联
- 在同一类样本中，`tblLoadSeg` 还可能走皮荷载分支：
  - `SectID -> tblSkinLoadSect.ID`
  - `idDef -> tblSkinLoadSect.idNew`
- 因此荷载表关系不应只按 `SectID -> tblLoadSect.ID` 单一路径理解，而应允许多目标匹配

## 5. 网格 / 楼板宿主关系

| 来源表 | 字段 | 目标表 | 说明 |
|--------|------|--------|------|
| `tblWallSeg` | `GridID` | `tblGrid.ID` | 墙沿网格布置 |
| `tblBeamSeg` | `GridID` | `tblGrid.ID` | 梁沿网格布置 |
| `tblWallHole` | `GridID` | `tblGrid.ID` | 洞口依附墙所在网格 |
| `tblCantiSlab` | `GridID` | `tblGrid.ID` | 悬挑板沿网格布置 |
| `tblSlabHole` | `SlabID` | `tblSlab.ID` | 板洞依附楼板 |

## 6. 属性与荷载关系

| 表 | 关系字段 | 说明 |
|----|----------|------|
| `tblProperty` | `ID` | 关联宿主构件；同一构件可对应多条属性 |
| `tblLoadSeg` | `ElementID_` | 关联具体构件 ID |
| `tblLoadSeg` | `Type_` | 荷载工况枚举 |
| `tblLoadSect` | `ElementKind` | 荷载对应构件类型枚举 |

## 7. 附录枚举与业务字段映射

| 业务字段 | 所在表 | 枚举来源 |
|----------|--------|----------|
| `StdFlrPara.Kind` | `tblStdFlrPara` | 标准层参数附录 |
| `Mat` | `tblWallSect`, `tblBeamSect`, `tblColSect`, `tblBraceSect` | 材质附录 |
| `Kind` | `tblWallSect`, `tblBeamSect`, `tblColSect`, `tblBraceSect`, `tblSlabHoleDef`, `tblCantiSlabDef` | 截面 / 形状附录 |
| `Type_` | `tblLoadSeg` | 荷载工况附录 |
| `ElementKind` | `tblLoadSect` | 构件类型附录 |
| `ParaVal` | `tblProjectPara`, `tblStdFlrPara` | 工程参数 / 标准层参数附录 |

## 8. 校验优先级

建议按以下优先级校验数据库：

1. `tblStdFlr`、`tblFloor`、`tblJoint`、`tblGrid`、`tblAxis`
2. `tblColSect` / `tblColSeg`、`tblBeamSect` / `tblBeamSeg`
3. `tblProjectPara`、`tblStdFlrPara`
4. `tblProperty`
5. 其他可选构件和附属表
