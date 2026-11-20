# Abaqus 模态分析完整工作流

## 流程总览

```
1. 几何建模 → 2. 材料(含密度) → 3. 装配 → 4. FrequencyStep → 5. BC(不需荷载) → 6. 网格 → 7. 提交并返回 → 8. 查询状态 → 9. 提取频率和模态
```

## 关键差异：与静力分析

| 方面 | 静力分析 | 模态分析 |
|------|---------|---------|
| 材料 | E, ν 必需 | E, ν, **ρ (密度) 必需** |
| 荷载 | 必须施加 | **不需要**（模态与荷载无关） |
| 约束 | 通常必须消除刚体运动 | 由目标决定：约束模态或自由—自由模态 |
| Step | StaticStep | **FrequencyStep** |
| 结果 | 应力/位移 | 固有频率 + 振型 |

## 步骤详解

### 1. 建模（同静力分析）

### 2. 材料 — 密度是必需的

```python
mat = model.Material(name='Steel')
mat.Elastic(table=((210000.0, 0.3),))
mat.Density(table=((7.85e-9,),))   # ← sequence of sequences；模态分析必须
```

### 3. 装配（同静力分析）

### 4. 分析步 — FrequencyStep

```python
model.FrequencyStep(name='Modal', previous='Initial',
                    numEigen=10,          # 提取10阶模态
                    eigensolver=LANCZOS)   # Lanczos法（大模型推荐）
```

### 5. BC — 由目标决定，不加外载荷

```python
# 完全固定可直接使用 EncastreBC；部分约束再使用 DisplacementBC。
model.EncastreBC(name='Fixed', createStepName='Initial',
                 region=instance.sets['FixedEnd'])
```

自由—自由模态不创建 BC，并应预期出现刚体模态；这不是约束遗漏。

### 6. 网格 — 对目标频段做收敛检查

低阶频率可能比局部应力对网格不敏感，但不能固定假设“粗 2–3 倍”。至少用
两档网格比较目标阶次的频率和振型，达到任务所需误差后再停止加密。

### 7. 提交并立即返回

```python
import os

job_name = 'ModalJob'
job = mdb.Job(name=job_name, model=model.name)
job.submit()
result = {
    'job_name': job_name,
    'status': str(job.status),
    'odb_path': os.path.abspath(job_name + '.odb'),
}
```

此调用到此结束，同时结束当前聊天回复；不执行 `waitForCompletion()`，也不紧接着自动查询。

### 8. 后续独立调用：查询一次状态

```python
from abaqus import mdb
from abaqusConstants import COMPLETED

job_name = 'ModalJob'
if job_name not in mdb.jobs:
    raise KeyError('当前受管 CAE 中不存在作业: %s' % job_name)
job = mdb.jobs[job_name]
result = {
    'job_name': job_name,
    'status': str(job.status),
    'ready': job.status == COMPLETED,
}
```

状态未完成时报告并停止。后续调用继续传入提交时相同的 `workspace_dir`。

### 9. 后续独立调用：完成后读取频率

```python
from abaqus import mdb
from abaqusConstants import COMPLETED
from odbAccess import openOdb
import os

job_name = 'ModalJob'
job = mdb.jobs[job_name]
if job.status != COMPLETED:
    result = {'job_name': job_name, 'status': str(job.status), 'ready': False}
else:
    odb = openOdb(os.path.abspath(job_name + '.odb'), readOnly=True)
    try:
        freqs = []
        for frame in odb.steps['Modal'].frames:
            if frame.mode > 0:
                freqs.append({
                    'mode': frame.mode,
                    'frequency': frame.frequency,
                })
        result = {
            'job_name': job_name,
            'status': str(job.status),
            'ready': True,
            'frequencies': freqs,
            'numModes': len(freqs),
        }
    finally:
        odb.close()
```

## 典型结果解读

```
自由—自由三维结构通常出现 6 个接近 0 的刚体模态
约束模型仍出现非预期的接近 0 频率 → 检查约束、连接和孤立部件
模态是否弯曲/扭转应查看振型，不能只凭频率排序判断
```

## 验证清单

- [ ] 材料密度已定义
- [ ] 已明确本次是约束模态还是自由—自由模态
- [ ] FrequencyStep 而非 StaticStep
- [ ] 已对目标阶次做至少两档网格的频率收敛比较
