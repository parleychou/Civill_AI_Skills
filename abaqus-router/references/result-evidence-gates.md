# 结果证据门禁

求解器返回 `COMPLETED` 只说明计算走到终态，不等于结果可信。先用 ODB 检查器确认实际可用
字段，再把确定性提取所得的数值整理成 `result-evidence.schema.json`，运行：

```text
`python scripts/evaluate_result_evidence.py analysis_spec.json result_evidence.json`
```

门禁会从原始向量/序列/网格样本重新计算指标，不接受“已平衡”“已收敛”之类的文本结论。
任一必需证据缺失、阈值没有来源或指标越界，顶层结果为 `FAIL`。只有经过至少两组
受控复现、记录 Abaqus 版本/运行模式/诊断且提供替代证据时，缺失证据才可标为
`BLOCKED_BY_ENVIRONMENT`；它表示环境能力阻断，**不是 PASS，也不能证明结果可信**。

`environment_limitations` 中每项必须列出受影响的 `gate_ids`、能力、原因、环境、至少两次
配置不同的失败尝试及其诊断位置，以及可供人工复核的替代证据。该状态只能用于环境无法
生成的缺失证据，不能覆盖求解错误、已有数值越界或观察到的接触状态不符。

## 证据层次

1. `provenance`：ODB 路径、Step、Frame、区域、坐标系、输出位置、平均方式和提取器。
2. `solver`：终态、分析错误数、警告数和诊断行。
3. `equilibrium`：同一坐标系、同一参考点下的外力/反力和外力矩/反力矩。
4. `energy`：显式分析的 ALLKE、ALLIE、ETOTAL，建议同时提供 ALLAE。
5. `contact`：实际可用接触字段、活动点数、穿透/滑移等。
6. `mesh_convergence`：按粗到细顺序给出至少两档网格的目标量。
7. `stress_singularity`：至少三档网格的原始最大应力与远离奇异点的稳健指标。

## 分析画像与必需门禁

| 分析画像 | 必需证据 |
|---|---|
| 全部 | provenance、求解终态、网格收敛 |
| 静力、温度-位移耦合 | 再加力平衡、关于指定参考点的力矩平衡 |
| 显式动力 | 再加能量平衡；有 ALLAE 时校核人工能比例 |
| 含接触 | 再加接触输出和预期接触状态 |
| 静力/耦合且声明 S 输出 | 再加奇异性与稳健应力网格研究 |

## 阈值规则

- 所有数值阈值来自 `analysis_spec.acceptance_criteria`，证据项用 `criterion_id` 引用。
- criterion 的 `metric` 必须与脚本计算的指标一致，并必须填写 `source`。
- Skill 不内置“力平衡 0.5%”“网格变化 3%”作为设计许用值。团队规范、试验、规范条文或
  经批准的数值分析方案可以提供这些阈值，但要明确来源。
- `review` 运算符需要人工判断，不能自动通过。

常用 metric 名称：

- `force_balance_relative_error`
- `moment_balance_relative_error`
- `energy_balance_relative_error`
- `artificial_energy_ratio`
- `kinetic_internal_ratio_final`
- `max_contact_penetration`
- `max_contact_slip`
- `min_contact_active_fraction`
- `mesh_convergence.<evidence.metric>`
- `stress_robust_mesh_change.<region>`

## 计算细节

- 力/力矩残差按 `applied + reaction` 计算，相对误差的尺度取两者范数与显式提供的
  characteristic value 的最大值。零尺度不会被伪装成 0% 误差。
- 力矩必须在同一参考点计算；反力产生的 `r × RF` 和节点 `RM` 应在证据提取时合并。
- 显式能量漂移按 ETOTAL 相对初始值的最大偏移除以 `|ALLIE|+|ALLKE|` 的最大尺度计算。
- 网格样本必须按粗到细排列且 `mesh_size` 严格递减，比较最后两档相对变化。
- 若原始最大应力随加密持续增长而稳健指标收敛，门禁标记疑似奇异并令
  `raw_max_usable=false`；不能拿该原始最大值做强度验收。
