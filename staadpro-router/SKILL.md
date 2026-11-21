---
name: staadpro
version: 1.0.5
display_name: STAADPro
display_name_en: STAADPro
description: 基于 Bentley 官方 openstaadpy 库操控 STAAD.Pro 完成空间结构有限元建模、荷载组合定义、求解分析及位移内力与钢结构规范校核结果提取，配备完整的 OpenSTAAD 39 个模块渐进式检索系统与全函数离线库。
description_zh: 基于 Bentley 官方 openstaadpy 库操控 STAAD.Pro 完成空间结构有限元建模、荷载组合定义、求解分析及位移内力与钢结构规范校核结果提取，配备完整的 OpenSTAAD 39 个模块渐进式检索系统与全函数离线库。
description_en: Controls STAAD.Pro via official openstaadpy for structural modeling, load combinations, finite element analysis, and member design checks, equipped with a progressive OpenSTAAD 39-module query system and complete offline API database.
license: Apache-2.0
---

# STAAD.Pro 操作技能(OpenSTAAD)

通过 Bentley 官方 `openstaadpy` 库操控 STAAD.Pro 完成建模、分析、查询和数据交互。全部 708 个 API 已从官方源码结构化至 `references/openstaad_api.db`,通过 `scripts/` 下的脚本渐进式检索。

## 1. 连接 STAAD.Pro(强制规范)

`os_analytical.connect()` 连接到**当前活动的** STAAD.Pro 模型,返回会话对象:

```python
from openstaadpy import os_analytical

s = os_analytical.connect()   # 连接当前活动的 STAAD.Pro 模型
print(s.GetSTAADFile())       # 当前 .std 完整路径,确认连上的是哪个模型
```

要点:

- **前提:STAAD.Pro 必须已经在运行且打开了模型。** `connect()` 只挂接已运行的实例,**不会启动软件、不会打开文件**;连不上会抛 `OsErrorBase("StaadPro Application not found!! ERROR with COM")`——此时结束执行,在回复中请用户先打开 STAAD.Pro 和目标模型。
- **存盘只能就地,严禁另存到别处。** 工程文件夹通常已由前置流程建好并在此打开,`connect()` 才挂得上;此后一律用 `s.SaveModel(True)` 就地写回,绝不要另存或改路径把 .std 挪走——一旦脱离既定目录,后续链接与产物路径都会断。
- 打开了多个模型、要连接特定的一个:传入其文件路径 `s = os_analytical.connect(r"C:\path\to\model.std")`(该文件必须已在某实例中打开)。要同时控制多个打开的模型,为每个模型各建一个会话。
- `connect()` 有一定开销,请利用 python_executor 的环境持久化特性**复用会话变量 `s`**,不要每段代码都重连。
- **API 按对象分组,不是平面的**:会话级函数直接挂在 `s` 上(单位/文件/分析/任务信息,对应模块 `Session/File (Root)`),其余都通过 9 个子对象调用:`s.Geometry`、`s.Property`、`s.Load`、`s.Support`、`s.Output`、`s.Command`、`s.Design`、`s.Table`、`s.View`。**模块名冒号前就是入口对象**(如模块 `Property: Materials` 的函数经 `s.Property.X()` 调用);无冒号的模块(Command/Design/Support/Table/View)模块名即入口。db 的 syntax 列一律给出完整调用路径,照抄即可。

## 2. OpenSTAAD API 渐进式检索

### 必须按照以下步骤先渐进式检索获取 OpenSTAAD 函数,再执行任务
**绝对禁止凭印象写函数签名**,严禁自己瞎猜任何的函数以及其入参和返回值,写代码前必须先渐进式检索获取准确无误的调用方法。

### Step 1:确定模块

```bash
python scripts/list_top_modules.py    # 列出所有模块(全名 + 短名 + 函数数)
```

39 个模块概览(检索时全名、短名均可用):

| 模块(短名) | 用途 |
|---|---|
| Session/File (Root) `session-file-root` | 会话级:打开/保存 .std、**单位设置**、任务信息、**运行分析与状态查询**(直接挂 `s`) |
| Geometry: Node `geometry_node` | 节点:增删改查、坐标、合并、选择读取 |
| Geometry: Member `geometry_member` | 杆件本体:增删、切分/合并/相交/打断、重编号、两端节点、选择 |
| Geometry: Plate `geometry_plate` | 板/壳单元:三四节点板增删查、面积、选择 |
| Geometry: Solid `geometry_solid` | 八节点实体单元:增删查、选择 |
| Geometry: Group `geometry_group` | 命名组:节点/杆件/板/实体的批量集合 |
| Geometry: Physical Member `geometry_physical-member` | 物理杆件:多段分析杆件合并为一根设计单元 |
| Geometry: Parametric Surface `geometry_parametric-surface` | 参数化曲面:定义/网格化生成板单元 |
| Geometry: Misc `geometry_misc` | 几何杂项:Z 轴向上判断、平移复制、重合检查开关、隐藏实体标志 |
| Load: Cases & Combinations `load_cases-combinations` | **主荷载工况与组合**:一切荷载的容器,先建工况、再激活、后加载;组合系数对 |
| Load: Nodal `load_nodal` | 节点荷载、支座强制位移 |
| Load: Member Loads `load_member-loads` | 杆件荷载:均布/集中/梯形/线变/温度/应变/面荷载/固端、集中与均布弯矩、杆上荷载拆分合并 |
| Load: Plate Loads `load_plate-loads` | 板上荷载:压力、静水压、梯形压力、集中 |
| Load: Self-weight & Floor `load_self-weight-floor` | **自重**与楼面荷载 |
| Load: Wind `load_wind` | 风荷载定义/强度/暴露面/加载 |
| Load: Seismic `load_seismic` | 地震荷载定义/重量源/加载 |
| Load: Spectrum & Direct Analysis `load_spectrum-direct-analysis` | 反应谱、Notional 荷载、直接分析参数 |
| Load: Reference Loads `load_reference-loads` | 参考荷载定义与查询 |
| Load: Lists & Envelopes `load_lists-envelopes` | 荷载列表与包络(下一命令/查询作用的工况集) |
| Property: Standard Table Sections `property_standard-table-sections` | 国家型钢库截面(含国家代码表)、**本地枚举有效截面名**(GetProfileSectionNameList,不依赖 STAAD 运行) |
| Property: Prismatic & Tapered `property_prismatic-tapered` | 自定义参数截面(A、Iy、Iz…)与变截面 |
| Property: UPT User Tables `property_upt-user-tables` | 用户表(UPT)截面 |
| Property: Assign & Query Sections `property_assign-query-sections` | 截面指派/移除与属性查询、β 角 |
| Property: Materials `property_materials` | 材料定义/指派/查询(E、ρ、ν 等) |
| Property: Member Specs `property_member-specs` | 杆件与节点规格:端部释放/半刚接、桁架/仅拉/仅压/索、偏移、失效杆件(Inactive)、忽略刚度(Ignore Stiffness)、主从节点约束(Control-Dependent) |
| Property: Plate Thickness & Element Specs `property_plate-thickness-element-specs` | 板厚、板单元规格(平面应力/忽略面内转动/节点释放)与偏移 |
| Property: Fireproofing `property_fireproofing` | 杆件防火涂层(算自重,不改刚度) |
| Property: Custom Attributes `property_custom-attributes` | 杆件/板自定义属性(标签) |
| Support `support` | 支座:固定/铰接/自定义释放/倾斜、弹性地基 |
| Output: Units & Status `output_units-status` | 输出单位查询、结果可用性检查 |
| Output: Node & Support Results `output_node-support-results` | 节点位移(含非线性)、**支座反力**、静力校核、基底压力、弹性地基影响面积(只读,需分析完成) |
| Output: Member Results `output_member-results` | 杆件结果:端力、截面内力、位移、应力(含物理杆件) |
| Output: Plate & Solid Results `output_plate-solid-results` | 板/实体应力、弯矩剪力、Von Mises、沿线合力 |
| Output: Dynamic & Buckling `output_dynamic-buckling` | 频率振型、质量参与系数、屈曲因子、时程 |
| Output: Steel Design Results `output_steel-design-results` | 钢设计校核结果:应力比、控制截面、设计参数块 |
| Command `command` | 分析/设计命令:静力/PDelta/屈曲/索/非线性/直接分析、钢设计命令、软弱层与不规则检查、楼板隔板 |
| Design `design` | 通用设计 Brief/参数/分组(**中国规范校核官方库暂未提供,待补齐**) |
| Table `table` | 报表:建报告、读写单元格 |
| View `view` | 视图:显示模式切换(线框↔实体截面渲染 Full Section、内力/应力/位移图)、显示/隐藏构件、标注、缩放、**程序化选择**(按方向/按组/按连接)、导出图片、剖切视图、比例尺、视口窗口 |

### Step 2:列出模块的函数

```bash
python scripts/list_module_functions.py geometry_node
python scripts/list_module_functions.py "Load: Member Loads" --limit 20
```

输出按 Create/Get/Set 等动词分类给出函数名 + 一行 purpose,据此判断该用哪个。

### Step 3:获取函数详情

```bash
python scripts/get_function_detail.py CreatePlateThicknessProperty        # 直接按函数名查(推荐)
python scripts/get_function_detail.py geometry_node GetNodeCount          # 同名多处时用模块限定
python scripts/get_function_detail.py --search reaction                   # 只知道大概时全文搜索
```

返回 syntax、purpose、parameters、returns、example(Python)。**写代码前必须确认 syntax 和 parameters**;国家代码、方向码等枚举表就在 parameters 里。注意模块限定必须用 Step 1 列表里的全名或短名(没有叫 "Property" 的模块)。

## 3. 调用规范

openstaadpy 已在内部完成全部 COM marshalling,不需要任何 VARIANT 辅助函数。

- **参数直接传原生 Python 类型**:数字传 int/float,ID 列表直接传 `[1, 2, 3]`。
- **返回值也是原生类型**:list / tuple / int / float / str / dict,可直接迭代、切片。
- **函数名大小写必须与 db 完全一致**(PascalCase 镜像官方),调用路径照抄 syntax 列。
- **错误以类型化异常抛出**:底层负错误码会被库自动转成 `OsErrorBase` 子类(如 OsNodeNotFound、OsInvalidArgument、OsGroupAlreadyExists,均在 `openstaadpy.os_analytical.oserrors`);个别路径仍可能抛 `comtypes.COMError`;函数在当前 STAAD 版本不可用时抛 OsErrorBase 提示升级。批量操作时用 `except (OsErrorBase, COMError)` 包住并打印上下文(哪个构件、哪个工况),便于定位。
- returns 写着"未标注返回值…先小范围验证"的条目(全库仅 2 个:View.CreateNewViewForSelections、View.SetLabel)返回值语义未核实;returns 为 `None` 的条目系按官方实现推断的无返回值。
- 极少数函数可能在不同模块同名:`get_function_detail.py <函数名>` 会把所有模块的版本都列出来,按 syntax 的调用路径甄别是哪一个。

## 4. 单位铁律

OpenSTAAD 的一切数值输入输出都按**模型当前输入单位制**解释,单位错了数值全错且不报错;
全局竖向轴方向(Y-up 还是 Z-up)决定了重力方向与坐标体系,建模前也务必确认。

```python
s.GetBaseUnit()               # 'English' 或 'Metric'
s.GetInputUnitForLength()     # 'Meter' / 'MilliMeter' / 'Feet' ...
s.GetInputUnitForForce()      # 'KiloNewton' / 'Kilopound' ...
s.Geometry.IsZUp()            # True=Z轴向上, False=Y轴向上
```
**注意：** 在 STAAD.Pro 中，同时有全局基本单位（Base Unit）和输入单位（InputUnitForLength/InputUnitForForce）两处控制单位制。当两者不一致时, 会导致材料特性（如弹性模量、密度等）、几何坐标、荷载数值都发生巨大的混乱，会带来很多极其严重的问题。
发现这种情况务必提醒用户按照以下步骤进行手动修正(BaseUnit无法通过API修改)：
1. 保存并关闭当前模型。
2. 在 STAAD.Pro 启动界面的配置（Configuration）选项中，找到 Base Unit。
3. 将其修改为您项目实际使用的单位制（如模型坐标和荷载是公制，就必须在此处选择 Metric）。

- **建模/加载/读结果之前,先跑上面四行确认单位与竖向轴**,再决定数值与方向。
- 竖向轴不要求必须为某一方向,但必须与建模逻辑一致:`IsZUp()=True` 时竖向坐标用 Z、自重方向码用 3;`IsZUp()=False` 时竖向坐标用 Y、自重方向码用 2;荷载方向码同理。
- 需要改单位用 `s.SetInputUnits(lengthUnit, forceUnit)`(长度/力代码各 0~7,完整映射查 `get_function_detail.py SetInputUnits`;常用 `(4, 5)` = 米+千牛)。
- 用户口头说的"kN、米"与模型单位不一致时,在 Python 侧换算后再传入。

## 5. 典型工作流

建模到出结果的标准顺序(乱序会失败或结果为空):

```
连接 → 确认单位 → 先查后建(枚举已有材料/截面/工况) → 几何(节点→杆件/板) → 截面/材料 → 支座
     → 荷载工况(先建、再激活、后加载) → 组合(可选) → Command.PerformAnalysis(0) → SaveModel → AnalyzeEx(1,0,1) → 状态检查 → 读结果
```

- **先查后建——撞名/撞号是各类静默失败的根源。** 材料、截面、工况与模型已有对象撞名时 API 不报错:创建变成更新、赋值返回 `True` 实未生效,直到分析才暴雷(如 `DENSITY NOT PROVIDED`)。故建前一律先枚举同类已有对象,**能复用就复用,要新建就避开已有命名/编号**。查法:材料 `s.Property.GetIsotropicMaterialCount()` + `GetIsotropicMaterialProperties(i)`(元组首项即材料名),新名加唯一前缀如 `MY_STEEL_01`;截面 `s.Property.GetSectionPropertyList()` + `GetSectionPropertyName(id)`,复用时编号直接交给 `AssignBeamProperty(beams, id)`;工况 `s.Load.GetPrimaryLoadCaseNumbers()`,新建号一律用 `CreateNewPrimaryLoad` 返回值、别硬编码 1/2/3,清场用 `DeletePrimaryLoadCases(existing, False)`(第二参 varIsReferenceLoads)。关键赋值后仍要抽查——如 `s.Property.GetBeamMaterialName(bid)` 返回空串即未生效,先 `s.SaveModel(True)` 再重赋一次。
- **几何编号:STAAD 里杆件(member)、板/壳(element)、实体(Solid)共用同一编号空间。** 一律用 `AddNode`/`AddBeam`/`AddPlate`/`AddSolid` 自动编号(取其返回值)作为新对象编号;如果撞号时 STAAD 静默通过、分析时才报 `MEMBER/ELEM. NO. n IS DUPLICATED`, Add系列函数可以规避此问题。
- **分析前必须先插入分析命令**:全部荷载工况和组合都建完后,调用一次 `s.Command.PerformAnalysis(0)` 把 `PERFORM ANALYSIS` 写在所有荷载之后。`AnalyzeEx`/`Analyze` 只启动求解器、不会补这条命令;漏掉它或提前(建组合之前)调用,STAAD 报 `FINISH COMMAND IN LOAD DATA … ANALYSIS COMMAND … MISSING IN CASE NO. n`。**每调一次都追加一条**:修模后重新分析前先 `s.Command.DeleteAllAnalysisCommands()` 清除旧命令,否则 .std 里会堆出多条 `PERFORM ANALYSIS`。
- 运行分析用 `s.AnalyzeEx(1, 0, 1)`:silentMode=1 抑制输入弹窗、hiddenMode=0 显示分析框(设 1 隐藏时一旦报错易卡死)、waitTillComplete=1 等完成。它**返回 int 状态码**:2/3=完成可读结果,4=有错误,5=尚未分析,负值/0=异常;官方示例还会跟 `while s.IsAnalyzing(): pass` 兜底等待。
- 读结果前先 `s.GetAnalysisStatus()`(返回 dict,含 ReturnValue/ReturnString/NoOfErrors 等),`ReturnValue` 为 2/3 才可读。
- **分析报错(`AnalyzeEx` 返回 4 或 `NoOfErrors` > 0)的排查链**:`GetAnalysisStatus()` 确认错误数 → 读同名 `.ANL` 分析输出文件、搜 `*** ERROR MESSAGE ***` 定位具体错误 → 对读 `.std` 核实际写出的命令 → 修复后重分析。常见:材料未赋(`DENSITY NOT PROVIDED`)、工况缺分析命令。
- 读结果都在 `s.Output.*`(杆件端力、支座反力、位移、振型等)。
- `references/common_examples.md` 的章节按**建模 → 分析 → 取结果**标准顺序排列,内容取自官方示例,连起来即完整流程,写代码前先查阅。

## 6. 使用注意事项

1. **无人值守,严禁任何交互**:agent 的脚本必须自己跑完。分析用 `s.AnalyzeEx(1, 0, 1)`——silentMode=1 抑制所有需用户输入的弹窗,分析进度框会自动关闭,不阻塞;保存用 `s.SaveModel(True)`;不要调用任何会弹对话框等用户确认的路径。
2. **用户预选必须支持,方式是"读"而不是"等"**:用 `s.Geometry.GetSelectedBeams()` / `s.Geometry.GetSelectedNodes()`(非阻塞,未选中返回空 list)读取用户在 STAAD.Pro 里已选好的对象;为空则结束本次执行并请用户先选好,不要原地等待。
3. **批量操作注意跨进程开销**:每次函数调用都是一次 COM 往返。取清单用 `s.Geometry.GetNodeList()` / `s.Geometry.GetBeamList()` 一次拿全,不要 `for i in range(...)` 里逐个试探;能传 list 的函数(`s.Property.AssignBeamProperty`、`s.Load.AddNodalLoad` 等)一次传一批。
4. **修改类操作完成后 `s.SaveModel(True)`**,否则改动只在内存里;分析前 STAAD 也要求模型已保存。
5. **所有输出文件一律落到会话工作目录**:python_executor 已注入 `WORKSPACE_DIR`,导出 CSV/报告用 `os.path.join(WORKSPACE_DIR, "文件名")` 拼绝对路径——STAAD.Pro 是独立进程,相对路径不会解析到工作目录。
6. **结果为空/为零先查三件事**:分析是否成功(`s.GetAnalysisStatus()`)、工况号是否存在(`s.Load.GetPrimaryLoadCaseNumbers()`)、单位制是否与预期一致(第 4 节)。
7. **严禁直接`.std` 文本文件**:除非用户明确要求可以编辑`.std`，并且明确告诉了你应该如何编辑，否则严禁通过编辑`.std`来达成目标。你不可能清楚知道这个文件的格式，错误编辑将会带来无法挽回的大崩溃，导致任务彻底失败。如确实被授权可以编辑并清楚的知道如何编辑，务必按 `SaveModel(True)` → `CloseSTAADFile()`(释放文件锁,之后 COM 会话失效)→ `time.sleep(2)` → 读写文件 → 重新 `connect()` + `OpenSTAADFile()` → 读关键数据验证 的顺序。