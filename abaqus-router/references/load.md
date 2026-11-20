# Abaqus 荷载参考

## 荷载类型选择

| 荷载类型 | Abaqus 类 | 适用 |
|----------|-----------|------|
| 集中力 | ConcentratedForce | 具有平移自由度的节点、顶点或参考点 |
| 压力 | Pressure | 面荷载（分布力） |
| 重力 | Gravity | 自重 |
| 位移（强制） | 用 DisplacementBC | 强制位移边界 |
| 力矩 | Moment | 弯矩/扭矩 |
| 壳边线荷载 | ShellEdgeLoad | 壳边分布荷载 |
| 体荷载 | BodyForce | 体积力（如离心力） |
| 温度场 | Temperature | 热载荷 |

## Abaqus Python API

### 集中力

```python
# LoadPoint 应由节点、顶点或参考点构成，不能是实体面。
model.ConcentratedForce(name='Force', createStepName='LoadStep',
                         region=assembly.sets['LoadPoint'],
                         cf1=0.0, cf2=-100.0, cf3=0.0)  # Y方向 -100N
```

### 压力

```python
model.Pressure(name='Pressure', createStepName='LoadStep',
               region=assembly.surfaces['TopSurface'],
               magnitude=1.0)  # 1 MPa
```

### 重力

```python
model.Gravity(name='Gravity', createStepName='LoadStep',
               region=assembly.sets['All'],
               comp2=-9810.0)  # Y方向重力加速度 (mm/s²)
```

### 强制位移

```python
model.DisplacementBC(name='Disp', createStepName='LoadStep',
                      region=assembly.sets['Top'],
                      u1=0.0, u2=-5.0, u3=0.0,  # Y方向下压5mm
                      ur1=UNSET, ur2=UNSET, ur3=UNSET)
```

## 力的正负号（右手系）

- X 正方向 → cf1 > 0
- Y 正方向 → cf2 > 0（通常向上）
- Z 正方向 → cf3 > 0

## 关键注意事项

1. **力、压力、重力等荷载施加在分析 Step 上**；强制位移是 BC，可按加载历史建在 `Initial` 或后续 Step
2. **使用命名 Set** 选区域：`assembly.sets['LoadPoint']` 而非 `findAt`
3. **重力必须配合密度**；N-mm-s-tonne 单位制中 g = 9810 mm/s²
4. **压力正值 = 指向面内**（压缩）
5. **实体面上的合力不能直接用 ConcentratedForce**：改用 Pressure/SurfaceTraction，或通过参考点与耦合约束传递集中力
