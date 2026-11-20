# Abaqus 材料定义参考

## 材料属性需求按分析类型

| 分析类型 | 需要的材料属性 |
|----------|---------------|
| 静力线弹性 | E, ν |
| 静力弹塑性 | E, ν, σy (屈服应力), 塑性应力-应变数据 |
| 模态分析 | E, ν, ρ (密度) |
| 热传导 | k (导热系数), c (比热容), ρ |
| 热-力耦合 | 弹性属性 + 热属性 + 热膨胀系数 α |
| 显式动力学 | E, ν, ρ, 塑性数据, 可能需要损伤参数 |
| 疲劳分析 | 弹性属性 + S-N曲线数据 |

## 截面类型选择

| 部件类型 | 截面类型 | 示例 |
|----------|----------|------|
| 3D 实体 | HomogeneousSolidSection | 通用金属/塑料零件 |
| 壳体 | HomogeneousShellSection | 薄板、压力容器 |
| 梁 | BeamSection (需指定Profile) | 框架结构、桁架 |
| 复合材料 | CompositeShellSection | 碳纤维层合板 |
| 桁架 (只受拉压) | TrussSection | 二力杆 |

## Abaqus Python API 模式

### 创建材料

```python
from abaqus import mdb
from abaqusConstants import *

model = mdb.models['Model-1']

# 线弹性
mat = model.Material(name='Steel')
mat.Elastic(table=((210000.0, 0.3),))       # E=210GPa, ν=0.30
mat.Density(table=((7.85e-9,),))            # ρ=7850 kg/m³ → 7.85e-9 tonne/mm³

# 弹塑性（多线性各向同性硬化）
plastic_mat = model.Material(name='Steel-Plastic')
plastic_mat.Elastic(table=((210000.0, 0.3),))
plastic_mat.Plastic(table=((235.0, 0.0),     # 屈服点
                           (300.0, 0.02),    # 2%塑性应变
                           (350.0, 0.05)))   # 5%塑性应变

# 超弹性 (橡胶-like)
mat = model.Material(name='Rubber')
mat.Hyperelastic(type=MOONEY_RIVLIN,
                 testData=OFF,
                 table=((0.5, 0.1, 0.01),))
```

使用超弹性材料的分析通常还需要在相应 Step 中启用 `nlgeom=ON`；不要把
仅用于说明 API 的材料定义混入无关的线性验证模型。

### 创建截面

```python
# 以下片段假设引用的材料和 BeamProfile 已在当前 model 中创建。
# 实体截面
model.HomogeneousSolidSection(name='SolidSection',
                               material='Steel')

# 壳截面 (厚度=2mm)
model.HomogeneousShellSection(name='ShellSection',
                               material='Aluminum',
                               thickness=2.0)

# 梁截面 (用预定义Profile)
model.BeamSection(name='BeamSection',
                   profile='BeamProfile',
                   material='Steel',
                   integration=DURING_ANALYSIS)
```

### 截面指派

```python
# 使用命名Set（推荐，稳定）
part.SectionAssignment(region=part.sets['Set-Beam'],
                       sectionName='BeamSection')

# `region` 必须是与截面维度匹配的 Set：实体用 cells，壳用 faces，梁/桁架用 edges。
# 不要把原始 `part.cells[0:1]` 直接作为 region。
```

## 验证清单

截面指派后验证：
- [ ] 材料名拼写正确（区分大小写）
- [ ] 单位制一致（E, ν, σy 是否用了正确的单位）
- [ ] 密度是否包含了（模态或动力学分析必需）
- [ ] 截面是否用命名 Set 指派（而非直接引用 cells）
- [ ] 在脚本的 `result` 中返回 material/section 名称，或用独立只读脚本确认

## 常见材料问题的中文参考值 (mm-N-MPa)

以下仅为示例量级，不能替代用户指定的牌号、标准、温度和试验数据，也不应
自动覆盖已有模型中的材料定义。

| 材料 | E | ν | ρ (tonne/mm³) | σy | 线膨胀系数 α |
|------|---|---|---------------|-----|-------------|
| Q235钢 | 206000 | 0.3 | 7.85e-9 | 235 | 1.2e-5 |
| Q345钢 | 206000 | 0.3 | 7.85e-9 | 345 | 1.2e-5 |
| 45钢 | 209000 | 0.3 | 7.85e-9 | 355 | 1.17e-5 |
| 304不锈钢 | 193000 | 0.31 | 7.93e-9 | 215 | 1.73e-5 |
| 6061-T6铝 | 69000 | 0.33 | 2.70e-9 | 276 | 2.36e-5 |
| 7075-T6铝 | 72000 | 0.33 | 2.81e-9 | 505 | 2.36e-5 |
| TC4钛合金 | 110000 | 0.34 | 4.43e-9 | 880 | 8.6e-6 |
| C30混凝土 | 30000 | 0.20 | 2.40e-9 | — | 1.0e-5 |
| HT200铸铁 | 120000 | 0.25 | 7.20e-9 | — | 1.04e-5 |
| 尼龙6 | 2500 | 0.39 | 1.14e-9 | 55 | 9.0e-5 |
| PMMA (有机玻璃) | 3000 | 0.35 | 1.19e-9 | 70 | 7.0e-5 |
