# 官方例子拆解（仿写模板）

以下例子全部来自官方 `BasicCards`，且**均继承自 `ProcessorCardBase`**（直接或经由 `ProcessorCard` 派生基类）。
仿写新卡片时，挑选与目标“形状”最接近的例子照抄骨架，再替换名字、Guid、端口、Build 逻辑。

> ⚠ 不要参考以下内容（不在本 skill 覆盖范围）：
> - 带 `[CardClass]` / `[ExcludeFromMenu]` 特性、或非标准注册方式的类
> - 继承 `DataCardBase`、`SoleDataCardLayout` 的类（如 FilePathDataCard、StringNewLineDataCard）
> - 只实现 `ICardSearchBoxQuickAccess` 等接口而不继承 ProcessorCardBase 的类

---

## A. 最简：单入单出（MakeLineCard 精简版）

**形状**：固定数量输入 → 计算 → 单个输出，全部 OneByOne。适合绝大多数“工具型”卡片。

```csharp
using ProjectPenguin.Cards.ProcessorCardHelpers;
using NSGeo.Geometry;

namespace BasicCards.CurveFile;

public class MakeLineCard : ProcessorCardBase
{
    public MakeLineCard() : base("直线（两点）", "直线", "通过起点和终点来构造一条直线段", "直线和曲线", "直线制作") { }

    public override string EnglishAlias => "Line";
    private static readonly Guid sc_guid = Guid.Parse("{58C762F0-EDAA-4E16-BA95-367DD2556305}");
    public override Guid CardGuid => sc_guid;

    protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(Point3d), "直线起点", "起点", "输入直线的起点", DataProcessingMode.OneByOne);
        helper.AddWellKnownTypeOfDataCard(typeof(Point3d), "直线终点", "终点", "输入直线的终点", DataProcessingMode.OneByOne);
    }

    protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(Line), "直线", "直线", "一条直线", DataProcessingMode.OneByOne);
    }

    public override void Build(IDataDelivery idd)
    {
        Point3d a = default, b = default;
        if (!idd.GetDataItem(0, ref a)) return;   // 收集失败即返回
        if (!idd.GetDataItem(1, ref b)) return;
        idd.SetDataItem(0, new Line(a, b));       // 写入 0 号输出端口
    }
}
```

**要点**：
- 主构造函数写法 `public MakeLineCard() : base(...)`；也可用 C# 主构造函数 `public class XxxCard() : ProcessorCardBase(...)`（见 MathNegativeCard）。
- `GetDataItem` 返回 false 立即 `return`——这是标准防御写法。
- `default` 初始化结构体接收变量。

---

## B. 带类型判断（CurveLengthCard）

单条曲线 → 长度。展示几何类型入口 + 直接方法调用。

```csharp
public override void Build(IDataDelivery idd)
{
    Curve cv = default;
    if (!idd.GetDataItem(0, ref cv)) return;
    idd.SetDataItem(0, cv.GetLength());
}
```

---

## C. 多输出 + 可选输出端口（MathAbsoluteCard 新版）

一个输入，多个输出；`Build` 里按需向多个输出端口写值。

```csharp
protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
{
    helper.AddWellKnownTypeOfDataCard(typeof(double), "|A|", "|A|", "绝对值结果", DataProcessingMode.OneByOne);
    helper.AddWellKnownTypeOfDataCard(typeof(bool), "原值是否小于零", "<0", "是否发生了取反", DataProcessingMode.OneByOne);
}

public override void Build(IDataDelivery idd)
{
    var x = 0.0;
    if (!idd.GetDataItem(0, ref x)) return;
    idd.SetDataItem(0, Math.Abs(x));
    idd.SetDataItem(1, x < 0);
}
```

---

## D. 列表输入（ListByList）+ 默认值 + 可选端口（JoinStringCard / StringEqualsCard）

```csharp
protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
{
    helper.AddWellKnownTypeOfDataCard(typeof(string), "字符串", "字符串", "需要合成的字符串", DataProcessingMode.ListByList);
    // 第 5 个参数是默认值 ","
    helper.AddWellKnownTypeOfDataCard(typeof(string), "合成分隔符", "分隔符", "用来连接的字符", DataProcessingMode.OneByOne, ",");
}

public override void Build(IDataDelivery idd)
{
    var values = new List<string>();
    string div = null;
    if (!idd.GetDataList(0, values)) return;   // ListByList 用 GetDataList
    if (!idd.GetDataItem(1, ref div)) return;
    idd.SetDataItem(0, string.Join(div, values));
}
```

可选端口（StringEqualsCard）：链式 `.SetOptionalFlag(true)`，且带默认值 `true`：

```csharp
helper.AddWellKnownTypeOfDataCard(typeof(bool), "忽略首尾空格", "忽略空格", "比较时是否忽略前后空格",
        DataProcessingMode.OneByOne, true)
    .SetOptionalFlag(true);
// Build 中可选端口即使收集失败也不 return，直接使用其默认值：
// idd.GetDataItem(2, ref trim);   // 不判返回值
```

---

## E. 万能 object 入口 + 日志 + 判断可选端口（MathSumCard / MathAdditionCard 思路）

处理“多种数值类型”时，用 `typeof(object)` 入口，运行时判断/转换，并用 `LogMessage` 提示：

```csharp
public override void Build(IDataDelivery idd)
{
    object a = null, b = null;
    var okA = idd.GetDataItem(0, ref a);
    var okB = idd.GetDataItem(1, ref b);
    if (!okA) return;
    if (!okB)
    {
        LogMessage(BuildLogLevel.Warning, "<B> 入口未收集到数据");
        idd.SetDataItem(0, a);   // 只有主入口时的降级处理
        return;
    }
    dynamic res = (dynamic)a + (dynamic)b;   // 让运行时决定 + 的语义（数值/点/向量/字符串）
    idd.SetDataItem(0, res);
}
```

判断可选/动态端口是否存在：`DataMngr.InputSideDataCards.Count` / `DataMngr.OutputSideDataCards.Count`。

---

## F. GUID 的三种等价写法

`CardGuid` 必须唯一。以下写法等价，**推荐第 1 种**（可读、易生成）：

```csharp
private static readonly Guid sc_guid = Guid.Parse("{95FAD3CB-B4DC-4E3A-9D94-F7266F2CA0DB}"); // 推荐
private static readonly Guid sc_guid = new Guid("95FAD3CB-B4DC-4E3A-9D94-F7266F2CA0DB");
private static readonly Guid sc_guid = new Guid(0x95FAD3CB, unchecked((short)0xB4DC), 0x4E3A, 0x9D, 0x94, 0xF7, 0x26, 0x6F, 0x2C, 0xA0, 0xDB); // 官方常见，等价
public override Guid CardGuid => sc_guid;
```

> 用 VS「工具 → 创建 GUID」生成新值，或任意 UUID 生成器。**绝不复用**其他卡片的 GUID。

---

## G. 目标案例：两数相加（教学最简版）

官方 `MathAdditionCard` 带“可变端口 + 快捷搜索”较复杂。教学/入门请生成如下**最简两数相加**卡片：

```csharp
using System;
using ProjectPenguin.Cards;
using ProjectPenguin.Cards.Enums;
using ProjectPenguin.Cards.ProcessorCardHelpers;

namespace MyCards;

public class TwoNumberAdditionCard : ProcessorCardBase
{
    public TwoNumberAdditionCard() : base("两数相加", "相加", "计算 A + B", "数学", "数学运算符") { }

    public override string EnglishAlias => "Add Two Numbers";
    private static readonly Guid sc_guid = Guid.Parse("{PUT-A-FRESH-GUID-HERE}"); // 生成新 GUID！
    public override Guid CardGuid => sc_guid;

    protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(double), "第一个数", "A", "加数 A", DataProcessingMode.OneByOne);
        helper.AddWellKnownTypeOfDataCard(typeof(double), "第二个数", "B", "加数 B", DataProcessingMode.OneByOne);
    }

    protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(double), "结果", "结果", "A + B 的结果", DataProcessingMode.OneByOne);
    }

    public override void Build(IDataDelivery idd)
    {
        double a = 0, b = 0;
        if (!idd.GetDataItem(0, ref a)) return;
        if (!idd.GetDataItem(1, ref b)) return;
        idd.SetDataItem(0, a + b);
    }
}
```

---

## H. ListByList：一个入口一次性接收整列数据（CurveFile · 多点 → 一条多段线）

**形状**：某个**输入端口**声明为 `DataProcessingMode.ListByList`，`Build` 里用
`idd.GetDataList(index, list)` **一次性拿到整列数据**（而不是逐项 `GetDataItem`），
把整列聚合成**一个**结果输出。适合“多点连成一条线/面”“整列求和/求极值”等聚合型卡片。

来源：官方 `BasicCards/CurveFile/CreatePolylineCurveCard.cs`（下面加了充分注释）。

```csharp
using System.Collections.Generic;          // List<T>
using ProjectPenguin.Cards;                 // ProcessorCardBase
using ProjectPenguin.Cards.Enums;           // DataProcessingMode, BuildLogLevel
using ProjectPenguin.Cards.ProcessorCardHelpers; // IDataDelivery, IDataCardEmbedmentHelper
using NSGeo.Geometry;                        // Point3d, PolylineCurve

namespace BasicCards.CurveFile;

// 卡片用途：把一列点按顺序连成一条多段线（Polyline）。
public class CreatePolylineCurveCard : ProcessorCardBase
{
    public CreatePolylineCurveCard() : base("制作多段直线", "多段线", "把一列点顺次连成多段线", "直线和曲线", "曲线制作") { }

    public override string EnglishAlias => "Polyline Curve";

    // 每张卡片都要有独立、全新的 GUID，切勿复用本示例中的值。
    private static readonly Guid sc_guid = Guid.Parse("{79154007-483A-41EA-A59F-4204F306546A}");
    public override Guid CardGuid => sc_guid;

    protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        // 0 号输入端口：一列点。关键在于 mode = ListByList —— 框架会把“整列点”一次性喂给 Build。
        helper.AddWellKnownTypeOfDataCard(typeof(Point3d), "点", "点", "构成多段线的一列点（按顺序）", DataProcessingMode.ListByList);
    }

    protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        // 0 号输出端口：聚合出的单条多段线，所以是 OneByOne（整列 → 一个结果）。
        helper.AddWellKnownTypeOfDataCard(typeof(PolylineCurve), "多段线", "多段线", "由输入点连成的多段线", DataProcessingMode.OneByOne);
    }

    public override void Build(IDataDelivery idd)
    {
        // ListByList 取数：先 new 好接收列表，再传给 GetDataList，方法会把该端口的整列数据追加进来。
        var points = new List<Point3d>();
        if (!idd.GetDataList(0, points)) return;   // 收集失败（未接线/上游报错）立即返回。

        // 边界条件：点太少连不成线时，给出提示并退出，避免构造无效几何。
        if (points.Count < 2)
        {
            LogMessage(BuildLogLevel.Warning, "点的数量少于 2，无法构成多段线");
            return;
        }

        // 聚合：整列点 → 一条多段线，写入 0 号输出端口。
        idd.SetDataItem(0, new PolylineCurve(points));
    }
}
```

**要点**：
- **输入端口** mode 设为 `ListByList` 是“整列处理”的开关；`Build` 里必须用 `GetDataList` 而非 `GetDataItem`。
- `GetDataList(index, list)`：`list` 先 `new` 好再传入，返回值 false 表示收集失败，照例 `return`。
- 典型模式是“**整列输入 → 单个输出**”，所以输出端口通常是 `OneByOne`。
- 计算前先判元素数量/空列表等边界条件。

---

## I. ListByList：整列 → 统计结果（MathFile · 数列最大值，含可空值处理）

来源：官方 `BasicCards/MathFile/MathMaximumOfList.cs`（此处精简为核心骨架并加充分注释；
原卡片还带“忽略 null/NaN”的右键菜单与持久化，属进阶功能，教学时可省略）。

```csharp
using System.Collections.Generic;          // List<T>
using System.Linq;                          // Max / Where / Select
using ProjectPenguin.Cards;                 // ProcessorCardBase
using ProjectPenguin.Cards.Enums;           // DataProcessingMode, BuildLogLevel
using ProjectPenguin.Cards.ProcessorCardHelpers; // IDataDelivery, IDataCardEmbedmentHelper

namespace BasicCards.MathFile;

// 卡片用途：从输入的一列数字里求最大值，并可选地输出该最大值在原列表中的索引。
public class MathMaximumOfList : ProcessorCardBase
{
    public MathMaximumOfList() : base("数列最大值", "最大值", "求输入的一列数中的最大值", "数学", "数列运算") { }

    // 独立、全新的 GUID。
    private static readonly Guid sc_guid = Guid.Parse("{98299139-5C04-4D2E-B00A-00DCED6A0BFA}");
    public override Guid CardGuid => sc_guid;

    protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        // 0 号输入端口：一列数字，ListByList —— 一次性拿到整列。
        helper.AddWellKnownTypeOfDataCard(typeof(double), "数列", "数列", "请输入一列数字", DataProcessingMode.ListByList);
    }

    protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        // 0 号输出：最大值（整列 → 单值，OneByOne）。
        helper.AddWellKnownTypeOfDataCard(typeof(double), "最大值", "最大值", "输入数列中的最大值", DataProcessingMode.OneByOne);
        // 1 号输出：最大值所在的索引；此端口可能被用户删除，Build 里要先判存在再写。
        helper.AddWellKnownTypeOfDataCard(typeof(int), "索引", "索引", "最大值在原列表中的索引", DataProcessingMode.OneByOne);
    }

    public override void Build(IDataDelivery idd)
    {
        // ListByList 取数：用 List<double?>（可空）接收，方便区分“缺失值 null”与真实数字。
        var list = new List<double?>();
        if (!idd.GetDataList(0, list)) return;      // 收集失败直接返回。

        // 边界条件：空列表无法求最大值。
        if (list.Count == 0)
        {
            LogMessage(BuildLogLevel.Error, "数列中不包含任何值");
            return;
        }

        // 边界条件：存在 null 值时，本教学版直接判错退出（进阶可加“忽略 null”开关）。
        if (list.Any(x => !x.HasValue))
        {
            LogMessage(BuildLogLevel.Error, "数列中有 null 值，请检查数据");
            idd.SetDataItem(0, null);
            return;
        }

        // 计算：取整列的最大值。
        var values = list.Select(x => x.Value).ToList();
        var max = values.Max();

        // 写出 0 号输出：最大值。
        idd.SetDataItem(0, max);

        // 1 号输出端口是可选的——只有当它还存在时才写，避免向不存在的端口写数据。
        if (DataMngr.OutputSideDataCards.Count > 1)
        {
            idd.SetDataItem(1, values.IndexOf(max));
        }
    }
}
```

**要点**：
- 用 `List<T?>`（可空）接收整列，能自然区分“上游缺失值”与真实数据；随后 `Where/Select/Max` 用 LINQ 聚合。
- **多输出且部分可选**：写第 1 号输出前用 `DataMngr.OutputSideDataCards.Count > 1` 判断端口是否还在。
- 求极值/求和/平均等“整列 → 单值”的统计卡片都遵循这个骨架（参见官方 `MathSumCard`、`MathAverageOfList`）。
- 官方原版还用 `idd.TryGetList<object, double?>(0, out var data)` 支持“多种数值类型自动解析”，需要时查该文件与 `references/api-reference.md` 第 4 节。
