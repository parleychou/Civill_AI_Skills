# -*- coding: utf-8 -*-
"""List compact member-name groups declared directly by one API type."""

import argparse

from _tekla_db import (
    KIND_LABELS,
    add_directory_arguments,
    add_version_argument,
    connect_db,
    directory_window,
    find_type,
    kind_from_name,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="Full type name or an unambiguous short type name")
    add_version_argument(parser)
    parser.add_argument(
        "--kind",
        required=True,
        help="method/property/field/event/constructor/operator",
    )
    add_directory_arguments(parser)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    contains = (args.contains or "").strip()
    member_kind = kind_from_name(args.kind)

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        type_row = find_type(conn, bit, args.type)
        if int(type_row["kind"]) == 5:
            raise ValueError("enumeration 类型请使用 list_enum_members_details.py")
        where = """
            s.parent_id = ?
            AND s.kind = ?
            AND EXISTS (
                SELECT 1 FROM revisions r
                WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
            )
            AND (? = '' OR instr(lower(s.name), lower(?)) > 0)
        """
        parameters: tuple[object, ...] = (
            int(type_row["id"]),
            member_kind,
            bit,
            contains,
            contains,
        )
        grouped = f"""
            SELECT s.kind, s.name, count(*) AS candidate_count,
                   CASE WHEN count(*) = 1 THEN min(s.symbol_key) END AS symbol_key
            FROM symbols s
            WHERE {where}
            GROUP BY s.kind, s.name COLLATE NOCASE
        """
        total = int(
            conn.execute(f"SELECT count(*) FROM ({grouped})", parameters).fetchone()[0]
        )
        rows = conn.execute(
            f"""
            {grouped}
            ORDER BY name COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        ).fetchall()
    finally:
        conn.close()

    label = KIND_LABELS[member_kind]
    print(f"{label.title()} name directory")
    print_directory_meta(
        year=year,
        parent_key=type_row["symbol_key"],
        total=total,
        offset=offset,
        count=len(rows),
    )
    for row in rows:
        count = int(row["candidate_count"])
        if count == 1:
            print(f"- {row['name']} ({label}) [{row['symbol_key']}]")
        else:
            print(f"- {row['name']} ({label}, overloads={count})")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
