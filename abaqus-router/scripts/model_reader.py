"""Send one read-only model, job, or ODB inspection into the Abaqus kernel.

No arguments prints a self-check and does not attach to Abaqus. With arguments,
the host interpreter must already provide ``Agent.abaqus``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

KERNEL_PATH = Path(__file__).with_name("model_reader_kernel.py")
_SAFE_JOB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def kernel_source(request: dict[str, Any]) -> str:
    kernel = KERNEL_PATH.read_text(encoding="utf-8")
    return "inspection_request = {0!r}\n{1}".format(request, kernel)


def request_from_args(args: argparse.Namespace) -> dict[str, Any]:
    workspace = args.workspace_dir.resolve()
    if args.job and not _SAFE_JOB_NAME.fullmatch(args.job):
        raise ValueError("job name may contain only letters, digits, dot, underscore, and hyphen")
    odb_path = None
    if args.odb:
        candidate = args.odb if args.odb.is_absolute() else workspace / args.odb
        odb_path = str(candidate.resolve())
    return {
        "model": args.model,
        "job": args.job,
        "odb_path": odb_path,
        "workspace_dir": str(workspace),
        "max_items": args.max_items,
        "max_log_lines": args.max_log_lines,
    }


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "self_check": True,
                    "kernel_present": KERNEL_PATH.is_file(),
                    "read_only": True,
                }
            )
        )
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Model name to inspect; omitted lists model names")
    parser.add_argument("--job", help="Job name to inspect; omitted lists job names")
    parser.add_argument("--odb", type=Path, help="Completed ODB path, absolute or relative to workspace")
    parser.add_argument("--workspace-dir", type=Path, default=Path.cwd())
    parser.add_argument("--max-items", type=int, default=200)
    parser.add_argument("--max-log-lines", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    try:
        request = request_from_args(args)
    except ValueError as error:
        parser.error(str(error))
    try:
        from Agent import abaqus
    except ImportError as error:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": "Agent.abaqus is not available in this interpreter: {0}".format(error),
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(2) from error
    response = abaqus.execute(
        code=kernel_source(request),
        timeout=args.timeout,
        workspace_dir=request["workspace_dir"],
    )
    print(json.dumps(response, ensure_ascii=False, default=str, indent=2))
    if not response.get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
