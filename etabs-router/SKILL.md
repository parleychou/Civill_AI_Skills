---
name: etabs
version: 1.0.4
display_name: ETABS
display_name_en: ETABS
description: 基于 COM 自动化接口驱动 ETABS 开展高层与多层建筑结构有限元建模、荷载组合配置、求解计算及内力位移提取，配备完整的 ETABS Open API 渐进式检索系统与全模块接口库。
description_zh: 基于 COM 自动化接口驱动 ETABS 开展高层与多层建筑结构有限元建模、荷载组合配置、求解计算及内力位移提取，配备完整的 ETABS Open API 渐进式检索系统与全模块接口库。
description_en: Drives ETABS via COM automation for structural modeling, load combinations, finite element analysis, and internal force/displacement extraction, equipped with a progressive ETABS Open API query system and complete module database.
license: Apache-2.0
---

## 典型工作流程

1.渐进式检索获取必须的 ETABS API 函数 → 2.连接/启动ETABS，依据用户需求执行 建模/施加荷载/运行分析/提取结果/设计校核 等任务

## 查询 API 函数 - 渐进式检索

**重要**：采用渐进式检索，不要一步到位！按层级逐步缩小范围。
**脚本目录**： `scripts/` 目录下提供了查询脚本，直接执行即可获取结果。

### Step 1: 确定一级模块

Agent 应根据任务类型定位到相关模块，先判断涉及哪个一级模块。一般可以直接通过模块概览表判断。

**一级模块概览**
| 模块 | 描述 | 典型用途 |
|------|------|----------|
| **cFile** | 文件操作 | 新建/打开/保存模型文件 |
| **cAnalyze** | 分析执行 | 运行分析、设置自由度、获取分析状态 |
| **cAnalysisResults** | 结果提取 | 节点位移、框架内力、应力、反力等结果 |
| **cFrameObj** | 框架对象 | 创建/修改梁柱等框架对象 |
| **cAreaObj** | 面对象 | 创建/修改墙、板、壳等面对象 |
| **cPointObj** | 节点对象 | 节点约束、荷载、坐标操作 |
| **cLinkObj** | 连接单元 | 创建/修改连接单元 |
| **cTendonObj** | 预应力筋 | 预应力筋操作 |
| **cPropFrame** | 截面定义 | 框架截面属性定义（含SD Shape） |
| **cPropArea** | 面截面定义 | 墙板截面属性定义 |
| **cPropAreaSpring** | 面弹簧属性 | 面弹簧属性定义 |
| **cPropLineSpring** | 线弹簧属性 | 线弹簧属性定义 |
| **cPropPointSpring** | 点弹簧属性 | 点弹簧属性定义 |
| **cPropMaterial** | 材料定义 | 材料属性定义 |
| **cPropLink** | 连接属性 | 连接单元属性定义 |
| **cPropRebar** | 钢筋定义 | 钢筋属性定义 |
| **cPropTendon** | 预应力筋属性 | 预应力筋属性定义 |
| **cLoadPatterns** | 荷载模式 | 定义荷载模式 |
| **cLoadCases** | 荷载工况 | 定义荷载工况 |
| **cCombo** | 荷载组合 | 定义荷载组合 |
| **cDesignSteel** | 钢结构设计 | 钢结构设计校核 |
| **cDesignConcrete** | 混凝土设计 | 混凝土设计校核 |
| **cDesignConcreteSlab** | 混凝土板设计 | 混凝土楼板设计 |
| **cDesignCompositeBeam** | 组合梁设计 | 组合梁设计校核 |
| **cDesignCompositeColumn** | 组合柱设计 | 组合柱设计校核 |
| **cDesignShearWall** | 剪力墙设计 | 剪力墙设计校核 |
| **cDesignStrip** | 设计条带 | 楼板设计条带 |
| **cDesignForces** | 设计力 | 设计内力提取 |
| **cDesignResults** | 设计结果 | 设计结果提取 |
| **cDetailing** | 详图 | 混凝土详图设计 |
| **cSelect** | 选择操作 | 选择对象 |
| **cStory** | 楼层操作 | 楼层定义与修改 |
| **cTower** | 塔楼操作 | 塔楼定义 |
| **cGridSys** | 网格系统 | 坐标网格定义 |
| **cGroup** | 组操作 | 分组管理 |
| **cConstraint** | 约束定义 | 刚性隔板等约束 |
| **cDiaphragm** | 楼板定义 | 楼板隔板定义 |
| **cDatabaseTables** | 数据库表 | 批量读写模型数据 |
| **cPierLabel** | 墙肢标签 | 墙肢标签定义 |
| **cSpandrelLabel** | 连梁标签 | 连梁标签定义 |
| **cSapModel** | 模型根对象 | 单位设置、初始化等全局操作 |
| **cAreaElm** | 面单元 | 分析模型面单元操作 |
| **cPointElm** | 节点单元 | 分析模型节点单元操作 |
| **cLineElm** | 线单元 | 分析模型线单元操作 |
| **cHelper** | 辅助对象 | API辅助对象创建与连接 |
| **cOAPI** | API根接口 | ETABS API顶层接口 |
| **cOptions** | 选项设置 | 程序选项与偏好设置 |
| **cView** | 视图操作 | 视图控制与刷新 |
| **cAutoSeismic** | 自动地震荷载 | 自动侧向荷载定义 |
| **cFunction** | 函数定义 | 定义响应谱/时程函数 |
| **cFunctionRS** | 反应谱函数 | 反应谱函数定义 |
| **cGenDispl** | 广义位移 | 广义位移定义 |
| **cEditFrame** | 编辑框架 | 框架对象编辑操作 |
| **cEditGeneral** | 通用编辑 | 通用编辑操作（撤销/重做等） |
| **cCaseStaticLinear** | 线性静力 | 线性静力分析工况 |
| **cCaseStaticNonlinear** | 非线性静力 | 非线性静力分析工况 |
| **cCaseStaticNonlinearStaged** | 分阶段非线性静力 | 施工阶段分析 |
| **cCaseDirectHistoryLinear** | 线性直接积分时程 | 线性时程分析工况 |
| **cCaseDirectHistoryNonlinear** | 非线性直接积分时程 | 非线性时程分析工况 |
| **cCaseModalEigen** | 特征值模态 | 特征值模态分析 |
| **cCaseModalRitz** | Ritz模态 | Ritz向量模态分析 |
| **cCaseModalHistoryLinear** | 线性模态时程 | 线性模态时程分析 |
| **cCaseModalHistoryNonlinear** | 非线性模态时程 | 非线性模态时程分析 |
| **cCaseResponseSpectrum** | 反应谱 | 反应谱分析工况 |
| **cCaseHyperStatic** | 超静定工况 | 超静定分析 |
| **cDConcreteShellDesignRequest** | 混凝土壳设计请求 | 混凝土壳设计 |
| **cPluginCallback** | 插件回调 | ETABS插件回调接口 |
| **cPluginContract** | 插件合约 | ETABS插件合约接口 |
| **Code** | 代码枚举 | API辅助代码定义 |
| **Enumeration** | 枚举类型 | 枚举常量定义 |

如需查看所有一级模块：
```bash
python scripts/list_top_modules.py
```
 **注意**：模块概览表中的 Code 和 Enumeration 比较特殊。Code 模块包含各国设计规范（如中国混凝土规范 `Code/cDCoChinese_2010`），Enumeration 模块包含所有枚举常量定义。它们的查询路径与普通模块不同，详见下方各 Step 说明。

### Step 2: 查看模块的子模块
查看指定模块下的**子模块**：
仅Code和Enumeration有子模块，其余模块无子模块。
```bash
python scripts/list_submodules.py <module_path>

# 示例
python scripts/list_submodules.py "Code"
python scripts/list_submodules.py "Enumeration"
```
执行 `python scripts/list_submodules.py "Enumeration"` 可以获取全部支持的枚举类型名称。

### Step 3: 查看模块直接包含的函数
查看指定模块直接包含的函数列表：
Code和Enumeration无直接包含的函数，其余模块直接包含函数。
```bash
python scripts/list_module_functions.py <module_path>

# 示例
python scripts/list_module_functions.py cFrameObj --limit 30
```
**注意**：如果当前模块属于 Enumeration（如 `Enumeration/eItemType`），应跳到 Step 5 查询枚举信息。

**判断是否需要继续深入**：
- 如果子模块名称更符合任务需求，继续深入
- 如果函数列表已包含所需函数，直接获取详情

### Step 4: 获取函数详细信息
**注意**：ETABS API 不同类中可能有同名函数。应通过**模块路径 + 函数名**精确定位。

**精确查询（推荐）**：
```bash
python scripts/get_function_or_enum_detail.py <module_path> <function_name>
# 示例
python scripts/get_function_or_enum_detail.py cFrameObj SetLoadDistributed
```

**只知函数名时，搜索所有匹配**：
```bash
python scripts/get_function_or_enum_detail.py --functionsearch <keyword>
# 示例
python scripts/get_function_or_enum_detail.py --functionsearch FrameForce
```

### Step 5（按需执行的步骤）: 获取枚举详细信息
**根据路径查找枚举信息**：

```bash
python scripts/get_function_or_enum_detail.py <module_path>
# 示例
python scripts/get_function_or_enum_detail.py "Enumeration/eShellType"
```
**根据枚举名查找直接枚举信息**：
```bash
python scripts/get_function_or_enum_detail.py --enumsearch <enum_name>
# 示例
python scripts/get_function_or_enum_detail.py --enumsearch eItemType
# 示例
python scripts/get_function_or_enum_detail.py --enumsearch Objects
```

**注意**：全文搜索是辅助手段，主要还是应该通过渐进式检索定位！

## 执行任务时的重要原则

### 1. 永远优先连接已运行的实例！
**注意**：在使用 COM 对象前需调用 comtypes.CoInitialize()。应先判断 ETABS 是否已运行，优先连接已有实例；连接失败时**询问用户**是否需要开启新的 ETABS
`GetObject` 在找不到运行中的实例时**返回 None 而不是抛异常**，必须先判断再访问 `SapModel`，否则会报 `'NoneType' object has no attribute 'SapModel'`：

```python
import comtypes.client
import comtypes.gen

comtypes.CoInitialize()
helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

# 1) 先尝试附着已运行实例
EtabsObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
if EtabsObject is None:
    # 2) 附不着 → 询问用户是否起新实例；确认后：
    EtabsObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
    EtabsObject.ApplicationStart()
SapModel = EtabsObject.SapModel
```

### 2. 确认单位制
- 执行任务前需使用 SapModel.GetPresentUnits() 先确认当前单位制。
- 新创建的模型，应采用**N_mm_C**单位制。
- 链接到的模型若已设定单位制，则按照原设定执行后续操作。
**单位制**
```python
lb_in_F = 1    # lb, in, F
lb_ft_F = 2    # lb, ft, F 
kip_in_F = 3   # kip, in, F
kip_ft_F = 4   # kip, ft, F
kN_mm_C = 5    # kN, mm, C
kN_m_C = 6     # kN, m, C
kgf_mm_C = 7   # kgf, mm,C   
kgf_m_C = 8    # kgf, m, C
N_mm_C = 9     # N, mm, C
N_m_C = 10     # N, m, C
Ton_mm_C = 11  # Ton, mm,C 
Ton_m_C = 12   # Ton, m, C
kN_cm_C = 13   # kN, cm, C
kgf_cm_C = 14  # kgf, cm,C 
N_cm_C = 15    # N, cm, C
Ton_cm_C = 16  # Ton, cm, C
SapModel.SetPresentUnits(N_mm_C)
```
**单位制重要提示**
当设置单位制为公制时，cFile.NewGridOnly 只接受m作为距离单位，请按需换算；当设置单位制为英制时，cFile.NewGridOnly 只接受ft作为距离单位，请按需换算

### 3. 文件保存
保存文件前通过`filepath = SapModel.GetModelFilename(True)`获取工程路径，如果`filename == '(Untitled)'`，则需要让用户告知工程路径，或在工作目录**新建一个文件夹**保存`.edb`文件。
计算前应执行 `SapModel.File.Save(filepath)`，否则可能无法获取结果。

## ⚠️ VB 示例转 Python 规范
**背景说明：** 你检索到的 API 说明都是 VB 的。但是需要编写 Python 代码以执行任务，你必须严格遵循以下转换规则，尤其是关于 ByRef（按引用传递）参数的特殊处理。

### 0. 每次调用 API 前的强制清单（先做这步，再写调用）

绝大多数运行时报错（`'list' object cannot be interpreted as an integer`、`required argument ... missing`、`'NoneType' ...`）都源于跳过了这步。**每写一个 API 调用前**，依次过一遍：

1. **查签名**：`python scripts/get_function_or_enum_detail.py <模块> <函数>`，拿到 `vb_signature`，看清每个参数的类型和是否 `ByRef`。
2. **数清 ByRef 参数**：签名里**所有** `ByRef` 的参数，Python 端都要按下表传占位符，并在返回元组里接收。**返回值不是单个整数，而是 `(所有 ByRef 输出..., 返回码)` 元组**——直接把返回值当整数用必报类型错误。
3. **不要漏非 Optional 入参**：签名里没标 `Optional` 的参数都要传，即使是数组/字符串也必须传占位 `[]` 或 `' '`。
4. **数组 ByRef 多为输入**：DatabaseTables 里很多数组参数（如 `FieldKeyList As String()`、`TableData As String()`）在签名中标了 `ByRef` 或写成 `As Type()`，但**语义上是输入**——照样要把实际列表传进去，**不要因为看到 ByRef 就省略**。

### 1. 核心机制：ByRef 参数与元组解包

COM 规定接口方法自身只返回一个 HRESULT，即表示这次调用本身是否成功的状态码。方法要向调用方交付任何数据，只能由调用方先传入指针，方法把结果写进指针指向的内存。类型库（type library）为每个参数记录了方向标记，VB 签名就是这些标记在 VB 语法里的写法：标 `ByRef` 的是 `[in,out]`（传进去的值会被覆盖，新值需交还调用方），未标的是 `[in]`（方法只读取），末尾的 `As Integer` 返回值本身也是一个输出指针。

Python 没有让被调方改写调用者变量的机制，因此 ctypes 换了个交付方式：把每个 `[in,out]` 被写回的新值连同末尾的返回码，依签名顺序收集成一个序列，作为调用结果返回。HRESULT 不在这个序列里——它指示失败时 comtypes 直接抛出 `COMError`。

**由此得到**：

- **传入的参数个数** = 签名参数总数。未标 `ByRef` 的传真实值；标 `ByRef` 的同样必须占位（占位符类型见下表），占位值不影响结果，调用时会被覆盖。带 `Optional` 的可从尾部省略。
- **返回值**按签名顺序排列各 `ByRef` 输出，末位是函数返回码 ret：**0 成功，非 0 失败**，每次调用后都要检查。它与 HRESULT 是两回事——COM 调用成功而 ETABS 业务失败是常见组合。

**一处要留意**：库里的 VB 签名摘自 CSI 文档，而 VB 的数组一律按引用传递，所以不少**语义上是输入**的数组参数也被标成了 `ByRef`（DatabaseTables 里尤其多，如 `SetTableForEditingArray` 的 `FieldsKeysIncluded` / `TableData`）。这类参数要传真实数据、且不会回传，返回序列因此会短于「`ByRef` 个数 + 1」。**判断标准：凡是必须传真实数据而不是占位符的参数，就是输入，不出现在返回序列里**；拿不准时按实际长度解包。

### 2. 参数类型映射与初始化对照表
在 Python 中调用含有`ByRef`的接口时，必须先为这些参数传入占位符（初始化），不能直接跳过或在解包右侧首次定义。

| VB 类型 | Python 传入 | Python 接收 | 示例 |
|---------|------------|------------|------|
| `ByVal String` | `'value'` | - | `AddByCoord(..., 'BEAM1', ...)` |
| `ByVal Double` | `3.14` (数值) | - | `SetLoadDistributed(..., 1.5, ...)` |
| `ByRef String` | `' '` (空字符串) | `变量名` | `GetPoints(name, p1, p2)` |
| `ByRef Double` | `0` (标量) | `[变量]` (元组) | `GetCoordCartesian(pt, 0, 0, 0)` |
| `ByRef Long` | `0` (标量) | `[变量]` (元组) | `GetSelected(0, [], [])` |
| `ByRef Array` | `[]` (空列表) | `[变量]` (元组) | `GetSelected(0, [], [])` |

### 3. 标准调用模板与对比示例
**示例 A：获取多项数据的复合接口 (GetSelected)**
```vb
'The function returns zero if the selection list is successfully retrieved, otherwise it returns a nonzero value.
Function GetSelected(ByRef NumberItems As Long, ByRef ObjectType() As Long, ByRef ObjectName() As String) As Long
```
```python
# 1. 传入占位符 (0, [], [])
# 2. 接收元组: (NumberItems, ObjectType, ObjectName, ReturnCode)
result = SapModel.SelectObj.GetSelected(0, [], [])
ret_code = result[3]  # 注意：最后一个元素才是状态码！
```

### 4. cDatabaseTables Interface中接口使用的注意事项

**先选对路径**（避免选错工具白踩坑）：
- **楼层**：用专用对象 `cStory.SetStories_2`（一次性定义多层及其高度，稳定可靠），**不要**用 DatabaseTables 写楼层表。
- **轴网线**：`cGridSys` 只有 `SetGridSys`（设轴网系统原点/旋转），**没有设置轴网线的 setter**（`GetGridSys_2` / `GetGridSysCartesian` 只能读出轴网线）。所以**程序化设置轴网线只能走 DatabaseTables**。

（1）**读表前先查结构**：使用 `GetTableForDisplayArray` / `GetTableForDisplayCSVFile` / `GetTableForDisplayCSVString` / `GetTableForDisplayXMLString` 获取数据前，需先调用 `GetAllTables` 找到目标**表键**、`GetAllFieldsInTable` 了解字段结构（`FieldKey` / `FieldName` 显示名 / `Description`），**严禁使用自己猜想的表键**。
（2）**写表前先读模板**：使用 `SetTableForEditingArray` / `SetTableForEditingCSVFile` / `SetTableForEditingCSVString` 前，需先调用对应的 `GetTableForEditingArray` / `GetTableForEditingCSVFile` / `GetTableForEditingCSVString` 获取当前表的格式，**以此作为模板**构建修改后的内容，**严禁凭借猜想去做修改**。

**写入优先 `SetTableForEditingArray`，CSV 仅作兜底**：
- `SetTableForEditingArray` 用**字段键** + 一维数组（行优先铺平），对语言/本地化不敏感，最可靠；
- `SetTableForEditingCSVString` 的 CSV **表头要用显示名**（不是字段键）、单元格取值要照读出来的样例，极易因显示名/取值不匹配（如 Visible 是 `"Yes"` 还是 `"是"`、BubbleLoc 是 `"Both"`/`"End"`/`"Start"`）导致 `ApplyEditedTables` 报“读取 0 条记录”甚至**清空原表**。

调用骨架（Array 方式：读结构 → 写 → 应用）：

```python
TableKey = "..."   # 先用 GetAllTables 查准，严禁猜

# 1) 读字段结构（FieldKey / FieldName / Description 等，按 ByRef 顺序解包）
[TableVersion, NumberFields, FieldKey, FieldName, Desc, Units, IsImportable, ret] = \
    SapModel.DatabaseTables.GetAllFieldsInTable(TableKey, 0, 0, [], [], [], [], [])

# 2) 写入：字段键 + 一维数组（行优先），NumberRecords = 行数
FieldKeys = ["LineType", "BubbleLoc", "Ordinate", "Visible"]   # 取自上一步 FieldKey
NumberRecords = 10
TableData = ["...", "...", ...]   # 共 NumberRecords * len(FieldKeys) 个字符串，行优先
[TableVersion, ret] = SapModel.DatabaseTables.SetTableForEditingArray(
    TableKey, 0, FieldKeys, NumberRecords, TableData)

# 3) 应用并读日志（务必检查 NumErr / ImportLog）
[NumFatal, NumErr, NumWarn, NumInfo, ImportLog, ret] = \
    SapModel.DatabaseTables.ApplyEditedTables(True, 0, 0, 0, 0, " ")
print(ImportLog, NumFatal, NumErr)
```

上面三处解包正是 §1 那条判断标准的例子：`GetAllFieldsInTable` 的数组传 `[]` 占位，是输出，7 个 `ByRef` 全部回传（8 元组）；`SetTableForEditingArray` 的 `FieldKeys` / `TableData` 传的是真实数据，是输入，不回传（只有 2 元组）。

### 5. 永远不要假设主观假设 ETABS 内部命名，遵循先查找再使用的原则。必须严格对照函数签名，ETABS API 参数顺序和类型非常严格，不能凭经验猜测

## 示例：创建简单框架模型并运行分析

```python
import os
import sys
import comtypes.client

comtypes.CoInitialize()
helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
# 先附着已运行实例；GetObject 找不到时返回 None，再起新实例
myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
if myETABSObject is None:
    myETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
    myETABSObject.ApplicationStart()
SapModel = myETABSObject.SapModel
#initialize model
N_mm_C = 9     # N, mm, C
SapModel.InitializeNewModel(N_mm_C)
#create new blank model
ret = SapModel.File.NewBlank()
#define rectangular frame section property
ret = SapModel.PropFrame.SetRectangle('ColumConc', 'C30', 500, 500)
ret = SapModel.PropFrame.SetRectangle('BeamConc', 'C30', 600, 300)
#define frame section property modifiers
ModValue = [1000, 0, 0, 1, 1, 1, 1, 1]
ret = SapModel.PropFrame.SetModifiers('ColumConc', ModValue)
ret = SapModel.PropFrame.SetModifiers('BeamConc', ModValue)
#add frame object by coordinates
Coloumn_FrameName1 = ' '
Coloumn_FrameName2 = ' '
Coloumn_FrameName3 = ' '
Coloumn_FrameName4 = ' '
[Coloumn_FrameName1, ret] = SapModel.FrameObj.AddByCoord(0, 0, 0, 0, 0, 3000, Coloumn_FrameName1, 'ColumConc', '1', 'Global')
[Coloumn_FrameName2, ret] = SapModel.FrameObj.AddByCoord(6000, 0, 0, 6000, 0, 3000, Coloumn_FrameName2, 'ColumConc', '2', 'Global')
[Coloumn_FrameName3, ret] = SapModel.FrameObj.AddByCoord(0, 6000, 0, 0, 6000, 3000, Coloumn_FrameName3, 'ColumConc', '3', 'Global')
[Coloumn_FrameName4, ret] = SapModel.FrameObj.AddByCoord(6000, 6000, 0, 6000, 6000, 3000, Coloumn_FrameName4, 'ColumConc', '4', 'Global')
FrameNameList = [Coloumn_FrameName1, Coloumn_FrameName2, Coloumn_FrameName3, Coloumn_FrameName4]    
#assign point object restraint at base
for FrameName in FrameNameList:
    PointName1 = ' '
    PointName2 = ' '
    Restraint = [True, True, True, True, True, True] # 固接支座
    [PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(FrameName, PointName1, PointName2)
    ret = SapModel.PointObj.SetRestraint(PointName1, Restraint)

Beam_FrameName1 = ' '
Beam_FrameName2 = ' '
Beam_FrameName3 = ' '
Beam_FrameName4 = ' '
[Beam_FrameName1, ret] = SapModel.FrameObj.AddByCoord(0, 0, 3000, 6000, 0, 3000, Beam_FrameName1, 'BeamConc', '1', 'Global')
[Beam_FrameName2, ret] = SapModel.FrameObj.AddByCoord(6000, 0, 3000, 6000, 6000, 3000, Beam_FrameName2, 'BeamConc', '2', 'Global')
[Beam_FrameName3, ret] = SapModel.FrameObj.AddByCoord(6000, 6000, 3000, 0, 6000, 3000, Beam_FrameName3, 'BeamConc', '3', 'Global')
[Beam_FrameName4, ret] = SapModel.FrameObj.AddByCoord(0, 6000, 3000, 0, 0, 3000, Beam_FrameName4, 'BeamConc', '4', 'Global')
Beam_FrameNameList = [Beam_FrameName1, Beam_FrameName2, Beam_FrameName3, Beam_FrameName4]
# refresh view, update (initialize) zoom
ret = SapModel.View.RefreshView(0, False)
# add load patterns
LTYPE_OTHER = 8
ret = SapModel.LoadPatterns.Add('1', LTYPE_OTHER, 1, True)
ret = SapModel.LoadPatterns.Add('2', LTYPE_OTHER, 0, True)
# assign loading for load pattern 1
[PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(Beam_FrameName1, PointName1, PointName2)
PointLoadValue = [0,0,-10,0,0,0]
ret = SapModel.PointObj.SetLoadForce(PointName1, '2', PointLoadValue)
ret = SapModel.FrameObj.SetLoadDistributed(Beam_FrameName1, '1', 1, 10, 0, 1, 1800, 1800)
# save model
ModelPath = r".\test.edb"
ret = SapModel.File.Save(ModelPath)
# run model (this will create the analysis model)
ret = SapModel.Analyze.RunAnalysis()
# initialize for results
[PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(Beam_FrameName1, PointName1, PointName2)
# get results for load cases 1
NumberResults = 0
Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3 = ([] for _ in range(11))
ObjectElm = 0
ret = SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = SapModel.Results.Setup.SetCaseSelectedForOutput(str(1))
[NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3, ret] = SapModel.Results.JointDispl(PointName2, ObjectElm, NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3)
# close the program
ret = myETABSObject.ApplicationExit(False)
SapModel = None
mySapObject = None

```