---
name: sap2000-python
description: Use when using Python with SAP2000 OAPI and comtypes to launch or attach to SAP2000, initialize models, define materials and sections, create point or frame objects, assign loads, run analysis, or extract results based on the CSI OAPI documentation.
---

# sap2000-python

## Overview

这个 skill 只覆盖 `CSI_OAPI_Documentation` 中能直接核实的 SAP2000 OAPI 内容，不把未经文档确认的参数、单位假设或旧版函数名写成可靠结论。

核心原则：
- Python 侧通常通过 `comtypes.client` 调用 SAP2000 OAPI
- 连接方式、函数签名、返回值、参数顺序以本地 `CSI_OAPI_Documentation` 为准
- 结果提取前通常需要先设置输出工况，而不是假设存在某个 `SetAnalysisCase`

## When to Use

适用场景：
- 需要从 Python 启动、附着或控制 SAP2000
- 需要初始化模型并设置单位
- 需要定义材料、杆件截面、点对象、框架对象
- 需要施加框架荷载并运行分析
- 需要提取位移、反力、杆件内力等结果
- 需要按本地 CSI OAPI 文档校核 Python 示例或 API 用法

不适用场景：
- 把旧版博客、论坛代码直接当成当前 OAPI 标准
- 未核对文档就自行编造参数表、枚举值含义或返回值结构
- 把不存在于文档中的函数写入 skill

## Quick Start

```python
import comtypes.client

helper = comtypes.client.CreateObject("SAP2000v1.Helper")
sap_object = helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")

sap_object.ApplicationStart()
sap_model = sap_object.SapModel
sap_model.InitializeNewModel()
sap_model.File.NewBlank()
```

文档要点：
- `Example_7_(Python).htm` 明确给出 `comtypes.client.CreateObject("SAP2000v1.Helper")`
- `Helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")` 会启动最近安装版本
- `Helper.CreateObject(fullPath)` 可按指定程序路径启动
- `InitializeNewModel` 文档明确写明：它已包含 `ApplicationStart` 的功能

## Connection Patterns

### 1. 按程序路径启动

```python
import comtypes.client

program_path = r"C:\Program Files (x86)\Computers and Structures\SAP2000 21\sap2000.exe"
helper = comtypes.client.CreateObject("SAP2000v1.Helper")
sap_object = helper.CreateObject(program_path)
sap_object.ApplicationStart()
sap_model = sap_object.SapModel
```

对应文档：
- `Getting_Started/Accessing_Sap2000_From_An_External_Application.htm`
- `General_Functions/Helper/CreateObject.htm`

### 2. 启动最近安装版本

```python
import comtypes.client

helper = comtypes.client.CreateObject("SAP2000v1.Helper")
sap_object = helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")
sap_object.ApplicationStart()
sap_model = sap_object.SapModel
```

对应文档：
- `Launching_the_Installed_Version_of_SAP2000_CSiBridge_Automatically.htm`
- `General_Functions/Helper/CreateObjectProgID.htm`

### 3. 连接到已打开实例

```python
import comtypes.client

helper = comtypes.client.CreateObject("SAP2000v1.Helper")
sap_object = helper.GetObject("CSI.SAP2000.API.SapObject")
sap_model = sap_object.SapModel
```

对应文档：
- `Example_Code/Example_7_(Python).htm`

## Return Values And Units

### 返回值

`Getting_Started/Function_Return_Values.htm` 明确说明：
- 非零返回值表示函数未成功执行

因此最稳妥的 Python 用法是：

```python
ret = sap_model.File.NewBlank()
if ret != 0:
    raise RuntimeError(f"NewBlank failed, ret={ret}")
```

### 单位

文档显示：
- `ApplicationStart(Optional Units As eUnits = kip_in_F, ...)`
- `InitializeNewModel(Optional Units As eUnits = kip_in_F)`
- `Example_7_(Python).htm` 明确演示了 `SetPresentUnits(kip_ft_F)` 和 `SetPresentUnits(kip_in_F)`

建议：
- 不要只写“SAP2000 默认是 kip-in”然后忽略后续单位切换
- 在建模或取结果前显式设置当前单位

## Core API

### 1. ApplicationStart / ApplicationExit / InitializeNewModel

```python
ret = sap_object.ApplicationStart()
ret = sap_model.InitializeNewModel()
ret = sap_object.ApplicationExit(False)
```

准确签名：
- `ApplicationStart(Optional Units As eUnits = kip_in_F, Optional Visible As Boolean = True, Optional FileName As String = "") As Long`
- `ApplicationExit(ByVal FileSave As Boolean) As Long`
- `InitializeNewModel(Optional ByVal Units As eUnits = kip_in_F) As Long`

### 2. File

```python
ret = sap_model.File.NewBlank()
ret = sap_model.File.OpenFile(model_path)
ret = sap_model.File.Save(model_path)
```

文档签名要点：
- `NewBlank() As Long`
- `OpenFile(ByVal FileName As String) As Long`
- `Save.htm` 页面给出的函数名是 `FileSave(Optional ByVal FileName As String = "") As Long`

说明：
- Python 侧通常仍通过 `sap_model.File.Save(...)` 调用
- 但在 skill 中应注明文档页面标题与签名文本是 `FileSave`

### 3. 模板模型

```python
ret = sap_model.File.New2DFrame(temp_type, number_storys, story_height, number_bays, bay_width)
ret = sap_model.File.New3DFrame(temp_type, number_storys, story_height, number_bays_x, bay_width_x, number_bays_y, bay_width_y)
```

准确签名：
- `New2DFrame(ByVal TempType As e2DFrameType, ByVal NumberStorys As Long, ByVal StoryHeight As Double, ByVal NumberBays As Long, ByVal BayWidth As Double, Optional ByVal Restraint As Boolean = True, Optional ByVal Beam As String = "Default", Optional ByVal Column As String = "Default", Optional ByVal Brace As String = "Default") As Long`
- `New3DFrame(ByVal TempType As e3DFrameType, ByVal NumberStorys As Long, ByVal StoryHeight As Double, ByVal NumberBaysX As Long, ByVal BayWidthX As Double, ByVal NumberBaysY As Long, ByVal BayWidthY As Double, Optional ByVal Restraint As Boolean = True, Optional ByVal Beam As String = "Default", Optional ByVal Column As String = "Default", Optional ByVal Area As String = "Default", Optional ByVal NumberXDivisions As Long = 4, Optional ByVal NumberYDivisions As Long = 4) As Long`

### 4. PointObj

```python
name = ""
ret = sap_model.PointObj.AddCartesian(0, 0, 0, name)
ret = sap_model.PointObj.SetRestraint("Point1", [True, True, True, False, False, False])
```

准确签名：
- `AddCartesian(ByVal x As Double, ByVal y As Double, ByVal z As Double, ByRef Name As String, Optional ByVal userName As String = "", Optional ByVal csys As String = "Global", Optional ByVal MergeOff As Boolean = False, Optional ByVal MergeNumber As Long = 0) As Long`
- `SetRestraint(ByVal Name As String, ByRef Value() As Boolean, Optional ByVal ItemType As eItemType = object) As Long`

### 5. FrameObj

```python
name = ""
ret = sap_model.FrameObj.AddByCoord(0, 0, 0, 100, 0, 0, name, "Default")
ret = sap_model.FrameObj.SetLoadDistributed("F1", "DEAD", 1, 10, 0, 1, 0.08, 0.08)
ret = sap_model.FrameObj.SetLoadPoint("F1", "LIVE", 1, 2, 0.5, -5.0)
```

准确签名：
- `AddByCoord(ByVal xi As Double, ByVal yi As Double, ByVal zi As Double, ByVal xj As Double, ByVal yj As Double, ByVal zj As Double, ByRef Name As String, Optional ByVal PropName As String = "Default", Optional ByVal UserName As String = "", Optional ByVal CSys As String = "Global") As Long`
- `SetLoadDistributed(ByVal Name As String, ByVal LoadPat As String, ByVal MyType As Long, ByVal Dir As Long, ByVal Dist1 As Double, ByVal Dist2 As Double, ByVal Val1 As Double, ByVal Val2 As Double, Optional ByVal CSys As String = "Global", Optional ByVal RelDist As Boolean = True, Optional ByVal Replace As Boolean = True, Optional ByVal ItemType As eItemType = Object) As Long`
- `SetLoadPoint(ByVal Name As String, ByVal LoadPat As String, ByVal MyType As Long, ByVal Dir As Long, ByVal Dist As Double, ByVal Val As Double, Optional ByVal CSys As String = "Global", Optional ByVal RelDist As Boolean = True, Optional ByVal Replace As Boolean = True, Optional ByVal ItemType As eItemType = Object) As Long`

注意：
- `SetLoadDistributed` 和 `SetLoadPoint` 的参数比旧版 skill 写得更长，不能简化成自定义的 `Direction, DistanceType, Force` 风格

### 6. PropFrame

```python
ret = sap_model.PropFrame.SetPipe("PIPE1", "A992Fy50", 8, 0.375)
ret = sap_model.PropFrame.SetRectangle("R1", "4000Psi", 20, 12)
ret = sap_model.PropFrame.SetISection_1("ISEC1", "A992Fy50", 20, 10, 1, 0.5, 10, 1, 0.0)
ret = sap_model.PropFrame.SetChannel_2("CHN1", "A992Fy50", 10, 3, 0.4, 0.25, 0.0, False)
```

准确签名要点：
- `SetPipe(Name, MatProp, t3, tw, ...)`
- `SetRectangle(Name, MatProp, t3, t2, ...)`
- 文档当前页是 `SetISection_1(...)`，不是旧版 skill 里的 `SetISection(...)`
- 文档当前页是 `SetChannel_2(...)`，不是旧版 skill 里的 `SetChannel(...)`

### 7. PropMaterial

```python
name = ""
ret = sap_model.PropMaterial.AddMaterial(name, mat_type, region, standard, grade)
ret = sap_model.PropMaterial.SetOSteel_1("Steel", 55, 68, 60, 70, 1, 2, 0.02, 0.1, 0.2, -0.1)
```

准确签名：
- `AddMaterial(ByRef Name As String, ByVal MatType As eMatType, ByVal Region As String, ByVal Standard As String, ByVal Grade As String, Optional ByVal UserName As String = "") As Long`
- `SetOSteel_1(ByVal Name As String, ByVal Fy As Double, ByVal Fu As Double, ByVal eFy As Double, ByVal eFu As Double, ByVal SSType As Long, ByVal SSHysType As Long, ByVal StrainAtHardening As Double, ByVal StrainAtMaxStress As Double, ByVal StrainAtRupture As Double, ByVal FinalSlope As Double, Optional ByVal Temp As Double = 0) As Long`

说明：
- `AddMaterial` 的文档参数是 `Region / Standard / Grade`，不是旧版 skill 里写的 `Grade / Type / Notes`
- 当前核对范围内没有把 `SetSteel`、`SetConcrete` 作为主推荐接口补进 skill，因为这轮校对重点基于已抽取的一手页面

### 8. LoadPatterns

```python
ret = sap_model.LoadPatterns.Add("DEAD", load_pattern_type, 1.0)
ret = sap_model.LoadPatterns.GetNameList(number_names, names)
```

准确签名：
- `Add(ByVal Name As String, ByVal MyType As eLoadPatternType, Optional ByVal SelfWTMultiplier As Double = 0, Optional ByVal AddLoadCase As Boolean = True) As Long`
- `GetNameList(ByRef NumberNames As Long, ByRef MyName() As String) As Long`

注意：
- 第三个参数默认值是 `0`
- 还有一个可选参数 `AddLoadCase = True`

### 9. Analyze

```python
ret = sap_model.Analyze.RunAnalysis()
```

准确签名：
- `RunAnalysis() As Long`

### 10. Results Setup

结果提取前，优先按文档设置输出工况：

```python
ret = sap_model.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = sap_model.Results.Setup.SetCaseSelectedForOutput("DEAD")
```

对应文档签名：
- `DeselectAllCasesAndCombosForOutput() As Long`
- `SetCaseSelectedForOutput(ByVal Name As String, Optional ByVal Selected As Boolean = True) As Long`

这比旧版 skill 中的 `Analyze.SetAnalysisCase(...)` 更可靠，因为本地文档中我已核到 `Results.Setup.SetCaseSelectedForOutput`，但未核到 `Analyze.SetAnalysisCase`。

### 11. Results

```python
ret = sap_model.Results.FrameForce(name, item_type_elm, number_results, obj, obj_sta, elm, elm_sta, load_case, step_type, step_num, p, v2, v3, t, m2, m3)
ret = sap_model.Results.JointDispl(name, item_type_elm, number_results, obj, elm, load_case, step_type, step_num, u1, u2, u3, r1, r2, r3)
ret = sap_model.Results.JointReact(name, item_type_elm, number_results, obj, elm, load_case, step_type, step_num, f1, f2, f3, m1, m2, m3)
```

准确签名要点：
- `FrameForce(...)` 里有 `NumberResults`、`ObjSta()`、`ElmSta()` 两组站点数组
- `JointDispl(...)` 与 `JointReact(...)` 也都包含 `NumberResults`
- 旧版 skill 把这些函数错误简写成只返回少量数组，这是不准确的

`Example_7_(Python).htm` 还显示了 `ObjectElm` 这种 `eItemTypeElm` 枚举用法。

## Minimal Example

```python
import comtypes.client

helper = comtypes.client.CreateObject("SAP2000v1.Helper")
sap_object = helper.CreateObjectProgID("CSI.SAP2000.API.SapObject")
sap_object.ApplicationStart()

sap_model = sap_object.SapModel
sap_model.InitializeNewModel()
sap_model.File.NewBlank()

name = ""
sap_model.PointObj.AddCartesian(0, 0, 0, name)
sap_model.PointObj.SetRestraint("Point1", [True, True, True, False, False, False])

frame_name = ""
sap_model.FrameObj.AddByCoord(0, 0, 0, 120, 0, 0, frame_name, "Default")

sap_model.LoadPatterns.Add("DEAD", 1, 1.0)
sap_model.Analyze.RunAnalysis()

sap_model.Results.Setup.DeselectAllCasesAndCombosForOutput()
sap_model.Results.Setup.SetCaseSelectedForOutput("DEAD")

sap_object.ApplicationExit(False)
```

## Common Mistakes

### 1. frontmatter 不合规

skill frontmatter 只应保留：
- `name`
- `description`

不要加 `compatibility`

### 2. 把注册 COM 的 `RegAsm` 命令写成必需步骤

这次校核所依据的 `CSI_OAPI_Documentation` 中，我没有核到旧版 skill 那段 `RegAsm` 注册说明，因此不把它保留为可靠标准流程。

### 3. 把 `InitializeNewModel` 和 `ApplicationStart` 的关系写错

本地文档明确说明：
- `InitializeNewModel` 已包含 `ApplicationStart` 的功能

因此不能一边写“必须先 `ApplicationStart`”，一边忽略文档这条说明。

### 4. `New2DFrame` / `New3DFrame` 参数表写错

旧版 skill 把它们写成了自定义的跨数、层数、方向参数顺序；文档实际签名不同，应按本地页面重写。

### 5. `PropFrame` 函数名写成旧名

当前文档页面显示：
- `SetISection_1`
- `SetChannel_2`

不是旧版 skill 里的：
- `SetISection`
- `SetChannel`

### 6. `AddMaterial` 参数语义写错

当前文档是：
- `Name, MatType, Region, Standard, Grade, UserName`

不是旧版 skill 里的：
- `Name, MatType, Grade, Type, Notes`

### 7. `SetLoadDistributed` / `SetLoadPoint` 签名被简化错了

文档里这两个函数都包含：
- `MyType`
- `Dir`
- 距离参数
- `CSys`
- `RelDist`
- `Replace`
- `ItemType`

不能缩写成非文档版本。

### 8. 结果接口漏掉 `NumberResults` 和站点数组

`FrameForce`、`JointDispl`、`JointReact` 在文档里都有完整的 ByRef 输出数组，旧版 skill 的“简写返回值”不可靠。

### 9. 把不存在于本轮校核范围内的 `Analyze.SetAnalysisCase` 写成标准接口

本地文档中我已核到：
- `Results.Setup.SetCaseSelectedForOutput`

但未核到旧版 skill 写的：
- `Analyze.SetAnalysisCase`

因此不应继续保留。

## References

- [Accessing_Sap2000_From_An_External_Application.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\Getting_Started\Accessing_Sap2000_From_An_External_Application.htm)
- [Launching_the_Installed_Version_of_SAP2000_CSiBridge_Automatically.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\Launching_the_Installed_Version_of_SAP2000_CSiBridge_Automatically.htm)
- [Example_7_(Python).htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\Example_Code\Example_7_(Python).htm)
- [Function_Return_Values.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\Getting_Started\Function_Return_Values.htm)
- [ApplicationStart.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\General_Functions\ApplicationStart.htm)
- [InitializeNewModel.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\General_Functions\InitializeNewModel.htm)
- [AddMaterial.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Material\AddMaterial.htm)
- [SetOSteel_1.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Material\SetOSteel_1.htm)
- [SetPipe.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Frame\SetPipe.htm)
- [SetISection_{Frame}.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Frame\SetISection_{Frame}.htm)
- [SetChannel_{Frame}.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Frame\SetChannel_{Frame}.htm)
- [SetRectangle.htm](E:\2026\20260313_02上海院项目\CSI_OAPI_Documentation\SAP2000_API_Fuctions\Definitions\Properties\Frame\SetRectangle.htm)
