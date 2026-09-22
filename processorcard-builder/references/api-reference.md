# ProcessorCardBase API 参考

来源：`ProjectPenguin.xml`（`ProjectPenguin.Cards.ProcessorCardBase` 及相关类型）。
本文件是生成卡片时的 API 事实依据，不确定签名时先查这里。

---

## 1. ProcessorCardBase（数据处理卡片基类）

> ProcessorCard（数据处理卡片）是 PenguinDeck 上最常用的卡片。构建数据时，它从**输入侧** DataCard 收集数据 → 用自身 `Build` 方法处理 → 把结果写入**输出侧** DataCard。
> 制作自定义卡片：从本类派生子类，实现必需方法，并提供**一个无参构造函数**；同时在 `CardGuid` 属性里返回一个**全局唯一的 Guid**，`CardCollectionManager` 才能自动加载。

### 构造函数

```csharp
protected ProcessorCardBase(string name, string nameShort, string description, string category, string subCategory)
```

| 参数 | 含义 |
|---|---|
| `name` | 卡片全名（画布/菜单显示） |
| `nameShort` | 缩写（空间不足时显示） |
| `description` | 描述，鼠标悬停 tooltip |
| `category` | 大类（决定在工具菜单的归属） |
| `subCategory` | 子类 |

> 不要把大类命名为“常用”（自动生成）。

### 必须实现 / 常用重写成员

| 成员 | 签名 | 说明 |
|---|---|---|
| `CardGuid` | `public override Guid CardGuid => ...;` | **全局唯一标识**，卡片“身份证”。每个新类必须使用**新的、不重复的** Guid，切勿手写臆造或复制他卡。 |
| `AddInputSideDataCards` | `protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)` | 声明左侧输入端口。无输入则留空实现。 |
| `AddOutputSideDataCards` | `protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)` | 声明右侧输出端口。 |
| `Build` | `public override void Build(IDataDelivery idd)` | **核心逻辑**：从输入侧取数 → 计算 → 写入输出侧。 |

### 可选重写成员

| 成员 | 用途 |
|---|---|
| `string EnglishAlias` | `public override string EnglishAlias => "...";` 英文别名，便于搜索。 |
| `BeforeDataBuilding()` / `AfterDataBuilding()` | 所有数据构建前/后的额外处理；`base` 实现为空，可安全省略 base 调用。 |
| `FillAdditionalCardMenuStripItem(ToolStripDropDown menu)` | 追加右键菜单项（进阶）。 |
| `ClearData()` | 清空数据；若重写**必须**调用 `base.ClearData()`。 |

### 常用受保护属性 / 方法

| 名称 | 用途 |
|---|---|
| `DataMngr` | 访问输入/输出侧 DataCard 集合：`DataMngr.InputSideDataCards`、`DataMngr.OutputSideDataCards`（可用 `.Count` 判断可选端口是否存在）。 |
| `RunCount` | `Build` 被调用的次数。 |
| `LogMessage(BuildLogLevel level, string msg)` | 向构建日志输出信息（见下）。 |
| `Rebuild(bool)` | 触发卡片重建。 |

---

## 2. DataProcessingMode（数据处理模式，枚举）

`ProjectPenguin.Cards.Enums.DataProcessingMode`

| 值 | 含义 | 在 Build 中的取数方式 |
|---|---|---|
| `OneByOne` | 逐项处理（最常用），框架按项配对调用 Build | `idd.GetDataItem(index, ref x)` |
| `ListByList` | 整列处理，一次拿到一整列 | `idd.GetDataList(index, list)` / `idd.TryGetList<...>(...)` |
| `ContainerAsOne` | 把整个数据容器当作一个整体 | `idd.GetDataContainer(index, out container)` |

---

## 3. IDataCardEmbedmentHelper（端口声明助手）

命名空间：`ProjectPenguin.Cards.ProcessorCardHelpers`

主要重载（在 `AddInputSideDataCards` / `AddOutputSideDataCards` 里使用）：

```csharp
// 非泛型：显式给 Type
IDataCard AddWellKnownTypeOfDataCard(
    Type dataType, string name, string nameShort, string description,
    DataProcessingMode mode);

IDataCard AddWellKnownTypeOfDataCard(
    Type dataType, string name, string nameShort, string description,
    DataProcessingMode mode, object defaultValue);

// 泛型版本亦可：AddWellKnownTypeOfDataCard<T>(name, nameShort, description, mode[, defaultValue])
```

- 返回值 `IDataCard` 仅用于**链式调用**，不要再手动加回 `DataMngr`。
- 链式常用：`.SetOptionalFlag(true)` —— 把端口设为可选（收集失败也不阻塞）。
- 端口**索引从 0 开始**，按添加顺序编号；`Build` 里的 index 与此一致。
- 类型转换由框架自动完成（如可行）；若想自己处理转换，用 `typeof(object)` 端口。

其它进阶重载：`AddInputSideClickableBooleanCard(...)`、`AddInputSideCheckBox(...)` 等（一般不需要）。

---

## 4. IDataDelivery（Build 中的数据通道）

命名空间：`ProjectPenguin.Cards.ProcessorCardHelpers`

### 取输入侧数据

| 方法 | 适用模式 | 用法 |
|---|---|---|
| `bool GetDataItem<T>(int index, ref T receiver)` | OneByOne | 取单项；返回 `false` 表示收集失败，通常直接 `return;` |
| `bool GetDataList<T>(int index, List<T> receiver)` | ListByList | 取整列并追加到 `receiver` |
| `bool TryGetList<TSource, TTarget>(int index, out IList<TTarget> data)` | ListByList | 尝试按目标类型解析整列 |
| `bool GetDataContainer<T>(int index, out DataContainer<T> c)` | ContainerAsOne | 取整个容器 |

### 写输出侧数据

| 方法 | 用法 |
|---|---|
| `bool SetDataItem(int index, object data)` | 向第 index 个输出端口写单个数据 |
| `bool SetDataList(int index, IEnumerable data)` | 向第 index 个输出端口写一列数据（会追加） |
| `SetDataContainer(int index, IDataContainer c)` | 直接写容器（完全控制数据结构） |

> 默认：若某输出端口未调用任何 Set，框架会填入 `null`。可用 `idd.NoNullForEmptyBuild` / `NoNullForEmptyBuild(index)` 关闭该行为。

---

## 5. BuildLogLevel（日志级别，枚举）

`ProjectPenguin.Cards.Enums.BuildLogLevel`：`Trace` / `Debug` / `Information` / `Warning` / `Error` / `Alert` / `Critical` / `Fatal`

```csharp
LogMessage(BuildLogLevel.Warning, "入口数据未成功收集，请检查结果是否符合预期");
```

---

## 6. 常用数据类型

| 类别 | 类型 | 命名空间 |
|---|---|---|
| 基础 | `int` `double` `float` `decimal` `bool` `string` `object` | System |
| 万能入口 | `typeof(object)` | 想自己处理类型转换/多类型时使用 |
| 几何 | `Point3d` `Vector3d` `Line` `Curve` `Arc` `Circle` 等 | `NSGeo.Geometry` |
| 类型常量 | `PenguinTypes.StringType` / `PenguinTypes.DecimalType` 等 | 用于运行时类型判断 |

---

## 7. 必需的 using（独立类库项目）

官方 BasicCards 项目开启了隐式/全局 using，源码里只写了 `using ProjectPenguin.Cards.ProcessorCardHelpers;`。
**在自建的外部类库中请写全**：

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using ProjectPenguin.Cards;                    // ProcessorCardBase
using ProjectPenguin.Cards.Enums;              // DataProcessingMode, BuildLogLevel
using ProjectPenguin.Cards.ProcessorCardHelpers; // IDataDelivery, IDataCardEmbedmentHelper
using NSGeo.Geometry;                           // 仅当用到几何类型
```
