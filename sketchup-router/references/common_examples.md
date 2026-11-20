# SketchUp 建筑建模示例

```python``` 代码块在 python_executor 里运行（`su` 已连接）；```ruby``` 代码块是一次完整的 `su.run(code)`。每个示例都能单独运行。尺寸单位 mm，从 Python 传进来的数字在 Ruby 里再加 `.mm`。

示例只演示写法。示例里没出现的类、方法、设置键，先按 SKILL.md 第 2 节查文档再用。不报错却会建错、拍错的规则在 SKILL.md 第 4、7 节（单位、拉伸方向、剖切面、场景与显示设置、截图），没读过先读。

改了示例建议在真实 SketchUp 环境中运行测试验证。

目录

1. 轴网与柱网（组件、可重跑）
2. 墙体与门窗洞口
3. 门窗组件与门窗表
4. 楼板与楼梯洞
5. 双坡屋顶
6. 幕墙立面分格
7. 方案体块与建筑面积估算
8. 高层框架：按楼层段批量建柱、梁、板
9. 标签与材质：按专业整理模型
10. 移动、旋转、阵列复制
11. 读取用户选中的对象
12. 统计：遍历全部构件，按标签汇总
13. 场景与视角
14. 剖切面
15. 效果图：阴影、人视角、去掉边线
16. 日照分析：逐时阴影
17. 导入 CAD 图纸
18. 保存与另存

## 1. 轴网与柱网（组件、可重跑）

柱用组件：几何只存一份，改定义所有柱一起变。生成的组和组件定义都写批次标记，重跑时先清掉上一版。

```python
grid = {"xs": [0, 8400, 16800, 25200], "ys": [0, 6600, 13200], "b": 600, "h": 600, "height": 3900}
su.run("""
model = Sketchup.active_model
batch = "柱网"
marked = ->(e) { e.get_attribute("agent_model", "batch") == batch }
model.entities.erase_entities(model.entities.select(&marked))
model.definitions.select(&marked).each { |d| model.definitions.remove(d) }   # 实例一并删除

column = model.definitions.add("KZ #{grid['b']}x#{grid['h']}")
column.set_attribute("agent_model", "batch", batch)
b, h = grid["b"].mm, grid["h"].mm
face = column.entities.add_face([-b / 2, -h / 2, 0], [b / 2, -h / 2, 0], [b / 2, h / 2, 0], [-b / 2, h / 2, 0])
face.reverse! if face.normal.z < 0
face.pushpull(grid["height"].mm)     # 组件原点在柱底中心，实例直接放在轴线交点

group = model.entities.add_group
group.name = batch
group.set_attribute("agent_model", "batch", batch)
tag = model.layers["结构-柱"] || model.layers.add("结构-柱")
grid["xs"].product(grid["ys"]).each do |x, y|
  group.entities.add_instance(column, Geom::Transformation.translation([x.mm, y.mm, 0])).layer = tag
end
{ id: group.persistent_id, columns: column.count_used_instances }
""", vars={"grid": grid}, operation="创建柱网")
```

## 2. 墙体与门窗洞口

先在 y=0 的立面上画墙轮廓：门（落地洞口）编进外轮廓，窗（悬空洞口）画成内框后删掉框内的面；再拉出墙厚，最后摆到墙中线上。不用布尔运算，结果是干净的实体。

```python
wall = {
    "name": "1F-南墙", "p1": [0, 0], "p2": [8400, 0], "height": 3900, "thickness": 200,
    # at：洞口中心到墙起点 p1 的距离；sill 为 0 是门
    "openings": [
        {"at": 1500, "width": 1000, "sill": 0, "height": 2100},
        {"at": 5200, "width": 1800, "sill": 900, "height": 1800},
    ],
}
su.run("""
model = Sketchup.active_model
x0, y0 = wall["p1"]
x1, y1 = wall["p2"]
length = Math.hypot(x1 - x0, y1 - y0)
h, t = wall["height"], wall["thickness"]
doors, windows = wall["openings"].partition { |o| o["sill"] <= 0 }

group = model.entities.add_group
group.name = wall["name"]
ents = group.entities
outline = [[0, 0]]
doors.sort_by { |o| o["at"] }.each do |o|
  a, b = o["at"] - o["width"] / 2.0, o["at"] + o["width"] / 2.0
  outline += [[a, 0], [a, o["height"]], [b, o["height"]], [b, 0]]
end
outline += [[length, 0], [length, h], [0, h]]
ents.add_face(outline.map { |x, z| [x.mm, 0, z.mm] })
windows.each do |o|
  a, b = o["at"] - o["width"] / 2.0, o["at"] + o["width"] / 2.0
  z0, z1 = o["sill"], o["sill"] + o["height"]
  ents.add_face([[a.mm, 0, z0.mm], [b.mm, 0, z0.mm], [b.mm, 0, z1.mm], [a.mm, 0, z1.mm]])
end
faces = ents.grep(Sketchup::Face).sort_by(&:area)
faces[0...-1].each(&:erase!)                       # 只留面积最大的墙面，删掉窗框内的面
face = ents.grep(Sketchup::Face).first
face.reverse! if face.normal.y < 0
face.pushpull(t.mm)                                # 立面在 y=0，墙厚向 +y

angle = Math.atan2(y1 - y0, x1 - x0)
group.transform!(Geom::Transformation.translation([x0.mm, y0.mm, 0]) *
                 Geom::Transformation.rotation(ORIGIN, Z_AXIS, angle) *
                 Geom::Transformation.translation([0, -t.mm / 2, 0]))   # 墙厚居中在中线上
group.layer = model.layers["建筑-墙"] || model.layers.add("建筑-墙")
{ id: group.persistent_id, solid: group.manifold?, length_mm: length.round }
""", vars={"wall": wall}, operation="创建墙体")
```

## 3. 门窗组件与门窗表

窗按编号建成组件（C1518 = 宽 1500、高 1800）：同号的窗只存一份几何，门窗表直接按组件定义统计。

```python
window = {"code": "C1518", "width": 1500, "height": 1800, "frame": 60, "depth": 80}
placements = [[1000, -2000, 900], [4000, -2000, 900]]   # 每樘窗左下角的位置 [x, y, z]
su.run("""
model = Sketchup.active_model
w, h, f, d = window["width"].mm, window["height"].mm, window["frame"].mm, window["depth"].mm
definition = model.definitions[window["code"]] || model.definitions.add(window["code"])
if definition.entities.length == 0
  frame = definition.entities.add_face([0, 0, 0], [w, 0, 0], [w, 0, h], [0, 0, h])     # 在 y=0 立面上画窗框
  definition.entities.add_face([f, 0, f], [w - f, 0, f], [w - f, 0, h - f], [f, 0, h - f]).erase!
  frame = definition.entities.grep(Sketchup::Face).max_by(&:area)
  frame.reverse! if frame.normal.y < 0
  frame.pushpull(d)
  glass = model.materials["玻璃"] || model.materials.add("玻璃")
  glass.color = Sketchup::Color.new(150, 190, 220)
  glass.alpha = 0.35
  pane = definition.entities.add_face([f, d / 2, f], [w - f, d / 2, f], [w - f, d / 2, h - f], [f, d / 2, h - f])
  pane.material = glass
  pane.back_material = glass
end
tag = model.layers["门窗"] || model.layers.add("门窗")
placements.each do |x, y, z|
  model.entities.add_instance(definition, Geom::Transformation.translation([x.mm, y.mm, z.mm])).layer = tag
end

# 门窗表：编号以 C（窗）或 M（门）开头的组件
model.definitions.select { |dfn| dfn.name =~ /\\A[CM]\\d/ }.map { |dfn| [dfn.name, dfn.count_used_instances] }.to_h
""", vars={"window": window, "placements": placements}, operation="放置窗")
```

## 4. 楼板与楼梯洞

楼板顶面在楼层标高，向下拉板厚。洞口先画成内框，再删掉框内的面。

```python
slab = {"name": "2F-楼板", "level": 3900, "thickness": 120,
        "outline": [[0, 0], [25200, 0], [25200, 13200], [0, 13200]],
        "holes": [[[8400, 6600], [11000, 6600], [11000, 12000], [8400, 12000]]]}
su.run("""
model = Sketchup.active_model
z = slab["level"].mm
group = model.entities.add_group
group.name = slab["name"]
outer = group.entities.add_face(slab["outline"].map { |x, y| [x.mm, y.mm, z] })
slab["holes"].each { |hole| group.entities.add_face(hole.map { |x, y| [x.mm, y.mm, z] }).erase! }
outer = group.entities.grep(Sketchup::Face).first
outer.reverse! if outer.normal.z < 0
outer.pushpull(-slab["thickness"].mm)      # 负值：沿法线反方向（向下）
group.layer = model.layers["结构-楼板"] || model.layers.add("结构-楼板")
{ id: group.persistent_id, solid: group.manifold?,
  z_mm: [group.bounds.min.z, group.bounds.max.z].map { |v| v.to_mm.round } }
""", vars={"slab": slab}, operation="创建楼板")
```

## 5. 双坡屋顶

在山墙所在的竖直面画屋顶截面三角形，沿房屋长度方向拉出。

```python
roof = {"length": 12000, "span": 8000, "eave": 6000, "rise": 2500, "origin": [0, 20000]}
su.run("""
model = Sketchup.active_model
l, s = roof["length"].mm, roof["span"].mm
eave, ridge = roof["eave"].mm, (roof["eave"] + roof["rise"]).mm
x0, y0 = roof["origin"].map(&:mm)
group = model.entities.add_group
group.name = "双坡屋顶"
gable = group.entities.add_face([x0, y0, eave], [x0, y0 + s, eave], [x0, y0 + s / 2, ridge])   # x=x0 处的山墙截面
gable.reverse! if gable.normal.x < 0
gable.pushpull(l)
{ id: group.persistent_id, solid: group.manifold?, ridge_mm: group.bounds.max.z.to_mm.round }
""", vars={"roof": roof}, operation="创建屋顶")
```

## 6. 幕墙立面分格

竖梃、横梁各做一个组件，按分格阵列；玻璃是一块带透明材质的面。

```python
facade = {"name": "南立面幕墙", "width": 25200, "height": 15600, "bay": 1400, "floor": 3900,
          "y": -3000, "mullion": [60, 150]}
su.run("""
model = Sketchup.active_model
width, height, bay, floor_h = facade["width"].mm, facade["height"].mm, facade["bay"].mm, facade["floor"].mm
mw, md = facade["mullion"].map(&:mm)
y = facade["y"].mm
bar = lambda do |name, sx, sy, sz|
  definition = model.definitions[name] || model.definitions.add(name)
  if definition.entities.length == 0
    face = definition.entities.add_face([0, 0, 0], [sx, 0, 0], [sx, sy, 0], [0, sy, 0])
    face.reverse! if face.normal.z < 0
    face.pushpull(sz)
  end
  definition
end
mullion = bar.call("竖梃 #{facade['mullion'].join('x')} H#{facade['height']}", mw, md, height)
transom = bar.call("横梁 #{facade['mullion'].join('x')} L#{facade['bay']}", bay, md, mw)

group = model.entities.add_group
group.name = facade["name"]
ents = group.entities
bays = (width / bay).round
(0..bays).each do |i|
  x = (i * bay - mw / 2).clamp(0, width - mw)          # 竖梃中心在分格线上，两端的收进幕墙范围内
  ents.add_instance(mullion, Geom::Transformation.translation([x, y, 0]))
end
levels = (0..(height / floor_h).floor).map { |i| i * floor_h }
levels.each do |level|
  z = (level - mw / 2).clamp(0, height - mw)           # 横梁中心在楼层线上，顶、底两根收进幕墙范围内
  (0...bays).each { |i| ents.add_instance(transom, Geom::Transformation.translation([i * bay, y, z])) }
end
glass = model.materials["玻璃"] || model.materials.add("玻璃")
glass.color = Sketchup::Color.new(150, 190, 220)
glass.alpha = 0.35
pane = ents.add_face([0, y + md / 2, 0], [width, y + md / 2, 0], [width, y + md / 2, height], [0, y + md / 2, height])
pane.material = glass
pane.back_material = glass
{ id: group.persistent_id, mullions: bays + 1, transoms: levels.size * bays }
""", vars={"facade": facade}, operation="幕墙分格")
```

## 7. 方案体块与建筑面积估算

每栋楼一个组：底面按层高 × 层数拉伸，再在每层标高画一圈楼层线。建筑面积按“底面积 × 层数”粗估。

```python
buildings = [
    {"name": "1#楼", "floors": 18, "floor_height": 3000,
     "footprint": [[0, 30000], [36000, 30000], [36000, 45000], [0, 45000]]},
    {"name": "2#楼", "floors": 11, "floor_height": 3000,
     "footprint": [[50000, 30000], [86000, 30000], [86000, 45000], [50000, 45000]]},
]
su.run("""
model = Sketchup.active_model
tag = model.layers["体块"] || model.layers.add("体块")
buildings.map do |b|
  group = model.entities.add_group
  group.name = b["name"]
  group.layer = tag
  base = group.entities.add_face(b["footprint"].map { |x, y| [x.mm, y.mm, 0] })
  base.reverse! if base.normal.z < 0
  area_m2 = base.area * 0.0254**2
  base.pushpull((b["floors"] * b["floor_height"]).mm)
  (1...b["floors"]).each do |i|
    ring = b["footprint"].map { |x, y| [x.mm, y.mm, (i * b["floor_height"]).mm] }
    group.entities.add_edges(ring + [ring.first])   # 楼层线把侧面分成一层一条
  end
  { name: b["name"], height_m: b["floors"] * b["floor_height"] / 1000.0,
    footprint_m2: area_m2.round(1), floor_area_m2: (area_m2 * b["floors"]).round(1) }
end
""", vars={"buildings": buildings}, operation="方案体块")
```

## 8. 高层框架：按楼层段批量建柱、梁、板

构件多（几千根梁柱）时的写法：柱、梁、板各建一个组件定义，按轴网放实例；每层一个组，写批次标记，可以重跑；在 Python 里按楼层段循环，每段一次 `run`。

```python
tower = {"origin": [0, 60000], "floors": 24, "floor_height": 3600,
         "xs": [0, 8400, 16800, 25200, 33600], "ys": [0, 8400, 16800, 25200],
         "column": [800, 800], "beam": [300, 700], "slab": 150}
code = """
model = Sketchup.active_model
box = lambda do |name, sx, sy, sz|              # 长方体组件：同名的只建一次，原点在左下角
  definition = model.definitions[name] || model.definitions.add(name)
  if definition.entities.length == 0
    face = definition.entities.add_face([0, 0, 0], [sx, 0, 0], [sx, sy, 0], [0, sy, 0])
    face.reverse! if face.normal.z < 0
    face.pushpull(sz)
  end
  definition
end
h = tower["floor_height"].mm
cb, ch = tower["column"].map(&:mm)
bb, bh = tower["beam"].map(&:mm)
t = tower["slab"].mm
ox, oy = tower["origin"]
xs, ys = tower["xs"], tower["ys"]               # 毫米数，用的时候再加 .mm
column = box.call("KZ #{tower['column'].join('x')} H#{tower['floor_height']}", cb, ch, h)
slab = box.call("LB #{xs.last - xs.first}x#{ys.last - ys.first} t#{tower['slab']}", (xs.last - xs.first).mm, (ys.last - ys.first).mm, t)
beam = ->(span) { box.call("KL #{tower['beam'].join('x')} L#{span}", span.mm, bb, bh) }
turn = Geom::Transformation.rotation(ORIGIN, Z_AXIS, 90.degrees)   # 梁定义沿 x，转 90° 用作 y 向梁
move = ->(x, y, z) { Geom::Transformation.translation([(ox + x).mm, (oy + y).mm, z]) }

floors.map do |i|
  batch = "框架-#{i + 1}F"
  old = model.entities.grep(Sketchup::Group).select { |g| g.get_attribute("agent_model", "batch") == batch }
  model.entities.erase_entities(old) unless old.empty?
  group = model.entities.add_group
  group.name = "#{i + 1}F 框架"
  group.set_attribute("agent_model", "batch", batch)
  ents = group.entities
  z, top = i * h, (i + 1) * h
  xs.product(ys).each { |x, y| ents.add_instance(column, move.(x, y, z) * Geom::Transformation.translation([-cb / 2, -ch / 2, 0])) }
  xs.each_cons(2) { |x0, x1| ys.each { |y| ents.add_instance(beam.(x1 - x0), move.(x0, y, top - bh) * Geom::Transformation.translation([0, -bb / 2, 0])) } }
  ys.each_cons(2) { |y0, y1| xs.each { |x| ents.add_instance(beam.(y1 - y0), move.(x, y0, top - bh) * Geom::Transformation.translation([bb / 2, 0, 0]) * turn) } }
  ents.add_instance(slab, move.(xs.first, ys.first, top - t))
  ents.length
end.sum
"""
segment = 8                                     # 每次 run 建 8 层
for start in range(0, tower["floors"], segment):
    floors = list(range(start, min(start + segment, tower["floors"])))
    count = su.run(code, vars={"tower": tower, "floors": floors}, operation=f"框架 {floors[0] + 1}-{floors[-1] + 1}F")
    print(f"{floors[0] + 1}-{floors[-1] + 1}F：{count} 个构件")
```

改了参数整段重跑，各层先删掉旧的再建，不会叠出两份。核对用 `su.summary()` 看每层组的包围盒标高，构件数看 `definitions` 里各定义的实例数。

## 9. 标签与材质：按专业整理模型

按名字把构件归到标签下；出图前可以隐藏标签。界面上的“标签”在 API 里仍叫 `layers` / `layer`。规则按顺序匹配，具体的写在前面（“幕墙”要排在“墙”前面）。

```ruby
model = Sketchup.active_model
rules = { /幕墙/ => "建筑-幕墙", /\AKZ|柱/ => "结构-柱", /墙/ => "建筑-墙", /楼板/ => "结构-楼板", /\A[CM]\d/ => "门窗" }
counts = Hash.new(0)
model.entities.each do |entity|
  next unless entity.is_a?(Sketchup::Group) || entity.is_a?(Sketchup::ComponentInstance)
  name = entity.is_a?(Sketchup::Group) ? entity.name : entity.definition.name
  rule = rules.find { |pattern, _| name =~ pattern }
  next unless rule
  entity.layer = model.layers[rule[1]] || model.layers.add(rule[1])
  counts[rule[1]] += 1
end
concrete = model.materials["混凝土"] || model.materials.add("混凝土")
concrete.color = Sketchup::Color.new(190, 190, 185)
model.entities.grep(Sketchup::Group).select { |g| g.layer.name == "结构-楼板" }.each { |g| g.material = concrete }
furniture = model.layers["家具"] || model.layers.add("家具")
furniture.visible = false            # 隐藏标签；截图后记得恢复 visible = true
counts
```

## 10. 移动、旋转、阵列复制

```ruby
model = Sketchup.active_model
unit = model.entities.add_group
unit.name = "车位"
face = unit.entities.add_face([0, 0, 0], [2500.mm, 0, 0], [2500.mm, 5300.mm, 0], [0, 5300.mm, 0])
face.reverse! if face.normal.z < 0
unit.transform!(Geom::Transformation.translation([0, -15000.mm, 0]))                       # 移动
unit.transform!(Geom::Transformation.rotation(unit.bounds.center, Z_AXIS, 90.degrees))     # 绕自身中心旋转 90°
copies = (1..9).map do |i|                                                                   # 沿 x 方向阵列 9 个，间距 2500
  copy = unit.copy
  copy.transform!(Geom::Transformation.translation([(i * 2500).mm, 0, 0]))
  copy
end
{ count: copies.size + 1, last_id: copies.last.persistent_id }
```

## 11. 读取用户选中的对象

```ruby
selected = Sketchup.active_model.selection.to_a
if selected.empty?
  { selected: 0 }    # 没选：结束本次执行，请用户先在 SketchUp 里选好
else
  selected.first(50).map do |e|
    name = e.respond_to?(:name) ? e.name : nil
    name = e.definition.name if e.is_a?(Sketchup::ComponentInstance) && name.to_s.empty?
    { type: e.typename, id: e.persistent_id, name: name, tag: e.layer.name,
      size_mm: [e.bounds.width, e.bounds.height, e.bounds.depth].map { |v| v.to_mm.round } }
  end
end
```

## 12. 统计：遍历全部构件，按标签汇总

递归进入组和组件，用累积变换得到世界坐标下的真实面积。这里统计每个标签下朝上的面的面积（如楼板顶面）。组件里的部件通常没设标签，算在它所在组的标签下。

```ruby
model = Sketchup.active_model
untagged = model.layers[0]                   # 默认标签（界面上叫“未标记”）
area = Hash.new(0.0)
walk = lambda do |entities, transformation, tag|
  entities.each do |entity|
    case entity
    when Sketchup::Face
      normal = entity.normal.transform(transformation)
      area[tag] += entity.area(transformation) if normal.z > 0.99
    when Sketchup::Group, Sketchup::ComponentInstance
      child_tag = entity.layer == untagged ? tag : entity.layer.name
      walk.call(entity.definition.entities, transformation * entity.transformation, child_tag)
    end
  end
end
walk.call(model.entities, Geom::Transformation.new, "未标记")
area.transform_values { |v| (v * 0.0254**2).round(2) }   # 平方英寸换算成平方米
```

## 13. 场景与视角

场景存的是 `page.update` 那一刻的视图。每个场景都是“`set_camera` 设好相机 → 这一个场景 `update`”，不经过 `selected_page=`。`set_camera` 的参数同 `su.capture`，自动取景。用户要场景图时，存完每个场景截一张交给用户。

```python
su.run("""
model = Sketchup.active_model
save_scene = lambda do |name, **camera|
  AgentBridge::SU.set_camera(**camera)
  page = model.pages[name] || model.pages.add(name)
  page.update                                 # 只更新这一个场景：存当前相机、剖切、样式、标签可见性
end
save_scene.("01 鸟瞰", view: [-1.0, -1.4, 0.9])                    # 西南方向鸟瞰
save_scene.("02 总平面", view: "top")                               # 平行投影
save_scene.("03 南立面", view: "front")
save_scene.("04 人视", eye: [-8000, -15000, 1600], target: [6000, 4000, 3000], fov: 50)
model.pages.map(&:name)
""", operation="存场景")
print([su.capture(scene=name) for name in ("01 鸟瞰", "02 总平面", "03 南立面", "04 人视")])
```

`capture(scene=...)` 截图后停在那个场景。代码里要把模型切到某个场景交给用户，用 `AgentBridge::SU.show_scene("01 鸟瞰")`。

## 14. 剖切面

剖切面激活后，之后所有截图都是剖开的。要保留的剖切状态存进场景，存完取消激活。

```ruby
model = Sketchup.active_model
section = model.entities.add_section_plane([0, 0, 1200.mm], [0, 0, -1])   # 1.2 m 高的水平剖切面，保留下方
section.name = "1F 平面剖切"
section.activate
AgentBridge::SU.set_camera(view: "top")
page = model.pages["03 一层平面"] || model.pages.add("03 一层平面")
page.update                                   # 场景记下“这个剖切面激活”
model.entities.active_section_plane = nil     # 取消激活：其他截图和场景不受影响
{ scenes: model.pages.map(&:name), active: model.entities.active_section_plane }
```

- 法线指向保留的一侧：`[0, 0, -1]` 保留剖切面以下的部分，从上往下看就是平面图。剖切面在组里时，取消激活用那个组的 `entities.active_section_plane = nil`。
- 用户要这个场景的图：`su.capture(scene="03 一层平面")`。截图后模型停在这个场景，剖切面也随之激活。
- 只是截一张平面图看看，用 `su.capture(view="top", section_z=1200)`，模型里不留剖切面。

## 15. 效果图：阴影、人视角、去掉边线

阴影和着色是模型的显示设置，没有场景时设一次一直有效（有场景时见 SKILL.md 第 16 条）；相机、边线用 `capture` 的参数只对这张图临时指定，出图后撤回。

```python
su.run("""
info = Sketchup.active_model.shadow_info
info["Latitude"] = 31.2                                  # 上海
info["Longitude"] = 121.5
info["TZOffset"] = 8
info["ShadowTime"] = Time.utc(2026, 6, 22, 15, 0, 0)     # 夏至下午 3 点，按当地时间设置
info["DisplayShadows"] = true
info["UseSunForAllShading"] = true                       # 各面按太阳方向分出明暗
nil
""", operation=None)
bird = su.capture(view="iso", edges=False, width=1920, height=1080)            # 鸟瞰：去掉边线，楼体不发黑
street = su.capture(eye=[-30000, -40000, 1600], target=[20000, 10000, 12000],   # 人视角：视点高 1.6 m
                    width=1920, height=1080)
print(bird, street)
```

用户只要一张图、不想改动模型的显示设置时，出图后把 `DisplayShadows`、`UseSunForAllShading` 改回原来的值。

用户要模型本身（SketchUp 里看到的、每个场景里的）都不显示线：

```ruby
model = Sketchup.active_model
ro = model.rendering_options
ro["EdgeDisplayMode"] = 0              # 边线
ro["DrawSilhouettes"] = false          # 轮廓线：不关的话物体外框还是黑的
model.styles.update_selected_style     # 存进样式，切场景也不会变回去
{ edges: ro["EdgeDisplayMode"], profiles: ro["DrawSilhouettes"] }
```

## 16. 日照分析：逐时阴影

设置地点和时刻、打开阴影，按小时各截一张图。

```python
su.run("""
info = Sketchup.active_model.shadow_info
info["Latitude"] = 39.9          # 北京
info["Longitude"] = 116.4
info["TZOffset"] = 8
info["DisplayShadows"] = true
nil
""", operation=None)
shots = []
for hour in range(8, 17, 2):
    su.run('Sketchup.active_model.shadow_info["ShadowTime"] = Time.utc(2026, 1, 20, hour, 0, 0)',
           vars={"hour": hour}, operation=None)   # 大寒日，按当地时间设置
    shots.append(su.capture(view="top"))
print(shots)
```

## 17. 导入 CAD 图纸

导入 DWG/DXF 作为描图底图。导入内容是一个组件实例，放在单独的标签下，描完可隐藏。

```python
import os
dwg = os.path.join(WORKSPACE_DIR, "一层平面.dwg")
su.run("""
model = Sketchup.active_model
before = model.entities.to_a
ok = model.import(path, { show_summary: false, preserve_origin: true, merge_coplanar_faces: false })
imported = model.entities.to_a - before
tag = model.layers["CAD底图"] || model.layers.add("CAD底图")
imported.each { |e| e.layer = tag if e.respond_to?(:layer=) }
{ ok: ok, imported: imported.map(&:typename) }
""", vars={"path": dwg}, operation="导入 CAD")
```

`show_summary: false` 不能省：导入摘要窗口会停在那里等用户点确定。

## 18. 保存与另存

```python
import os
path = os.path.join(WORKSPACE_DIR, "方案A.skp")
copy_path = os.path.join(WORKSPACE_DIR, "方案A_备份.skp")
su.run("""
model = Sketchup.active_model
copied = model.save_copy(copy_path)   # 存一份副本，当前文档路径不变
saved = model.save(path)              # 另存为：之后当前文档就是这个文件
{ copied: copied, saved: saved, path: model.path }
""", vars={"path": path, "copy_path": copy_path}, operation=None)
```

不带参数的 `model.save` 保存到当前路径；新建且没保存过的模型 `model.path` 为空，必须给路径。