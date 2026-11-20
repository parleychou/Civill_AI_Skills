# -*- coding: utf-8 -*-
"""Build one concrete portal frame in an ETABS session.

No arguments runs a local self-check and does not start ETABS. --run attaches
to a process that is already open. --launch is the only flag that may start
a new ETABS process.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from unit_table import NEW_MODEL_UNIT


COLUMN_SECTION = "ColumConc"
BEAM_SECTION = "BeamConc"
BAY_MM = 6000.0
HEIGHT_MM = 3000.0
COLUMN_SIZE_MM = (500.0, 500.0)
BEAM_SIZE_MM = (500.0, 300.0)
DEAD_PATTERN = "DEAD_LOAD"
LIVE_PATTERN = "LIVE_LOAD"
DISTRIBUTED_LOAD = 10.0  # N/mm, which is 10 kN/m in N_mm_C


def self_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "self_check": True,
        "vendor_process_required": True,
        "units": {"code": NEW_MODEL_UNIT, "name": "N_mm_C"},
        "calls": [
            "ETABSv1.Helper.GetObject",
            "SapModel.InitializeNewModel",
            "PropFrame.SetRectangle",
            "FrameObj.AddByCoord",
            "PointObj.SetRestraint",
            "LoadPatterns.Add",
            "FrameObj.SetLoadDistributed",
            "File.Save",
            "Analyze.RunAnalysis",
        ],
    }


def _attach(helper, launch_if_missing: bool):
    etabs = None
    try:
        etabs = helper.GetObject("CSI.ETABS.API.ETABSObject")
    except Exception:
        etabs = None
    if etabs is None and not launch_if_missing:
        raise RuntimeError("No running ETABS instance. Open ETABS, or pass --launch to start one.")
    if etabs is None:
        etabs = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
        etabs.ApplicationStart()
    return etabs


def _add_frame(sap_model, start, end, section, label):
    name, _ret = sap_model.FrameObj.AddByCoord(
        start[0], start[1], start[2], end[0], end[1], end[2], " ", section, label, "Global"
    )
    return name


def run_etabs_portal_frame(
    attach_to_instance: bool = True,
    model_path: str | None = None,
    run_analysis: bool = True,
    launch_if_missing: bool = False,
) -> dict[str, Any]:
    """Model a 6000 mm bay, 3000 mm tall, with fixed bases and a dead-load beam."""
    try:
        import comtypes.client
        import comtypes.gen
    except ImportError as exc:
        raise RuntimeError(
            "comtypes package is required for ETABS COM automation: pip install comtypes"
        ) from exc

    comtypes.CoInitialize()
    helper = comtypes.client.CreateObject("ETABSv1.Helper")
    helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
    if not attach_to_instance and not launch_if_missing:
        raise RuntimeError("No running ETABS instance. Open ETABS, or pass --launch to start one.")
    etabs = _attach(helper, launch_if_missing) if attach_to_instance or launch_if_missing else None
    sap_model = etabs.SapModel
    sap_model.InitializeNewModel(NEW_MODEL_UNIT)
    sap_model.File.NewBlank()

    sap_model.PropFrame.SetRectangle(COLUMN_SECTION, "C30", COLUMN_SIZE_MM[0], COLUMN_SIZE_MM[1])
    sap_model.PropFrame.SetRectangle(BEAM_SECTION, "C30", BEAM_SIZE_MM[0], BEAM_SIZE_MM[1])
    modifiers = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    sap_model.PropFrame.SetModifiers(COLUMN_SECTION, modifiers)
    sap_model.PropFrame.SetModifiers(BEAM_SECTION, modifiers)

    corners = ((0.0, 0.0), (BAY_MM, 0.0), (0.0, BAY_MM), (BAY_MM, BAY_MM))
    column_names = [
        _add_frame(sap_model, (x, y, 0.0), (x, y, HEIGHT_MM), COLUMN_SECTION, str(index))
        for index, (x, y) in enumerate(corners, start=1)
    ]
    fixed = [True, True, True, True, True, True]
    for column in column_names:
        point_i, _point_j, _ret = sap_model.FrameObj.GetPoints(column, " ", " ")
        sap_model.PointObj.SetRestraint(point_i, fixed)

    beam_plan = (
        ((0.0, 0.0), (BAY_MM, 0.0), "B1"),
        ((BAY_MM, 0.0), (BAY_MM, BAY_MM), "B2"),
        ((BAY_MM, BAY_MM), (0.0, BAY_MM), "B3"),
        ((0.0, BAY_MM), (0.0, 0.0), "B4"),
    )
    beam_names = [
        _add_frame(
            sap_model,
            (start[0], start[1], HEIGHT_MM),
            (end[0], end[1], HEIGHT_MM),
            BEAM_SECTION,
            label,
        )
        for start, end, label in beam_plan
    ]
    sap_model.View.RefreshView(0, False)
    sap_model.LoadPatterns.Add(DEAD_PATTERN, 1, 1.0, True)
    sap_model.LoadPatterns.Add(LIVE_PATTERN, 2, 0.0, True)
    if beam_names:
        sap_model.FrameObj.SetLoadDistributed(
            beam_names[0], DEAD_PATTERN, 1, 10, 0.0, 1.0, DISTRIBUTED_LOAD, DISTRIBUTED_LOAD
        )

    save_path = model_path or os.path.abspath(os.path.join(os.getcwd(), "etabs_portal_frame.edb"))
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    sap_model.File.Save(save_path)
    results: dict[str, Any] = {
        "status": "created",
        "model_path": save_path,
        "columns": column_names,
        "beams": beam_names,
    }
    if not run_analysis:
        return results

    sap_model.Analyze.RunAnalysis()
    sap_model.Results.Setup.DeselectAllCasesAndCombosForOutput()
    sap_model.Results.Setup.SetCaseSelectedForOutput(DEAD_PATTERN)
    if beam_names:
        _point_i, point_j, _ret = sap_model.FrameObj.GetPoints(beam_names[0], " ", " ")
        number_results = 0
        u1, u2, u3, r1, r2, r3 = [], [], [], [], [], []
        displacement = sap_model.Results.JointDispl(
            point_j, 0, number_results, [], [], [], [], [], u1, u2, u3, r1, r2, r3
        )
        results["displacements"] = {
            "joint": point_j,
            "u1": list(displacement[8]),
            "u2": list(displacement[9]),
            "u3": list(displacement[10]),
        }
        results["status"] = "analyzed"
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Attach to ETABS and build the sample frame")
    parser.add_argument("--launch", action="store_true", help="With --run, start ETABS when none is running")
    parser.add_argument("--model", help="Path for the saved .edb file")
    parser.add_argument("--no-analyze", action="store_true", help="With --run, stop before the solver")
    args = parser.parse_args(argv)
    if not args.run:
        print(json.dumps(self_check(), ensure_ascii=False))
        return 0
    try:
        result = run_etabs_portal_frame(
            attach_to_instance=True,
            model_path=args.model,
            run_analysis=not args.no_analyze,
            launch_if_missing=args.launch,
        )
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
