# Abaqus 几何建模参考

## 创建方式

| 方式 | 适用 |
|------|------|
| Abaqus内 2D草绘+拉伸 | 简单棱柱体、板、梁 |
| Abaqus内 2D草绘+旋转 | 轴对称体 |
| 导入 CAD 文件 | 复杂几何 |

## Abaqus Python API

### 方式A：草绘 + 拉伸

```python
from abaqus import mdb
from abaqusConstants import *

model_name = 'EngineeringAgent-Geometry-Example'
if model_name in mdb.models:
    raise ValueError('模型已存在，拒绝覆盖: %s' % model_name)
model = mdb.Model(name=model_name)

# 草绘
sketch = model.ConstrainedSketch(name='Profile', sheetSize=200.0)
sketch.rectangle(point1=(0.0, 0.0), point2=(10.0, 10.0))

# 创建部件
part = model.Part(name='Block', dimensionality=THREE_D, type=DEFORMABLE_BODY)

# 拉伸
part.BaseSolidExtrude(sketch=sketch, depth=100.0)
```

### 草绘常用形状

```python
# 矩形
sketch.rectangle(point1=(0, 0), point2=(10, 10))

# 圆
sketch.CircleByCenterPerimeter(center=(50, 50), point1=(50, 60))

# 线
sketch.Line(point1=(0, 0), point2=(100, 0))

# 弧
sketch.ArcByCenterEnds(center=(50, 0), point1=(0, 0), point2=(100, 0),
                       direction=COUNTERCLOCKWISE)
```

### 方式B：导入 CAD

```python
step_file = r'D:\path\to\model.step'
geometry = mdb.openStep(fileName=step_file, scale=1.0)
part = model.PartFromGeometryFile(
    name='ImportedPart',
    geometryFile=geometry,      # 必须是 openStep/openIges 返回的 AcisFile
    combine=False,
    dimensionality=THREE_D,
    type=DEFORMABLE_BODY,
)
```

### 创建命名 Set（关键！）

```python
# 面Set — 用于 BC、荷载、截面指派
part.Set(faces=part.faces[0:1], name='TopFace')

# 边Set — 用于种子、BC
part.Set(edges=part.edges[0:1], name='Edge')

# 体Set — 用于截面指派
part.Set(cells=part.cells, name='AllCells')

# 用边界盒选取（比 findAt 更稳定）
faces = part.faces.getByBoundingBox(
    xMin=0.0, yMin=0.0, zMin=0.0,
    xMax=100.0, yMax=10.0, zMax=10.0,
)
if not faces:
    raise ValueError('FrontFace 选区为空')
part.Set(faces=faces, name='FrontFace')
```

### 表面（用于接触、压力、对流）

```python
# 用命名Set创建表面
part.Surface(side1Faces=part.sets['TopFace'].faces, name='TopSurface')
```

## 命名 Set vs 坐标引用

```python
# ✅ 好：命名Set（稳定）
part.Set(faces=part.faces.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax),
         name='Top')

# ❌ 差：硬编码坐标（模型改变后失效）
face = part.faces.findAt(((100.0, 50.0, 0.0),))
```

## 验证清单

- [ ] 创建完 Part 后立即创建命名 Set
- [ ] 使用 boundingBox 或拓扑过滤而非 findAt 坐标
- [ ] 导入 CAD 时检查单位缩放（STEP 文件可能是米制→需要缩放到 mm）
- [ ] `PartFromGeometryFile.geometryFile` 来自 `mdb.openStep/openIges`，不是文件路径字符串
- [ ] 用户或下一里程碑确实需要业务确认时，先把查询动作纳入 API bundle，再在同一脚本的最小 `result` 中返回；写操作成功后不另起只读脚本重复验证
