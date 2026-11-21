# Tekla 官方组件调用工作流

用于 Agent 调用当前 Tekla 中已安装的组件。只负责**选组件、传输入、加载参数、插入并验收**；不替代结构节点设计。

## 核心原则

创建前必须同时取得：

1. **当前年度 API 文档**：确认类、成员和调用顺序；
2. **当前 Tekla 组件目录**：确认组件实际存在及其 `Name / Number / Type`；
3. **当前项目属性模板**：确认组件参数。

禁止凭界面文字、其他版本或历史经验猜编号、类型和属性键。

## 组件体系

```text
BaseComponent
├── Connection   主构件 + 次构件，典型：梁柱节点
├── Detail       主构件 + 参考点，典型：柱脚、端部细部
├── Component    ComponentInput，典型：通用宏、钢筋组件
└── Seam         主构件 + 次构件 + 边界，典型：沿边连接
```

共同流程：

```text
确定 Name/Number → LoadAttributesFromFile → SetAttribute 覆盖
→ 设置输入与方向 → Insert → CommitChanges → 重新查询验收
```

`SetAttribute()` 覆盖属性文件中的同名值。

## 查询当前组件目录

```python
from Tekla.Structures.Catalogs import CatalogHandler

def find_components(query="", component_type=None, limit=50):
    catalog = CatalogHandler()
    if not catalog.GetConnectionStatus():
        raise RuntimeError("无法连接 Tekla component catalog")

    needle = query.strip().casefold()
    wanted = component_type.strip().upper() if component_type else ""
    items, result = catalog.GetComponentItems(), []

    while items.MoveNext():
        item = items.Current
        row = {
            "ui_name": str(item.UIName or "").strip(),
            "name": str(item.Name or "").strip(),
            "number": int(item.Number),
            "type": str(item.Type).strip().upper(),
            "attribute_extension": str(item.AttributeFileExtension or "").strip(),
        }
        text = f"{row['ui_name']} {row['name']} {row['number']}".casefold()
        if needle and needle not in text:
            continue
        if wanted and row["type"] != wanted:
            continue
        result.append(row)
        if limit and len(result) >= limit:
            break

    return result
```

零结果时停止；多结果且会改变建模结果时，列出候选让用户确认。

## 按目录类型路由

| `ComponentItem.Type` | 模型 API | 必要输入 |
|---|---|---|
| `CONNECTION` | `Model.Connection` | 主构件、一个或多个次构件 |
| `DETAIL` | `Model.Detail` | 主构件、参考点 |
| `COMPONENT` | `Model.Component` | `ComponentInput` |
| `SEAM` | `Model.Seam` | 主次构件、起终点或多边形 |
| `CUSTOM_PART` | `Model.CustomPart` | 按定义要求 |

`UIName` 只用于搜索和展示；创建时使用目录返回的内部 `Name / Number / Type`。

## 官方调用范式

> 下列编号和属性键来自 Tekla 2026 官方示例，只用于说明调用顺序。实际执行必须以当前组件目录和项目模板为准。

### Connection：梁柱节点

```csharp
Connection c = new Connection
{
    Name = "Test End Plate",
    Number = 144,
    UpVector = new Vector(0, 0, 1000),
    PositionType = PositionTypeEnum.COLLISION_PLANE,
    AutoDirectionType = AutoDirectionTypeEnum.AUTODIR_FROM_ATTRIBUTE_FILE
};

c.LoadAttributesFromFile("standard");
c.SetPrimaryObject(column);
c.SetSecondaryObject(beam);
c.SetAttribute("e1", 10.0);
c.SetAttribute("e2", 10.0);
bool ok = c.Insert();
```

多个次构件使用 `SetSecondaryObjects()`。


### Detail：柱脚或端部细部

```csharp
Detail d = new Detail
{
    Name = "Test End Plate Detail",
    Number = 1002,
    PositionType = PositionTypeEnum.MIDDLE_PLANE,
    AutoDirectionType = AutoDirectionTypeEnum.AUTODIR_DETAIL,
    DetailType = DetailTypeEnum.END
};

d.LoadAttributesFromFile("standard");
d.SetPrimaryObject(column);
d.SetReferencePoint(referencePoint);
bool ok = d.Insert();
```


### Component：通用组件

```csharp
ComponentInput input = new ComponentInput();
input.AddInputObject(beam);

Component c = new Component
{
    Name = "Beam Reinforcement",
    Number = 30000063
};

c.SetComponentInput(input);
c.LoadAttributesFromFile("standard");
c.SetAttribute("side_bar_space", 333.0);
bool ok = c.Insert();
```

`ComponentInput` 可包含对象、点或多边形。


### Seam：沿边连接

```csharp
Seam s = new Seam
{
    Name = catalogName,
    Number = catalogNumber,
    AutoDirectionType = AutoDirectionTypeEnum.AUTODIR_BASIC,
    AutoPosition = true
};

s.LoadAttributesFromFile("standard");
s.SetPrimaryObject(mainPart);
s.SetSecondaryObject(secondaryPart);
s.SetInputPositions(startPoint, endPoint);
bool ok = s.Insert();
```

复杂边界使用 `SetInputPolygon()`。


## 属性规则

- 优先加载项目中已验证的命名模板：

  ```python
  component.LoadAttributesFromFile("project_component_preset")
  ```

- 只对已确认的内部属性键调用 `SetAttribute()`。
- 对话框标签、翻译文字和其他组件的字段不能作为属性键证据。
- 没有模板且参数会改变工程结果时，修改模型前请求确认。

## 最小执行闭环

首次使用某组件时只处理一个目标：

1. 查询目录，确认唯一组件及 `Type`；
2. 按 `Type` 选择 API 类；
3. 加载已验证属性模板；
4. 设置主次构件、参考点、边界或 `ComponentInput`；
5. 设置方向与定位；
6. 检查所有布尔返回值；
7. `Insert()`，成功后 `CommitChanges()`；
8. 按组件标识重新查询组件及子对象；
9. 验收通过后才批量执行。

## 验收

`Insert() == true` 只表示 Tekla 接受了对象，不表示节点正确。至少验证：

- 组件类型、编号及输入对象正确；
- 主次构件、参考点、方向和局部坐标正确；
- 生成板件、螺栓、焊缝和切割的数量、尺寸及位置正确；
- 应接触处贴合，应留缝处净距正确；
- 螺栓和焊缝实际连接了预期对象。

## 失败处理

失败时依次检查：

1. 组件是否存在于当前目录；
2. `Type` 与 API 类是否一致；
3. 输入对象和位置是否满足组件要求；
4. 方向、定位和局部坐标是否正确；
5. 属性模板及属性键是否有效；
6. 是否留下部分结果。

不得换名称变体、猜属性键或批量重试。只清理本次操作新增对象。

## 返回给 Agent

```json
{
  "success": true,
  "component_id": 123456,
  "type": "CONNECTION",
  "name": "End plate",
  "number": 144,
  "primary_guid": "...",
  "secondary_guids": ["..."],
  "warnings": []
}
```

失败时返回失败阶段、错误信息、输入 GUID 和参数摘要，不只返回 `false`。
