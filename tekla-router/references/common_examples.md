# Tekla pythonnet 创建与修改执行模式

本文只在需要创建或修改 Tekla 模型时加载。所有代码都在 `python_executor` 中执行；同一任务后续调用直接复用 `tekla`、`model` 及已导入类型。

## 建模前置规则

### Catalog 与环境值

- Call shape is in the Tekla Open API reference at https://developer.tekla.com/tekla-structures/api-reference and in `<TEKLA_DIR>\bin\Tekla.Structures.Model.xml`. The live Catalog is the only source for profile, material, and bolt values that exist in this model. Do not copy those values from notes, examples, or memory.
- Before `Insert()` uses an environment-specific value, confirm the Catalog type and member for the connected release, then read the value from the running Tekla Catalog. Do not call a convenience helper that hard-codes a name.
- 用户要求的值不存在时，查询并列出当前环境的候选，再按用户意图选择并明确告知替换；不要静默采用第一个结果。

### 操作返回值、提交与失败清理

- 检查所有 `Insert()`、`Modify()`、`Delete()` 和 `CommitChanges()` 的布尔返回值；任何一步失败都要停止，不得宣称成功。
- 将一项任务的改动集中后只提交一次，不要在逐对象循环中调用 `CommitChanges()`。提交后重新查询关键对象，确认数量、标识和修改字段符合任务要求。
- 记录本次任务成功插入的对象。中途失败时逐个删除这些对象并提交清理；若任务修改既有对象，修改前记录原值，失败时逐项恢复并验证。

### 单位

Tekla 几何坐标和长度通常使用 mm；其他量仍以当前年度 API 对相应属性的说明为准。

## 截面选择与使用

所有构件最终都通过 `part.Profile.ProfileString` 使用截面。Agent 按以下优先级处理。

### 1. 型钢：优先

- 从当前环境的 Profile Catalog 查询并使用准确名称，如环境中实际存在的 `HEA300`、`IPE300` 或国标型钢名称。
- 用 `LibraryProfileItem.Select(name)` 校验；不存在就返回候选，不得猜名称。
- 型钢已包含轮廓和截面属性，Agent 只负责选择，不修改 Catalog。

### 2. 参数化截面字符串：次选

- 用于板厚、宽高等尺寸明确，而 Catalog 没有对应固定型钢的情况。
- 前缀、参数顺序和分隔符由当前环境决定；不得直接拼接类似 `HI400-200-8-12` 的字符串并假定有效。
- 应先取得当前环境的 `ParametricProfileItem`，读取 `aProfileItemParameters`，按 `Symbol` 设置 `Value`，再调用 `CreateProfileString()`；最后用 `SelectByProfileName()` 复核。

### 3. 任意截面：不推荐 Agent 创建

- 任意多边形、偏心或多轮廓截面应由人工、专用插件或经审核的导入文件预先写入 Profile Catalog。
- Agent 只使用已经存在且验证通过的 `ProfileString`；不得在普通建模任务中临时绘制轮廓、修改 Catalog 或导入未知 `.lis`、`.uel` 文件。

统一校验后再赋值：

```python
member.Profile.ProfileString = verified_profile_string
```

## 创建构件：梁、柱和斜杆

直线梁与直线柱都使用 `Beam`；严格的柱必须通过 `Beam(Beam.BeamTypeEnum.COLUMN)` 创建，因为 `Beam.Type` 只读，而两点构造函数的默认类型是 `BEAM`。
Tekla 没有独立的 `Brace` 类或枚举值，直线斜杆使用 `Beam.BeamTypeEnum.BEAM`，由两端不同标高的几何表达其斜向布置。

下面的函数以全局坐标一次创建一根水平梁、一根柱和一根斜杆。`beam_profile`、`column_profile`、`brace_profile` 和 `material` 必须来自当前 Tekla Catalog 的查询结果；示例不硬编码环境值。

```python
from Tekla.Structures.Catalogs import LibraryProfileItem, ParametricProfileItem
from Tekla.Structures.Geometry3d import Point
from Tekla.Structures.Model import Beam, TransformationPlane


def _required_catalog_value(label: str, value: str) -> str:
    checked = value.strip()
    if not checked:
        raise ValueError(f"{label} 必须是当前 Tekla Catalog 中已确认的非空值")
    return checked


def _validated_profile_string(label: str, value: str) -> str:
    """校验并返回当前环境可识别的规范化截面字符串。"""
    checked = _required_catalog_value(label, value)

    library_item = LibraryProfileItem()
    if library_item.Select(checked):
        return str(library_item.ProfileName)

    parametric_item = ParametricProfileItem()
    if parametric_item.SelectByProfileName(checked):
        canonical = str(parametric_item.CreateProfileString()).strip()
        if canonical:
            return canonical

    raise ValueError(f"{label} {checked!r} 不存在于当前 Tekla Profile Catalog")


def _insert_linear_member(label, name, member_type, start, end, profile, material):
    member = Beam(member_type)
    member.Name = name
    member.StartPoint = start
    member.EndPoint = end
    member.Profile.ProfileString = profile
    member.Material.MaterialString = material
    if not member.Insert():
        raise RuntimeError(f"{label} {name!r} 创建失败：Insert() 返回 False")
    return member


def _point_coordinates(point):
    return (float(point.X), float(point.Y), float(point.Z))


def create_beam_column_and_brace(
    beam_profile: str,
    column_profile: str,
    brace_profile: str,
    material: str,
):
    """在全局坐标中创建 B1、C1 和 BR1，并在一次提交后重新查询验证。"""
    if not model.GetConnectionStatus():
        raise RuntimeError("Tekla 连接已断开")

    profiles = {
        "梁": _validated_profile_string("梁截面", beam_profile),
        "柱": _validated_profile_string("柱截面", column_profile),
        "斜杆": _validated_profile_string("斜杆截面", brace_profile),
    }
    checked_material = _required_catalog_value("材质", material)
    created = []

    try:
        handler = model.GetWorkPlaneHandler()
        previous_plane = handler.GetCurrentTransformationPlane()
        try:
            if not handler.SetCurrentTransformationPlane(TransformationPlane()):
                raise RuntimeError("切换到全局工作平面失败")

            specs = [
                # 水平梁：API 类型为 BEAM。
                (
                    "梁", "B1", Beam.BeamTypeEnum.BEAM,
                    Point(0.0, 0.0, 3000.0),
                    Point(6000.0, 0.0, 3000.0),
                    profiles["梁"],
                ),
                # 严格柱：必须在构造时指定 COLUMN，不能事后修改只读 Type。
                (
                    "柱", "C1", Beam.BeamTypeEnum.COLUMN,
                    Point(0.0, 0.0, 0.0),
                    Point(0.0, 0.0, 3000.0),
                    profiles["柱"],
                ),
                # 直线斜杆：API 类型仍为 BEAM，两端 Z 坐标不同。
                (
                    "斜杆", "BR1", Beam.BeamTypeEnum.BEAM,
                    Point(0.0, 0.0, 0.0),
                    Point(6000.0, 0.0, 3000.0),
                    profiles["斜杆"],
                ),
            ]

            for label, name, member_type, start, end, profile in specs:
                member = _insert_linear_member(
                    label,
                    name,
                    member_type,
                    start,
                    end,
                    profile,
                    checked_material,
                )
                created.append((label, name, member_type, start, end, member))

            if not model.CommitChanges():
                raise RuntimeError("创建梁、柱和斜杆后 CommitChanges() 返回 False")

            verified = {}
            for label, name, member_type, start, end, member in created:
                reloaded = model.SelectModelObject(member.Identifier)
                if reloaded is None or not isinstance(reloaded, Beam):
                    raise RuntimeError(f"{label} {name!r} 提交后无法按 Identifier 重查")
                if reloaded.Type != member_type:
                    raise RuntimeError(
                        f"{label} {name!r} 类型验证失败：actual={reloaded.Type}"
                    )
                if str(reloaded.Name) != name:
                    raise RuntimeError(
                        f"{label} {name!r} 名称验证失败：actual={str(reloaded.Name)!r}"
                    )
                if _point_coordinates(reloaded.StartPoint) != _point_coordinates(start):
                    raise RuntimeError(f"{label} {name!r} 起点验证失败")
                if _point_coordinates(reloaded.EndPoint) != _point_coordinates(end):
                    raise RuntimeError(f"{label} {name!r} 终点验证失败")
                actual_profile = str(reloaded.Profile.ProfileString).strip()
                if actual_profile.casefold() != profile.casefold():
                    raise RuntimeError(
                        f"{label} {name!r} 截面验证失败：actual={actual_profile!r}"
                    )
                actual_material = str(reloaded.Material.MaterialString).strip()
                if actual_material.casefold() != checked_material.casefold():
                    raise RuntimeError(
                        f"{label} {name!r} 材质验证失败：actual={actual_material!r}"
                    )
                verified[label] = reloaded
        finally:
            if not handler.SetCurrentTransformationPlane(previous_plane):
                raise RuntimeError("恢复原工作平面失败")

        return verified
    except Exception as task_error:
        cleanup_failures = []
        for label, name, _member_type, _start, _end, member in reversed(created):
            try:
                if not member.Delete():
                    cleanup_failures.append(f"{label} {name}: Delete() 返回 False")
            except Exception as cleanup_error:
                cleanup_failures.append(f"{label} {name}: {cleanup_error}")

        cleanup_commit_ok = bool(model.CommitChanges()) if created else True
        if cleanup_failures or not cleanup_commit_ok:
            raise RuntimeError(
                f"创建任务失败且清理不完整："
                f"delete_failures={cleanup_failures}, "
                f"commit_ok={cleanup_commit_ok}"
            ) from task_error
        raise
```

调用时传入前面通过 Catalog 查询得到的实际字符串：

```python
members = create_beam_column_and_brace(
    beam_profile=verified_beam_profile,
    column_profile=verified_column_profile,
    brace_profile=verified_brace_profile,
    material=verified_material,
)
```

这里的“斜杆”是结构语义，不是独立的 Open API 类型。若需要折线斜杆，应另外查询并使用 `PolyBeam`；截面朝向、偏心或旋转有要求时，还必须查询并设置 `Position`，提交后通过实体几何验证实际方向。

---

## 创建轮廓板（ContourPlate）与倒角

轮廓板用于节点连接板、加劲肋、基底承压板及预埋钢板。通过顺时针或逆时针闭合的点集定义多边形轮廓。

```python
from Tekla.Structures.Model import ContourPlate, ContourPoint, Chamfer
from Tekla.Structures.Geometry3d import Point


def create_contour_plate(name, profile_str, material_str, points, chamfer_radius=0.0):
    """
    创建轮廓板（例如节点板或加劲肋）。
    :param points: 顶点坐标列表 [(x1,y1,z1), (x2,y2,z2), ...]
    :param profile_str: 板厚截面（如 PL16, PL20）
    :param chamfer_radius: 倒角半径（默认 0，直角）
    """
    if len(points) < 3:
        raise ValueError("轮廓板至少需要 3 个顶点定义闭合区域")

    plate = ContourPlate()
    plate.Name = name
    plate.Profile.ProfileString = _validated_profile_string("板截面", profile_str)
    plate.Material.MaterialString = _required_catalog_value("材质", material_str)

    chamfer = Chamfer()
    if chamfer_radius > 0:
        chamfer.Type = Chamfer.ChamferTypeEnum.CHAMFER_ROUNDING
        chamfer.X = chamfer_radius

    for pt in points:
        cp = ContourPoint(Point(float(pt[0]), float(pt[1]), float(pt[2])), chamfer if chamfer_radius > 0 else None)
        plate.AddContourPoint(cp)

    if not plate.Insert():
        raise RuntimeError(f"轮廓板 {name!r} 创建失败：Insert() 返回 False")
    return plate
```

---

## 创建螺栓群（BoltArray）

螺栓群通过主构件（PartToBeBolted）、次构件（PartToBoltTo）以及基准参考点与间距数组定义。

```python
from Tekla.Structures.Model import BoltArray
from Tekla.Structures.Geometry3d import Point


def create_bolt_array(primary_part, secondary_part, ref_pt1, ref_pt2, bolt_size, bolt_standard, dx_list, dy_list):
    """
    在两个构件之间插入标准螺栓群。
    :param dx_list: X 向螺栓间距列表，如 [80.0, 80.0]
    :param dy_list: Y 向螺栓间距列表，如 [100.0]
    """
    bolt_array = BoltArray()
    bolt_array.PartToBeBoltedThrough = primary_part
    bolt_array.AddOtherPartner(secondary_part)

    bolt_array.FirstPosition = Point(float(ref_pt1[0]), float(ref_pt1[1]), float(ref_pt1[2]))
    bolt_array.SecondPosition = Point(float(ref_pt2[0]), float(ref_pt2[1]), float(ref_pt2[2]))

    bolt_array.BoltSize = float(bolt_size)
    bolt_array.BoltStandard = _required_catalog_value("螺栓标准", bolt_standard)
    bolt_array.CutLength = 100.0  # 穿透有效握裹厚度
    bolt_array.Tolerance = 2.0    # 螺栓孔径公差（如孔径 = 螺栓直径 + 2mm）

    for dx in dx_list:
        bolt_array.AddBoltDistX(float(dx))
    for dy in dy_list:
        bolt_array.AddBoltDistY(float(dy))

    if not bolt_array.Insert():
        raise RuntimeError(f"螺栓群创建失败：Insert() 返回 False")
    return bolt_array
```

---

## 创建焊缝（Weld）

焊缝将两个构件装配为单一装配体（Assembly）或现场拼接焊接。

```python
from Tekla.Structures.Model import Weld


def create_shop_weld(main_part, secondary_part, size_above=6.0, size_below=6.0, weld_type=Weld.WeldTypeEnum.WELD_TYPE_FILLET):
    """
    创建车间角焊缝，将次构件焊接到主构件。
    """
    weld = Weld()
    weld.MainObject = main_part
    weld.SecondaryObject = secondary_part
    weld.TypeAbove = weld_type
    weld.TypeBelow = weld_type
    weld.SizeAbove = float(size_above)
    weld.SizeBelow = float(size_below)
    weld.AroundWeld = False
    weld.ShopWeld = True  # True 为车间焊，False 为工地焊

    if not weld.Insert():
        raise RuntimeError("焊缝创建失败：Insert() 返回 False")
    return weld
```

---

## 构件贴合与切割（Fitting & CutPlane）

使用 `Fitting` 对梁端或柱端进行平齐斜切，使用 `CutPlane` 对构件多边形边界进行面切割。

```python
from Tekla.Structures.Model import Fitting, CutPlane, Plane
from Tekla.Structures.Geometry3d import Point, Vector


def fit_member_end(part, plane_origin, plane_normal):
    """
    沿指定平面斜切并贴合构件端部。
    """
    fitting = Fitting()
    fitting.Father = part
    cut_plane = Plane()
    cut_plane.Origin = Point(float(plane_origin[0]), float(plane_origin[1]), float(plane_origin[2]))
    cut_plane.AxisX = Vector(1000.0, 0.0, 0.0)
    cut_plane.AxisY = Vector(0.0, 1000.0, 0.0)
    fitting.Plane = cut_plane

    if not fitting.Insert():
        raise RuntimeError("构件端部贴合 (Fitting) 失败：Insert() 返回 False")
    return fitting
```

