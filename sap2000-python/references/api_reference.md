# SAP2000 Python API Complete Reference

> Source: CSI_OAPI_Documentation.chm (extracted to CSI_OAPI_extracted/)
> Total API Functions: ~2000+

## Table of Contents
1. [General Functions](#general-functions) - 应用程序控制
2. [File Functions](#file-functions) - 文件操作
3. [Point Object (节点)](#point-object---节点) - 节点操作
4. [Frame Object (框架)](#frame-object---框架) - 框架/梁/柱操作
5. [Area Object (面单元)](#area-object---面单元) - 墙/板操作
6. [Link Object (连接)](#link-object---连接) - 隔震/支座操作
7. [Load Patterns (荷载模式)](#load-patterns-荷载模式) - 荷载定义
8. [Load Cases (工况)](#load-cases-工况) - 分析工况
9. [Analysis (分析)](#analysis-分析) - 运行分析
10. [Results (结果)](#results-结果) - 结果提取
11. [Select (选择)](#select---选择) - 对象选择
12. [Material Properties (材料)](#material-properties---材料) - 材料属性
13. [Section Properties (截面)](#section-properties---截面) - 截面属性

---

## General Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `InitializeNewModel()` | 初始化新模型 | 无 |
| `ApplicationStart(Visible=True)` | 启动SAP2000 | `Visible` (bool): 是否显示窗口 |
| `ApplicationExit(Save=False)` | 退出SAP2000 | `Save` (bool): 是否保存 |
| `GetVersion()` | 获取版本号 | 返回 [版本字符串, 主版本, 次版本] |
| `GetOAPIVersionNumber()` | 获取API版本号 | 返回版本号 |
| `GetModelFilename()` | 获取模型文件名 | 返回文件名 |
| `GetModelFilepath()` | 获取模型文件路径 | 返回完整路径 |
| `GetPresentUnits()` | 获取当前单位 | 返回单位代码 |
| `SetPresentUnits(Units)` | 设置当前单位 | `Units` (int): 单位代码 (见下文) |
| `GetPresentCoordSystem()` | 获取当前坐标系 | 返回坐标系名称 |
| `SetPresentCoordSystem(CoordSys)` | 设置当前坐标系 | `CoordSys` (str): 坐标系名称 |
| `GetProjectInfo()` | 获取项目信息 | |
| `SetProjectInfo(Name, Description, Engineer, Company)` | 设置项目信息 | 各参数为字符串 |
| `GetMergeTol()` | 获取合并容差 | |
| `SetMergeTol(Tol)` | 设置合并容差 | `Tol` (double): 容差值 |
| `GetModelIsLocked()` | 检查模型是否锁定 | 返回 bool |
| `SetModelIsLocked(Locked)` | 设置模型锁定状态 | `Locked` (bool) |
| `Visible(Show)` | 设置可见性 | `Show` (bool) |

---

## File Functions

| Function | Description | Parameters |
|----------|-------------|------------|
| `NewBlank()` | 创建空白模型 | 返回 0=成功 |
| `New2DFrame(TemplateType, NumSpans, SpanLength, NumStories, StoryHeight)` | 创建2D框架 | 见下表 |
| `New3DFrame(TemplateType, NumberOfX, NumberOfZ, SBetweenX, SBetweenZ, NumberOfY, StoryHeight)` | 创建3D框架 | |
| `NewBeam(TemplateType, ...)` | 创建梁 | |
| `NewWall(TemplateType, ...)` | 创建墙 | |
| `NewSolidBlock(TemplateType, ...)` | 创建实体块 | |
| `OpenFile(FileName)` | 打开模型文件 | `FileName` (str): 文件路径 |
| `Save()` | 保存模型 | |
| `SaveAs(FileName)` | 另存为 | `FileName` (str): 文件路径 |

**Template Types (2D Frame):**
- `1` = Simple Beam (简支梁)
- `2` = Portal Frame (门式框架)
- `3` = Moment Frame (刚接框架)
- `4` = V-Braced Frame (V形支撑框架)
- `5` = X-Braced Frame (X形支撑框架)

**New2DFrame 参数说明:**
- `TemplateType` (int): 模板类型 (1-5)
- `NumSpans` (int): 跨数
- `SpanLength` (double): 跨长 [L] (默认单位: kip-in)
- `NumStories` (int): 层数
- `StoryHeight` (double): 层高 [L]

---

## Point Object (节点)

### 创建节点

| Function | Description | Parameters |
|----------|-------------|------------|
| `AddCartesian(X, Y, Z, Name, UserName, CSys, MergeOff, MergeNumber)` | 通过笛卡尔坐标创建 | 见下表 |
| `AddCylindrical(X, Y, Z, Name, UserName, CSys, MergeOff, MergeNumber)` | 通过圆柱坐标创建 | |
| `AddSpherical(X, Y, Z, Name, UserName, CSys, MergeOff, MergeNumber)` | 通过球坐标创建 | |

**AddCartesian 参数说明:**
- `X` (double): X坐标 [L]
- `Y` (double): Y坐标 [L]
- `Z` (double): Z坐标 [L]
- `Name` (str, returned): 程序分配的名称
- `UserName` (str, optional): 用户指定名称
- `CSys` (str, optional): 坐标系，默认 "Global"
- `MergeOff` (bool, optional): False=与同位置点合并
- `MergeNumber` (int, optional): 合并编号

### 获取节点

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetNameList()` | 获取节点列表 | 返回名称数组 |
| `GetCoordCartesian(Name, CSys)` | 获取笛卡尔坐标 | |
| `GetCoordCylindrical(Name, CSys)` | 获取圆柱坐标 | |
| `GetRestraint(Name)` | 获取约束 | 返回 [U1,U2,U3,R1,R2,R3] (bool数组) |
| `GetSpring(Name)` | 获取弹簧 | 返回弹簧属性 |

### 设置约束和弹簧

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetRestraint(Name, U1, U2, U3, R1, R2, R3)` | 设置约束 | 各参数为 bool: True=约束, False=释放 |
| `SetSpring(Name, SpringType, K, K2, K3, K2K3, CSys)` | 设置弹簧 | 见下表 |

**SetRestraint 参数说明:**
- `Name` (str): 节点名称
- `U1` (bool): X方向位移约束
- `U2` (bool): Y方向位移约束
- `U3` (bool): Z方向位移约束
- `R1` (bool): 绕X轴转动约束
- `R2` (bool): 绕Y轴转动约束
- `R3` (bool): 绕Z轴转动约束

**SetSpring 参数说明:**
- `SpringType` (int): 弹簧类型 (1=线性, 2=非线性)
- `K` (double): 主方向刚度 [F/L]
- `K2` (double): 2方向刚度 [F/L]
- `K3` (double): 3方向刚度 [F/L]
- `K2K3` (bool): K2/K3是否耦合
- `CSys` (str): 坐标系

### 节点荷载

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetLoadForce(Name)` | 获取节点荷载 | 返回荷载信息 |
| `SetLoadForce(Name, LoadPat, Direction, Force, Moment, CSys)` | 设置节点荷载 | |
| `GetLoadDispl(Name)` | 获取节点强制位移 | |
| `SetLoadDispl(Name, LoadPat, U1, U2, U3, R1, R2, R3, CSys)` | 设置节点强制位移 | |

**SetLoadForce 参数说明:**
- `Name` (str): 节点名称
- `LoadPat` (str): 荷载模式名称
- `Direction` (int): 方向 (1=Global X, 2=Global Y, 3=Global Z, 4-6=Local)
- `Force` (double): 力值 [F]
- `Moment` (double): 力矩 [F*L]
- `CSys` (str): 坐标系

---

## Frame Object (框架)

### 创建框架

| Function | Description | Parameters |
|----------|-------------|------------|
| `AddByPoint(Point1, Point2, PropName, UserName, CSys)` | 通过两点创建 | |
| `AddByCoord(X1, Y1, Z1, X2, Y2, Z2, Name, PropName, UserName, CSys)` | 通过坐标创建 | |

**AddByCoord 参数说明:**
- `X1, Y1, Z1` (double): I端(起点)坐标 [L]
- `X2, Y2, Z2` (double): J端(终点)坐标 [L]
- `Name` (str, returned): 框架名称
- `PropName` (str): 截面属性名称 ("Default"或"None"或具体名称)
- `UserName` (str): 用户指定名称
- `CSys` (str): 坐标系

### 获取框架信息

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetNameList()` | 获取框架列表 | |
| `GetPoints(Name)` | 获取端点 | 返回 [Point1, Point2] |
| `GetProperty(Name)` | 获取截面 | 返回截面名称 |
| `GetLocalAxes(Name)` | 获取局部轴 | 返回 [Angle, isMirrored, Axis] |
| `GetReleases(Name)` | 获取释放 | 返回 [I1,I2,I3,J1,J2,J3] (端部释放) |

### 框架荷载

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetLoadPoint(Name, LoadPat, Direction, Distance, DistanceType, Force)` | 设置点荷载 | |
| `SetLoadDistributed(Name, LoadPat, Direction, StartDist, EndDist, StartValue, EndValue, DistanceType)` | 设置分布荷载 | |
| `SetLoadTemperature(Name, LoadPat, Temp, TempPattern)` | 设置温度荷载 | |
| `SetLoadGravity(Name, LoadPat, X, Y, Z)` | 设置重力荷载 | |

**SetLoadPoint 参数说明:**
- `Name` (str): 框架名称
- `LoadPat` (str): 荷载模式名称
- `Direction` (int): 方向 (1=Global X, 2=Global Y, 3=Global Z, 4=Local 1, 5=Local 2, 6=Local 3)
- `Distance` (double): 到I端的距离
- `DistanceType` (int): 1=相对(0-1), 2=绝对距离
- `Force` (double): 荷载值 [F]

**SetLoadDistributed 参数说明:**
- `StartDist` (double): 起始距离
- `EndDist` (double): 结束距离
- `StartValue` (double): 起始荷载值 [F/L]
- `EndValue` (double): 结束荷载值 [F/L]

---

## Area Object (面单元)

### 创建面单元

| Function | Description | Parameters |
|----------|-------------|------------|
| `AddByPoint(Point1, Point2, Point3, PointName, PropName, UserName, CSys)` | 通过点创建 | |
| `AddByCoord(Coordinates, PropName, UserName, CSys)` | 通过坐标创建 | |

### 获取面单元信息

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetNameList()` | 获取列表 | |
| `GetThickness(Name, ThickType)` | 获取厚度 | |
| `GetProperty(Name)` | 获取属性 | |

### 面荷载

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetLoadUniform(Name, LoadPat, Dir, Value, PressurePattern)` | 均匀荷载 | |
| `SetLoadTemperature(Name, LoadPat, Temp, TempPattern)` | 温度荷载 | |
| `SetLoadGravity(Name, LoadPat, X, Y, Z)` | 重力荷载 | |

**SetLoadUniform 参数说明:**
- `Dir` (int): 方向 (1-6, 同框架荷载)
- `Value` (double): 荷载值 [F/L²]
- `PressurePattern` (str): 压力模式名称 (可选)

---

## Link Object (连接)

### 创建连接

| Function | Description | Parameters |
|----------|-------------|------------|
| `AddByPoint(Point1, Point2, PropName, Name, UserName, CSys)` | 通过点创建 | |
| `AddByCoord(X1, Y1, Z1, X2, Y2, Z2, PropName, Name, UserName, CSys)` | 通过坐标创建 | |

### 获取/设置连接属性

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetProperty(Name)` | 获取属性 | |
| `SetProperty(Name, PropName)` | 设置属性 | `PropName` (str): 连接属性名称 |

---

## Load Patterns (荷载模式)

### 创建荷载模式

| Function | Description | Parameters |
|----------|-------------|------------|
| `Add(Name, Type, SelfWtMultiplier)` | 添加荷载模式 | |

**Add 参数说明:**
- `Name` (str): 荷载模式名称
- `Type` (int): 荷载类型
  - `1` = DEAD (恒荷载)
  - `2` = SuperDead (附加恒荷载)
  - `3` = LIVE (活荷载)
  - `4` = REDUCED_LIVE (折减活荷载)
  - `5` = QUAKE (地震荷载)
  - `6` = WIND (风荷载)
  - `7` = SNOW (雪荷载)
  - `8` = OTHER (其他)
- `SelfWtMultiplier` (double): 自重系数 (0=不考虑, 1=全部)

### 获取/设置荷载模式

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetNameList()` | 获取列表 | |
| `GetLoadType(Name)` | 获取类型 | |
| `GetSelfWtMultiplier(Name)` | 获取自重系数 | |
| `SetLoadType(Name, LoadType)` | 设置类型 | |
| `SetSelfWtMultiplier(Name, Mult)` | 设置自重系数 | |

---

## Load Cases (工况)

### 静力分析工况

| Function | Description | Parameters |
|----------|-------------|------------|
| `StaticLinear.Add(Name, LoadPattern, Type, Auto)` | 创建静力线性工况 | |
| `StaticLinear.SetLoadFactor(Name, LoadFactor)` | 设置荷载系数 | |

**StaticLinear.Add 参数说明:**
- `Name` (str): 工况名称
- `LoadPattern` (str): 荷载模式名称
- `Type` (int): 类型 (1=Linear Static, 等)
- `Auto` (bool): 是否自动计算

### 模态分析工况

| Function | Description | Parameters |
|----------|-------------|------------|
| `Modal.Add(Name, MaxCycles, MaxIter, MinFreq, MaxFreq, Cutoff)` | 创建模态工况 | |
| `Modal.SetNumberOfModes(Name, NumModes)` | 设置模态数 | |

### 反应谱工况

| Function | Description | Parameters |
|----------|-------------|------------|
| `ResponseSpectrum.Add(Name, LoadPattern, Type, ModalCase)` | 创建反应谱工况 | |
| `ResponseSpectrum.SetDirection(Name, Dir, Eccen)` | 设置方向 | |
| `ResponseSpectrum.SetSpectrum(Name, SpecType, SpecFile)` | 设置反应谱 | |

### 线性时程分析

| Function | Description | Parameters |
|----------|-------------|------------|
| `TimeHistoryLinear.Add(Name, LoadPattern, Type, ModalCase)` | 创建线性时程 | |
| `TimeHistoryLinear.SetTimeStep(Name, Dt, Steps)` | 设置时间步 | |

---

## Analysis (分析)

### 运行分析

| Function | Description | Parameters |
|----------|-------------|------------|
| `RunAnalysis()` | 运行分析 | 返回 0=成功 |
| `CreateAnalysisModel()` | 创建分析模型 | |

### 分析选项

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetActiveDOF(DOF1, DOF2, DOF3, DOF4, DOF5, DOF6)` | 设置有效自由度 | |
| `GetActiveDOF()` | 获取有效自由度 | |

**SetActiveDOF 参数说明:**
- `DOF1` - `DOF6` (bool): 各方向是否有效
  - DOF1: U1 (X位移)
  - DOF2: U2 (Y位移)
  - DOF3: U3 (Z位移)
  - DOF4: R1 (绕X转角)
  - DOF5: R2 (绕Y转角)
  - DOF6: R3 (绕Z转角)

### 工况控制

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetRunCaseFlag(CaseName, Run)` | 设置是否运行 | `Run` (bool) |
| `GetCaseStatus(CaseName)` | 获取工况状态 | |

---

## Results (结果)

### 框架内力

| Function | Description | Parameters |
|----------|-------------|------------|
| `FrameForce(FrameName, ItemType, LoadCase)` | 获取框架内力 | |

**返回值:**
- `P` (double): 轴力 [F]
- `V2` (double): 剪力V2 (局部2方向) [F]
- `V3` (double): 剪力V3 (局部3方向) [F]
- `T` (double): 扭矩 [F*L]
- `M2` (double): 弯矩M2 (绕2轴) [F*L]
- `M3` (double): 弯矩M3 (绕3轴) [F*L]

**参数说明:**
- `FrameName` (str): 框架名称
- `ItemType` (int): 0=All, 1=Object, 2=Element
- `LoadCase` (str): 荷载工况名称

### 节点位移

| Function | Description | Parameters |
|----------|-------------|------------|
| `JointDispl(JointName, ItemType, LoadCase)` | 获取节点位移 | |

**返回值:**
- `U1, U2, U3` (double): 三个方向位移 [L]
- `R1, R2, R3` (double): 三个方向转角 [弧度]

### 支座反力

| Function | Description | Parameters |
|----------|-------------|------------|
| `JointReact(JointName, ItemType, LoadCase)` | 获取支座反力 | |

**返回值:**
- `F1, F2, F3` (double): 三个方向反力 [F]
- `M1, M2, M3` (double): 三个方向反力矩 [F*L]

### 节点加速度/速度

| Function | Description | Parameters |
|----------|-------------|------------|
| `JointAcc(JointName, ItemType, LoadCase)` | 获取节点加速度 | |
| `JointVel(JointName, ItemType, LoadCase)` | 获取节点速度 | |

### 模态结果

| Function | Description | Parameters |
|----------|-------------|------------|
| `ModalPeriod(FrameName, ItemType, LoadCase)` | 获取模态周期 | |
| `ModeShape(FrameName, ItemType, LoadCase)` | 获取振型 | |
| `ModalParticipatingMassRatios(...)` | 获取模态参与质量比 | |

### 链接单元结果

| Function | Description | Parameters |
|----------|-------------|------------|
| `LinkDeformation(LinkName, ItemType, LoadCase)` | 获取链接变形 | |
| `LinkForce(LinkName, ItemType, LoadCase)` | 获取链接力 | |

### 面单元结果

| Function | Description | Parameters |
|----------|-------------|------------|
| `AreaStressShell(AreaName, ItemType, LoadCase)` | 获取壳单元应力 | |
| `AreaForceShell(AreaName, ItemType, LoadCase)` | 获取壳单元力 | |

---

## Select (选择)

| Function | Description | Parameters |
|----------|-------------|------------|
| `All()` | 全选 | |
| `ClearSelection()` | 清除选择 | |
| `Object(Name, Type)` | 按名称选择 | `Type`: 0=Point, 1=Frame, 2=Area, 3=Link |
| `Group(GroupName)` | 按组选择 | |
| `InvertSelection()` | 反选 | |
| `GetSelected()` | 获取选中对象 | |

---

## Material Properties (材料)

### 钢材

| Function | Description | Parameters |
|----------|-------------|------------|
| `AddMaterial(Name, MatType, Grade, Type, Notes)` | 添加材料 | |
| `SetOSteel_1(Name, Fy, Fu, eFy, eFu, SSType, SSHysType, ...)` | 设置钢材属性(推荐) | |
| `SetSteel(Name, Fy, Fu, E, G, Density, ThermalCoeff, SteelType)` | 设置钢材属性(旧版) | |

**AddMaterial 参数说明:**
- `Name` (str): 材料名称
- `MatType` (int): 材料类型
  - `1` = Aluminum
  - `2` = Steel
  - `3` = Concrete
  - `4` = Tendon
  - `5` = Masonry
  - `6` = ColdFormed
  - `7` = Rebar
  - `8` = Other
- `Grade` (str): 规范/等级，如 "China"
- `Type` (str): 子类型，如 "Q355"

**SetOSteel_1 参数说明:**
- `Name` (str): 材料名称
- `Fy` (double): 屈服强度 [ksi]
- `Fu` (double): 极限强度 [ksi]
- `eFy` (double): 预期屈服强度 [ksi]
- `eFu` (double): 预期极限强度 [ksi]
- `SSType` (int): 1=Steel, 2=Concrete Encased, 3=Concrete Filled
- `SSHysType` (int): 滞回类型 (1=Kinematic, 2=Isotropic, 3=Custom)
- `StrainAtHardening` (double): 硬化时应变
- `StrainAtMaxStress` (double): 最大应力时应变
- `StrainAtRupture` (double): 断裂时应变
- `FinalSlope` (double): 极限斜率

### 混凝土

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetConcrete(Name, fc, E, G, Density, IsLightweight, FcsFactor)` | 设置混凝土属性 | |

**参数说明:**
- `fc` (double): 抗压强度 [psi]
- `IsLightweight` (bool): 是否轻质混凝土
- `FcsFactor` (double): 折减系数

### 铝材

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetAluminum(Name, Fy, Fu, E, G, Density, ThermalCoeff)` | 设置铝材属性 | |

### 获取材料

| Function | Description | Parameters |
|----------|-------------|------------|
| `GetNameList()` | 获取材料列表 | |
| `GetType(Name)` | 获取材料类型 | |

---

## Section Properties (截面)

### 框架截面

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetISection(Name, tfs, tft, w, bfb, bft, d, Area, I33, I22, S33, S22, Z33, Z22)` | I型截面 | |
| `SetRectangle(Name, t3, t2, Area, I33, I22, S33, S22, Z33, Z22, J)` | 矩形截面 | |
| `SetCircle(Name, t3, Area, I33, I22, ...)` | 圆形截面 | |
| `SetBox(Name, t3, t2, tf, tw, Area, I33, I22, ...)` | 箱型截面 | |
| `SetAngle(Name, t3, t2, tf, tw, Area, I33, I22, ...)` | 角钢截面 | |
| `SetPipe(Name, MatProp, t3, tw)` | 圆管截面 | |
| `SetChannel(Name, t3, t2, tf, tw, Area, I33, I22, ...)` | 槽钢截面 | |
| `SetGeneral(Name, Area, I33, I22, S33, S22, Z33, Z22, J)` | 自定义截面 | |

**SetPipe 参数说明:**
- `Name` (str): 截面名称
- `MatProp` (str): 材料属性名称
- `t3` (double): 外径 [L]
- `t3` (double): 壁厚 [L]

**SetRectangle 参数说明:**
- `t3` (double): 截面高度 [L]
- `t2` (double): 截面宽度 [L]

**SetISection 参数说明:**
- `tfs`: 上翼缘宽度
- `tft`: 上翼缘厚度
- `w`: 腹板厚度
- `bfb`: 下翼缘宽度
- `bft`: 下翼缘厚度
- `d`: 截面高度
- `Area`: 面积 [L²]
- `I33, I22`: 惯性矩 [L⁴]
- `S33, S22`: 截面模量 [L³]
- `Z33, Z22`: 塑性截面模量 [L³]

### 面截面

| Function | Description | Parameters |
|----------|-------------|------------|
| `SetSlab(Name, SlabType, Thickness, MatProp)` | 板截面 | |
| `SetWall(Name, WallType, Thickness, MatProp)` | 墙截面 | |

**参数说明:**
- `SlabType` (int): 板类型 (1=Plate, 2=Shell, 等)
- `WallType` (int): 墙类型
- `Thickness` (double): 厚度 [L]
- `MatProp` (str): 材料名称

---

## Complete Example: Portal Frame Analysis

```python
import comtypes.client as client

def create_and_analyze_portal():
    """创建并分析2D门式框架"""

    # 连接SAP2000
    SapObject = client.CreateObject("CSI.SAP2000.API.SapObject")
    SapObject.ApplicationStart(True)
    SapModel = SapObject.SapModel

    # 初始化
    SapModel.InitializeNewModel()

    # 创建2D门式框架 (Portal Frame)
    # Template=2, 3跨, 跨长480in, 3层, 层高144in
    SapModel.File.New2DFrame(2, 3, 480, 3, 144)

    # 添加荷载模式
    SapModel.LoadPatterns.Add("DEAD", 1, 1.0)  # 恒荷载
    SapModel.LoadPatterns.Add("LIVE", 3, 0.0)  # 活荷载

    # 获取框架列表并施加荷载
    ret, FrameNames = SapModel.FrameObj.GetNameList()
    for frame in FrameNames:
        SapModel.FrameObj.SetLoadDistributed(
            frame, "DEAD", 2, 0, 1, -1.0, -1.0, 1
        )

    # 运行分析
    SapModel.Analyze.RunAnalysis()

    # 提取结果
    for frame in FrameNames:
        ret, Obj, Elm, LoadCase, StepType, StepNum, \
            P, V2, V3, T, M2, M3 = SapModel.Results.FrameForce(frame, 0, "DEAD")
        print(f"Frame: {frame}, M2(端部)={M2}")

    # 保存
    SapModel.File.SaveAs(r"C:\temp\portal.sdb")

    # 断开
    SapObject.ApplicationExit(False)
    SapModel = None
    SapObject = None

if __name__ == "__main__":
    create_and_analyze_portal()
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 0 | Success (成功) |
| -1 | Error (错误) |
| 1 | Warning (警告) |

---

## Units

| Code | Unit | 说明 |
|------|------|------|
| 1 | kip-in | 千磅-英寸 |
| 2 | kip-ft | 千磅-英尺 |
| 3 | N-mm | 牛顿-毫米 |
| 4 | N-m | 牛顿-米 |
| 5 | kgf-mm | 千克-毫米 |
| 6 | kgf-m | 千克-米 |
| 7 | Ton-mm | 吨-毫米 |
| 8 | Ton-m | 吨-米 |
| 9 | kN-cm | 千牛-厘米 |
| 10 | kN-m | 千牛-米 |
| 11 | kN-mm | 千牛-毫米 |

---

## Quick Reference Card

```python
# === 快速连接 ===
SapObject = client.CreateObject("CSI.SAP2000.API.SapObject")
SapObject.ApplicationStart(True)
SapModel = SapObject.SapModel
SapModel.InitializeNewModel()

# === 常用操作 ===
SapModel.File.NewBlank()
SapModel.File.OpenFile(path)
SapModel.File.Save()
SapModel.File.SaveAs(path)

SapModel.PointObj.AddCartesian(x, y, z)
SapModel.FrameObj.AddByPoint(p1, p2, "截面名")
SapModel.AreaObj.AddByPoint(p1, p2, p3, p4, "属性名")

SapModel.LoadPatterns.Add("DEAD", 1, 1.0)
SapModel.FrameObj.SetLoadDistributed(frame, "DEAD", 2, 0, 1, -1, -1, 1)

SapModel.Analyze.RunAnalysis()

ret, data = SapModel.Results.FrameForce(frame, 0, "DEAD")
ret, data = SapModel.Results.JointDispl(joint, 0, "DEAD")
ret, data = SapModel.Results.JointReact(joint, 0, "DEAD")

# === 断开 ===
SapObject.ApplicationExit(False)
SapModel = None
SapObject = None
```

---

*Generated from CSI_OAPI_Documentation.chm*
*Location: CSI_OAPI_extracted/SAP2000_API_Fuctions/*