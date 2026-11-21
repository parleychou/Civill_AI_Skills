# `analysis_spec` 分析任务契约

在创建分析步、提交 Job 或解释结果前，用一个结构化 `analysis_spec` 固定用户要求。
它是任务契约，不是 Abaqus 输入文件，也不能代替后续的版本化 API 契约查询。

## 使用时机

- 纯查询、纯几何编辑或只查看模型时不强制创建。
- 完整分析任务、提交 Job、提取并判定结果时必须创建或沿用同一份规格。
- 不提交 Job、不宣称分析正确的独立材料、网格或载荷修改，不强制建立完整规格。
- 信息不足时保留缺项并报告，不能自行补材料、单位、边界条件、接触、`nlgeom` 或验收阈值。

机器可读约束见 `references/analysis-spec.schema.json`。将规格保存为 JSON 后运行：

```text
`python scripts/validate_analysis_spec.py analysis_spec.json`
```

该调用一次完成结构规范化和按分析类型的工程语义检查。分析配置完成后、首次提交 Job 前
运行一次；规格变化后，只在下一次提交或结果判定前重新运行，不在每个建模里程碑重复运行。

- `PASS`：现有规格证据通过全部规则，不表示求解结果已经验证正确。
- `WARN`：配置可能合法，但需要用户或工程依据确认；不能自动修改。
- `FAIL`：存在确定缺项、未知字段或内部矛盾，停止写入或提交。
- `UNSUPPORTED`：规则集未覆盖该求解过程，不能套用相近分析类型。

退出码 `0` 对应 `PASS/WARN`，退出码 `2` 对应 `FAIL/UNSUPPORTED`。判断流程状态时读取
JSON 顶层 `status`，不能仅依赖退出码。

## 顶层字段

| 字段 | 含义 | 关键约束 |
|---|---|---|
| `schema_version` | 契约版本 | 当前固定为 `1.0` |
| `analysis_type` | 求解过程 | 使用 schema 中的规范值 |
| `units` | 一致单位约定 | 明确长度、力、质量、时间和温度单位 |
| `materials` | 材料与指派意图 | 分析允许无材料时显式写 `[]`，不能省略 |
| `geometry` | 零件/实例/现有模型引用 | 至少一项，选区写入 `regions` |
| `steps` | 分析步及其关键参数 | 至少一项，`kind` 应对应预期求解过程 |
| `boundary_conditions` | 约束和边界条件 | 自由模态等无约束任务显式写 `[]` |
| `connections` | Tie、耦合、接触等 | 无连接时显式写 `[]` |
| `loads` | 荷载、预定义场、初始条件 | 无载荷的模态分析写 `[]` |
| `mesh` | 几何与单元库/单元类型映射 | 解析刚体可使用 `NONE` 和空单元列表 |
| `outputs` | 所需场输出/历史输出 | 至少一项，变量名必须显式列出 |
| `acceptance_criteria` | 可判定的验收条件 | 至少一项；最低限度可检查求解终态 |

`name`、`model_name`、`job_name` 和 `metadata` 是可选追踪字段。类别对象不认识的扩展数据
放进其 `parameters`、`properties` 或顶层 `metadata`，不要添加近似拼写的新字段。

传给 Abaqus `name=` 的名称必须先满足 CAE 官方命名规范，不能因为内核 repository 暂时
接受就视为合法：名称不得以下划线或空格开头/结尾，不得包含句点、双引号或反斜杠，
`Assembly` 为保留名；Model/Job 的数字开头例外和额外禁用字符分别处理。Part、Model、
Instance、Set、Surface、Feature、Job 最长 80 字符，其他对象通常最长 38 字符。普通
Python 变量名、`mesh.id` 和验收准则 ID 不属于 Abaqus 对象名，不套用这组规则。

## 分析类型

规范值为：

- `static`
- `modal`
- `dynamic_implicit`
- `dynamic_explicit`
- `heat_transfer_steady`
- `heat_transfer_transient`
- `coupled_temp_displacement`

接触是分析特征，不是求解过程。接触静力问题应写 `analysis_type: "static"`，并在
`connections` 中加入 `kind: "contact"`；不要把 `contact` 填入 `analysis_type`。

## 按分析类型执行的检查

| 分析类型 | 重点检查 |
|---|---|
| 静力 | StaticStep、Standard 单元、材料指派、本构、刚体位移控制、荷载路径 |
| 模态 | FrequencyStep、弹性与密度、Standard 单元、自由/约束边界意图、振型输出 |
| 隐式动力 | ImplicitDynamicsStep、密度、Standard 单元、正的事件时长和动力激励 |
| 显式动力 | ExplicitDynamicsStep、密度、Explicit 单元、事件时长、激励、能量历史、质量缩放证据 |
| 稳态热 | HeatTransferStep、导热系数、热单元、热边界/热源、温度输出 |
| 瞬态热 | 稳态热检查项，再加密度、比热和正的持续时间 |
| 温度—位移耦合 | 耦合分析步、热—力材料属性、耦合单元、热边界、力学约束、U/NT 输出 |
| 接触附加检查 | 接触属性、接触形式、接触面角色、初始间隙、接触输出、有限滑移的 nlgeom 决策 |

接触检查与主分析类型叠加。例如接触静力同时执行静力和接触规则；接触本身不是
`analysis_type`。

### 容易误判的边界

- 自由—自由模态允许 `boundary_conditions: []`，但必须在 FrequencyStep 的
  `parameters.boundary_mode` 中明确写 `free_free`。
- 模态不要求普通外载荷；发现外载荷只给警告，不把它当成模态激励。
- 解析/离散刚体可以没有材料和网格；混合模型只对可变形几何要求材料指派和单元。
- 塑性或接触本身不等于必须 `nlgeom=ON`；有限滑移且关闭时给出风险警告，但不自动修改。
- 瞬态热必须同时有密度和比热，稳态热不套用该要求。
- 接触对采用 main/secondary 面；general contact 不强制 master/slave。
- 校验只检查规格证据。集合是否为空、截面是否实际指派、Job 消息和 ODB 字段是否存在，
  由后续模型、Job 和 ODB 检查器确认。

## 最小示例

```json
{
  "schema_version": "1.0",
  "name": "cantilever-static",
  "analysis_type": "static",
  "units": {
    "system": "N-mm-s-tonne-degC",
    "length": "mm",
    "force": "N",
    "mass": "tonne",
    "time": "s",
    "temperature": "degC"
  },
  "materials": [
    {
      "id": "steel",
      "kind": "elastic_isotropic",
      "properties": {"youngs_modulus": 210000.0, "poisson_ratio": 0.3}
    }
  ],
  "geometry": [
    {
      "id": "beam",
      "kind": "solid",
      "source": "parametric",
      "parameters": {"length": 1000.0, "width": 50.0, "height": 100.0},
      "regions": ["FIXED_END", "TIP"]
    }
  ],
  "steps": [
    {
      "id": "LoadStep",
      "kind": "StaticStep",
      "previous": "Initial",
      "parameters": {"nlgeom": false, "timePeriod": 1.0}
    }
  ],
  "boundary_conditions": [
    {
      "id": "fixed-end",
      "kind": "EncastreBC",
      "step": "Initial",
      "region": "FIXED_END"
    }
  ],
  "connections": [],
  "loads": [
    {
      "id": "tip-force",
      "kind": "concentrated_force",
      "step": "LoadStep",
      "region": "TIP",
      "components": {"cf2": -1000.0}
    }
  ],
  "mesh": [
    {
      "id": "beam-mesh",
      "geometry": "beam",
      "element_library": "STANDARD",
      "element_types": ["C3D8R"],
      "seed": 20.0
    }
  ],
  "outputs": [
    {
      "id": "main-field",
      "kind": "field",
      "variables": ["U", "S", "RF"],
      "step": "LoadStep",
      "region": "MODEL"
    }
  ],
  "acceptance_criteria": [
    {
      "id": "solver-completed",
      "metric": "solver_terminal_state",
      "operator": "==",
      "limit": "COMPLETED",
      "required": true
    },
    {
      "id": "tip-displacement",
      "metric": "displacement_magnitude",
      "operator": "<=",
      "limit": 5.0,
      "unit": "mm",
      "region": "TIP",
      "source": "design requirement",
      "required": true
    }
  ]
}
```

## 不可静默处理的细节

- Abaqus 不保存或转换单位制；`system` 只是项目标签，各物理量仍须量纲自洽。
- 材料密度、比热、导热系数等数值保留用户原值，规范化脚本不做单位换算。
- `loads: []` 可能是合法的自由模态；`materials: []` 可能是合法的解析刚体。是否合理由
  同一次校验中的分析类型规则判断，不能在结构规范化阶段一刀切。
- 自由—自由模态必须把 `boundary_conditions` 明确写成 `[]`；不能因列表为空就自动补固定约束。
- `element_library` 只接受 `STANDARD`、`EXPLICIT` 或 `NONE`。规范化器会统一大小写，
  但不会替换单元类型。
- `outputs` 写用户要判定的量；不能因为 Abaqus 有默认输出就省略。
- 验收阈值必须带来源。没有设计阈值时可只保留 `solver_terminal_state`，但不能把经验值冒充
  设计许用值。
