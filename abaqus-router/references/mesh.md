# Abaqus 网格划分参考

## 单元类型速查

| 问题 | 推荐单元 | 积分方式 |
|------|----------|----------|
| 通用 3D 线弹性 | C3D8R | 减积分 (沙漏控制) |
| 3D 高精度弯曲 | C3D20R | 二次+减积分 |
| 3D 不可压缩 | C3D8H | 杂交元 |
| 壳 通用 | S4R | 4节点减积分 |
| 梁 Timoshenko | B31 | 剪切变形 |
| 平面应变 | CPE4R / CPE8R | — |
| 四面体 | C3D10 | 二次（比C3D4好得多） |

## Abaqus Python API

### 基本网格流程

```python
from abaqus import mdb
from abaqusConstants import *
from mesh import ElemType

part = mdb.models['Model-1'].parts['Beam']

# 1. 设网格种子（全局尺寸）
part.seedPart(size=5.0)
# 局部种子应先通过命名 Set 或边界盒获得目标 edges，再调用 seedEdgeBySize。

# 2. 先按分析意图设置网格形状和技术；不能只指定单元类型。
part.setMeshControls(regions=part.cells,
                     elemShape=HEX, technique=STRUCTURED)

# 3. 再设与目标形状对应的单元类型
part.setElementType(regions=(part.cells,), elemTypes=(
    ElemType(elemCode=C3D8R, elemLibrary=STANDARD),
))

# 4. 生成网格
part.generateMesh()
```

`setElementType` 只给适用的形状槽位指定单元代码，不会把当前 `TET + FREE` 网格控制
改成六面体。若 `analysis_spec.mesh` 要求全六面体，必须先设置 `HEX + STRUCTURED`
（CAE 中可能回读为 `HEX_DOMINATED + STRUCTURED`），再重新划分。

### 结构化六面体网格

```python
# 结构化 HEX 只适用于可映射的几何；设置单元类型本身不会改变网格技术。
part.setMeshControls(regions=part.cells,
                     elemShape=HEX, technique=STRUCTURED)
part.setElementType(regions=(part.cells,), elemTypes=(
    ElemType(elemCode=C3D8R, elemLibrary=STANDARD),
))
part.generateMesh()
```

不要根据 Cell 的面数、边数或“看起来像四面体”来断言不能划六面体。对已分区几何，
先让 Abaqus 实际尝试结构化六面体；只有 `STRUCTURED` 不可用、划分失败，或生成后的
质量/类型不符合验收标准时，才继续增加分区或评估 `SWEEP`。用户明确要求全六面体时，
不得静默回退到 `TET + FREE`。

### 生成后回读（强制）

网格写入成功不等于意图已实现。应在同一次 Abaqus 脚本中返回最小回读结果：

```python
controls = []
for cell in part.cells:
    controls.append({
        'elem_shape': str(part.getMeshControl(region=cell, attribute=ELEM_SHAPE)),
        'technique': str(part.getMeshControl(region=cell, attribute=TECHNIQUE)),
    })

stats = part.getMeshStats(regions=(part.cells,))
actual_types = {}
for element in part.elements:
    actual_types[element.type] = actual_types.get(element.type, 0) + 1

result = {
    'controls': controls,
    'element_types': actual_types,
    'num_hex': stats.numHexElems,
    'num_wedge': stats.numWedgeElems,
    'num_pyramid': stats.numPyramidElems,
    'num_tet': stats.numTetElems,
}
```

全六面体意图至少要求：所有目标区域的技术为 `STRUCTURED`（或规格允许的 `SWEEP`）、
实际单元类型只有目标 HEX 代码、`numHexElems == len(part.elements)`，且 wedge/pyramid/tet
均为 0。`getElementType` 只能说明槽位指派，不能替代对已生成 `element.type` 的检查。

### 局部加密

```python
# 孔/槽附近加密
edges_near_hole = part.edges.getByBoundingBox(
    xMin=x_min, yMin=y_min, zMin=z_min,
    xMax=x_max, yMax=y_max, zMax=z_max,
)
if not edges_near_hole:
    raise ValueError('局部加密边选区为空')
part.seedEdgeBySize(edges=edges_near_hole, size=1.0)
```

## 网格质量验收

网格形状正确不等于质量合格。宽高比、扭曲/翘曲、Jacobian、稳定时间增量、厚度方向
单元数及关键响应的网格收敛阈值应来自 `analysis_spec.acceptance_criteria`、项目规范或
经确认的求解策略；Skill 不用一组无来源的通用数字替代项目验收标准。

## 验证清单

- [ ] 单元尺寸是否适合几何特征（孔、槽、薄壁）
- [ ] 通过厚度的单元数是否足够
- [ ] 单元类型是否匹配分析类型（Standard vs Explicit）
- [ ] 实际网格控制、`element.type` 和 `MeshStats` 是否与网格意图一致
- [ ] 全 HEX 要求下是否确认 wedge/pyramid/tet 均为 0
- [ ] 应力集中区是否已加密
