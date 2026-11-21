# 常用操作示例

内容整理自官方 openstaadpy 示例脚本(建模 / 取结果 / 视图与选择),**「连接 → 单位 → 几何 → 截面/材料 → 端部释放 → 支座 → 荷载 → 分析 → 读结果」各章节即标准全流程,新建模型按章节顺序连起来写即可**。所有示例默认已执行过准备代码,`s` 即连接好的会话:

```python
from openstaadpy import os_analytical

try:
    s = os_analytical.connect()    # 前提:STAAD.Pro 已打开且加载了模型
except Exception as e:
    print(f"连接 STAAD.Pro 失败: {e}")   # 结束执行,请用户先打开软件和目标模型
```

## 连接与基本信息

```python
s.GetSTAADFile()             # 当前 .std 完整路径
s.GetApplicationVersion()    # 如 '25.0.0.x'
s.GetBaseUnit()              # 'English' 或 'Metric' —— 建模/读数前先确认!
s.GetInputUnitForLength()    # 如 'Meter' / 'Feet'
s.GetInputUnitForForce()     # 如 'KiloNewton' / 'Kilopound'

# 指定模型(该 .std 必须已在某个 STAAD.Pro 实例中打开;connect 不会启动软件)
s2 = os_analytical.connect(r"C:\models\tower.std")
```

## 单位设置

```python
# 长度 0=Inch 1/2=Feet 3=cm 4=Meter 5=mm 6=dm 7=km;力 0=Kip 1=Pound 2=kg 3=t 4=N 5=kN 6=MN 7=daN
s.SetInputUnits(1, 0)        # 英尺 + Kip(官方示例的英制)
s.SetInputUnits(4, 5)        # 米 + 千牛(国内常用)
s.SaveModel(True)            # 官方示例在改单位后随手保存
```

## 几何:节点与杆件

用自动编号的 `Add*` 系列建对象、取其返回值作为新编号。

```python
# 自动编号建对象(返回新分配的编号),不要自己挑编号
n1 = s.Geometry.AddNode(0.0, 0.0, 0.0)          # (x, y, z) 单位=当前长度单位
n2 = s.Geometry.AddNode(30.0, 0.0, 0.0)
n3 = s.Geometry.AddNode(0.0, 20.0, 0.0)

b1 = s.Geometry.AddBeam(n1, n3)                  # (起始节点, 终止节点) -> 新杆件号
new_plate = s.Geometry.AddPlate(n1, n2, n3)      # (节点A,B,C,D=0) -> 新板号;三角板第4节点传0
# new_solid = s.Geometry.AddSolid(n1,n2,n3,n4,n5,n6,n7,n8)  # 八节点实体,后两节点可传0

# 查询(返回原生 int / list / tuple)
s.Geometry.GetNodeCount();  s.Geometry.GetMemberCount()
s.Geometry.GetNodeList();   s.Geometry.GetBeamList()     # list[int]
s.Geometry.GetNodeCoordinates(1)                         # (x, y, z)
s.Geometry.GetMemberIncidence(1)                         # (起节点, 终节点)
```

## 截面、材料与 β 角

```python
# 从国家型钢库建截面属性 → property_id;截面名必须与型钢库完全一致(含大小写:
# 国标 H 型钢是小写 x 如 "HW250x250",角钢是大写 X 如 "L30X30X4")
# 拿不准的名字先本地枚举核实(读包内 Profiles/*.db3,不走 COM):
s.Property.GetProfileDatabaseList()                       # 有哪些型钢库(含 country_code)
s.Property.GetProfileSectionTableList(5)                  # 5=Chinese:各截面表(类型)与截面数
s.Property.GetProfileSectionNameList(5, keyword="HW250")  # ['HW250x250', 'HW250x255']
s.Property.GetProfileSectionNameList(5, shape="Angle")    # 全部角钢名(shape 还有 "Wide Flange"/"HSS Round" 等)

# 国家代码/类型参数全表查 get_function_detail.py CreateBeamPropertyFromTable
cc = 1                                                   # 官方示例:1=American(5=Chinese)
w14 = s.Property.CreateBeamPropertyFromTable(cc, "W14X90", 0, 0.0, 0.0)
s.Property.AssignBeamProperty([1, 3, 4], w14)            # 杆件号 list 直接传

# 角钢用专用函数
angle = s.Property.CreateAnglePropertyFromTable(cc, "L40404", 0, 0.0)
s.Property.AssignBeamProperty(list(range(14, 24)), angle)

# 内置材料名直接赋(STEEL / CONCRETE / ALUMINUM 等)
s.Property.AssignMaterialToMember("STEEL", list(range(1, 24)))

# β 角(度):截面绕杆轴旋转
s.Property.AssignBetaAngle([3, 4], 90.0)
```

## 杆件端部释放(铰接/半刚接)

```python
# 完全释放:位置 0=起端 1=终端;[FX,FY,FZ,MX,MY,MZ] 1=释放;第三参数为对应弹簧刚度(纯铰给 0)
start_mz = s.Property.CreateMemberReleaseSpec(0, [0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0])
s.Property.AssignMemberSpecToBeam([5], start_mz)

# 部分释放(半刚接):[MPX,MPY,MPZ],factor 为对应释放比例 0~1;起、终两端各建各派
start_my_mz = s.Property.CreateMemberPartialReleaseSpec(0, [0, 1, 1], [0.0, 0.99, 0.99])
end_my_mz   = s.Property.CreateMemberPartialReleaseSpec(1, [0, 1, 1], [0.0, 0.99, 0.99])
s.Property.AssignMemberSpecToBeam(list(range(14, 24)), start_my_mz)
s.Property.AssignMemberSpecToBeam(list(range(14, 24)), end_my_mz)
```

桁架/仅拉/仅压等行为规格(`CreateMemberTrussSpec` 等)同模式:先 Create 得 id,再 `AssignMemberSpecToBeam`。

## 支座

```python
fixed_id  = s.Support.CreateSupportFixed()       # 返回支座规格 id
pinned_id = s.Support.CreateSupportPinned()
s.Support.AssignSupportToNode([1], fixed_id)     # 单个 int 或 list 都可
s.Support.AssignSupportToNode([2], pinned_id)
```

## 荷载:工况、加载与组合

```python
# 新建主工况:(标题, 荷载类型, 工况号) → 返回工况号,0=失败
# 类型:0=Dead 1=Live 2=RoofLive 3=Wind 4=Seismic-H 5=Seismic-V…全表查 db
case1 = s.Load.CreateNewPrimaryLoadEx2("DEAD AND LIVE LOAD", 0, 1)
s.Load.SetLoadActive(case1)              # ⚠️ 先激活目标工况,后续加载都进入该工况

s.Load.AddSelfWeightInXYZ(2, -1.0)       # 自重:方向 1=X 2=Y 3=Z,系数 -1.0=沿 -Y 重力

# 节点荷载:(节点list, FX, FY, FZ, MX, MY, MZ) 单位=当前力/长度单位
s.Load.AddNodalLoad([4], 0.0, -15.0, 0.0, 0.0, 0.0, 0.0)

# 杆件均布荷载:(杆件list, 方向码, 荷载值, d1, d2, d3)
# 方向码 1~9:1/2/3=局部X/Y/Z,4/5/6=整体X/Y/Z,7/8/9=投影X/Y/Z
# d1,d2=荷载起、止点到杆起端距离(0,0=全长),d3=荷载平面偏离剪心距离
s.Load.AddMemberUniformForce(list(range(8, 14)), 2, -0.9, 0.0, 0.0, 0.0)

# 第二个工况(风):同样先建、再激活、后加载
case2 = s.Load.CreateNewPrimaryLoadEx2("WIND FROM LEFT", 3, 2)
s.Load.SetLoadActive(case2)
s.Load.AddMemberUniformForce([1, 2], 4, 0.6, 0.0, 0.0, 0.0)   # 4=整体X

# 荷载组合:先建组合(标题, 组合号),再逐对添加 (组合号, 工况号, 系数)
s.Load.CreateNewLoadCombination("75 PERCENT DL LL WL", 3)
s.Load.AddLoadAndFactorToCombination(3, 1, 0.75)
s.Load.AddLoadAndFactorToCombination(3, 2, 0.75)

# 查询
s.Load.GetPrimaryLoadCaseCount()
s.Load.GetPrimaryLoadCaseNumbers()       # list[int]
```

## 保存与运行分析

⚠️ `AnalyzeEx`/`Analyze` 只启动求解器,**不会写入分析命令**。全部工况和组合建完后,必须先用 `Command.PerformAnalysis(0)` 把 `PERFORM ANALYSIS` 写在所有荷载之后,否则 STAAD 报 `FINISH COMMAND IN LOAD DATA … ANALYSIS COMMAND IS OUT OF ORDER OR MISSING IN CASE NO. n`(FINISH 落在荷载数据里、缺分析命令)。也别在建组合之前就调用它——组合会排到分析命令之后,同样报错。

```python
# 1. 全部工况/组合建完后插入分析命令(整个模型只调一次,且必须在所有荷载之后)
s.Command.PerformAnalysis(0)             # 0=不打印

# 2. 保存(分析前 STAAD 要求模型已存盘)
s.SaveModel(True)

# 3. 运行求解器:silentMode=1 抑制输入弹窗;hiddenMode=0 显示分析框(设 1 隐藏时报错易卡死);waitTillComplete=1 等完成
status = s.AnalyzeEx(1, 0, 1)
# -1=中止 0=错误 1=进行中 2=完成无警告 3=完成有警告 4=有错误 5=尚未分析
if status < 0:
    print("分析失败,状态码:", status)
while s.IsAnalyzing():                   # 官方示例的兜底等待
    pass

# 完成后核对状态,返回 dict:
# {'ReturnValue': 2, 'ReturnString': '...', 'NoOfWarnings': 0, 'NoOfErrors': 0, 'CPUTime': ...}
info = s.GetAnalysisStatus()
if info['ReturnValue'] not in (2, 3):
    # STAAD 2024 起 GetAnalysisErrorMessages() 不可用;直接读同名 .ANL 搜错误(同 SKILL §5 排查链)
    anl_path = s.GetSTAADFile().rsplit(".", 1)[0] + ".ANL"
    with open(anl_path, encoding="utf-8", errors="ignore") as f:
        errs = [ln.strip() for ln in f if "*** ERROR MESSAGE ***" in ln]
    print("\n".join(errs) or "无 *** ERROR MESSAGE ***,见 .ANL 全文")
```

## 读结果(要求分析已完成且成功)

```python
lc = 1                                   # 工况号

# 杆件端力:(杆件号, 端部 0=起|1=终, 工况, 坐标系 0=局部|1=整体) → [FX,FY,FZ,MX,MY,MZ]
# 官方模式:逐条 try/except,报错时打印是哪根杆
for b in s.Geometry.GetBeamList()[:5]:
    try:
        start_forces = s.Output.GetMemberEndForces(b, 0, lc, 0)
        end_forces   = s.Output.GetMemberEndForces(b, 1, lc, 0)
        print(b, start_forces, end_forces)
    except Exception as e:
        print(f"杆件 {b} 读取失败: {e}")

# 支座反力(整体坐标):(节点号, 工况) → [FX,FY,FZ,MX,MY,MZ]
for nid in [1, 2]:
    print(nid, s.Output.GetSupportReactions(nid, lc))

# 节点位移:(节点号, 工况) → [dx,dy,dz,rx,ry,rz]
s.Output.GetNodeDisplacements(16, lc)
```

## 读取用户预选(用"读"不用"等")

```python
sel_beams = s.Geometry.GetSelectedBeams()    # list[int],未选中返回空 list,非阻塞
sel_nodes = s.Geometry.GetSelectedNodes()
if not sel_beams:
    print("请先在 STAAD.Pro 中选好杆件")       # 结束本次执行,不要原地等待
```

## 程序化选择与组

官方案例链条:按方向选杆 → 读回编号 → 固化为命名组 → 之后随时按组重选:

```python
from openstaadpy.os_analytical.oserrors import OsGroupAlreadyExists

s.View.SelectMembersParallelTo("X")          # 传轴名字符串 "X"/"Y"/"Z"
beams = s.Geometry.GetSelectedBeams()
if beams:
    try:
        s.Geometry.CreateGroupEx(2, "_ParallelX", beams)   # 2=杆件组(组类型全表查 db)
    except OsGroupAlreadyExists:
        s.Geometry.UpdateGroup("_ParallelX", 0, beams)     # 已存在则更新(0=替换 1=移除 2=追加)
    s.Geometry.ClearMemberSelection()

s.View.SelectGroup("_ParallelX")             # 之后随时按组重选
s.Geometry.SelectMultipleBeams([1, 2, 3])    # 或程序直接指定
```

## 保存与导出

```python
s.SaveModel(True)                            # 修改类操作完成后必须保存,否则改动只在内存里

# 结果/导出文件一律落到会话工作目录(python_executor 已注入 WORKSPACE_DIR)
import os
csv_path = os.path.join(WORKSPACE_DIR, "reactions.csv")
```

## 严禁编辑 .std 文件

由于你不可能清楚知道 .std 文件的格式，错误编辑将会带来无法挽回的大崩溃，导致任务彻底失败。**仅当用户明确要求可以编辑`.std`，并且明确告诉了你应该如何编辑，你才可以动这个文件**(属少数情况)。改文件前必须先让 STAAD 释放文件锁,改完再挂回来:

```python
from openstaadpy import os_analytical
import time

# 1. 趁会话有效先取好路径,再把内存改动落盘(不落盘则关闭时丢失)
s = os_analytical.connect()
std_path = s.GetSTAADFile()
s.SaveModel(True)

# 2. 关闭文件释放文件锁(不关直接写会 PermissionError);关闭后 s 这个 COM 会话即失效
s.CloseSTAADFile()
time.sleep(2)                              # Windows 文件锁释放有延迟,这 2 秒不能省

# 3. 读取—修改—写回(读用容错编码,写回统一 utf-8)
with open(std_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
# ... 按需修改 lines ...
with open(std_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

# 4. 重新连接拿新会话,再打开文件(STAAD.Pro 进程没退,connect 仍能挂上)
s = os_analytical.connect()                # 必须重连:上一步的 s 已失效
s.OpenSTAADFile(std_path)

# 5. 读关键数据验证改动已生效,再往下走
print(s.GetSTAADFile())                    # OpenSTAADFile 后首次可能返回空(加载延迟),不影响后续读取
print(s.Load.GetPrimaryLoadCaseNumbers())  # 能读到工况即文件已正确加载、修改已生效
```

要点:① `SaveModel(True)` 必须在 `CloseSTAADFile()` 之前;② 关闭后 COM 会话失效,必须重新 `connect()` 拿新对象;③ `time.sleep(2)` 不可省;④ `OpenSTAADFile()` 后 `GetSTAADFile()` 可能首次返回空,读工况/几何不受影响;⑤ 改完务必读关键数据验证,再继续。
