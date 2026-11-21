# -*- coding: utf-8 -*-
"""List one kind of type directly contained by a namespace or another type."""

import argparse

from _tekla_db import (
    KIND_LABELS,
    add_directory_arguments,
    add_version_argument,
    connect_db,
    directory_window,
    find_container,
    print_directory_meta,
    resolve_query_version,
    run_cli,
    type_kind_from_name,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", help="Exact N:/T: parent key, full namespace, or full type name")
    parser.add_argument(
        "--kind",
        required=True,
        help="class/interface/structure/enumeration/delegate",
    )
    add_version_argument(parser)
    add_directory_arguments(parser)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    type_kind = type_kind_from_name(args.kind)
    contains = (args.contains or "").strip()

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        parent = find_container(conn, bit, args.parent)
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
            int(parent["id"]),
            type_kind,
            bit,
            contains,
            contains,
        )
        total = int(
            conn.execute(f"SELECT count(*) FROM symbols s WHERE {where}", parameters).fetchone()[0]
        )
        rows = conn.execute(
            f"""
            SELECT s.kind, s.name, s.symbol_key
            FROM symbols s
            WHERE {where}
            ORDER BY s.name COLLATE NOCASE, s.symbol_key
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        ).fetchall()
    finally:
        conn.close()

    print(f"{KIND_LABELS[type_kind].title()} directory")
    print_directory_meta(
        year=year,
        parent_key=parent["symbol_key"],
        total=total,
        offset=offset,
        count=len(rows),
    )
    for row in rows:
        print(f"- {row['name']} ({KIND_LABELS[row['kind']]}) [{row['symbol_key']}]")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
