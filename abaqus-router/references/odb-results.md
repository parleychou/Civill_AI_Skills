# Abaqus ODB 结果读取

只有 Job 已确认 `COMPLETED` 后才按聊天工作流读取其 ODB。对外部已有 ODB，先记录来源并
以 `readOnly=True` 打开。始终用 `try/finally` 关闭自己打开的 ODB。

不要删除 `.lck`。锁存在时报告占用状态，由用户关闭写入进程或确认文件来源；删除锁可能
破坏正在写入的数据库。

## 先检查后提取

先运行 `scripts/inspect_abaqus.py --odb PATH`，确认：

- 实际 Step 名和 Frame 数。
- Frame 的 `frameValue/mode/frequency`。
- Field output 名、`componentLabels`、`validInvariants` 和 position。
- History region 名及其 history output。
- ODB 诊断中的终态、错误和警告。

只有检查结果中存在的字段、component 或 invariant 才能进入提取脚本。

## Step 与 Frame

- 终态分析可以选择 `frames[-1]`，但要记录索引和 `frameValue`。
- 时间历程不能只读取最后一帧。
- 模态每个 Frame 对应一个模态，读取 `frame.mode` 和 `frame.frequency`；不要解析
  `frame.description` 文本。
- 多 Step ODB 不默认使用第一个或最后一个 Step，必须与 `analysis_spec` 对应。

## FieldOutput 选择

版本化 API：

- `FieldOutput.getSubset(...)` 有 region、position、elementType、sectionPoint 等不同重载。
- `FieldOutput.getScalarField(invariant=...)` 或
  `FieldOutput.getScalarField(componentLabel=...)` 是不同重载。

`getSubset(position=ELEMENT_NODAL/CENTROID, readOnly=...)` 可能从积分点外推。如果只做只读
提取，明确 `readOnly=ON`，并在证据中标记这是外推值。不要把它与原始积分点值混为一谈。

计算 Mises 前先确认 `MISES` 位于 `validInvariants`；读取 `S11` 前确认它位于
`componentLabels`。复数结果的 scalar field 操作只处理实部，频域结果需要单独定义复数
处理方式。

## 区域、标签与坐标系

- 优先使用 ODB 中已存在的 node/element Set，通过 `getSubset(region=...)` 限定区域。
- 节点/单元标签属于实例；只按 label 匹配可能把不同实例的同号实体混在一起。
- 向量和张量必须记录全局或局部坐标系。
- 反力总和要限定真实支座区域；力矩还必须选择参考点，并计入 `r × RF` 和节点 `RM`。

## 极值和奇异性

全模型 `max(value.mises)` 只能作为定位线索。固定端尖角、点载荷、接触边缘、裂纹尖端和
材料突变处的应力可能随网格加密持续增长。报告应同时记录：

- Step/Frame、实例/区域和节点或单元标签。
- position、section point、坐标系和平均方式。
- 原始最大值与排除已知奇异区后的稳健指标。
- 至少三档网格的原始峰值和稳健指标趋势。

## History output

History region 名称由模型和求解过程产生，不能猜。先列出 repository，再读取所需变量的
`data` 序列。显式能量、监测点响应和反力历程应保留时间值，而不是只取数组最大值。

## 最小结果证据

每项最终数值至少携带：ODB 路径、Job、Step、Frame/时间、region、变量、component 或
invariant、position、坐标系、平均方式和提取方法。需要声称可信/合格时，把这些数据交给
`scripts/evaluate_result_evidence.py`，不能仅凭脚本执行成功下结论。
