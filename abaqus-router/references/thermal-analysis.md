# Abaqus 热传导分析

热传导分析计算温度与热流，不自动计算热应力。温度引起的应力/变形应使用顺序耦合或
完全耦合流程，并读取 `coupled-analysis.md`。

## 稳态与瞬态

- `heat_transfer_steady`：只求平衡温度场；需要导热系数。
- `heat_transfer_transient`：求温度随时间变化；还需要密度和比热以及真实持续时间。

不能因为模型最终需要一个温度场就默认稳态；如果热惯性、升温时间或冷却时间影响结论，
必须使用瞬态。

## 单位与材料

Abaqus 不做单位换算。必须独立核对：

- Conductivity：能量 /（时间·长度·温差）。
- Specific heat：能量 /（质量·温差）。
- Density：质量 / 长度³。
- Film coefficient：能量 /（时间·面积·温差）。
- Surface heat flux：能量 /（时间·面积）。
- Body heat flux：能量 /（时间·体积）。

例如 N-mm-s-tonne 制中 `1 J = 1000 N·mm`。把 J/(kg·K) 换到 N·mm/(tonne·K)
时必须同时处理能量和质量换算；不要复制来源不明的比热数量级。

在 Scripting Reference（`abaqus doc` 或 https://help.3ds.com/）中核对：

- `Material.Conductivity(table=...)`
- `Material.SpecificHeat(table=...)`
- `Material.Density(table=...)`
- `Model.HeatTransferStep(name, previous, response=..., ...)`

温度依赖数据的表列顺序以当前安装的 Scripting Reference 材料页为准。

## 热边界与载荷

- `Model.TemperatureBC`：指定温度，使用 `region`。
- `Model.SurfaceHeatFlux`：面热流，必需参数含 `region/magnitude`。
- `Model.BodyHeatFlux`：体积热源，必需参数含 `region/magnitude`。
- `Model.FilmCondition`：对流换热属于 interaction，必需参数使用 `surface/definition`，
  不是 `region`。
- 辐射需同时明确绝对温标、辐射率和环境温度；不能把摄氏温度直接代入绝对温度项。

至少有一个能形成温差或热输入/输出的条件。只有统一初始温度且没有热边界/热源的模型虽
可能运行，但没有目标热过程。

## 分析步与网格

- 稳态 `response=STEADY_STATE`；`timePeriod` 不解释为真实升温时间。
- 瞬态 `timePeriod` 为真实时长，并根据允许温度变化设置增量控制和 `deltmx`。
- 热传导使用 DC*/DS* 热单元；不能把结构 C3D* 单元直接用于纯热步骤。
- 对薄壁、接触热阻、局部热源和大梯度区域做针对性网格加密。

## 输出与验收

常用输出包括 `NT/NT11`（节点温度）、`HFL`（热流）和适用时的 `RFL`。完成后：

1. 先检查 ODB 实际字段和 position。
2. 稳态核对热量输入与输出平衡。
3. 瞬态核对能量、时间步与温度历程。
4. 用至少两档网格比较目标温度或热流；边角热流峰值可能有奇异性。
5. 与解析解、试验或有来源的工程限值比较，而不是仅凭温度云图颜色。
