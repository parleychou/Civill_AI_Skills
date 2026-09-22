// ProcessorCard 模板 —— 复制本文件，替换所有 <占位符> 后即可编译为 GAMA 自定义卡片。
// 生成前务必：1) 用新的唯一 GUID 替换 sc_guid；2) 按需增删输入/输出端口；3) 在 Build 中写核心逻辑。
// 排除范围：不要加 [CardClass] 特性，不要继承 DataCardBase —— 本模板仅覆盖 ProcessorCardBase 子类。

using System;
using System.Collections.Generic;
using System.Linq;
using ProjectPenguin.Cards;                     // ProcessorCardBase
using ProjectPenguin.Cards.Enums;               // DataProcessingMode, BuildLogLevel
using ProjectPenguin.Cards.ProcessorCardHelpers; // IDataDelivery, IDataCardEmbedmentHelper
// using NSGeo.Geometry;                          // 需要 Point3d/Line/Curve 等几何类型时取消注释

namespace <你的命名空间>;

public class <卡片类名>Card : ProcessorCardBase
{
    // base(全名, 缩写, 描述, 大类, 子类)
    public <卡片类名>Card() : base("<全名>", "<缩写>", "<悬停描述>", "<大类>", "<子类>") { }

    // 可选：英文别名，便于搜索
    public override string EnglishAlias => "<English Alias>";

    // 必须：全局唯一 GUID —— 用 VS「工具→创建GUID」生成新值，切勿复用他卡的 GUID
    private static readonly Guid sc_guid = Guid.Parse("{<GENERATE-A-FRESH-GUID>}");
    public override Guid CardGuid => sc_guid;

    // 输入端口（索引从 0 开始，按添加顺序）；无输入则留空方法体
    protected override void AddInputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(double), "<入口全名>", "<入口缩写>", "<入口描述>", DataProcessingMode.OneByOne);
        // 列表入口：DataProcessingMode.ListByList
        // 带默认值：AddWellKnownTypeOfDataCard(typeof(bool), "...", "...", "...", DataProcessingMode.OneByOne, true)
        // 可选入口：上一行末尾 .SetOptionalFlag(true)
    }

    // 输出端口
    protected override void AddOutputSideDataCards(IDataCardEmbedmentHelper helper)
    {
        helper.AddWellKnownTypeOfDataCard(typeof(double), "<出口全名>", "<出口缩写>", "<出口描述>", DataProcessingMode.OneByOne);
    }

    // 核心逻辑：取输入 → 计算 → 写输出
    public override void Build(IDataDelivery idd)
    {
        double a = 0;
        if (!idd.GetDataItem(0, ref a)) return;   // OneByOne 取单项；失败即返回

        // 列表输入示例：
        // var list = new List<double>();
        // if (!idd.GetDataList(0, list)) return;

        var result = a; // TODO: 替换为你的运算

        idd.SetDataItem(0, result);               // 写 0 号输出端口
        // 需要提示时：LogMessage(BuildLogLevel.Warning, "……");
    }
}
