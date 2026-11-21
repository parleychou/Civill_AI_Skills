"""Run one read-only Abaqus model, Job, and ODB inspection call."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

KERNEL_PATH = Path(__file__).with_name("_abaqus_inspector_kernel.py")
_SAFE_JOB_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def build_kernel_code(request: dict[str, Any]) -> str:
    """把检查请求注入 Abaqus 端内核脚本，生成一次可执行代码。"""
    kernel = KERNEL_PATH.read_text(encoding="utf-8")
    return f"inspection_request = {request!r}\n{kernel}"


def build_request(args: argparse.Namespace) -> dict[str, Any]:
    """校验命令行参数，并构造传给 Abaqus 内核的只读检查请求。"""
    workspace = args.workspace_dir.resolve()
    if args.job and not _SAFE_JOB_NAME.fullmatch(args.job):
        raise ValueError("job name may contain only letters, digits, dot, underscore, and hyphen")
    odb_path = None
    if args.odb:
        odb_path = args.odb if args.odb.is_absolute() else workspace / args.odb
        odb_path = str(odb_path.resolve())
    return {
        "model": args.model,
        "job": args.job,
        "odb_path": odb_path,
        "workspace_dir": str(workspace),
        "max_items": args.max_items,
        "max_log_lines": args.max_log_lines,
    }


def main() -> None:
    """执行模型、Job 或 ODB 的一次只读检查并输出 JSON 结果。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Model name to inspect; omitted lists model names")
    parser.add_argument("--job", help="Job name to inspect; omitted lists job names")
    parser.add_argument(
        "--odb", type=Path, help="Completed ODB path, absolute or relative to workspace"
    )
    parser.add_argument("--workspace-dir", type=Path, default=Path.cwd())
    parser.add_argument("--max-items", type=int, default=200)
    parser.add_argument("--max-log-lines", type=int, default=40)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    try:
        request = build_request(args)
    except ValueError as error:
        parser.error(str(error))

    try:
        import abaqus
        response = abaqus.execute(
            code=build_kernel_code(request),
            timeout=args.timeout,
            workspace_dir=request["workspace_dir"],
        )
    except Exception as e:
        response = {"ok": False, "error": f"Abaqus not connected: {e}", "request": request},
        timeout=args.timeout,
        workspace_dir=request["workspace_dir"],
    )
    print(json.dumps(response, ensure_ascii=False, default=str, indent=2))
    if not response.get("ok"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
