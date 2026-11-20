# -*- coding: utf-8 -*-
"""STAAD.Pro OpenSTAAD portal-frame workflow.

No arguments performs a local self-check and does not attach to STAAD.Pro.
Pass --run only when STAAD.Pro is already open with a model.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from code_tables import FORCE_DIRECTIONS, FORCE_KN, LENGTH_METER, LOAD_TYPES


def workflow_calls() -> list[str]:
    """Call order used by the live workflow."""
    return [
        "os_analytical.connect",
        "SetInputUnits(4, 5)",
        "Geometry.AddNode",
        "Geometry.AddBeam",
        "Support.CreateSupportFixed",
        "Support.AssignSupportToNode",
        "Load.CreateNewPrimaryLoadEx2",
        "Load.SetLoadActive",
        "Load.AddMemberUniformForce",
        "Command.PerformAnalysis(0)",
        "SaveModel(True)",
        "AnalyzeEx(1, 0, 1)",
    ]


def self_check() -> dict[str, Any]:
    calls = workflow_calls()
    required = {
        "Support.CreateSupportFixed",
        "Support.AssignSupportToNode",
        "Command.PerformAnalysis(0)",
        "AnalyzeEx(1, 0, 1)",
    }
    missing = sorted(required.difference(calls))
    if missing:
        raise RuntimeError("workflow contract is incomplete: " + ", ".join(missing))
    if (LENGTH_METER, FORCE_KN) != (4, 5):
        raise RuntimeError("input units must be metre and kilonewton")
    if LOAD_TYPES[0] != "Dead" or FORCE_DIRECTIONS[2] != "local Y":
        raise RuntimeError("dead load must use type 0 and local Y")
    return {
        "status": "ok",
        "self_check": True,
        "vendor_process_required": True,
        "units": {"length_code": LENGTH_METER, "length": "Meter", "force_code": FORCE_KN, "force": "kN"},
        "calls": calls,
    }


def _connect(model_path: str | None):
    try:
        from openstaadpy import os_analytical
    except ImportError as exc:
        raise RuntimeError(
            "openstaadpy is required to attach to STAAD.Pro. Install it in the interpreter that can see the OpenSTAAD type library."
        ) from exc
    try:
        if model_path:
            return os_analytical.connect(model_path)
        return os_analytical.connect()
    except Exception as exc:
        raise RuntimeError(
            "STAAD.Pro is not attached. Open the target model in STAAD.Pro, then retry with --run."
        ) from exc


def _build_geometry(session) -> dict[str, Any]:
    n1 = session.Geometry.AddNode(0.0, 0.0, 0.0)
    n2 = session.Geometry.AddNode(6.0, 0.0, 0.0)
    n3 = session.Geometry.AddNode(0.0, 3.5, 0.0)
    n4 = session.Geometry.AddNode(6.0, 3.5, 0.0)
    return {
        "nodes": [n1, n2, n3, n4],
        "columns": [session.Geometry.AddBeam(n1, n3), session.Geometry.AddBeam(n2, n4)],
        "beam": session.Geometry.AddBeam(n3, n4),
        "bases": [n1, n2],
    }


def _assign_fixed_bases(session, node_ids) -> int:
    fixed_id = session.Support.CreateSupportFixed()
    session.Support.AssignSupportToNode(node_ids, fixed_id)
    return fixed_id


def _assign_dead_load(session, beam_id) -> int:
    case_id = session.Load.CreateNewPrimaryLoadEx2("DEAD", 0, 1)
    if not case_id:
        raise RuntimeError("CreateNewPrimaryLoadEx2 returned 0")
    session.Load.SetLoadActive(case_id)
    session.Load.AddMemberUniformForce([beam_id], 2, -1.0, 0.0, 0.0, 0.0)
    return case_id


def run_staad_frame_automation(
    model_path: str | None = None,
    length_unit: int = LENGTH_METER,
    force_unit: int = FORCE_KN,
    run_analysis: bool = False,
) -> dict[str, Any]:
    """Build a 6 m by 3.5 m portal frame on the already-open STAAD.Pro model.

    CreateSupportFixed takes no node argument. AssignSupportToNode applies the
    returned specification. PerformAnalysis writes the command before AnalyzeEx.
    """
    session = _connect(model_path)
    session.SetInputUnits(length_unit, force_unit)
    session.SaveModel(True)
    geometry = _build_geometry(session)
    fixed_id = _assign_fixed_bases(session, geometry["bases"])
    case_id = _assign_dead_load(session, geometry["beam"])
    session.SaveModel(True)
    results: dict[str, Any] = {
        "status": "modeled",
        "staad_file": session.GetSTAADFile(),
        "version": session.GetApplicationVersion(),
        "nodes": geometry["nodes"],
        "columns": geometry["columns"],
        "beams": [geometry["beam"]],
        "support_id": fixed_id,
        "load_case": case_id,
    }
    if run_analysis:
        session.Command.PerformAnalysis(0)
        session.SaveModel(True)
        results["analysis_status"] = session.AnalyzeEx(1, 0, 1)
        results["status"] = "analyzed"
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Attach to an already-open STAAD.Pro model")
    parser.add_argument("--model", help="Path of an .std file that is already open in STAAD.Pro")
    parser.add_argument("--analyze", action="store_true", help="With --run, write PERFORM ANALYSIS and solve")
    args = parser.parse_args(argv)
    if not args.run:
        print(json.dumps(self_check(), ensure_ascii=False))
        return 0
    try:
        result = run_staad_frame_automation(model_path=args.model, run_analysis=args.analyze)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
