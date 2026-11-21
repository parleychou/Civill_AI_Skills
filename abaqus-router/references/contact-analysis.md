# Abaqus 接触分析

接触是叠加在静力、隐式动力或显式动力过程上的分析特征，不是独立的
`analysis_type`。先确定主求解过程，再在 `analysis_spec.connections` 中声明接触。

## 建模决策

| 物理关系 | 建模方式 |
|---|---|
| 永久粘结且不允许分离/滑移 | Tie 或相应约束，不要伪装成高摩擦接触 |
| 两个已知表面接触 | Surface-to-surface contact pair |
| 多体、未知接触组合或显式冲击 | General contact，明确包含域和排除域 |
| 表面可能与自身接触 | Self-contact 或包含 SELF 的 general contact |

Contact pair 才需要明确 main/secondary 两侧。优先依据表面离散、刚度、曲率和接触算法
选择角色；“较硬的一定是 main”只能作为候选判断，不能替代具体模型检查。General
contact 不应被错误要求提供 main/secondary 对。

## 建模前证据

- 两侧 Surface 名称存在，实体数量非零，且位于预期实例。
- 壳面 side1/side2 或法向方向符合接触方向；不能只凭 Surface 名称判断。
- 初始间隙、干涉或几何接触状态已记录，避免依赖默认自动调整。
- 用户已明确允许分离、滑移形式、摩擦数据来源和预期接触状态。
- 接触体的整体刚体运动仍由 BC、连接或惯性条件控制。

## 版本化 API 路径

写脚本前查询本机版本的精确契约。Abaqus API 数据库（`references/abaqus_api_2024.db`）中应核对：

- `Model.ContactProperty`
- `NormalBehavior.NormalBehavior`，实际访问路径为
  `model.interactionProperties[name].NormalBehavior(...)`
- `ContactTangentialBehavior.TangentialBehavior`，实际访问路径为
  `model.interactionProperties[name].TangentialBehavior(...)`
- `Model.SurfaceToSurfaceContactStd`
- `Model.SurfaceToSurfaceContactExp`
- `Model.ContactStd` / `Model.ContactExp`（general contact）

接触对 API 的必需参数包括 `name/createStepName/main/secondary/sliding/interactionProperty`。
Standard 与 Explicit 方法不能互换。General contact 的参数结构随版本和重载变化较大，必须
读取当前版本完整契约，不能从 contact pair 参数猜写。

## 接触属性

- Normal behavior 的 `pressureOverclosure`、`allowSeparation` 和约束执行方式必须符合任务。
- Tangential behavior 默认可以是 frictionless；需要摩擦时由用户或资料提供系数及依赖项。
- 不内置钢—钢、橡胶—金属等“典型摩擦系数”作为模型输入。
- 接触稳定化、接触刚度和自动调整会改变结果，只在有诊断证据时使用并记录。

## `nlgeom` 边界

塑性或接触本身不自动推出 `nlgeom=ON`。应根据转动、变形、滑移路径和接触法向变化
决定。有限滑移且显著运动时通常需要考虑几何非线性；小滑移、小变形问题可以明确保持
`OFF`。Skill 只能警告不一致，不能擅自修改。

## 输出与验证

根据过程和单元支持情况请求并在 ODB 中确认接触输出，例如：

- `CSTRESS` / `CPRESS`：接触压力和切向应力信息。
- `CDISP` / `COPEN`：相对位移和开闭状态。
- `CSLIP`：滑移信息。

提交前检查 Surface 计数；完成后检查：

1. ODB 实际含有请求的接触变量。
2. 活动/分离状态符合 `analysis_spec` 的预期，而非仅看一张云图。
3. 穿透、接触压力和滑移按有来源的验收阈值判定。
4. 接触边缘的应力峰值先做奇异性和网格敏感性分析，不能直接作为材料强度结论。

不要把“收敛困难”自动归因于增量过大。先查空面、反向法线、初始过闭合、刚体运动、
材料/单位和接触属性，再决定是否调整增量或稳定化。
