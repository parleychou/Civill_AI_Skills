---
name: abaqus
version: 1.0.5
display_name: Abaqus
display_name_en: Abaqus
description: 提供对 Abaqus/SIMULIA 有限元分析全流程的自动化控制能力，涵盖几何建模、非线性材料、网格剖分、接触设定、分析步工况与求解计算及 ODB 后处理，配备完整的 18 项核心专业规约参考手册与结果证据门禁校验体系。
description_zh: 提供对 Abaqus/SIMULIA 有限元分析全流程的自动化控制能力，涵盖几何建模、非线性材料、网格剖分、接触设定、分析步工况与求解计算及 ODB 后处理，配备完整的 18 项核心专业规约参考手册与结果证据门禁校验体系。
description_en: Provides comprehensive automation for SIMULIA Abaqus finite element analysis, covering geometry modeling, nonlinear materials, meshing, contact interactions, load steps, and ODB post-processing, equipped with 18 core reference specifications and result verification gates.
license: Apache-2.0
---

# Abaqus Link

## 工作流

连接 Abaqus → 明确本轮任务 → 查询所需 API → 编写并执行一个完整里程碑 → 返回结果并停止。

### Step 1：连接 Abaqus

先在 `python_executor` 中建立或复用 Abaqus 连接，并取得实际版本：

```python
import json
import os
from PKPMAgent import abaqus

connection = abaqus.connect(workspace_dir=os.getcwd())
print(json.dumps(connection, ensure_ascii=False, default=str))
```

`ok` 为 `false` 时报告连接错误并停止。连接成功后，后续 API 查询自动使用返回的 Abaqus 版本。

### Step 2：明确本轮任务

先确定本轮属于查询、建模、修改、划分网格、分析设置、提交作业、查询状态还是读取结果。复杂任务拆成有明确结果的里程碑，每次只执行当前里程碑。

- 完整分析任务、提交 Job、提取并判定结果时，读取 `references/analysis-spec.md`，建立或沿用同一份 `analysis_spec`。纯查询、纯几何编辑以及不提交 Job、不宣称分析正确的独立建模里程碑不强制创建。
- `analysis_spec` 必须显式记录分析类型、单位、材料、几何、分析步、边界条件、连接、载荷、网格、输出和验收标准。结构校验失败时报告缺项并停止，不能自行补材料、单位、边界条件、接触、`nlgeom` 或验收阈值。
- 分析配置完成后、首次提交 Job 前，运行一次 `scripts/validate_analysis_spec.py`；规格发生变化时，只在后续提交或结果判定前重新运行，不在每个几何、材料或网格里程碑重复校验。`FAIL` 或 `UNSUPPORTED` 时停止；`WARN` 必须连同证据交给用户判断。
- 修改已有模型时，只有目标名称或当前状态会影响脚本且无法在写入前安全判断，才先建立一个只读查询里程碑。
- 用户说“在某模型中”时按已有模型处理；如果该模型不存在，报告不存在，不自行创建同名模型。
- 新建对象时，在写入脚本中检查名称冲突，不默认覆盖已有对象。
- 只执行用户当前要求包含的阶段，不自行扩展到提交作业、读取结果或关闭 Abaqus。

### Step 3：查询所需 API

写脚本前，列出当前脚本会使用的全部 Abaqus 方法、属性和 repository。把已知规范符号和未知操作合并到一次 `scripts/retrieve_api_bundle.py` 调用中，取回当前版本的完整契约：

```text
`python scripts/retrieve_api_bundle.py --hint Mdb.Model --hint Model.ConstrainedSketch --hint ConstrainedSketch.rectangle --hint Model.Part --hint Part.BaseSolidExtrude --hint Part.faces --hint FaceArray.getByBoundingBox --hint Part.Set`
```

- 已知规范符号时必须使用 `--hint Receiver.symbol`。方法、属性和 repository 都通过 `--hint` 验证；同一符号不再重复写成 `--need`。
- 只有不知道规范符号时才使用 `--need`。每个 `--need` 只描述一个操作，并写明接收对象和动作，例如 `--need "method on FaceArray that selects faces inside a bounding box"`；禁止把“选择面并创建集合”合成一个 need。
- 当前脚本的全部 `--hint` 和 `--need` 在首次 bundle 调用中一并提交；编写过程中只有出现此前无法识别的具体操作时，才追加定向查询。
- 名称是否存在、条件判断、循环和结果组装属于普通脚本逻辑，不作为 `--need` 提交。
- `VERIFIED hint` 可以直接使用其完整契约；`UNVERIFIED` 符号禁止写入脚本。
- 对 `--need` 返回的候选，根据接收对象、用途和参数重载选择；候选排名不是最终答案。选中的候选已经附带完整契约，不再重复查询。

按检索结果执行下列动作；禁止枚举模块或模块方法：

```text
`python scripts/get_api_detail.py --call Part.BaseSolidExtrude`
`python scripts/get_api_detail.py --member Part.cells`
`python scripts/get_api_detail.py --search-calls `
`python scripts/get_api_detail.py --search-members `
```

- 最终代码形态为 `receiver.name(...)` 的符号一律是方法，数组选择方法也不例外，例如 `FaceArray.getByBoundingBox(...)`。已知规范名称时直接使用 `--call`，名称未知时才使用 `--search-calls`；禁止改用成员查询。
- 最终代码形态为不带调用括号的 `receiver.name`，且值是属性或 repository，才是对象成员，例如 `Part.faces`。已知规范名称时直接使用 `--member`，名称未知时才使用 `--search-members`；禁止改用方法查询。
- `scripts/retrieve_api_bundle.py` 已返回所需方法或成员的完整契约：直接使用输出中的规范符号和契约，不再查询。
- `--search-calls` 或 `--search-members` 没有返回规范候选：报告当前 Abaqus 版本的 API 数据库未找到该能力并停止，不编写或执行对应代码。
- 当前版本 API 数据库没有返回规范符号及契约的方法、属性或 repository，禁止写入 Abaqus 脚本，不凭记忆补写。

### Step 4：编写并执行脚本

一次 `abaqus.execute` 完成一个里程碑。重复构件用数据和循环表达，不拆成大量调用。

```python
import json
import os
from PKPMAgent import abaqus

abaqus_script = r'''
from abaqus import mdb, session
from abaqusConstants import *

# 当前里程碑的 Abaqus 代码

# 只有用户或下一里程碑需要业务数据时才定义 result
# result = {...}
'''

response = abaqus.execute(
    code=abaqus_script,
    timeout=120,
    workspace_dir=os.getcwd(),
)
print(json.dumps(response, ensure_ascii=False, default=str))
```

- Abaqus 脚本显式导入 `abaqusConstants`；可按需导入 `abaqus`、`odbAccess` 等模块。
- 所有传给 Abaqus `name=` 的用户可见对象名遵守官方 CAE 命名规范；内核 repository
  暂时接受但 GUI 树不可见不算成功，不主动生成 `_name`、`name_` 或 `__name`。
- 纯写操作不定义 `result`；需要返回数据时，只返回当前任务需要的最小结构化结果。
- 网格生成任务是例外：在同一次脚本中回读目标区域的 `getMeshControl`、生成后的
  `element.type` 和 `getMeshStats`。不能把 `setElementType` 成功当作实际单元类型成功，
  也不能依据 Cell 面数猜测能否结构化划分；具体规则见 `references/mesh.md`。
- 长脚本可保存为纯 Abaqus `.py` 文件，再调用 `abaqus.execute(file_path=..., workspace_dir=os.getcwd(), timeout=...)`。
- `timeout` 只控制本次脚本执行时间，不用于等待后台求解完成。

### Step 5：处理结果

- 以 `abaqus.execute` 返回的顶层 `ok/error` 判断执行状态；内层 `result` 只承载业务数据。
- 执行成功后停止，不额外截图、不查询全模型，也不另起脚本重复验证。
- 执行失败时不自动重试。先读取顶层 `error.recovery` 中的真实对象类型、可用成员、调用签名、相近参数名和 repository 键；这些是当前 Abaqus 运行时证据。
- 运行时证据足以定位对象路径、名称或参数错误时，直接报告原因和修正依据，不做宽泛 API 检索。只有仍缺少精确契约时，才针对原操作使用一次 `--call`、`--member`、`--search-calls` 或 `--search-members` 定向查询；禁止通过改写关键词连续试探。
- 如果异常前可能已经写入模型，只查询一次目标对象的实际状态，报告结果后停止连续试探。

## 补充规则

### 模型状态与文件安全

- 每次执行中的普通 Python 变量相互隔离，`mdb` 和 `session` 中的 Abaqus 模型状态会持续。
- 脚本应识别已经完成的目标，避免重复创建同名对象；但不能据此推断用户同意覆盖或删除。
- 覆盖 `.cae/.inp/.odb`、删除已有对象和关闭 Abaqus 前，必须确认这些操作属于用户要求。
- 对可能部分写入的新建任务，在同一脚本中记录本次创建的对象；仅在能安全确认对象属于本次操作时做最小回滚。

### 作业提交与结果读取

- 提交前用独立只读里程碑运行 `scripts/inspect_abaqus.py --model MODEL`，对照 `analysis_spec` 检查仓库、材料/截面、分析步和 Set/Surface 实体数量；空选区或对象缺失时不提交。
- 提交里程碑只执行 `job.submit()`，返回 `job_name/status/odb_path` 后立即停止。
- 后续里程碑可用 `scripts/inspect_abaqus.py --job JOB` 一次查询状态和 `.sta/.msg/.dat/.log` 诊断；状态未完成时报告当前值并停止。
- 只有状态为 `COMPLETED` 后才读取 ODB。
- 完成后用同一次检查调用追加 `--odb PATH`，先枚举实际 Step、Frame、field output、component、invariant 和 history output，再决定提取方式。
- 对需要判定“可信/合格”的结果，读取 `references/result-evidence-gates.md`，将确定性提取值写入 `result_evidence`，运行 `scripts/evaluate_result_evidence.py`。门禁未通过时只能报告未验证或失败，不能仅凭 `COMPLETED` 宣称结果正确。
- 聊天执行脚本不调用 `job.waitForCompletion()`，也不循环轮询状态。

### 单位约定

Abaqus 没有内建单位开关，模型中的全部数值必须自洽。

- 纯几何任务未说明长度单位时按 mm 解释，不询问 N-mm 或 kN-mm。
- 修改已有工程时沿用工程现有单位约定。
- 新工程涉及材料、密度、荷载、时间或结果解释，而单位信息不足时，再向用户确认完整的自洽单位约定。
- 最终回复说明采用的单位约定，不把 N-mm、kN-mm 描述成 Abaqus 内置选项。

### 按需参考资料

不要一次加载整个 `references` 目录。根据当前里程碑只读取需要的文档：

- 几何创建、CAD 导入、Set/Surface：`references/geometry.md`
- 材料、截面和截面指派：`references/material.md`
- 边界条件与刚体约束：`references/bc.md`
- 集中力、压力、重力和强制位移：`references/load.md`
- 分析步、非线性和增量控制：`references/step.md`
- 单元类型、种子和网格控制：`references/mesh.md`
- 完整静力流程：`references/static-analysis.md`
- 完整频率提取流程：`references/modal-analysis.md`
- 接触对、general contact、初始间隙和接触输出：`references/contact-analysis.md`
- 隐式/显式动力选择、初始速度、质量缩放和能量：`references/dynamic-analysis.md`
- 稳态/瞬态热传导、热边界、热单元和单位：`references/thermal-analysis.md`
- 顺序与完全温度—位移耦合、参考温度和映射：`references/coupled-analysis.md`
- Field/History output、变量、频率和输出位置：`references/output-requests.md`
- ODB 的 Step/Frame/region/invariant、平均和证据提取：`references/odb-results.md`
- 分析任务规格、字段约束、规范化和语义校验：`references/analysis-spec.md`
- mdb 模型仓库、选区计数、Job 诊断和 ODB 字段清单：`references/inspectors.md`
- 力/力矩、能量、接触、终态、奇异应力和网格收敛门禁：`references/result-evidence-gates.md`
- 启动、连接、API 或收敛失败：`references/troubleshooting.md`

使用 `` 读取。参考资料用于选择建模方式和组合流程；涉及的 API 方法或参数仍以当前 Abaqus 版本的查询结果为准。