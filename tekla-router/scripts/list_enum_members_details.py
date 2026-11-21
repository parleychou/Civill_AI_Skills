# -*- coding: utf-8 -*-
"""List enum member names together with their values for one Tekla version."""

import argparse
import re

from _tekla_db import (
    add_directory_arguments,
    add_version_argument,
    connect_db,
    detail_text,
    directory_window,
    find_type,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


ENUM_VALUE_PATTERN = re.compile(r"\s*Value:\s*([^\r\n]+)\s*\Z")


def enum_value(symbol_key: str, detail_blob: bytes) -> str:
    """Extract the documented enum value from one revision detail body."""
    body = detail_text(detail_blob)
    match = ENUM_VALUE_PATTERN.fullmatch(body)
    if match is None:
        raise ValueError(f"{symbol_key} 的枚举成员详情中缺少可解析的 Value")
    return match.group(1).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("enum", help="Full enumeration type name or exact T: key")
    add_version_argument(parser)
    add_directory_arguments(parser)
    parser.set_defaults(limit=100)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    contains = (args.contains or "").strip()

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        enum_type = find_type(conn, bit, args.enum)
        if int(enum_type["kind"]) != 5:
            raise ValueError(f"{enum_type['symbol_key']} 不是 enumeration 类型")
        parameters: tuple[object, ...] = (
            int(enum_type["id"]),
            bit,
            contains,
            contains,
        )
        where = """
            s.parent_id = ?
            AND s.kind = 10
            AND (r.version_mask & ?) != 0
            AND (? = '' OR instr(lower(s.name), lower(?)) > 0)
        """
        total = int(
            conn.execute(
                f"""
                SELECT count(*)
                FROM symbols s
                JOIN revisions r ON r.symbol_id = s.id
                WHERE {where}
                """,
                parameters,
            ).fetchone()[0]
        )
        rows = conn.execute(
            f"""
            SELECT s.name, s.symbol_key, r.detail_blob
            FROM symbols s
            JOIN revisions r ON r.symbol_id = s.id
            WHERE {where}
            ORDER BY s.name COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        ).fetchall()
        members = [
            (row["name"], enum_value(row["symbol_key"], row["detail_blob"]))
            for row in rows
        ]
    finally:
        conn.close()

    print("Enumeration member details")
    print_directory_meta(
        year=year,
        parent_key=enum_type["symbol_key"],
        total=total,
        offset=offset,
        count=len(members),
    )
    for name, value in members:
        print(f"- {name} = {value}")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
