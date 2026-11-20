# Abaqus 边界条件参考

## BC 类型

| 约束类型 | Abaqus BC | 适用场景 |
|----------|-----------|----------|
| 完全固定 | ENCASTRE (U1=U2=U3=UR1=UR2=UR3=0) | 焊接、墙面 |
| 铰接/简支 | DisplacementBC（约束平移、释放适用的转动） | 梁/壳端部；实体需按支承面实际运动定义 |
| 滚动支座 | DisplacementBC (部分自由度=0) | 热膨胀允许 |
| 对称面 X | XSYMM (U1=UR2=UR3=0) | X 对称面 |
| 对称面 Y | YSYMM (U2=UR1=UR3=0) | Y 对称面 |
| 对称面 Z | ZSYMM (U3=UR1=UR2=0) | Z 对称面 |
| 反对称 X | XASYMM (U2=U3=UR1=0) | X 反对称 |
| 自定义 | DisplacementBC (指定 u1, u2, u3, ur1, ur2, ur3) | 任意约束 |

## 决策流程

```
用户说 → 分析 → BC
──────────────────
"固定"           → ENCASTRE
"铰接"、"简支"    → DisplacementBC, U1=U2=U3=0
"滚动"、"滑动"    → DisplacementBC, 部分自由度=0
"利用对称性"      → XSYMM/YSYMM/ZSYMM
"反对称"         → XASYMM/YASYMM/ZASYMM
"施加位移"       → DisplacementBC, 指定非零值
```

## 避免刚体位移

除非分析目标本来就是自由体，静力模型的边界条件组合必须消除整体的 6 个
刚体模态（3 个平移、3 个转动）。不能只用“约束了几个点”判断充分性：

- **3D 实体单元**节点通常只有平移自由度，但多个节点约束的空间分布共同决定是否仍可整体转动。
- **壳/梁单元**具有适用的转动自由度，应根据真实铰接、固接或对称关系明确释放/约束。
- 模态分析允许有意建立自由—自由模型，此时接近 0 Hz 的刚体模态是预期结果。

## Abaqus Python API 模式

### 固定端 (ENCASTRE)

```python
from abaqus import mdb
from abaqusConstants import *

model = mdb.models['Model-1']
assembly = model.rootAssembly

# 假设已在 Assembly 中创建了 Set 'FixedFace'
model.EncastreBC(name='Fixed', createStepName='Initial',
                  region=assembly.sets['FixedFace'])
```

### 铰接支座 (DisplacementBC)

```python
# 以下区域应由梁/壳端部节点、顶点或参考点构成；实体支承不能机械套用。
model.DisplacementBC(name='Pinned', createStepName='Initial',
                      region=assembly.sets['SupportPoint'],
                      u1=0.0, u2=0.0, u3=0.0,
                      ur1=UNSET, ur2=UNSET, ur3=UNSET)
```

### 对称面

```python
model.XsymmBC(name='SymX', createStepName='Initial',
               region=assembly.sets['SymFace'])
```

### 滚动支座

```python
model.DisplacementBC(name='Roller', createStepName='Initial',
                      region=assembly.sets['RollerSupport'],
                      u1=UNSET, u2=0.0, u3=UNSET,  # 只约束Y
                      ur1=UNSET, ur2=UNSET, ur3=UNSET)
```

### 施加位移载荷

```python
model.DisplacementBC(name='PrescribedDisp', createStepName='LoadStep',
                      region=assembly.sets['LoadPoint'],
                      u1=0.0, u2=-5.0, u3=0.0)  # Y方向-5mm
```

## 验证清单

- [ ] 结构是否完全约束（无刚体位移）
- [ ] 约束面/点使用命名 Set（而非坐标 `findAt`）
- [ ] 对称/反对称条件正确
- [ ] createStepName 正确（通常 Initial 步施加约束）
