"""命令行校验YJK数据库。"""

import argparse
import json
from pathlib import Path

from yjk_db import YJKDatabase


def main():
    parser = argparse.ArgumentParser(description="Validate a YJK database against a reference database.")
    parser.add_argument("--reference", required=True, help="Reference .db/.ydb path")
    parser.add_argument("--target", required=True, help="Target .db/.ydb path")
    parser.add_argument("--strict-minimum", action="store_true", help="Validate against the strict minimum profile of the reference database")
    args = parser.parse_args()

    reference_path = Path(args.reference)
    target_path = Path(args.target)

    reference_db = YJKDatabase(str(reference_path))
    try:
        if args.strict_minimum:
            report = reference_db.validate_strict_minimum_model(str(target_path))
        else:
            report = reference_db.validate_target_database(str(target_path))
    finally:
        reference_db.close()

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
