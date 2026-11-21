# -*- coding: utf-8 -*-
"""List exact signatures for one member-name group without loading API details."""

import argparse

from _tekla_db import (
    KIND_LABELS,
    add_directory_arguments,
    add_version_argument,
    compact_member_signature,
    connect_db,
    directory_window,
    find_type,
    kind_from_name,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


OVERLOADABLE_KINDS = {7, 8, 9, 12}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="Full declaring type name or exact T: key")
    parser.add_argument("member", help="Exact member name returned by list_type_members.py")
    parser.add_argument(
        "--kind",
        default="method",
        help="method/property/constructor/operator (default: method)",
    )
    add_version_argument(parser)
    add_directory_arguments(parser, include_contains=False)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    member_kind = kind_from_name(args.kind)
    if member_kind not in OVERLOADABLE_KINDS:
        raise ValueError("--kind 只允许 method/property/constructor/operator")

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        type_row = find_type(conn, bit, args.type)
        parameters: tuple[object, ...] = (
            int(type_row["id"]),
            member_kind,
            args.member,
            bit,
        )
        where = """
            s.parent_id = ?
            AND s.kind = ?
            AND s.name = ? COLLATE NOCASE
            AND EXISTS (
                SELECT 1 FROM revisions r
                WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
            )
        """
        total = int(
            conn.execute(f"SELECT count(*) FROM symbols s WHERE {where}", parameters).fetchone()[0]
        )
        if total == 0:
            raise LookupError(
                f"{type_row['symbol_key']} 在 Tekla {year} 中没有"
                f" {KIND_LABELS[member_kind]} {args.member}"
            )
        rows = conn.execute(
            f"""
            SELECT s.name, s.symbol_key
            FROM symbols s
            WHERE {where}
            ORDER BY s.symbol_key
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        ).fetchall()
    finally:
        conn.close()

    print(f"{KIND_LABELS[member_kind].title()} overload directory")
    print_directory_meta(
        year=year,
        parent_key=type_row["symbol_key"],
        total=total,
        offset=offset,
        count=len(rows),
    )
    for row in rows:
        signature = compact_member_signature(type_row["symbol_key"], row["symbol_key"])
        print(f"- {signature} [{row['symbol_key']}]")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
