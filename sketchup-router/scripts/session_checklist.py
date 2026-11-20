# -*- coding: utf-8 -*-
"""Silent-failure checklist for a SketchUp su.run session.

Printing this file does not start SketchUp and does not send Ruby. Run it
before the first modeling call and treat any skipped rule as an open defect.
"""

from __future__ import annotations

import json


RULES = (
    {"id": 1, "topic": "units", "check": "Bare numbers are inches. Write 3000.mm or 3.m. Zero may stay bare."},
    {"id": 2, "topic": "units", "check": "Lengths read from the model are inches. Convert with .to_mm. face.area is square inches."},
    {"id": 3, "topic": "units", "check": "entity.bounds is a world axis-aligned box. Part size is entity.definition.bounds."},
    {"id": 4, "topic": "faces", "check": "A z=0 face has a downward normal. reverse! when normal.z < 0 before pushpull."},
    {"id": 5, "topic": "faces", "check": "face.material paints the front. The back is back_material."},
    {"id": 6, "topic": "faces", "check": "material.alpha is transparency. ModelTransparency is X-ray mode."},
    {"id": 7, "topic": "geometry", "check": "Draw new geometry in a new group. Loose entities stick to existing geometry."},
    {"id": 8, "topic": "geometry", "check": "pushpull, add_face, erase!, and intersect_with can delete faces you still hold."},
    {"id": 9, "topic": "geometry", "check": "subtract and union return a new group and drop persistent_id. Both inputs must be manifold."},
    {"id": 10, "topic": "geometry", "check": "Repeated parts are components. make_unique before editing one instance."},
    {"id": 11, "topic": "geometry", "check": "Do not erase while iterating. Collect the list, then erase_entities."},
    {"id": 12, "topic": "identity", "check": "Return persistent_id. entityID and locals from the previous run do not survive."},
    {"id": 13, "topic": "identity", "check": "Mark a batch with set_attribute('agent_model', 'batch', name) and erase that mark before rebuilding."},
    {"id": 14, "topic": "display", "check": "Clear an active section plane. Do not park an empty plane far away."},
    {"id": 15, "topic": "display", "check": "page.update stores the current camera. Do not call pages.each(&:update) or assign selected_page."},
    {"id": 16, "topic": "display", "check": "After scenes exist, store rendering, shadow, and tag changes or the next scene switch drops them."},
    {"id": 17, "topic": "ui", "check": "Do not call UI.messagebox, UI.inputbox, UI.openpanel, select_tool, Sketchup.open_file, or Sketchup.file_new."},
    {"id": 18, "topic": "ui", "check": "Read model.selection. If it is empty, stop and ask. Do not wait."},
)

RUN_CONTRACT = {
    "one_undo_step": True,
    "start_operation_inside_run": False,
    "operation_none_for_reads": True,
    "vars_keys": "lowercase or leading underscore",
    "no_fstring_interpolation": True,
}


def self_check() -> dict:
    ids = [rule["id"] for rule in RULES]
    if ids != list(range(1, 19)):
        raise RuntimeError("checklist must contain rules 1 through 18")
    if any(not rule["check"].strip() for rule in RULES):
        raise RuntimeError("checklist rule text is empty")
    if RUN_CONTRACT["start_operation_inside_run"]:
        raise RuntimeError("su.run already owns the undo step")
    return {
        "status": "ok",
        "self_check": True,
        "vendor_process_required": False,
        "rule_count": len(RULES),
        "rules": [dict(rule) for rule in RULES],
        "run_contract": dict(RUN_CONTRACT),
    }


if __name__ == "__main__":
    print(json.dumps(self_check(), ensure_ascii=False))
