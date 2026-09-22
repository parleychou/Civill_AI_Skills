---
name: processorcard-builder
description: Build GAMA custom cards by subclassing ProjectPenguin.Cards.ProcessorCardBase, following the official BasicCards examples (Math/Curve/String). Use when the user wants to create or scaffold a GAMA ProcessorCard / 数据处理卡片 / 二次开发卡片 / .crd module, e.g. an addition card, a curve/string/math card, or asks to mimic the official card examples. Covers only classes that inherit ProcessorCardBase (directly or via a ProcessorCard-derived base); explicitly ignores [CardClass]-attributed cards and DataCardBase classes.
---

# GAMA ProcessorCard Builder

## Overview

指引 AI 仿照官方 `BasicCards` 例子，生成继承自 `ProjectPenguin.Cards.ProcessorCardBase` 的
新卡片类，作为 GAMA 二次开发的可执行模块（编译为 .dll，改后缀 `.crd` 后由 GAMA 加载）。

## Preflight（动手前必做）

**在写任何代码前，先完成这两步判断，缺一不可：**

1. **询问 ProjectPenguin.dll 的路径**（同目录一般还有 `NSGeo3dm.dll`）。
   - 必须拿到这两个 DLL 的实际磁盘位置，用作工程引用的 `HintPath`。
   - 若用户未提供，明确向其索要；不要臆造路径。二者通常位于 GAMA 安装目录，常见位置为 `X:\Program Files (x86)\E-GAMA`（`X` 代表任意盘符，如 C、D、E 等），也可能在 `run\x64\release` 之类的子目录。
   - **强约束（不可违反）**：若用户未提供 DLL 引用目录，或你查找后仍无法确认这两个 DLL 的真实路径，**立即停止所有动作**——不要新建工程、不要写任何 `.cs`、不要臆造 `HintPath`。先明确告知用户缺少 DLL 路径，请其提供后再继续。

2. **判断当前工作目录是否已存在 C# 工程**（`*.csproj`）：
   - **已存在工程** → 只需**新增一个 .cs 文件**（一个卡片类）到该工程；不要新建工程、不要改动其框架/引用设置（若该工程尚未引用两个 DLL，提示用户按需添加引用并设 `Private=false`）。
   - **不存在工程** → **创建整个工程**。工程文件**必须使用 SDK 风格 csproj**（`<Project Sdk="Microsoft.NET.Sdk">`），以 `assets/CardProject.csproj` 为模板：
     - `<TargetFramework>net472</TargetFramework>`（不得高于 4.7.2，且必须是 .NET Framework）
     - 通过 `<Reference>` + `<HintPath>` 引用两个 DLL，并设 `<Private>false</Private>`（即“复制本地=否”）
     - 可选：配置生成后事件，把产物复制为 `.crd` 到 `%AppData%\nonstructure\Penguin\Cards`
   - 无法确定时，先询问用户希望“加入现有工程”还是“新建工程”。

   > **.crd 命名规则（务必明确）**：`.crd` 就是编译出的 `.dll` **仅把扩展名 .dll 改成 .crd**，文件名保持与程序集/工程同名（如 `MyCards.dll` → `MyCards.crd`），不要另起名字。最终目录固定为 `%AppData%\nonstructure\Penguin\Cards`。

## 覆盖范围（务必先确认）

**只生成**继承 `ProcessorCardBase` 的“数据处理卡片”，包括：
- 直接 `: ProcessorCardBase`
- 经由官方派生基类（如 `InputSideAutoParseNumberProcessorCard`）间接继承 ProcessorCardBase 的卡片

**绝不参考、绝不生成**以下内容（不由本 skill 覆盖）：
- 带 `[CardClass]`、`[ExcludeFromMenu]` 等特性或使用非标准注册方式的类
- 继承 `DataCardBase` / `SoleDataCardLayout` 的数据卡（如 FilePathDataCard、StringNewLineDataCard）
- 仅实现 `ICardSearchBoxQuickAccess` 等接口而不继承 ProcessorCardBase 的类

若用户需求属于排除范围，明确说明本 skill 不覆盖，并停止生成。

## 一个卡片的五个组成部分

每个 ProcessorCard 子类都由这五部分构成（缺一不可，除“英文别名”为可选）：

1. **类声明 + 无参构造函数** — `: base(全名, 缩写, 描述, 大类, 子类)`
2. **CardGuid** — `public override Guid CardGuid => sc_guid;`，全局唯一
3. **AddInputSideDataCards** — 声明左侧输入端口
4. **AddOutputSideDataCards** — 声明右侧输出端口
5. **Build(IDataDelivery idd)** — 核心逻辑：取输入 → 计算 → 写输出
6. （可选）`EnglishAlias` 英文别名

`assets/ProcessorCardTemplate.cs` 是可直接复制填空的骨架。

## 生成工作流

按顺序执行：

0. **先做 Preflight**（见上）：拿到 DLL 路径 + 判定“加入现有工程”还是“新建 SDK 工程”。
1. **明确需求**：卡片做什么？输入是什么（类型、数量、单值还是列表）？输出是什么？归属大类/子类？
2. **读参考**：
   - 端口/Build/API 不确定 → 读 `references/api-reference.md`
   - **若对 `ProcessorCardBase` 的成员、签名或行为仍有不清楚的地方** → 查阅与 `ProjectPenguin.dll` **同级目录下一定存在的 `ProjectPenguin.xml`** 描述文件（即 Preflight 中拿到的 DLL 路径旁边）。该文件包含官方的 XML 文档注释（`<summary>` / `<param>` / `<returns>`），信息量足够，是最权威的事实依据。用 grep 搜类名/方法名（如 `ProcessorCardBase`、`AddWellKnownTypeOfDataCard`、`GetDataList`）定位对应 `<member>` 节点。
   - 选一个形状最接近的官方例子照抄骨架 → 读 `references/examples.md`
     - 固定单/多输入、单输出 → 例 A / B
     - 多输出 → 例 C
     - 列表输入 / 默认值 / 可选端口 → 例 D
     - 多类型（object 入口 + dynamic + 日志）→ 例 E
     - **两数相加（教学最简版）→ 例 G**
     - **ListByList：一个入口一次性接收整列数据（而非逐项）→ 例 H（曲线：多点→一条多段线）/ 例 I（数学：整列→最大值）**
3. **复制模板**：以 `assets/ProcessorCardTemplate.cs` 为起点，或直接改写最接近的例子。
4. **逐项替换**：
   - 类名、命名空间、base(...) 五个字符串
   - **生成全新唯一 GUID**（VS「工具→创建GUID」或任意 UUID 生成器），绝不复用
   - 按需增删 `AddWellKnownTypeOfDataCard(...)` 端口，注意索引从 0 开始、按添加顺序
   - 在 `Build` 中：OneByOne 用 `GetDataItem(i, ref x)`（失败即 return）、ListByList 用 `GetDataList(i, list)`；用 `SetDataItem(i, value)` / `SetDataList(i, list)` 写出
   - **写足够多的注释**：这些卡片面向二次开发教学与后续维护，最终交付的代码必须注释充分——在类上写明卡片用途；在每个端口声明处标注它是第几号（索引）、类型与含义；在 `Build` 里对“取输入→校验→计算→写输出”每一步都用中文注释解释意图与边界条件（如空列表、收集失败、单位约定）。宁可多注释，不要惜字。
5. **补全 using**（独立类库要写全，见 api-reference 第 7 节）。
6. **落盘**：
   - 加入现有工程 → 仅写入一个 `<卡片类名>.cs`。
   - 新建工程 → 以 `assets/CardProject.csproj` 为模板生成 SDK 风格工程（net472 + 两个 DLL 引用 `Private=false`），再写入 .cs。
7. **自检**（见下）。
8. **交付**：给出完整 .cs（及新建的 csproj）源码，并提醒后续步骤（引用 ProjectPenguin.dll / NSGeo3dm.dll 且“复制本地=否”、编译、把 dll 改后缀为 .crd 放入 `%AppData%\nonstructure\Penguin\Cards`、重启软件）。

## 关键约定（照抄即可，别自创）

- **构造函数两种等价写法**：`public XxxCard() : base(...) {}` 或 C# 主构造 `public class XxxCard() : ProcessorCardBase(...)`。必须有**无参**构造。
- **GetDataItem 返回 false 立即 `return;`** —— 标准防御写法；可选端口（`.SetOptionalFlag(true)` + 默认值）则不判返回值、直接用默认值。
- **端口默认值** = `AddWellKnownTypeOfDataCard(...)` 第 6 个参数。
- **想处理多种数据类型**用 `typeof(object)` 入口 + `dynamic` 运算 + `LogMessage(BuildLogLevel.Warning, ...)` 提示。
- **几何类型**（Point3d/Line/Curve...）来自 `NSGeo.Geometry`。
- DataProcessingMode：单值 `OneByOne` / 整列 `ListByList` / 容器 `ContainerAsOne`。
- **ListByList 入口**：`Build` 里用 `idd.GetDataList(index, list)` 一次性拿到整列（`list` 先 new 好再传入，方法把数据追加进去，返回 false 即 return）；需要按目标类型解析时用 `idd.TryGetList<TSource, TTarget>(index, out data)`。务必先判空列表（`Count == 0`）再计算。详见例 H / 例 I。
- **仍不确定 API 时**：查 `ProjectPenguin.dll` 同级目录的 `ProjectPenguin.xml`（官方 XML 注释，权威）。

## 自检清单

- [ ] 继承 `ProcessorCardBase`，**未**使用 `[CardClass]`，**非** DataCardBase
- [ ] 有无参构造函数，base(...) 五参数齐全
- [ ] `CardGuid` 返回**新生成的唯一** GUID（未复用示例中的值）
- [ ] Input/Output 端口的 type / name / mode 正确，索引从 0 连续
- [ ] `Build` 中输入用 GetDataItem/GetDataList 且必输入判 false-return，输出用 SetDataItem/SetDataList，索引与声明一致
- [ ] using 齐全，可独立编译
- [ ] **注释充分**：类用途、每个端口的索引/类型/含义、Build 各步骤意图与边界条件都有中文注释
- [ ] 无残留 `<占位符>` / `throw new NotImplementedException()`

## Resources

- `references/api-reference.md` — ProcessorCardBase / DataProcessingMode / IDataDelivery / IDataCardEmbedmentHelper / BuildLogLevel / 常用类型 / using（来自 ProjectPenguin.xml）
- `references/examples.md` — 官方例子按“形状”分类拆解（A–I），含两数相加教学最简版（G）与两个 ListByList 整列处理例（H 曲线 / I 数学）
- `assets/ProcessorCardTemplate.cs` — 复制填空的卡片骨架
- `assets/CardProject.csproj` — 新建工程时的 SDK 风格 csproj 模板（net472 + DLL 引用 Private=false + .crd 生成后事件）
- **`ProjectPenguin.xml`**（不在本 skill 内）— 与 `ProjectPenguin.dll` 同级目录下一定存在的官方 XML 注释文件；API 仍不清楚时的最终事实依据，用 grep 搜成员名定位。
