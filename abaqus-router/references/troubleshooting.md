# Abaqus 常见错误排查

## 连接错误

| 错误 | 原因 | 解决 |
|------|------|------|
| "未找到Abaqus安装" | Abaqus 未安装或PATH中找不到 | 安装Abaqus，或设置 `ABAQUS_COMMAND` 环境变量 |
| Abaqus 启动或连接失败 | 安装、许可证或进程状态异常 | 保留原始错误；不要反复启动 Abaqus，修复原因后再重试 |
| 检测到已运行的 Abaqus/CAE | 当前会话无法确定目标实例 | 关闭不需要的 Abaqus/CAE 后重试 |
| "request did not complete" | 本次请求超时 | 记录 `request_id`；先检查模型状态，不要盲目重放写脚本 |

## Python API 常见错误

### KeyError — 键不存在

```
KeyError: 'badKey'
```
→ 根据错误返回的可用键和相似键检查对象名称

### AttributeError — 属性/方法不存在

```
AttributeError: 'Material' object has no attribute 'Elestic'
```
→ 先读取顶层 `error.recovery` 返回的真实对象类型和 `possible_members`。已知规范名称时用 `--call` 或 `--member` 精确查询；名称未知时才把原始操作拆成一个原子 `--need`，只从数据库返回的真实候选中重新选择

### NameError — 未导入模块

```
NameError: name 'THREE_D' is not defined
```
→ 在 Abaqus 脚本中添加：`from abaqusConstants import *`

### TypeError — 参数错误

```
TypeError: unexpected keyword argument 'E'
```
→ 立即停止猜参；先读取 `error.recovery` 的 `callable_signature` 和 `possible_keywords`。如果仍缺少完整重载，已知规范名称时用 `get_api_detail.py --call Receiver.method` 精确查询，名称未知时才提交一个原子 `--need`

## 不收敛问题

| 症状 | 可能原因 | 解决 |
|------|----------|------|
| Too many increment attempts | 增量过大或强非线性 | 减小 initialInc；增大 maxNumInc |
| 刚体位移 (numerical singularity) | 约束不足 | 添加额外约束；检查是否有未连接的部件 |
| 负特征值 | 局部失稳或约束不足 | 添加稳定化 (stabilization)；检查接触 |
| 局部塑性应变过大 | 网格过粗或荷载过大 | 加密网格；分步施加荷载 |

## 建模常见错误

| 错误 | 解决 |
|------|------|
| 忘记指派截面 | `part.SectionAssignment(region=..., sectionName=...)` |
| 材料缺少密度（模态分析） | `mat.Density(table=((7.85e-9,),))` |
| 作业未创建就提交 | 先 `mdb.Job(name=..., model=...)` |
| 提交后 ODB 尚无结果帧 | 作业仍在 SUBMITTED/RUNNING，或已 ABORTED/TERMINATED | 用后续短调用查询一次 `job.status`；只有 `COMPLETED` 才读取 ODB，失败时查看 `.dat/.msg/.sta` |
| 单位制混乱 | Abaqus 没有内建单位开关；沿用现有工程约定，或在材料/荷载/时间进入任务时明确一套自洽单位 |
| 坐标硬编码 | 用 `part.sets['MySet']` 代替 `findAt((x,y,z))` |

## 应遵循的调试原则

1. **错误不是 API 文档**：诊断信息只用于定位失败；方法名、参数数量和类型以 离线 API 数据库的精确详情为准
2. **按里程碑执行**：复杂模型分阶段创建；对已有模型先用独立的只读脚本查询目标状态
3. **生成前取上下文**：把当前里程碑的全部写入、结果和诊断 needs 一次交给 `scripts/retrieve_api_bundle.py`；数据库不能证明 Region、几何选取和求解流程正确，复杂任务仍要拆成可观察的里程碑
4. **API 错误停止重试**：遇到 `KeyError`、`AttributeError`、`TypeError` 或参数错误时，先使用 `error.recovery` 的运行时证据；证据不足时只做一次精确符号查询或原子操作检索，不凭报错猜下一个名称或参数，也不自动重复执行
