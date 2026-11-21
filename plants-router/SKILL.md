---
name: plants
version: 1.0.5
display_name: PlantS
display_name_en: PlantS
description: 基于 MCP 通信通道操控工业建筑及工厂结构三维设计环境，支持梁柱斜撑建模、独立基础及工业通廊栈桥自动化装配，配套输煤通廊与结构建模自动化工具链。
description_zh: 基于 MCP 通信通道操控工业建筑及工厂结构三维设计环境，支持梁柱斜撑建模、独立基础及工业通廊栈桥自动化装配，配套输煤通廊与结构建模自动化工具链。
description_en: Controls 3D industrial structural engineering environments via MCP channels, supporting framing members, foundations, and conveyor corridor automation.
license: Apache-2.0
---

# PlantS 操作技能

作为 PlantS 工厂结构建模助手，你的核心任务是通过 PlantS MCP API 帮助用户完成梁、柱、支撑、截面、材料等模型对象的创建、查询和修改。

## 核心工作流：连接 -> 检索 -> 执行

必须按以下顺序操作。

### 第一步：连接 PlantS

在执行任何 PlantS 操作前，先用 `python_executor` 连接 MCP：

```python
# 导入自动化控制接口

result = connect_to_plants()
print(result)
```

返回 `True` 表示连接成功。若用户没有显式指定路径，系统会优先复用已经启动且 MCP 畅通的 PlantS；如果没有可用进程，则自动查找 PlantS，并复制安装目录下的 `Interface\P3DTemplate\temp.p3d` 到当前 workspace 后启动。

如果用户指定了 PlantS 主程序路径或 `.p3d` 工程文件路径，用 `python_executor` 连接 MCP：

```python
# 导入自动化控制接口

result = connect_to_plants(
    exe_path=r"F:\software\GYP\BIMBase.exe",
    project_path=r"F:\software\GYP\test.p3d",
)
print(result)
```

只指定 `exe_path` 时，系统仍会优先复用该 exe 对应的已运行 PlantS；若需从零启动且没有 `project_path`，会打开临时工程。
只指定 `project_path` 时，系统会用已记录或自动发现的 PlantS exe 打开该工程。

连接成功后，系统会自动完成两件事：
1. 将 PlantS MCP 提供的工具函数映射为 Python 函数，注入 `python_executor` 脚本环境。
2. 在 `python_executor` 的返回结果中附带一份 `MCP_Connected` 连接简报，列出可用函数类别与已注入脚本环境的数据结构。

### 第二步：函数检索

连接成功后，用 `function_search` 检索可用函数——它是注入脚本环境的普通函数，不是工具。先从连接简报的“可用函数类别”里选择 `func_type`（也可用 `function_search(action="GetType")` 重取），再获取具体函数说明。PlantS 常用分类包括：`plantsmcp新建`、`plantsmcp修改`、`plantsmcp查询`、`plantsmcp截面`、`plantsmcp独立基础轮廓`、`plantsmcp独立基础截面`。

选择分类后获取函数名：

```python
print(function_search(action="GetName", func_type="plantsmcp新建"))
```

获取函数详细说明：

```python
print(function_search(action="GetDescription", func_type="plantsmcp新建", func_names=["CreateBeam"]))
```

检索策略：
- 在任务开始阶段集中检索所需函数。
- 不要在执行过程中反复零散检索。
- 如果连续 3 次仍找不到足够完成任务的函数，应明确告知用户当前 MCP 能力不足。

### 第三步：脚本编写与执行

确认函数后，在 `python_executor` 中编写 Python 脚本执行。

关键规则：
- 通过 `function_search` 找到的函数已经注入脚本环境，严禁在脚本中 import 这些函数。
- 只有 `print()` 输出会返回给用户，需要展示的信息必须 print。
- 默认单位为 mm，三维点坐标使用 `[x, y, z]`。
- DataKeyRef 通常使用 `{"class_id": "...", "data_id": "..."}` 格式，ID 用字符串表达。

示例：

```python
result = CreateBeam(start_point=[0, 0, 0], end_point=[6000, 0, 0])
print(result)
```

## DataKeyRef 访问规则

PlantS MCP 返回到 `python_executor` 后，`DataKeyRef` 一律按 Python `dict` 使用，不是 Pydantic 对象。正确访问方式：

```python
beam = CreateBeam(start_point=[0, 0, 0], end_point=[6000, 0, 0])
beam_key = beam["beam_key"]
print(beam_key["class_id"], beam_key["data_id"])
```

禁止使用以下对象式访问：

```python
beam.beam_key
beam_key.class_id
beam_key.model_dump()
```

截面相关函数必须使用当前工具名：

```python
section_data = Generate_BarSectionData_Rectangle(width=300, height=300)
section_key = Find_Or_Add_BeamSection(section=section_data)
```


## 判断是否需要重新连接

如果系统提示词中显示 `plantsmcp: 已连接`，说明之前已经建立过连接。若调用函数时报错，先检查连接状态：

```python
print(is_server_connected("plantsmcp"))
```

返回 `False` 时再重新连接。

## IndustryCorridor 通廊自动建模

当用户提到“通廊”、“皮带通廊”、“输煤栈桥”、“桁架通廊”、“工业通廊”、“廊道结构”，并且意图是创建、生成、建模或参数化修改通廊结构时，优先执行内置脚本 `scripts/IndustryCorridor.py`，不要重新从零编写梁、柱、支撑的生成逻辑。

执行前从用户自然语言中提取可识别参数，写入 `INDUSTRY_CORRIDOR_PARAMS`。未提到的参数保持脚本默认值。常用参数如下：

- `length`: 通廊总长度，单位 mm。
- `bay_length` 或 `bay_spacing`: 目标标准节长度，单位 mm，默认 `3500`；当指定 `length` 时，脚本先按此值估算节间数量，再用总长反推均匀的实际标准节长度。
- `num_bays` 或 `bay_count`: 节间数量，仅作为未指定 `length` 时的重复次数；指定 `length` 时会被脚本按 `bay_length` 自动反算，通常不要从用户自然语言中提取这个参数。
- `width`: 横向宽度，单位 mm。
- `truss_height` 或 `height`: 桁架高度，单位 mm。
- `slope_angle_deg` 或 `slope`: 倾斜角度，单位度。
- `origin`: 起点坐标 `[x, y, z]`，单位 mm。
- `side_v_apex`: 侧面 V 形斜杆顶点位置，可选 `"bottom"` 或 `"top"`。
- `reverse_end_diagonals`: 每个廊身跨度两端相邻斜杆是否反向。
- `support_span_m`: 自动布置支撑柱时的廊身跨度/支架间距，单位 m，默认 `30`；推荐 `20-36`，最大不超过 `60`，脚本会落到标准节节点并尽量均分总长。
- `support_indices`: 支撑柱所在节点编号列表；不传或传 `None` 时按 `support_span_m` 自动布置，传 `[]` 时不建支撑柱。
- `ground_z`: 支撑柱柱脚标高，也是独立基础顶标高，单位 mm。
- `create_foundations`: 是否在支撑柱底部创建独立基础，默认 `True`。
- `foundation_type`: 独立基础类型，默认 `"StepCast"`。
- `foundation_steps`: 独立基础台阶列表，默认二阶矩形基础：`2200x2200x500`、`1400x1400x400`，单位 mm。
- `foundation_angle_deg`: 独立基础角度，单位度，默认 `0`。
- `chord_section`, `web_section`, `cross_brace_section`, `support_section`: 弦杆、腹杆、交叉支撑、支架截面名称。
- `material`: 材料名称。

执行模板：

```python
from pathlib import Path
import CADAgent

INDUSTRY_CORRIDOR_PARAMS = {
    "length": 36000,
    "bay_length": 3500,
    "width": 3000,
    "height": 3800,
    "slope": 14,
}

script_path = (
    Path(CADAgent.__file__).resolve().parent
    / "skills"
    / "PlantS-Link"
    / "scripts"
    / "IndustryCorridor.py"
)

exec(compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec"), globals())
```

如果用户显式指定 PlantS 主程序或工程文件，可在执行脚本前设置：

```python
INDUSTRY_CORRIDOR_EXE_PATH = r"F:\software\GYP\BIMBase.exe"
INDUSTRY_CORRIDOR_PROJECT_PATH = r"F:\software\GYP\test.p3d"
```

不要长期记录用户指定的 `project_path`。脚本内部会调用 `connect_to_plants()`，自动复用已连接 PlantS，或按配置/注册表发现 PlantS 并打开工程。