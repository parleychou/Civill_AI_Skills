"""一次完成 Abaqus ``analysis_spec`` 的结构规范化和工程语义校验。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from preflight_analysis_spec import semantic_preflight


def _invalid_json_report(error: Exception) -> dict[str, Any]:
    """构造分析规格文件无法读取或解析时的统一失败报告。"""
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
    """读取一个分析规格 JSON 文件并返回完整校验报告。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return _invalid_json_report(error)
    return semantic_preflight(raw)


def main() -> None:
    """执行一次完整校验，输出 JSON，并对失败或不支持状态返回非零退出码。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to an analysis_spec JSON file")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    args = parser.parse_args()

    report = validate_file(args.spec)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2))
    if report["status"] in {"FAIL", "UNSUPPORTED"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
