---
name: sketchup
version: 1.0.2
display_name: SketchUp
display_name_en: SketchUp
description_zh: 通过 Python 桥接实时驱动 SketchUp 执行三维建筑方案推敲、体块推演、构件建模与效果出图。
description_en: Controls SketchUp in real time via Python bridge for 3D architectural massing, BIM geometry from drawings, element modeling, and viewport rendering.
license: Apache-2.0
---
# SketchUp Architectural 3D Modeling Guide (SketchUp Router)

Connect with Python, send SketchUp Ruby into the open model, then hand the model back. Order: connect, confirm the Ruby calls, run, check the numbers, deliver.

| When | Read |
|---|---|
| Grids, walls, openings, slabs, roofs, curtain walls, massing, towers, materials, scenes, sections, shadows, CAD import | `references/common_examples.md` |
| Furniture and interior models | `references/interior_layout.md` |
| Class, method, and argument shape | [https://ruby.sketchup.com/](https://ruby.sketchup.com/). On the connected model, list what this release actually exposes: `su.run("Sketchup::Camera.instance_methods(false).sort", operation=None)`. A method whose minimum release is newer than `print(su)` cannot be used. |

## 1. Connect

A model is a `.skp` file the user can find again.

```python
import os
from Agent.software_link_kit.sketchup import get_sketchup

su = get_sketchup(os.path.join(WORKSPACE_DIR, "office_massing.skp"))
print(su)  # <SketchUp 26.0.429 pid=... file=...>  26 means SketchUp 2026
```

| Request | Call | Result |
|---|---|---|
| A named `.skp` | `get_sketchup(path)` | Attach if that file is open; otherwise start SketchUp and open it |
| A new model | `get_sketchup(os.path.join(WORKSPACE_DIR, "name.skp"))` | Copy the default template and open it |
| "The current model", no file named | `get_sketchup()` | Attach when exactly one SketchUp is running. Several open: stop and ask. None open: create `sketchup_model.skp` in the workspace |

- Connect once. `su` stays available on later turns and reconnects if the bridge drops. If SketchUp itself was closed, connect again.
- Starting SketchUp can take from several seconds to a few minutes. Wait on `get_sketchup`. Do not start a second copy.
- A new file is a template copy and often contains a scale figure such as `Sree`. Unless the user wants it, erase geometry first, then purge definitions, then purge materials. A material cannot be purged while its component definition still exists: `model.entities.erase_entities(model.entities.to_a)`, then `model.definitions.purge_unused`, then `model.materials.purge_unused`.
- If `print(su)` says the model is unsaved, ask where to save it before delivery.
- The bridge plugin loads only when SketchUp starts. A SketchUp that was already open before the plugin was installed must be restarted by the user.
- On failure, report the exception text. Do not close or restart the user's SketchUp.

| Exception | Action |
|---|---|
| `SketchUpSelectionRequiredError` | More than one SketchUp is open. List the files from the exception and connect with `get_sketchup(path)`. If the wanted model was never saved, ask the user to save it first |
| `SketchUpUnavailableError` | SketchUp is open but not connected. Follow the reason in the exception. "Starting" means call `get_sketchup` again with the same arguments. "Plugin installed after launch", a welcome window, or a missing plugin means the user must finish that step |

`list_sketchup_instances()` lists running SketchUp processes. `su.status()` reports whether a job is running. `su.document` is the current title, path, dirty flag, and display units. `su.dialog_titles()` lists windows other than the main window.

## 2. `su.run`

`su.run` is one undo step. Do not call `start_operation`, `commit_operation`, or `abort_operation` inside the Ruby. Any error, including a syntax error or a timeout, rolls the whole step back, including definitions, materials, and tags created in that step.

```python
result = su.run("""
model = Sketchup.active_model
grid = model.entities.add_group
grid.name = "grid"
# build inside grid.entities
{ id: grid.persistent_id, count: grid.entities.length }
""", vars={"xs": [0, 8400, 16800], "ys": [0, 6600]}, operation="Create grid")
```

- The last Ruby expression is the Python return value. Hashes, arrays, numbers, and strings become Python objects. Other Ruby objects come back as their inspect string. `puts` and `warn` print directly. The full payload is `su.last_result`.
- Pass data with `vars`. Each key becomes a Ruby local, so the key must start with a lowercase letter or `_`. `P` and `CFG` are Ruby constants and are rejected. Numbers in `vars` have no unit; append `.mm` in Ruby. Do not interpolate values with an f-string. Ruby braces collide with f-strings, and paths break on quotes and backslashes.
- `operation` is the undo name. Pass `operation=None` for a read-only query or a display-only change.
- Each `run` starts clean. Locals and `def` methods from the previous call are gone. Ruby helpers that must be reused belong in a Python string prepended to each call. A `def` cannot see outer locals, including `vars`. Write helpers as lambdas: `box = ->(x, y) { ... }` and call `box.(x, y)`. `ORIGIN`, `X_AXIS`, `Y_AXIS`, `Z_AXIS`, and `IDENTITY` are top-level constants. Do not prefix them with `Geom::`.
- `SketchUpRubyError` includes the Ruby exception class, the line `(agent):N`, and whether the edit was rolled back. `NoMethodError` and `ArgumentError` mean the method, argument, or rendering key is wrong. Check https://ruby.sketchup.com/ before editing again.
- `timeout` defaults to 120 seconds. `SketchUpTimeoutError` means the geometry operation may still be running. Do not submit the same code again. Continue with `su.wait(job_id)`. If the exception names a dialog, tell the user which button to press. Do not click it with desktop automation.
- SketchUp does not respond while Ruby runs. Split a large model by element type or story, each call well under a minute. Do not use one `run` per element. Build a family of elements in one loop.

## 3. Rules that fail silently

### Units

1. Bare numbers are inches. `3000` is 3000 inches and does not raise. Write `3000.mm` or `3.m`. A coordinate is `[1000.mm, 0, 0]`. Zero may stay bare. Display units do not change this. Angles use `30.degrees`. For many points, define `pt = ->(x, y, z = 0) { Geom::Point3d.new(x.mm, y.mm, z.mm) }` and use only that.
2. Lengths read from the model are inches. Convert with `.to_mm` before returning them to Python. Do not call `.to_mm` on a millimetre value that came from `vars` or from your own arithmetic. `face.area` is square inches. Multiply by `0.0254 ** 2` for square metres.
3. `entity.bounds` is an axis-aligned box in world space. A rotated object measures larger than the part. The part's own size is `entity.definition.bounds`.

### Faces and materials

4. A face drawn on the z=0 plane has a downward normal regardless of vertex order. At other heights the normal follows vertex order. Before extruding, write `face.reverse! if face.normal.z < 0`, then `face.pushpull(h)`. On a vertical face, check `face.normal` points toward the extrusion.
5. `face.material` paints the front only. The back is `back_material`. A single surface such as glass or a roof panel should have its normal toward the outside. A material on a group or component fills unpainted faces, front and back. Paint a window frame or a balcony slab by putting it in its own group.
6. `material.alpha` from 0 to 1 is transparency. `rendering_options["ModelTransparency"]` is X-ray mode, not a material.

### Geometry

7. Draw new geometry in a new group: `group = model.entities.add_group`, then draw in `group.entities`. Loose geometry in `model.entities` sticks to and splits whatever is already there.
8. `pushpull`, `add_face`, `erase!`, and `intersect_with` can delete faces and edges you still hold. Using a deleted reference raises `reference to deleted DrawingElement`. After the operation, find the face again from `group.entities` by normal and area. One solid per group avoids most of this.
9. `subtract` and `union` return a new group and delete both inputs. Name, tag, attributes, and `persistent_id` are not kept. Rename and record the new id. Both inputs must be manifold (`manifold?`). Otherwise the call returns `nil` and does not raise. An opening is usually cheaper as a hole in the wall profile before `pushpull`.
10. Repeated parts are components: `model.definitions.add`, then `add_instance`. Editing `definition.entities` edits every instance. Call `instance.make_unique` before changing one instance.
11. Do not erase while iterating. Collect the entities, then `entities.erase_entities(list)`.

### Across calls

12. Return `entity.persistent_id` and later call `model.find_entity_by_persistent_id(id)`. A name or an attribute also works. `entityID` and locals from the previous `run` do not.
13. Mark a generated batch with `set_attribute("agent_model", "batch", "grid")`. Before rebuilding, erase groups with that mark and `model.definitions.remove(d)` for definitions with that mark. Removing a definition removes its instances. Otherwise a second run stacks a second copy, and an existing definition name keeps the old geometry.

### Sections, scenes, and display

14. An active section plane stays active and makes later images look like a broken model. Clear it with `entities.active_section_plane = nil` on the entities that own it, or delete it. Do not park an empty section plane far away. That inflates the model bounds. A section the user should keep belongs in a scene.
15. `page.update` stores the camera, style, shadows, tag visibility, and section at that moment. Set the camera with `su.capture` parameters or `PKPM::SU.set_camera`, then `page = pages[name] || pages.add(name)` and `page.update`. Do not call `pages.each(&:update)`. That writes the current camera into every scene. Hidden tags and an active section are stored too. Do not assign `pages.selected_page`. That plays a transition and breaks a camera or capture that runs during it. Switch immediately with `PKPM::SU.show_scene("name")`.
16. After scenes exist, display changes must be stored or the next scene switch drops them. `rendering_options` changes need `model.styles.update_selected_style`. Shadow flags are per scene: `page.shadow_info["DisplayShadows"] = true`. Tag visibility needs `page.update(PAGE_USE_LAYER_VISIBILITY)`. Without that flag, `update` also replaces the camera.

### No UI

17. Do not call `UI.messagebox`, `UI.inputbox`, `UI.openpanel`, `select_tool`, `Sketchup.open_file`, or `Sketchup.file_new`. Those dialogs stall the bridge. Open or create files with `get_sketchup(path)`. Import and export with `show_summary: false`.
18. Read a selection the user already made from `model.selection`. If it is empty, stop and ask the user to select. Do not wait.

## 4. How to build

1. Name the source of every size: the user, a drawing, or a stated default such as storey height, wall thickness, or sill height. Ask when a required size is missing. List every default you used.
2. A CAD or plan drawing is the authority. Inventory every layer that has content before modeling. Build each layer or say why it is skipped. Do not add objects the drawing does not have, skip a block because it is unfamiliar, move furniture for a nicer path, or replace distinct blocks with one generic component. Keep existing walls and new walls in separate groups. Block in the drawing positions first and check the returned coordinates, then add detail inside that outline.
3. One `run` per batch, in this order: grid, walls and openings, slabs and stairs, roof, facade, materials and tags. Check the returned counts and elevations before the next batch. A tower is batched by storey ranges.
4. One group or component per element, with a usable name. Tags follow discipline and category.
5. A whole building belongs in one workspace script, parameters at the top, one batch per section. Derived sizes are computed once. Stair height is riser count times riser height, not a second typed number.

## 5. Deliver

Check numbers in the modeling code. Do not hunt for errors by taking many screenshots.

1. The last expression of each batch returns counts, bounds, and top elevation. Compare them with the request. A correct group count can still place a storey below grade. Read back any rendering key you changed.
2. Do not add scenes, renderings, shadows, colors, or small details the user did not ask for. Offer them as a next step.
3. One overall image is enough to see a missing part, a shift, or an active section. Add a top view when the model follows a drawing. Produce only the images the user asked for.
4. Save. A new unsaved model has an empty `model.path`, so `model.save` needs a path. `kept = su.keep_captures([paths to keep])` moves those images into the workspace and deletes the rest. Show `kept` in the reply and list the numbers that do not match the request.

`info = su.summary()` returns millimetres: `bounds_mm` (bounds without section planes, construction lines, text, or dimensions), `top_level_counts`, `containers` (name, tag, face count, manifold, bounds, `persistent_id`), `definitions`, `section_planes`, `scenes`, `tags`, `materials`, and `selection`. `su.summary(depth=2)` adds `children` with world bounds. A wildly large size usually means a missing `.mm`.

## 6. Images and display

`path = su.capture(view="iso")`. Images land in a captures folder under the workspace until `keep_captures` keeps the ones for the user.

| Argument | Meaning |
|---|---|
| `view` | `iso` (default, perspective), `top`, `bottom`, `front`, `back`, `left`, `right` (parallel), a direction `[x, y, z]` from the model toward the camera, or `current` for the view as it is |
| `focus`, `isolate` | `focus` is persistent ids or top-level names. The camera frames them. `isolate=True` hides everything else for that image |
| `eye`, `target`, `fov` | Eye and target are `[x, y, z]` in millimetres. `fov` is degrees, default 30, 50–60 indoors. `eye` replaces `view` and does not auto-zoom |
| `section_z` | Horizontal cut at this elevation in millimetres, keeping what is below. Use with `view="top"` |
| `sections=False` | Ignore an active section plane for this image |
| `scene` | Use that scene's camera, style, shadows, and section. Cannot be combined with `view`, `eye`, `fov`, `focus`, or `section_z`. The model stays on that scene |
| `edges=False` | This image draws no edges. To turn edges off in the model, change rendering options |
| `width`, `height` | Pixels. Default 1280 by 800 |
| `path` | File name inside the captures folder. The same name overwrites |

Camera, `edges`, `sections`, `section_z`, and `isolate` are restored after the image. `scene` is not. Several captures can run in one call. Do not `sleep` between them.

| Effect | Call |
|---|---|
| No edges at all | `rendering_options["EdgeDisplayMode"] = 0` and `rendering_options["DrawSilhouettes"] = false` |
| Shadows | `shadow_info["DisplayShadows"] = true`, and set `Latitude`, `Longitude`, and `TZOffset` together |
| Sun time | `shadow_info["ShadowTime"] = Time.utc(year, month, day, hour)` using the local clock hour. Do not use `Time.local` |

Edge and background keys are `rendering_options`. Sun keys are `shadow_info`. Confirm unfamiliar keys on https://ruby.sketchup.com/ under `RenderingOptions` and `ShadowInfo`. If scenes exist, store the change as in rule 16. Inside Ruby, `PKPM::SU.summary`, `PKPM::SU.capture`, `PKPM::SU.set_camera`, and `PKPM::SU.show_scene` are the same helpers.

---

## 7. Checklist script

[scripts/session_checklist.py](scripts/session_checklist.py) prints rules 1–18 and the `su.run` contract as JSON. Running it does not start SketchUp. Use it before the first modeling `su.run` when a step might skip units, groups, persistent ids, scenes, or UI calls.

## Official documentation

- SketchUp Ruby API: https://ruby.sketchup.com/
- Sketchup module: https://ruby.sketchup.com/Sketchup.html
- Geom: https://ruby.sketchup.com/Geom.html
- Developer portal: https://developer.sketchup.com/
- The Ruby Console in SketchUp (`Window -> Ruby Console`) shows what the installed release accepts.

## Intellectual property

Product names and the SketchUp Ruby API are their owners' property. This skill names them so an agent can drive an installed SketchUp. It does not include the Ruby API manual.
