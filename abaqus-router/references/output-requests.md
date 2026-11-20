# Abaqus 输出请求

输出请求必须从 `analysis_spec.outputs` 和验收指标反推，避免依赖默认 PRESELECT，也不默认
使用 ALL。输出不足无法验证，输出过多会显著放大 ODB 和运行时间。

## Field 与 History

| 类型 | 用途 | 典型范围 |
|---|---|---|
| Field output | 云图、空间分布、区域极值 | 全模型或有限区域的多个 Frame |
| History output | 时间/频率序列、能量、监测点 | 指定 Set、Surface、Interaction 或 MODEL |

在 Scripting Reference（`abaqus doc` 或 https://help.3ds.com/）中核对：

- `Model.FieldOutputRequest(name, createStepName, ...)`
- `Model.HistoryOutputRequest(name, createStepName, ...)`

两者的 `variables/region/frequency/timeInterval/numIntervals` 含义相近但不是任意组合。写入前
打开对应的 Scripting Reference 页，且不要把一个方法的专用参数搬到另一个方法。

## 变量按分析规划

- 静力：按任务选择 `U/S/RF`；力平衡需要反力证据。
- 模态：`U` 用于振型；频率读取 Frame 的 `frequency/mode` 元数据，不从描述文本解析。
- 动力：`U/S/V/A`，塑性时按需加 `PEEQ`。
- 显式能量：使用 MODEL 范围的 history outputs，例如 `ALLKE/ALLIE/ETOTAL/ALLAE/ALLWK`。
- 热：`NT/NT11/HFL`，按平衡要求选择反应热流。
- 接触：按过程支持情况选择 `CSTRESS/CPRESS/CDISP/COPEN/CSLIP`。

变量名是否有效取决于过程、单元、材料和输出域。文档中的列表是规划候选，不是存在性
保证；求解后必须检查 ODB 的实际 `fieldOutputs/historyOutputs`。

## 频率和文件规模

- `frequency=1` 表示每个增量写出，不是“平衡设置”。
- `numIntervals` 控制目标间隔数；动态峰值问题还要考虑输出采样能否解析目标频率。
- `LAST_INCREMENT` 只适合确实只需要终态的指标。
- 限定 region、变量和 section point 通常比事后删除 ODB 更安全。
- 修改已有默认请求前先检查名称和当前变量；不要假定一定叫 `F-Output-1/H-Output-1`。

## 输出位置与平均

应力等单元结果要在规格中明确 integration point、centroidal、element-nodal 或 averaged-at-
nodes。位置和平均方式会改变极值，不能在后处理阶段静默切换。壳/复合材料还要明确
section point。

## 提交前检查

- 输出请求创建在正确 Step，引用的 region 非空。
- 验收指标所需变量都已请求。
- 显式能量使用 HistoryOutput，而不是假定一个通用 `ENER` 场变量。
- 输出间隔覆盖事件关键时刻，不因追求小 ODB 丢失峰值。
- 预计 ODB 规模与磁盘空间可接受。
