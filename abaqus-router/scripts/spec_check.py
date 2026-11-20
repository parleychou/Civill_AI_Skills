"""Validate one analysis_spec JSON file and print a JSON report.

No arguments prints a self-check and exits 0. A missing or invalid file, or a
report whose status is FAIL or UNSUPPORTED, exits 2. PASS and WARN exit 0.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from spec_rules import review_spec


def unreadable_report(error: Exception) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "profiles": [],
        "summary": {"PASS": 0, "WARN": 0, "FAIL": 1, "UNSUPPORTED": 0},
        "checks": [
            {
                "id": "contract.json",
                "status": "FAIL",
                "message": "analysis_spec is not readable JSON",
                "evidence": [str(error)],
            }
        ],
        "analysis_spec": None,
    }


def validate_file(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return unreadable_report(error)
    return review_spec(raw)


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "self_check": True,
                    "usage": "spec_check.py SPEC.json",
                }
            )
        )
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to an analysis_spec JSON file")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    args = parser.parse_args(argv)
    report = validate_file(args.spec)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2))
    if report["status"] in {"FAIL", "UNSUPPORTED"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
