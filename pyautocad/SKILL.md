---
name: pyautocad
description: Use when using Python with pyautocad to connect to AutoCAD, iterate layouts or drawing objects, prompt for selection, use APoint and typed arrays, work with documented utility helpers, or import and export tabular data through the documented API.
---

# pyautocad

## Overview

这个 skill 只覆盖 `pyautocad` 官方文档明确出现的内容，不把 AutoCAD ActiveX 全量接口误写成 pyautocad 自带 API。

核心原则：
- `pyautocad` 是 AutoCAD COM 自动化的轻量 Python 封装
- `pyautocad` 负责连接、常用遍历、点对象、类型数组、少量辅助工具
- 具体绘图方法如 `AddLine`、`AddCircle` 等，本质上来自 AutoCAD COM/ActiveX 对象本身，不是 pyautocad 额外发明的新接口

## When to Use

适用场景：
- 需要从 Python 连接已打开的 AutoCAD，或按需启动 AutoCAD
- 需要遍历模型空间对象，并按对象名过滤
- 需要遍历布局或在图纸中查找首个匹配对象
- 需要让用户在 AutoCAD 里手选对象
- 需要用 `APoint` 做点坐标和向量运算
- 需要用 `aDouble`、`aInt`、`aShort` 传 COM 所需数组
- 需要导入导出表格数据文件，或批量写 AutoCAD 表格时做性能优化
- 需要通过 `Cached` 或 `iter_objects_fast` 优化大量对象读取速度

不适用场景：
- 把 AutoCAD 所有 COM 方法都当作 pyautocad 官方 API 说明
- 没有核对 AutoCAD ActiveX 文档，就断言某个 `Add*`、标注、三维建模、图层、选择集接口一定可用
- 编造 pyautocad 文档里不存在的模块、参数或辅助函数

## Quick Start

```python
from pyautocad import Autocad, APoint

acad = Autocad(create_if_not_exists=True, visible=True)
acad.prompt("Hello, AutoCAD from Python!\n")

print(acad.app.Name)
print(acad.doc.Name)
print(acad.model.Count)

p1 = APoint(0, 0)
p2 = APoint(10, 5)
print(p1 + p2)
print(p1.distance_to(p2))
```

说明：
- `Autocad(create_if_not_exists=False, visible=True)` 是官方文档给出的构造参数
- `acad.app`、`acad.doc`、`acad.model` 是官方文档明确列出的常用入口
- `prompt()` 会向 AutoCAD 命令行输出文本
- 官网 `usage` 页面示例直接通过 `acad.model.AddText(...)`、`AddLine(...)`、`AddCircle(...)` 调用 AutoCAD COM 方法

## Core API

### 1. 连接 AutoCAD

```python
from pyautocad import Autocad

acad = Autocad()
acad = Autocad(create_if_not_exists=True)
acad = Autocad(visible=False)
```

常用属性：
- `acad.app`: AutoCAD Application COM 对象
- `acad.doc`: 当前 ActiveDocument
- `acad.ActiveDocument`: `acad.doc` 的同义入口
- `acad.Application`: `acad.app` 的同义入口
- `acad.model`: ModelSpace

常用方法：
- `acad.prompt(text)`: 在 AutoCAD 命令行输出信息

### 2. 遍历布局

```python
for layout in acad.iter_layouts():
    print(layout.Name)
```

要点：
- `iter_layouts(doc=None, skip_model=True)` 在 API 文档中明确列出
- 默认跳过 `ModelSpace`

## 3. 遍历对象

```python
for obj in acad.iter_objects():
    print(obj.ObjectName)

for text in acad.iter_objects("Text"):
    print(text.TextString)
```

要点：
- `iter_objects()` 遍历模型空间对象
- 可传对象名片段过滤，如 `"Text"`、`"Line"`
- 也可传对象名列表，如 `["Text", "Line"]`
- 返回的是最佳接口转换后的对象

更快但更“裸”的版本：

```python
for obj in acad.iter_objects_fast():
    print(obj.ObjectName)
```

适合大量对象读取；如果需要更稳定的属性访问，优先用 `iter_objects()`。

## 4. 查找首个匹配对象

```python
def text_contains_3(text_obj):
    return "3" in text_obj.TextString

text = acad.find_one("Text", predicate=text_contains_3)
if text:
    print(text.TextString)
```

说明：
- `find_one(object_name_or_list, container=None, predicate=None)` 在 `usage` 与 `api` 页面都出现了
- 未找到时返回 `None`

## 5. 选择对象

```python
for obj in acad.get_selection():
    print(obj.ObjectName)
```

要点：
- `get_selection()` 会提示用户在 AutoCAD 中手动选择对象
- 可选参数 `text` 用于自定义提示语
- 默认提示语是 `"Select objects"`

```python
for obj in acad.get_selection("Select objects"):
    print(obj.ObjectName)
```

## 6. 最佳接口转换

```python
for obj in acad.iter_objects(dont_cast=True):
    obj = acad.best_interface(obj)
    print(obj.ObjectName)
```

说明：
- `best_interface(obj)` 用于把原始 COM 对象转换成更易用的最佳接口
- 当你为了性能先关闭自动转换时，这个方法很有用

## 7. APoint

```python
from pyautocad import APoint

p1 = APoint(10, 20)
p2 = APoint(30, 40, 5)

print(p1.x, p1.y, p1.z)
print(p1 + p2)
print(p2 - p1)
print(p1 * 2)
print(p1 / 2)
print(tuple(p1))
print(p1.distance_to(p2))
```

要点：
- `APoint` 是三维点/向量辅助类
- 支持常见算术运算
- 支持从可迭代对象构造，如 `APoint([10, 20, 30])`
- 常用于传给 AutoCAD COM 方法，如 `AddLine(APoint(...), APoint(...))`

也可使用文档中的距离函数：

```python
from pyautocad.types import distance

print(distance((0, 0, 0), (3, 4, 0)))
```

## 8. COM 数组辅助

```python
from pyautocad import aDouble, aInt, aShort

coords = aDouble(0, 0, 0, 100, 0, 0, 100, 50, 0)
ints = aInt(1, 2, 3)
shorts = aShort(4, 5, 6)
```

用途：
- `aDouble`: 浮点数组，常用于坐标序列
- `aInt`: 整数数组
- `aShort`: 短整数数组

这些类型主要用于满足 COM 接口的参数要求。

也可以通过 `Autocad.aDouble(...)`、`Autocad.aInt(...)`、`Autocad.aShort(...)` 调用这些快捷入口。

## 9. ACAD 常量

```python
from pyautocad import ACAD

for text in acad.iter_objects("Text"):
    old_point = APoint(text.InsertionPoint)
    text.Alignment = ACAD.acAlignmentRight
    text.TextAlignmentPoint = old_point
```

说明：
- `ACAD` 是 AutoCAD 类型库常量入口
- `usage` 页面用它演示了文本对齐方式设置

## 10. 性能与便利工具

### timing

```python
from pyautocad.utils import timing

with timing("iterate objects"):
    for obj in acad.iter_objects_fast():
        pass
```

用于简单测量代码执行时间。

### Cached

```python
from pyautocad.cache import Cached

for obj in acad.iter_objects("Text"):
    cached = Cached(obj)
    print(cached.TextString)
```

适用场景：
- 大量重复读取同一 COM 对象属性
- 希望减少跨 COM 边界反复取值造成的性能损耗

### suppressed_regeneration_of

```python
from pyautocad import ACAD
from pyautocad.utils import suppressed_regeneration_of

table = acad.model.AddTable(pos, rows, columns, row_height, col_width)
with suppressed_regeneration_of(table):
    table.SetAlignment(ACAD.acDataRow, ACAD.acMiddleCenter)
    for row in range(rows):
        for col in range(columns):
            table.SetText(row, col, "%s %s" % (row, col))
```

说明：
- 这是官网 `usage` 和 `api` 都明确给出的表格性能优化方式
- 用于大量修改 AutoCAD Table 对象时减少重生成开销

### 文字处理辅助

官网 API 还列出这些 `utils` 函数：
- `unformat_mtext(s, exclude_list=('P', 'S'))`
- `mtext_to_string(s)`
- `string_to_mtext(s)`
- `text_width(text_item)`
- `dynamic_print(text)`

其中 `unformat_mtext` / `mtext_to_string` 适合处理 MText 格式串。

## 11. 表格数据导入导出

```python
from pyautocad.contrib.tables import Table

table = Table()
for obj in acad.iter_objects("Text"):
    x, y, z = obj.InsertionPoint
    table.writerow([obj.TextString, x, y, z])

table.save("data.xls", "xls")
data = Table.data_from_file("data.xls")
print(data)
```

说明：
- `contrib.tables.Table` 用于导入导出通用表格数据，不是官网文档中的 AutoCAD Table 对象包装器
- 官方文档支持的格式包括 `csv`、`xls`、`xlsx`（只写）、`json`
- `usage` 页面说明：要使用表格功能，需要安装可选依赖 `xlrd` 和 `tablib`

## Using AutoCAD COM Methods Safely

可以这样调用 AutoCAD 自身的 COM 绘图方法：

```python
from pyautocad import Autocad, APoint

acad = Autocad(create_if_not_exists=True)
line = acad.model.AddLine(APoint(0, 0), APoint(100, 0))
print(line.Length)
```

但需要明确：
- `AddLine`、`AddCircle` 这类方法属于 AutoCAD 的 COM/ActiveX 对象
- 是否存在某个具体方法、参数顺序、角度单位、返回对象类型，应以 AutoCAD ActiveX 文档和当前 AutoCAD 版本为准
- 不要因为 pyautocad 能调用它，就把它写成 pyautocad 官方独有 API

## Common Mistakes

### 1. 把不存在的 pyautocad 参数写进构造函数

应使用官方文档给出的参数：

```python
acad = Autocad(create_if_not_exists=True, visible=True)
```

不要擅自扩展为文档未说明的命名参数。

### 2. 把 AutoCAD COM 方法清单伪装成 pyautocad API 清单

错误写法：
- 宣称大量 `Add*`、标注、三维实体、图层、选择集方法都是 pyautocad 自带封装

正确写法：
- pyautocad 提供连接和辅助能力
- 具体绘图/建模能力主要来自 AutoCAD COM 对象

### 3. 编造未在文档中出现的辅助模块

不要直接写成已知 pyautocad API：
- `find_objects(...)`
- `batch_operation(...)`
- `extentsion_data`
- 文档未说明的 `files`、`preferences`、`paper`

如果项目确实需要这些能力，必须先核对源码或其他一手资料。

### 4. 把 `contrib.tables.Table` 误写成 AutoCAD Table 对象包装器

官网文档给出的 `Table` 能力是：
- 通用表格数据读写
- 配合文本对象坐标导出到 `xls/csv/json`

官网文档没有把它描述为 `Table(existing_autocad_table)` 这种包装器。

### 5. 混淆性能与易用性

- `iter_objects()`：更易用，默认做接口转换
- `iter_objects_fast()`：更快，但通常更接近底层 COM 对象

## Recommended Workflow

1. 先用 `Autocad(...)` 建立连接
2. 优先从 `acad.doc` 和 `acad.model` 进入当前图纸
3. 若要找第一个匹配对象，优先用 `find_one(...)`
4. 遍历时先用 `iter_objects()`，性能不够再换 `iter_objects_fast()`
5. 需要用户交互选择时用 `get_selection()`
6. 涉及点坐标时统一用 `APoint`
7. 涉及常量枚举时用 `ACAD`
8. 涉及 COM 数组参数时用 `aDouble`、`aInt`、`aShort`
9. 涉及 AutoCAD Table 批量写入时考虑 `suppressed_regeneration_of(...)`
10. 涉及具体 AutoCAD 实体方法时，同时核对 AutoCAD ActiveX 文档

## References

- pyautocad docs: <https://pyautocad.readthedocs.io/en/latest/>
- getting started: <https://pyautocad.readthedocs.io/en/latest/gettingstarted.html>
- usage: <https://pyautocad.readthedocs.io/en/latest/usage.html>
- API: <https://pyautocad.readthedocs.io/en/latest/api.html>
- AutoCAD ActiveX 本地帮助位置：`help\\acad_aag.chm`、`help\\acadauto.chm`，以及 `C:\Program Files\Common Files\Autodesk Shared\acadauto.chm`
