# Abaqus 静力分析完整工作流

## 流程总览

```
1. 几何建模 → 2. 材料+截面 → 3. 装配 → 4. 分析步 → 5. BC+荷载 → 6. 网格 → 7. 提交并返回 → 8. 查询状态 → 9. 后处理
```

## 步骤详解

### 1. 几何建模

```python
from abaqus import mdb
from abaqusConstants import *

model_name = 'PKPM-Static-Example'
job_name = 'PKPM-Static-Job'
if model_name in mdb.models or job_name in mdb.jobs:
    raise ValueError('示例模型或作业已存在，拒绝覆盖')

model = mdb.Model(name=model_name)

# 方式A：在Abaqus中创建
sketch = model.ConstrainedSketch(name='BeamProfile', sheetSize=200.0)
sketch.rectangle(point1=(0.0, 0.0), point2=(10.0, 10.0))
part = model.Part(name='Block', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=100.0)

# 拉伸方向为 Z；创建与实体截面、固定端和受压端匹配的区域。
tol = 1.0e-6
part.Set(cells=part.cells, name='AllCells')
fixed_faces = part.faces.getByBoundingBox(
    xMin=-tol, yMin=-tol, zMin=-tol,
    xMax=10.0 + tol, yMax=10.0 + tol, zMax=tol,
)
loaded_faces = part.faces.getByBoundingBox(
    xMin=-tol, yMin=-tol, zMin=100.0 - tol,
    xMax=10.0 + tol, yMax=10.0 + tol, zMax=100.0 + tol,
)
if len(fixed_faces) != 1 or len(loaded_faces) != 1:
    raise ValueError('端面选取失败')
part.Set(faces=fixed_faces, name='FixedEnd')
part.Surface(side1Faces=loaded_faces, name='LoadSurface')

# 方式B：导入CAD（如有step/iges文件）
# geometry = mdb.openStep(fileName=r'D:\model.step', scale=1.0)
# part = model.PartFromGeometryFile(
#     name='Imported', geometryFile=geometry,
#     combine=False, dimensionality=THREE_D, type=DEFORMABLE_BODY)
```

### 2. 材料 + 截面

```python
# 材料
mat = model.Material(name='Steel')
mat.Elastic(table=((210000.0, 0.3),))

# 截面
model.HomogeneousSolidSection(name='BeamSection', material='Steel')

# 实体截面必须指派给 cell Set，而不是 face Set。
part.SectionAssignment(region=part.sets['AllCells'],
                       sectionName='BeamSection')
```

### 3. 装配

```python
assembly = model.rootAssembly
instance = assembly.Instance(name='Block-1', part=part, dependent=ON)
```

### 4. 分析步

```python
model.StaticStep(name='LoadStep', previous='Initial',
                 nlgeom=OFF, timePeriod=1.0,
                 initialInc=0.1, maxNumInc=100)
```

### 5. BC + 荷载

```python
# 固定 Z=0 端面
model.EncastreBC(name='FixLeft', createStepName='Initial',
                 region=instance.sets['FixedEnd'])

# 在 Z=100 端面施加 1 MPa 向内压力。
model.Pressure(name='EndPressure', createStepName='LoadStep',
               region=instance.surfaces['LoadSurface'], magnitude=1.0)
```

### 6. 网格

```python
from mesh import ElemType

part.seedPart(size=5.0)
part.setMeshControls(regions=part.cells,
                     elemShape=HEX, technique=STRUCTURED)
part.setElementType(regions=(part.cells,), elemTypes=(
    ElemType(elemCode=C3D8R, elemLibrary=STANDARD),
))
part.generateMesh()
```

### 7. 提交并立即返回

```python
import os

job = mdb.Job(name=job_name, model=model_name)
job.submit()
result = {
    'job_name': job_name,
    'status': str(job.status),
    'odb_path': os.path.abspath(job_name + '.odb'),
}
```

此调用到此结束，同时结束当前聊天回复。不要调用 `waitForCompletion()`，也不要
紧接着自动查询或在同一脚本中循环查询。

### 8. 后续独立调用：查询一次状态

```python
from abaqus import mdb
from abaqusConstants import COMPLETED

job_name = 'PKPM-Static-Job'
if job_name not in mdb.jobs:
    raise KeyError('当前受管 CAE 中不存在作业: %s' % job_name)
job = mdb.jobs[job_name]
result = {
    'job_name': job_name,
    'status': str(job.status),
    'ready': job.status == COMPLETED,
}
```

若状态不是 `COMPLETED`，报告当前状态并停止；不要在聊天调用中等待或自动重查。
后续 `abaqus.execute` 调用应继续传入提交时相同的 `workspace_dir`。

### 9. 后续独立调用：完成后读取 ODB

```python
from abaqus import mdb
from abaqusConstants import COMPLETED
from odbAccess import openOdb
import os

job_name = 'PKPM-Static-Job'
odb_path = os.path.abspath(job_name + '.odb')  # 使用与提交时相同的 workspace_dir
job = mdb.jobs[job_name]
if job.status != COMPLETED:
    result = {'job_name': job_name, 'status': str(job.status), 'ready': False}
else:
    odb = openOdb(odb_path, readOnly=True)
    try:
        last_frame = odb.steps['LoadStep'].frames[-1]
        disp = last_frame.fieldOutputs['U']
        stress = last_frame.fieldOutputs['S']
        result = {
            'job_name': job_name,
            'status': str(job.status),
            'ready': True,
            'max_displacement': max(v.magnitude for v in disp.values),
            'max_vonMises': max(v.mises for v in stress.values),
        }
    finally:
        odb.close()
```

## 验证清单

- [ ] 材料参数单位一致（mm-N-MPa）
- [ ] 约束充分（消除刚体位移）
- [ ] 荷载施加在正确的面和方向上
- [ ] 网格密度合理（至少 2 层单元通过厚度）
- [ ] 分析步为 StaticStep（非动力）
- [ ] 作业名唯一（不重复）
