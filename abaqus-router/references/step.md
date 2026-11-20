# Abaqus 分析步设置参考

## 分析步类型选择

| 分析目标 | Step 类型 | nlgeom | 时间 | 增量 |
|----------|-----------|--------|------|------|
| 静载应力/位移 | StaticStep | OFF/ON | 1.0 | initialInc=0.1 |
| 固有频率 | FrequencyStep | — | — | numEigen=10 |
| 屈曲模态 | BuckleStep | — | — | numEigen=5 |
| 瞬态响应（平滑） | ImplicitDynamicsStep | ON | 实际时间 | initialInc=0.01 |
| 冲击/碰撞 | ExplicitDynamicsStep | ON | ~ms | 自动确定 |
| 稳态热传导 | HeatTransferStep (STEADY_STATE) | — | 1.0 | — |
| 瞬态热传导 | HeatTransferStep (TRANSIENT) | — | 实际时间 | deltmx=5.0 |
| 热-力耦合 | CoupledTempDisplacementStep | ON | 1.0 | initialInc=0.1 |

## nlgeom 判定

| 条件 | nlgeom | 场景 |
|------|--------|------|
| 小变形，线弹性材料 | OFF | 默认，最快 |
| 大转动/大位移 | ON | 细长结构、缆索 |
| 塑性材料 | 按变形程度决定 | 材料非线性本身不等于几何非线性 |
| 接触 | 按滑移/变形程度决定 | 大滑移或大变形接触通常使用 ON |
| 后屈曲 | ON | 屈曲后行为 |

## 增量控制参数

| 收敛难度 | initialInc | minInc | maxInc | maxNumInc |
|----------|-----------|--------|--------|-----------|
| 容易（线性） | 1.0 | 1e-6 | 1.0 | 100 |
| 中等 | 0.1 | 1e-8 | 0.2 | 200 |
| 困难（接触、塑性） | 0.01 | 1e-12 | 0.05 | 500 |

## Abaqus Python API 模式

### 创建静力分析步

```python
from abaqus import mdb
from abaqusConstants import *

model = mdb.models['Model-1']

# 线性静力
model.StaticStep(name='LoadStep', previous='Initial',
                 nlgeom=OFF, timePeriod=1.0,
                 initialInc=0.1, maxNumInc=100)

# 非线性静力（大变形）
model.StaticStep(name='LoadStep', previous='Initial',
                 nlgeom=ON, timePeriod=1.0,
                 initialInc=0.01, minInc=1e-10, maxInc=0.05,
                 maxNumInc=500)
```

### 创建模态分析步

```python
model.FrequencyStep(name='Modal', previous='Initial',
                    numEigen=10, eigensolver=LANCZOS)
```

### 多步链式

```python
model.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
model.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
model.FrequencyStep(name='Modal', previous='Step-2',
                    eigensolver=LANCZOS, numEigen=10)
# 这里的 Modal 基于 Step-2 结束时的预载状态；
# 不考虑预载时才通常令 previous='Initial'。
```

## 常见问题

| 问题 | 可能原因 | 解决方法 |
|------|----------|----------|
| Too many increments | 收敛困难 | 减小 maxInc，增大 maxNumInc |
| Negative eigenvalues | 未约束或失稳 | 检查 BCs，添加稳定化 |
| Time increment too small | 强非线性 | 增加稳定化，检查材料 |
| 模态频率为 0 | 有刚体位移 | 添加足够的约束 |

## 验证清单

- [ ] Step 类型与实际物理问题匹配
- [ ] nlgeom 设置适合变形程度
- [ ] 增量控制参数合理
- [ ] 多步链式正确（previous 指向正确的步骤）
