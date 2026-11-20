# Abaqus 动力分析

先根据事件物理选择隐式或显式，不使用固定的“10 ms/100 ms”阈值替代判断。

## 过程选择

| 特征 | 隐式动力 | 显式动力 |
|---|---|---|
| 平滑、较长时间响应 | 通常适合 | 可能因稳定时间步而昂贵 |
| 强接触、冲击、严重材料/几何非线性 | 可能难收敛 | 通常更稳健 |
| 准静态过程 | 可直接求解 | 可用，但必须证明惯性效应足够小 |
| 高频波传播 | 需解析足够时间/空间尺度 | 常用 |

事件持续时间、最小单元尺寸、材料波速、载荷频谱、非线性和输出需求共同决定方案。不能只
根据用户描述中的“快/慢”选择求解器。

## 必需规格

- 可变形材料必须有与单位制一致的密度。
- `timePeriod` 是真实事件时长，必须为正数。
- 明确载荷幅值随时间的变化或初始速度；不能用默认幅值掩盖阶跃冲击。
- 网格单元库与求解器匹配：Implicit 使用 `STANDARD`，Explicit 使用 `EXPLICIT`。
- 接触问题同时读取 `contact-analysis.md`。

## Scripting calls to confirm

Confirm these calls in the installed Abaqus Scripting Reference (`abaqus doc` or https://help.3ds.com/) before use:

- `Model.ImplicitDynamicsStep(name, previous, ...)`
- `Model.ExplicitDynamicsStep(name, previous, ...)`
- `Model.Velocity(name, region, velocity1, velocity2, velocity3, omega, axisBegin, axisEnd, ...)`

`Model.Velocity` 是初始预定义场。Scripting Reference 中的 `Velocity` 页没有 `createStepName`。不要把 BC/FieldOutputRequest
的参数迁移到 Velocity。旋转速度不使用时，仍按该页列出的参数提供 `omega/axisBegin/axisEnd`
所需值，而不是猜测它们可省略。

## 隐式动力检查

- 根据载荷频率和响应时间尺度设置 `initialInc/minInc/maxInc`，而不是复制静力步参数。
- 数值阻尼、`application` 和半增量残差控制会影响响应，只在目标明确时设置。
- `noStop` 不应被用来接受未满足平衡容限的增量。
- 输出帧必须足以解析目标最高频率；仅有起点和终点不能描述瞬态峰值。

## 显式动力检查

- 记录稳定时间增量受哪个最小/畸变单元控制。
- Mass scaling 会改变质量和惯性响应。使用时必须记录策略、增加质量以及验收标准。
- 准静态显式需要用能量比例证明准静态性，不能仅凭加载速度“看起来很慢”。
- 不默认把 C3D8R 或任何单元写成万能推荐；按锁死、沙漏、接触和畸变风险选择。

## 输出和结果门禁

常见场输出：`U/S/V/A`；塑性材料按需加 `PEEQ`。显式分析至少应规划历史输出：

- `ALLKE`：动能。
- `ALLIE`：内能。
- `ETOTAL`：总能量平衡量。
- `ALLAE`：存在减缩积分/人工控制时用于人工能评估。
- `ALLWK`：需要核对外功时使用。

具体变量是否可用必须由当前过程和 ODB 检查结果确认。结果至少检查求解终态、事件时间
覆盖、能量平衡、人工能、质量缩放、接触状态和目标响应的时间/网格收敛。
