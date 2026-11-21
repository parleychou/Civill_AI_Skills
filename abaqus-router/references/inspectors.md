# 模型、Job 与 ODB 只读检查器

需要确认 Abaqus 中的实际状态时，使用一次只读检查调用，不让大模型逐个猜仓库路径或 ODB
字段。检查器不会写模型、等待作业、删除 `.lck` 或覆盖文件。

```text
`python scripts/inspect_abaqus.py --workspace-dir `
```

三个参数都可选：省略 `--model` 或 `--job` 时只列出可用名称；省略 `--odb` 时不打开
ODB。相对 ODB 路径按 `--workspace-dir` 解析。只有作业已确认 `COMPLETED` 后才能在聊天
工作流中传 `--odb`。

## 返回内容

- `model.available_models`：当前 mdb 的模型名。
- `model.repositories`：材料、截面、分析步、BC、载荷、相互作用、约束、输出请求等的
  名称、类型和创建步。
- `model.parts` / `model.root_assembly`：几何与网格实体计数，以及每个 Set/Surface 的
  vertices/edges/faces/cells/nodes/elements 数量。用这些计数阻止空选区静默进入作业。
- `model.parts.items.<part>.mesh`：Part 各 Cell/Face 的实际网格控制组合、生成后的
  `element.type` 计数和 `MeshStats` 形状计数。它用于识别“指派了 C3D8R 槽位，但仍按
  `TET + FREE` 生成四面体”这类静默偏差；不能用 Cell 面数代替该回读。
- `job.job_status`：当前状态的单次快照；不轮询。
- `job.messages`：当前 Job 消息尾部。
- `job.diagnostic_files`：同工作目录下 `.sta/.msg/.dat/.log` 的受限尾部和包含
  ERROR/WARNING/FATAL/ABORT/TERMINAT 的诊断行。检查器不会读取或删除 `.lck`。
- `odb.diagnostic_data`：ODB 内记录的求解终态及分析错误/警告计数（若该版本提供）。
- `odb.steps`：每个 Step 的 frame 数、首末 frame 元数据、跨所有 frame 汇总的
  field output、component labels、valid invariants、position 和 history region/output。
- `odb.root_assembly`：实例节点/单元数，以及节点集、单元集和表面名称。

## 使用边界

- 顶层 `ok` 只说明检查脚本执行成功；业务结果还要检查内层 `result.status` 和各子项
  `status`。`PARTIAL` 通常表示请求的模型、Job 或 ODB 不存在。
- `truncated: true` 表示达到 `--max-items` 或日志行上限，不代表仓库只有返回的项目。
- `mesh.element_types.truncated: true` 表示实际单元类型只扫描了前若干单元；此时不得据此
  宣称整个 Part 的单元类型一致。
- Set/Surface 非空只证明存在实体，不证明选区方向、物理角色或载荷方向正确；仍须与
  `analysis_spec` 对照。
- ODB 字段必须先从检查结果确认，再选择 invariant 和 position。不能假定 `S` 一定有
  `MISES`，也不能假定所有 frame 拥有相同字段。
