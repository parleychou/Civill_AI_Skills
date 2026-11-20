# -*- coding: utf-8 -*-
"""Read-only probe of an open Tekla model.

With no arguments this prints the contract and exits 0. It does not start
Tekla and does not insert, modify, or delete objects. Pass --run only when
Tekla is already open with a model.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


READ_ONLY_SYMBOLS = (
    "ModelObjectSelector.GetAllObjects",
    "ModelObject.GetReportProperty",
    "ModelObject.GetUserProperty",
    "Part.Name",
)


def contract() -> dict[str, Any]:
    from find_install import SUPPORTED_YEARS

    return {
        "status": "ok",
        "self_check": True,
        "vendor_process_required": True,
        "supported_years": list(SUPPORTED_YEARS),
        "symbols_to_confirm": list(READ_ONLY_SYMBOLS),
        "empty_result_is_not_proof": True,
        "forbidden_in_this_script": ["Insert", "Modify", "Delete", "CommitChanges"],
    }


def _count_objects(model) -> int | None:
    selector = model.GetModelObjectSelector()
    enumerator = selector.GetAllObjects()
    count = 0
    mover = getattr(enumerator, "MoveNext", None)
    if not callable(mover):
        return None
    while mover():
        count += 1
    return count


def probe() -> dict[str, Any]:
    from session import connect_tekla

    session = connect_tekla()
    model = session.model
    connected = bool(model.GetConnectionStatus())
    report: dict[str, Any] = {
        "status": "connected" if connected else "not_connected",
        "program_version": session.program_version,
        "api_year": session.api_year,
        "read_only": True,
    }
    if not connected:
        report["object_count"] = None
        report["note"] = "GetConnectionStatus is false. An empty count would not describe the model."
        return report
    try:
        report["object_count"] = _count_objects(model)
    except Exception as exc:
        report["status"] = "unreadable"
        report["object_count"] = None
        report["error"] = str(exc)
        return report
    report["note"] = (
        "A zero or missing count is not proof the model is empty. "
        "Check the selector, filters, and whether the model has been committed."
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Attach to Tekla and count objects")
    args = parser.parse_args(argv)
    if not args.run:
        print(json.dumps(contract(), ensure_ascii=False))
        return 0
    try:
        report = probe()
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, default=str))
    if report["status"] != "connected":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
