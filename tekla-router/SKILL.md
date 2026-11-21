---
name: tekla
version: 1.0.6
display_name: Tekla
display_name_en: Tekla
description: 实现对活动状态下 Tekla Structures 实例的编程控制与模型交互，支持结构构件建模（梁、柱、斜撑、板）、节点细部连接（加劲肋、螺栓群、焊缝）、官方标准组件参数化调用及图纸自动化。
description_zh: 实现对活动状态下 Tekla Structures 实例的编程控制与模型交互，支持结构构件建模（梁、柱、斜撑、板）、节点细部连接（加劲肋、螺栓群、焊缝）、官方标准组件参数化调用及图纸自动化。
description_en: Programmatic control and model interaction with active Tekla Structures instances, supporting structural modeling (beams, columns, braces, plates), steel detailing (stiffeners, bolt arrays, welds), official standard component workflows, and drawing automation.
license: Apache-2.0
---

## 工作流

在 `python_executor` 的当前 work 线程内连接已运行 Tekla → 取得程序实际年度版本 → 按该版本渐进检索 API → 按用户要求完成模型创建、读取、修改和工程自动化等任务。

需要创建或修改模型时，读取 ``。

需要创建、修改或排查 Tekla 节点及组件（包括连接、细部、宏和自定义组件）的代码示例，读取 ``。

## 1. 连接Tekla

连接必须发生在 `python_executor` 内。它按会话保留一个常驻子进程，CLR、导入的 Tekla 类型、`tekla` 和 `model` 会在后续调用中继续存在。

```python
from PKPMAgent.software_link_kit.tekla import connect_tekla

tekla = connect_tekla()
model = tekla.model
print({"connected": model.GetConnectionStatus(),
       "version": tekla.program_version,
       "api_year": tekla.api_year})
```

- 只连接已经运行且已打开模型的 Tekla，不自动启动软件。
- `connect_tekla()` 已按运行实例锁定年度、以绝对路径初始化并加载程序集且校验实际连接版本；不要在 work 线程自行调用 `clr.AddReference(...)` 替代连接，以免按程序集名绑定到错误年度，连接后只需用 `from Tekla... import ...` 显式导入任务所需类型。
- 后续先检查 `model.GetConnectionStatus()`；仍为 `True` 时复用对象，不要反复初始化 CLR。若为 `False`，只重新执行一次 `connect_tekla()`；仍未连接则停止并报告，不要循环重试。

## 2. 版本铁律

- 数据库支持 Tekla 2020–2026。
- API 查询默认读取当前任务 workspace 中由连接写入的 `tekla_env.json`，查询输出中的 `query_version` 必须等于 `tekla.api_year`。
- 不得在版本未知时查询或编写调用代码。遇到不支持的版本时停止实时操作并告知用户；经用户明确同意后，可以相邻版本的 API 说明作为参考，但相邻版本可能存在类型、成员或重载差异，不得据此直接执行创建、修改或删除。
- `--version` 只用于明确的离线查询或测试，正常连接流程不要手填版本。


## 3. 查询 API 函数 —— 渐进式检索

**按版本和层级逐步缩小范围，不要一步列出整棵类型树、整个继承链或一个类下所有成员的详情。**
查询分为目录与详情：目录脚本只返回名称、种类、定位键、重载数和必要的目录元信息；只有选定唯一 `symbol_key` 后，才调用 `get_api_detail.py` 加载一个 API 的正文。
除命名空间目录固定一次返回全部外，其他目录支持各自帮助中列出的筛选和分页参数；输出有 next_offset 时按需翻页。目标已知时可以从相应步骤开始，不必机械地从命名空间重走。

### Step 0: 锁定当前 API 版本

连接 Tekla 后，以 `tekla.api_year` 和写入当前任务 workspace 的 `tekla_env.json` 为本次查询上下文。正常连接流程省略 `--version`；只有明确的离线查询或测试才手工指定。查询输出中的 `query_version` 必须与实际连接版本一致。

### Step 1: 确定命名空间

一次列出当前版本的全部命名空间：

```text
`python scripts/list_namespaces.py`
```

`list_namespaces.py` 不接受名称筛选或分页参数。根据任务确定目标命名空间，并保留输出中的精确 `N:` 键供下一步使用。

### Step 2: 确定目标类型

用 `list_types.py` 查询某个命名空间或类型下面直属的 `class`、`interface`、`structure`、`enumeration` 或 `delegate`：

```text
`python scripts/list_types.py`
```

类型可以包含嵌套类型。需要继续深入时，把当前类型的 `T:` 键作为新的父节点再次查询；每次只进入一层：

```text
`python scripts/list_types.py`
```

必须区分两种关系：

- `list_types.py` 查询命名空间或类型的**包含/嵌套关系**；
- `list_type_relations.py` 查询类型的**直属基类或直属接口关系**。

需要观察继承结构时，每次只查看一层：

```text
`python scripts/list_type_relations.py`
`python scripts/list_type_relations.py`
```

### Step 3: 确定目标成员及其声明位置

先用 `list_type_members.py` 查询目标类型自身直接声明的 `method`、`property`、`field`、`event`、`constructor` 或 `operator`：

```text
`python scripts/list_type_members.py`
`python scripts/list_type_members.py`
```

成员目录不自动混入基类和接口成员。已经知道准确成员名，但当前类型的直属目录未命中，或需要确认成员真正声明在哪个基类/接口上时，才使用 `resolve_member.py`：

```text
`python scripts/resolve_member.py`
```

`type` 参数填写代码中实际使用成员的对象类型，不要预先猜声明类型。结果中的 `declared_on` 是真实声明类型，`via` 是从实际类型到声明类型的继承路径，唯一 `symbol_key` 是后续详情查询的准确入口。`resolve_member.py` 是继承成员的定点解析工具，不用于模糊搜索，也不需要对每个直属成员重复调用。

构造函数和运算符不参与继承成员定位；即使脚本接受相应 `kind`，也应直接从实际声明类型的直属成员目录和重载目录查询，不使用 `resolve_member.py` 沿继承关系查找。

### Step 4: 选择重载并查询单项详情

目录结果若直接给出唯一 `symbol_key`，可进入单项详情。若返回 `overloads=N`，必须先用真实声明类型调用 `list_member_overloads.py`，取得紧凑的完整签名：

```text
`python scripts/list_member_overloads.py`
```

不得猜测参数，不得一次读取全部重载正文。选定完成任务所需的唯一签名后，再查询该项详情：

```text
`python scripts/get_api_detail.py`"')
```

`get_api_detail.py` 适用于类型、方法、属性、字段、事件、构造函数和运算符。枚举成员名称和值由 Step 5 一次取得，不要为此逐项查询详情。以返回的 C# 声明、参数、返回值、异常和版本范围为准；示例仅在 Tekla 原始文档包含时才会出现。

### Step 5: 查询枚举成员和值

确定一个 `enumeration` 类型后，用 `list_enum_members_details.py` 一次列出枚举成员名称及其整数值：

```text
`python scripts/list_enum_members_details.py`
```

输出为 `- MEMBER_NAME = VALUE`。脚本默认最多返回 100 项，若输出仍有 `next_offset`，再按该偏移量继续查询。

### Step 6: 兜底全文搜索

只有命名空间、类型位置或准确成员名不明确时，才使用 `search_api.py` 按 API 名称或英文文档关键词定位候选：

```text
`python scripts/search_api.py`
`python scripts/search_api.py`
```

搜索结果只是旁路候选，不是最终 API 证据。命中类型后回到 Step 2，命中成员后回到 Step 3；只有取得唯一完整 `symbol_key` 后，才进入 Step 4 查询详情。

### 补充说明：查询脚本详细参数

`--contains` 是可选的目录缩小工具，不是固定步骤。目标名称较明确或预计目录较大时可以使用；需要观察完整直属目录时应省略。请根据当前任务决定是否传入，不要为了套用示例而机械添加。`list_namespaces.py` 固定返回全部命名空间，不支持该参数。

| 检索层级 | 脚本 | 查询范围与返回内容 | 参数（全部） | 示例 |
|---|---|---|---|---|
| 版本入口 | `list_versions.py` | 列出数据库支持的 Tekla 年度版本及各版本 API 条目数；不查询 API 符号详情。 | 无参数。 | ``python scripts/list_versions.py`` |
| 一级：命名空间目录 | `list_namespaces.py` | 一次列出指定版本中的全部命名空间名称和 `N:` 符号键；不筛选、不分页，也不列类型、成员或详情。 | `--version VERSION`：可选，Tekla 版本；省略时读取当前任务 workspace 中的 `tekla_env.json`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_namespaces.py`` |
| 二级：直属类型目录 | `list_types.py` | 只列出某个命名空间或类型下面指定种类的直属类型；不递归列后代类型，不查询属性、方法或详情。 | `parent`：必填位置参数；父命名空间或父类型，可传精确 `N:` / `T:` 键、完整命名空间名或完整类型名。<br>`--kind KIND`：必填；`class`、`interface`、`structure`、`enumeration`、`delegate`，另接受 `struct`、`enum` 别名。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--contains TEXT`：可选；需要按名称缩小目录时使用，省略则返回该种类的完整直属目录。<br>`--limit N`：可选，`1–100`，默认 `50`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_types.py`` |
| 三级：直属成员名目录 | `list_type_members.py` | 只列出某个类型自身声明的指定种类成员名称；同名重载只显示成员名和重载数量，不加载签名详情或正文，也不自动列继承成员。 | `type`：必填位置参数；完整类型名或无歧义的短类型名。<br>`--kind KIND`：必填；`method`、`property`、`field`、`event`、`constructor`、`operator`。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--contains TEXT`：可选；需要按成员名缩小目录时使用，省略则返回该种类的完整直属成员目录。<br>`--limit N`：可选，`1–100`，默认 `50`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_type_members.py`` |
| 三级：枚举成员和值 | `list_enum_members_details.py` | 一次列出一个已确定枚举的成员名称和整数值，格式为 `MEMBER_NAME = VALUE`；不返回冗长的 `F:` 键。 | `enum`：必填位置参数；枚举完整类型名或精确 `T:` 键。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--contains TEXT`：可选；需要按枚举成员名缩小结果时使用，省略则返回完整枚举。<br>`--limit N`：可选，`1–100`，默认 `100`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_enum_members_details.py`` |
| 关系辅助：直属继承关系 | `list_type_relations.py` | 只列出某个类型的直属基类或直属接口；不递归展开完整继承图，不查询成员详情。 | `type`：必填位置参数；完整类型名或精确 `T:` 键。<br>`--kind {base,interface}`：必填；`base` 查询直属基类，`interface` 查询直属接口。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--contains TEXT`：可选；目标关系较多时可按目标类型名缩小目录，省略则返回完整直属关系目录。<br>`--limit N`：可选，`1–100`，默认 `50`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_type_relations.py`` |
| 关系辅助：继承成员定位 | `resolve_member.py` | 从实际使用该成员的类型出发，按当前版本沿基类和接口关系查找一个精确成员名，返回声明类型、到达路径、重载数量或唯一符号键；不加载成员正文。 | `type`：必填位置参数；实际使用成员的类型。<br>`member`：必填位置参数；精确成员名。<br>`--kind KIND`：必填；`method`、`property`、`field`、`event`、`constructor`、`operator`。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--limit N`：可选，`1–100`，默认 `50`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/resolve_member.py`` |
| 三级扩展：重载签名目录 | `list_member_overloads.py` | 对已确定的声明类型和成员名列出所有精确重载签名及符号键；只返回签名目录，不加载每个重载的文档正文。 | `type`：必填位置参数；成员的完整声明类型名或精确 `T:` 键。<br>`member`：必填位置参数；由成员目录或继承解析得到的精确成员名。<br>`--kind KIND`：可选；`method`、`property`、`constructor`、`operator`，默认 `method`。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--limit N`：可选，`1–100`，默认 `50`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/list_member_overloads.py`` |
| 四级：单个 API 详情 | `get_api_detail.py` | 只加载一个已确定 API 符号的完整文档，包括类型、可用版本、摘要、语法、参数、返回值等；不会批量加载一个类下所有成员的详情，枚举名称和值改用 `list_enum_members_details.py`。 | `symbol_key`：必填位置参数；精确 Microsoft Help ID，例如 `T:`、`M:`、`P:`；方法重载必须包含完整参数签名。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`-h, --help`：显示帮助。 | ``python scripts/get_api_detail.py`` |
| 兜底入口：关键词搜索 | `search_api.py` | 当命名空间、类型或成员位置未知时，按 API 名称或英文文档关键词搜索，只返回紧凑候选目录；不直接加载候选项详情。 | `query`：必填位置参数；API 名称或英文文档关键词。<br>`--version VERSION`：可选，省略时读取环境缓存。<br>`--limit N`：可选，`1–100`，默认 `10`。<br>`--offset N`：可选，默认 `0`。<br>`-h, --help`：显示帮助。 | ``python scripts/search_api.py`` |

## 4. 可靠执行闭环

### 4.1 明确任务边界与成功条件

执行前明确对象范围、只读或修改性质、预期输出和完整性要求。只读任务不得调用 `Insert()`、`Modify()`、`Delete()` 或 `CommitChanges()`；创建或修改模型时先读取 `references/common_examples.md`，遵守其中的 Catalog、提交、清理和单位规则。

### 4.2 确认 API 契约

以渐进式查询得到的 API 详情为调用依据，确认声明类型、成员名称、精确重载、参数、返回值、异常和调用前提。不得依据相似名称、用途、继承关系或其他类型的用法推断成员；搜索结果和示例只用于定位候选，不能代替 API 详情。运行报错只能证明当前写法失败，不能证明接口结构。

### 4.3 构造符合 CLR 契约的调用

按已确认的签名构造 pythonnet 参数，不依赖未经验证的隐式转换：使用实际的 .NET 枚举而非裸整数，区分 Python `type` 与 `System.Type`，并按要求创建强类型数组及其他 CLR 对象。文档确定调用契约，最小运行负责验证 pythonnet 中的实际调用形状。

### 4.4 从最小闭环扩大到批量执行

先在一个对象或最小范围内验证连接与上下文、返回类型和可观察的业务结果，通过后再扩大到批量对象或完整模型。不得把草稿、占位调用或未经验证的分支混入批量脚本。

缓存、懒加载、过滤和批处理设置可能改变数据完整性或刷新时机；启用前先建立默认正确性基线，再对比关键结果。批量任务中的局部失败必须记录对象标识、操作和异常，并将整体结果标记为不完整；不得用空字符串、零、`None` 或无记录的 `except Exception: pass` 掩盖失败，只有 API 契约确认可选时才能提供默认值。

### 4.5 验证结果并限定结论

脚本无异常只代表执行结束，不代表任务成功。按预先定义的成功条件检查相关布尔返回值、对象数量与范围、字段一致性及必要的重新查询结果。结果为空、为零、明显过少或前后矛盾时，先检查连接与调用上下文、数据加载、过滤、缓存和优化设置，不得直接解释为模型没有数据。

最终结论不得超过实际验证范围：只检查部分对象时不声称覆盖整个模型；存在跳过项或局部失败时明确报告结果不完整；未经验证的推测不得描述成 API 事实。