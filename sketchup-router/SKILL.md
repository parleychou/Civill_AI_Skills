---
name: sketchup
version: 1.0.3
display_name: SketchUp
display_name_en: SketchUp
description: 通过 Python-Ruby 桥接插件操控 SketchUp 进行三维建筑体块、轴网柱网、墙体门窗、楼板屋顶、幕墙立面及室内方案建模，配置场景剖切与阴影，配备完整的 SketchUp Ruby API 渐进式检索系统与常用构件范式库。
description_zh: 通过 Python-Ruby 桥接插件操控 SketchUp 进行三维建筑体块、轴网柱网、墙体门窗、楼板屋顶、幕墙立面及室内方案建模，配置场景剖切与阴影，配备完整的 SketchUp Ruby API 渐进式检索系统与常用构件范式库。
description_en: Controls SketchUp via Python-Ruby bridge for 3D architectural massing, framing, envelopes, materials, scenes, and shadows, equipped with a progressive SketchUp Ruby API query system and complete modeling patterns.
license: Apache-2.0
---

# SketchUp 建模技能

用 Python 连接 SketchUp，把 **SketchUp Ruby API** 代码发进 SketchUp 执行。流程：连接（第 1 节）→ 查文档（第 2 节）→ 执行（第 3、4 节）→ 交付（第 6 节）。

| 资料 | 什么时候用 |
|---|---|
| `references/common_examples.md` | 写某类构件或操作前，找对应示例：柱网、墙体门窗、楼板、屋顶、幕墙、体块、高层框架、标签材质、场景、剖切、日照、效果图、导入 CAD、保存 |
| `references/interior_layout.md` | 布置家具、做室内模型 |
| `scripts/ruby_api.py` | 查 Ruby API 的类、方法、参数、设置键和最低版本（第 2 节） |

## 1. 连接

按文件连接，模型始终对应一个 .skp 文件，用户以后能找到、复用：

```python
import os
# 导入自动化控制接口

su = get_sketchup(os.path.join(WORKSPACE_DIR, "办公楼方案体块.skp"))
print(su)   # <SketchUp 26.0.429 pid=… 文件=…>，26 即 SketchUp 2026
```

| 用户的要求 | 写法 | 结果 |
|---|---|---|
| 处理某个 .skp 文件 | `get_sketchup(该文件路径)` | 有 SketchUp 开着这个文件就连它；没有就新开一个 SketchUp 打开它 |
| 新建模型 | `get_sketchup(os.path.join(WORKSPACE_DIR, "名称.skp"))`，名称按内容起 | 按用户的默认模板新建这个文件，新开一个 SketchUp 打开它 |
| 处理“当前模型”“开着的 SketchUp”，没说是哪个文件 | `get_sketchup()` | 只开着一个 SketchUp 时连它；开着多个时报错，问用户；一个都没开时在工作目录新建 `sketchup_model.skp` |

- 只在第一段代码里连接一次。`su` 在 python_executor 里跨调用保留，后面直接用；连接断了会自动重连。SketchUp 被关掉后再用 `su` 会报错，这时重新连接。
- 新开 SketchUp 要十几秒到两三分钟，`get_sketchup` 会一直等到能连上，期间不要另想办法。
- 新建的文件是默认模板的副本，通常带一个人物组件（如 `Sree`）。建模前删掉，除非用户要保留：`model.entities.erase_entities(model.entities.to_a)`，再依次 `model.definitions.purge_unused`、`model.materials.purge_unused`。要先清定义：人物的组件定义还在，它的材质就清不掉。
- `get_sketchup()` 连上的模型如果还没保存过（`print(su)` 显示“未保存”），交付前问用户存到哪里。
- 第一次连接时自动给 SketchUp 装插件。SketchUp 只在启动时加载插件，装插件之前就开着的 SketchUp 要重启一次才能连上。
- 连接失败时，把异常里的说明转告用户，等用户处理好再连。不要自己关闭或重启用户的 SketchUp：

| 异常 | 处理 |
|---|---|
| `SketchUpSelectionRequiredError` | 开着多个 SketchUp，`get_sketchup()` 不知道连哪个。把异常里列出的文件告诉用户，问清是哪个，再用 `get_sketchup(该文件路径)` 连。用户要的模型还没保存过时，请用户先在 SketchUp 里保存 |
| `SketchUpUnavailableError` | SketchUp 开着但连不上，异常里逐个写明原因和处理办法，照着做。“正在启动”：稍后用同样的参数再调用一次，不会重复打开，不要让用户重启；“插件安装前启动”“停在欢迎窗口”“没有加载插件”：请用户按说明处理后再连 |

## 2. 查文档

**先查文档，再写代码。** 开工前必须先确认要用到哪些类、方法、设置键，逐个查清正确用法（参数、单位、返回值、注意事项），全部查清才能开始写代码。不知道该用哪个 API 就按下面的步骤找，不要猜一个名字去试。报错或效果不对时，先查文档弄清原因，再改。

原因：API 用错多半不报错，只会悄悄把用户的模型改坏；凭猜测反复试错，错误的修改会叠加在用户的模型上，后果可能无法挽回。

库里是 SketchUp Ruby API 官方文档的全部内容，另有标【补充】的本地实测说明：官方没讲清的设置键含义和取值、容易用错的方法。以下命令都作为 ``python scripts/ruby_api.py ...`` 的 `run_args`，例如 `run_args='catalog geom'`。

### Step 1：确定分类

| 分类 | 内容 | 常用类 |
|---|---|---|
| `model` | 当前模型、打开保存、导入导出、撤销操作、选择集、模型选项 | `Sketchup`、`Model`、`Selection` |
| `entities` | 往模型里加几何；面、边、曲线、顶点，辅助线、尺寸、文字、剖切面 | `Entities`、`Face`、`Edge`、`SectionPlane` |
| `components` | 组、组件定义与实例、属性字典 | `Group`、`ComponentDefinition`、`ComponentInstance`、`AttributeDictionary` |
| `materials` | 材质、贴图、颜色、标签（Layer）、线型 | `Material`、`Materials`、`Color`、`Layer`、`Layers` |
| `view` | 视图、截图、相机、场景 | `View`、`Camera`、`Page`、`Pages` |
| `display` | 显示设置（边线、平面样式、背景）、阴影与日照、样式 | `RenderingOptions`、`ShadowInfo`、`Styles` |
| `geom` | 点、向量、变换、包围盒、求交与距离 | `Geom::Point3d`、`Geom::Vector3d`、`Geom::Transformation`、`Geom::BoundingBox` |
| `core` | 单位换算、`Length`、数组当作点和向量、`ORIGIN` 等全局常量 | `Numeric`、`Length`、`Array`、`TopLevel` |
| `guides` | 专题：导出、导入选项，大批量生成几何的方式 | `exporter_options`、`importer_options`、`generating_geometry` |

另有 `ui`（对话框、交互工具）、`observers`（观察者）、`system`（扩展与系统）、`layout`（LayOut 文档），建模用不到。`catalog` 列出全部分类。

### Step 2：列出分类里的类

`catalog <分类>` 列出这个分类的类、一句话说明和最低版本：

```text
catalog components
catalog display
```

### Step 3：查看类

`class <类名>` 返回类的说明、常量、全部方法（一句话说明和最低版本），以及从父类继承来的方法名。类名可省略 `Sketchup::`。一次可以查多个类：

```text
class Face
class Geom::Transformation
class RenderingOptions ShadowInfo
```

显示设置按键读写（`rendering_options["键"]`、`shadow_info["键"]`），官方文档只列键名。`class RenderingOptions`、`class ShadowInfo` 的末尾附有【补充】设置键说明：每个键对应界面上哪一项、取什么值、和哪些键相互影响。

### Step 4：查看方法

`method <类名#方法名>` 返回签名、参数、Hash 选项、返回值、最低版本、注意事项和示例。类方法写 `类名.方法名`；继承来的方法用子类名也能查到。一次可以查多个方法，开工前把要用的一起查完。专题全文用 `guide <专题名>`。

```text
method Face#pushpull
method Entities#add_group Entities#add_instance DefinitionList#remove
method Sketchup.active_model
guide exporter_options
```

### 辅助：关键词检索

不知道在哪个分类时用 `search`，类名、方法名、设置键、常量名、说明都能搜，名称命中的排在前面。官方文档是英文的，关键词用英文；设置键的【补充】说明是中文的，界面上的叫法也能搜到。按返回的 `类名#方法名` 接着做 Step 4。

```text
search section plane
search edge display
search 轮廓线
```

### 版本

文档是最新版。方法的最低版本高于用户的 SketchUp（`print(su)` 的版本号，26 = 2026）就不能用。要确认用户这台 SketchUp 的实际情况，直接在里面查：`su.run("Sketchup::Camera.instance_methods(false).sort", operation=None)`。

## 3. 执行代码：`su.run`

```python
result = su.run("""
model = Sketchup.active_model
grid = model.entities.add_group
grid.name = "柱网"
xs.product(ys).each { |x, y| ... }
{ id: grid.persistent_id, count: grid.entities.length }
""", vars={"xs": [0, 8400, 16800], "ys": [0, 6600]}, operation="创建柱网")
```

- **返回值**：代码最后一个表达式的值。哈希、数组、数字、字符串转成对应的 Python 对象；其他 Ruby 对象返回 inspect 字符串。Ruby 里 `puts`、`warn` 的内容会直接打印出来。完整结果在 `su.last_result`。
- **传数据用 `vars`**：每一项成为同名的 Ruby 局部变量，所以键名要以小写字母或下划线开头（`P`、`CFG` 在 Ruby 里是常量，会被拒）。数字不带单位，在代码里再加 `.mm`。不要用 f-string 把数据拼进代码：Ruby 的 `{ }` 会和 f-string 冲突，路径里的引号、反斜杠也容易出错。
- **撤销**：`operation` 是撤销步骤的名字，一次 `run` 就是一步撤销。代码出任何错（包括语法错误、超时）都会整体撤销，这次新建的组件定义、材质、标签也一起撤掉，模型里不留半成品。只读查询和只改显示设置时传 `operation=None`。代码里不要再写 `start_operation` / `commit_operation`。
- **作用域**：每次 `run` 都从零开始，上一次的局部变量和 `def` 定义的方法都不在了。接着处理上次建的对象，按第 12 条找回。好几次 `run` 都要用的 Ruby 辅助函数，在 Python 里写成一个字符串，拼在每段代码前面。
- **Ruby 写法**：`def` 定义的方法看不到外面的局部变量（包括 `vars` 传进来的），代码里的辅助函数写成 lambda：`box = ->(x, y) { ... }`，调用 `box.(x, y)`。`ORIGIN`、`X_AXIS`、`Y_AXIS`、`Z_AXIS`、`IDENTITY` 是顶层常量，不加 `Geom::`。
- **出错**：抛 `SketchUpRubyError`，消息里有 Ruby 异常类、出错行 `(agent):行号`，以及修改是否已撤销。`NoMethodError`、`ArgumentError` 说明方法、参数或设置键用错了，按第 2 节查准再改。
- **超时**：`timeout` 默认 120 秒。抛 `SketchUpTimeoutError` 时任务可能还在执行（SketchUp 的建模运算没法中途打断），不要重新提交同样的代码，用 `su.wait(job_id)` 接着等。如果异常里列出了对话框，说明 SketchUp 停在对话框上：告诉用户该点哪个按钮，等用户处理；不要用桌面自动化替用户点击。
- **分批**：执行期间 SketchUp 界面不响应。大模型按构件或楼层分几次 `run`，每次控制在几十秒内；也不要一个构件一次 `run`，每次往返都有固定开销，同类构件在一次 `run` 里循环建完。

## 4. 编码规范

这些错误多数不报错，只会悄悄建错，写代码时逐条注意。

### 4.1 单位与尺寸

1. **长度一律带单位**：裸数字按英寸处理，`3000` 就是 3000 英寸，不报错，只会把构件放大 25.4 倍。写 `3000.mm`、`3.m`；坐标写 `[1000.mm, 0, 0]`（0 可以不带）。模型的显示单位不影响这条。角度用 `30.degrees`。坐标多的代码先定义 `pt = ->(x, y, z = 0) { Geom::Point3d.new(x.mm, y.mm, z.mm) }`，所有点都经它生成，就不会漏。
2. **读回的长度要换算**：从模型读到的坐标、长度、`bounds` 是英寸，返回给 Python 前用 `.to_mm` 换成毫米。`.to_mm` 只用在从模型读到的值上：`vars` 传进来或自己算出来的毫米数再 `.to_mm` 会放大 25.4 倍。面积 `face.area` 是平方英寸，乘 `0.0254**2` 得平方米。
3. **旋转后的包围盒**：`entity.bounds` 是世界坐标下、与坐标轴对齐的包围盒，旋转过的构件量出来比实物大。要构件本身的尺寸，量 `entity.definition.bounds`。

### 4.2 面的方向与材质

4. **拉伸方向**：z=0 平面上画的面，法线一律朝下，与顶点顺序无关；其他高度的面，法线方向随顶点顺序。所以拉伸前统一写 `face.reverse! if face.normal.z < 0`，再 `face.pushpull(h)`。在竖直面上拉伸时同理，先确认 `face.normal` 朝向要拉的方向。
5. **正反面**：面分正反，背面默认显示为浅蓝灰色。`face.material` 只涂正面，背面要设 `back_material`。玻璃、幕墙板、屋面板这类单片面，建完让法线朝向室外（`reverse!`），两面都可能被看到就两面都设材质。组或组件上设的材质，会填到里面没设材质的面上，正反两面都填。所以要单独上色的部分（窗框、阳台板）各建一个组，给组设材质，不用去找刚建出来的是哪几个面。
6. **透明**：给材质设 `alpha`（0–1）就是透明，不用改显示设置。`rendering_options["ModelTransparency"]` 是 X 光模式，不是材质透明。

### 4.3 几何与对象

7. **新几何建在新组里**：`group = model.entities.add_group`，再往 `group.entities` 里画。直接画在 `model.entities` 里，会和已有几何粘连、互相切分，破坏用户的模型。
8. **几何操作后旧引用可能失效**：`pushpull`、`add_face`、`erase!`、`intersect_with` 会合并、切分同一个 entities 里的几何。之前拿到的面、边可能已被删除，再用就报 `reference to deleted DrawingElement`。例如一个面和相邻的面共边时，拉伸后原来的面就被删了；推穿洞口后洞口面也没了。操作之后要用的面，从 `group.entities` 里按法线、面积重新找。一个组只建一个实体最不容易出这种问题。
9. **布尔运算会换掉对象**：`subtract`、`union` 等返回一个新组，参与运算的两个组都被删除；名字、标签、属性、`persistent_id` 都不保留。运算后重新命名、设标签、写属性，并记下新的 `persistent_id`。两边都必须是实体组（`manifold?` 为 true），否则静默返回 `nil`。墙上开洞，直接把洞口画进墙的立面轮廓再拉出墙厚更省事（示例 2）。
10. **重复构件用组件**：柱、梁、门窗、家具用 `model.definitions.add` 建一次定义，再 `add_instance` 放置。几何只存一份，几千个构件也很快；改 `definition.entities` 会改到全部实例，只想改一个先 `instance.make_unique`。
11. **删除**：不要一边遍历一边删，先收集到数组，再 `entities.erase_entities(list)`。

### 4.4 跨次操作

12. **找回上次建的对象**：建对象时返回 `entity.persistent_id`，以后用 `model.find_entity_by_persistent_id(id)` 找回；或者给对象起名字、写属性，再按名字或属性查找。不要依赖 `entityID` 或上一次 `run` 的变量。
13. **可以重跑**：给每批生成的组和这一批专用的组件定义写批次标记（`set_attribute("cad_bridge", "batch", "柱网")`），重建前先删掉带同一标记的旧对象：组用 `erase_entities`，组件定义用 `model.definitions.remove(d)`，它的实例会一并删除（示例 1）。否则改了参数重跑，模型里会叠出两份，同名定义也会沿用旧几何。

### 4.5 剖切面、场景与显示设置

14. **剖切面激活后一直生效**：之后所有截图都是剖开的，画面像是模型建坏了（截图时会打印提醒）。用完就取消激活：`entities.active_section_plane = nil`（剖切面在哪个组里，就用那个组的 `entities`）；不再需要就删掉。不要在远处建一个空剖切面来“顶替”：它会撑大模型包围盒，缩放和构图都跟着跑偏。要长期保留的剖切状态存进场景（示例 14）。
15. **场景存的是 `page.update` 那一刻的视图**（相机、样式、阴影、标签可见性、剖切）：先用 `SketchupBridge::SU.set_camera(...)` 设好相机（参数同 `capture`，自动取景），再 `page = pages[名称] || pages.add(名称)`、`page.update`（示例 13）。`page.update` 只对正在存的这个场景调：不带参数会把当前视图全部写进去，`pages.each(&:update)` 会把所有场景的相机都换成当前这一个。前面步骤隐藏的标签、激活的剖切面也会一起存进去，存之前确认视图里只有这个场景该有的。不要用 `pages.selected_page =` 切场景：它播放过渡动画，执行结束后才慢慢切过去，这期间设相机、截图、`update` 都会打断动画。代码里切场景用 `SketchupBridge::SU.show_scene("名称")`，立即生效。
16. **有了场景，改显示设置要存进去**：切场景（`show_scene`、`capture(scene=)`）会换成场景存的样式、阴影和标签可见性，当前视图上的改动随之丢失，`page.update` 也不保存样式的改动。边线、平面样式、背景这类 `rendering_options` 改完调 `model.styles.update_selected_style`，所有场景一起生效；阴影逐个场景写 `page.shadow_info["DisplayShadows"] = true`；标签可见性设好后逐个场景 `page.update(PAGE_USE_LAYER_VISIBILITY)`，必须带这个参数，否则相机也被换成当前的。切场景时有没存进样式的改动会打印提醒。

### 4.6 不要和用户交互

17. 不调用 `UI.messagebox`、`UI.inputbox`、`UI.openpanel` 等对话框（会被直接拒绝），不切换交互工具（`select_tool`），不调用 `Sketchup.open_file` / `Sketchup.file_new`（会弹出“是否保存”，卡住 SketchUp）。换文件、新建模型用 `get_sketchup(path)`。导入导出传 `show_summary: false`。
18. 用户事先选好的对象，用 `model.selection` 读取；没选就结束本次执行，请用户先在 SketchUp 里选好。

## 5. 建筑建模的工作方式

1. **先定尺寸来源**：用户给的数字、图纸、或常规默认值（层高、墙厚、窗台高）。缺关键尺寸先问；用了默认值，在回复里列出来。
2. **照 CAD、平面图建模时，图纸是权威**：用户要的是和图一致的模型，不是看起来更合理的模型。
   - 先清点再建模：列出图上所有有内容的图层（承重墙、新建墙、拆改墙、门窗、家具、洁具等），每一层要么建，要么说明为什么不建。不要只挑一个墙图层就开工。
   - 图上的对象，数量、位置、尺寸、朝向都按图：不增加图上没有的东西，不因为看不懂某个块就略过（问用户），不为了好看或动线挪动家具，不用同一个通用模板代替不同的对象。保留墙和新建墙分开建组。
   - 先用简单体块按图对好位置（对照返回的坐标和尺寸），再加细节；细节只加在已经对好的轮廓以内。
3. **按构件分批**：轴网柱网 → 墙体门窗 → 楼板楼梯 → 屋顶 → 立面 → 材质标签。每批一次 `run`，返回的数字对了（第 6 节）再建下一批。高层按楼层段分批（示例 8）。
4. **整理成建筑师能接着改的模型**：每个构件一个组或组件，名字有意义（`KZ1`、`1F-南墙`、`C1518`）；标签按专业和类别分（`结构-柱`、`建筑-墙`、`门窗`、`家具`）。
5. **整栋楼、多批次的建模写成脚本**：把参数（轴网、层高、墙厚、门窗表）集中写在工作目录 `build_xxx.py` 的开头，各批次代码放在同一个文件里，用 python_executor 的 `file_path` 执行。改参数后重跑，配合第 13 条不会重复。相互推导的尺寸只写一处，例如楼梯高度写成踏步数 × 踏步高，不要另填一个数。

## 6. 交付

建完就交付，由用户看模型、定下一步。不另做截图校验：一栋楼在截图里只有几百像素宽，细节看不清，数字核对查不出的问题看图也查不出；反复换角度截图只会浪费用户的时间和钱。

1. **数字核对写在建模代码里**：每批代码最后一个表达式返回这批的数量、包围盒、顶标高，和要求逐项对照，不对就改。核对位置和尺寸，不只核对数量：组数、名字都对，整层构件却长到了地下，只有看标高才发现。改了显示设置，读回键值确认设上了。
2. **只做用户要求的**：用户没要求的场景、效果图、阴影、背景、配色、细部（模板缝、螺栓孔之类）都不做，写进回答的可选下一步。原因：每多做一项，用户都要多等、多花钱，做出来的也未必是用户要的。
3. **截图有数**：交付时截一张总体图（照图纸建模再加一张俯视图），看有没有缺构件、错位、被剖开，有就改了重截这一张。用户要几张图就出几张，每张按第 7 节一次设好参数；构图、明暗、颜色上拿不准的写进回答由用户定，不换角度、换参数重截。
4. **收尾**：保存模型（新建且没保存过的 `model.path` 为空，`model.save` 必须给路径）；`kept = su.keep_captures([要给用户的图])` 把这些图移到工作目录、删掉其余截图；回答里放 `kept` 里的图 `![说明](path)`，列出关键数字和与要求、图纸不一致的地方，结束这一轮。

`info = su.summary()` 返回模型概况，长度 mm：`bounds_mm`（模型包围盒，不含剖切面、辅助线、文字、尺寸）、`top_level_counts`（顶层对象按类型计数）、`containers`（顶层组和组件的名称、标签、面数、是否实体、包围盒、`persistent_id`）、`definitions`（组件定义及实例数）、`section_planes`（是否激活）、`scenes`、`tags`、`materials`、`selection`。`su.summary(depth=2)` 再展开组里的组和组件（`children`，包围盒是世界坐标）。模型尺寸大得离谱时会打印提醒，多半是有长度漏了 `.mm`。

## 7. 截图与显示设置

`path = su.capture(view="iso")`，再用 view_image 查看 `path`。截图默认存到工作目录下的 `截图` 文件夹，交付时用 `keep_captures` 留下要给用户的（第 6 节）。打印出提醒时先看提醒。

| 参数 | 用法 |
|---|---|
| `view` | `iso`（默认，透视）、`top`、`bottom`、`front`、`back`、`left`、`right`（平行投影），或方向 `[x, y, z]`（从模型指向相机，透视，如东北向鸟瞰 `[1, 1, 0.8]`），都自动缩放到放满画面。`current` 是当前视图原样，不缩放 |
| `focus`、`isolate` | `focus` 列出对象的 `persistent_id` 或顶层组、组件的名称，相机缩放到它们，如一片墙的立面 `view="left", focus=["端墙"]`；前面的东西照样会挡住，`isolate=True` 临时隐藏其他对象 |
| `eye`、`target`、`fov` | 人视角、室内视角：相机位置和注视点 `[x, y, z]`（毫米），如 `eye=[0, -30000, 1600]`；`fov` 是视角（度），默认 30，室内取 50–60。给了 `eye` 就不用 `view`，也不缩放 |
| `section_z` | 在这个标高（毫米）水平剖切、保留下方，配合 `view="top"` 出平面图。剖到的实体按剖面填充色（默认黑色）显示 |
| `sections=False` | 不显示模型里激活着的剖切面的剖切效果，看完整模型。激活着剖切面又没加这个参数时，会打印提醒 |
| `scene` | 切到这个场景，用场景存的相机、样式、阴影、剖切出图；截图后模型停在这个场景。不能和 `view`、`eye`、`fov`、`focus`、`section_z` 同用 |
| `edges=False` | 这张图不画任何线（边线和轮廓线），模型大、线条密到整片发黑时用。要模型本身不显示线，改显示设置（下表） |
| `perspective` | `True` 透视、`False` 平行投影，默认随 `view` |
| `width`、`height` | 像素，默认 1280 × 800。大模型看细部时加大，或用 `focus` 拉近 |
| `path` | 第一个参数，如 `su.capture("鸟瞰.png")`，存在 `截图` 文件夹里，同名覆盖。不给时按视图和时间命名，不覆盖之前的截图 |

截图按模型现有的显示设置（阴影、边线、隐藏的标签）出图；为这张图临时改的相机、`edges`、`sections`、`section_z`、`isolate` 出图后撤回，模型和撤销记录不留痕迹。`scene` 例外：切过去就停在那个场景，显示设置也换成场景存的（第 16 条）。`capture` 当场出图，一次执行里可以连续截多张，前后不用 `sleep`。

**显示设置**改的是 `model.rendering_options`（边线、平面样式、背景）和 `model.shadow_info`（阴影、日照），两者的键不通用，键的含义和取值查 `class RenderingOptions`、`class ShadowInfo`。常用的：

| 效果 | 写法 |
|---|---|
| 去掉模型上所有的线 | `rendering_options["EdgeDisplayMode"] = 0` 且 `rendering_options["DrawSilhouettes"] = false`。只关前一个，轮廓线还在，物体外框照样是黑的 |
| 显示阴影 | `shadow_info["DisplayShadows"] = true`。地点三项一起设：`"Latitude"`、`"Longitude"`、`"TZOffset"`（当地时区，如上海 8），只改经纬度，太阳位置会错 |
| 日照时刻 | `shadow_info["ShadowTime"] = Time.utc(2026, 6, 22, 15)`，填当地钟点；不要用 `Time.local`，会差几个小时 |

模型里有场景时，改完还要存进场景（第 16 条）。效果图的完整做法见示例 15。Ruby 代码里也能直接调用 `SketchupBridge::SU.summary`、`SketchupBridge::SU.capture(path: ..., view: "top")`、`SketchupBridge::SU.set_camera(view: "front")` 和 `SketchupBridge::SU.show_scene("名称")`。

## 8. 其他接口

| 接口 | 说明 |
|---|---|
| `su.status()` | 是否在执行任务、排队情况、当前文档 |
| `su.wait(job_id)` | 接着等之前超时的任务 |
| `su.document` | 当前文档：标题、路径、是否已修改、显示单位 |
| `su.dialog_titles()` | SketchUp 主窗口以外打开着的窗口标题，通常是对话框 |
| `list_sketchup_instances()` | 所有运行中的 SketchUp 及连接状态（从 `CADAgent.software_link_kit.sketchup` 导入） |