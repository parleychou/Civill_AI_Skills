# -*- coding: utf-8 -*-
"""List direct base-class or interface edges for one API type."""

import argparse

from _tekla_db import (
    RELATION_BASE,
    RELATION_INTERFACE,
    RELATION_LABELS,
    add_directory_arguments,
    add_version_argument,
    connect_db,
    directory_window,
    find_type,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="Full type name or exact T: key")
    parser.add_argument("--kind", required=True, choices=("base", "interface"))
    add_version_argument(parser)
    add_directory_arguments(parser)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    contains = (args.contains or "").strip()
    relation_kind = RELATION_BASE if args.kind == "base" else RELATION_INTERFACE

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        type_row = find_type(conn, bit, args.type)
        where = """
            tr.type_id = ?
            AND tr.relation_kind = ?
            AND (tr.version_mask & ?) != 0
            AND (? = '' OR instr(lower(target.name), lower(?)) > 0)
        """
        parameters: tuple[object, ...] = (
            int(type_row["id"]),
            relation_kind,
            bit,
            contains,
            contains,
        )
        total = int(
            conn.execute(
                f"""
                SELECT count(*)
                FROM type_relations tr
                JOIN symbols target ON target.id = tr.target_id
                WHERE {where}
                """,
                parameters,
            ).fetchone()[0]
        )
        rows = conn.execute(
            f"""
            SELECT target.name, target.symbol_key
            FROM type_relations tr
            JOIN symbols target ON target.id = tr.target_id
            WHERE {where}
            ORDER BY target.name COLLATE NOCASE, target.symbol_key
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset),
        ).fetchall()
    finally:
        conn.close()

    print(f"Direct {RELATION_LABELS[relation_kind]} type directory")
    print_directory_meta(
        year=year,
        parent_key=type_row["symbol_key"],
        total=total,
        offset=offset,
        count=len(rows),
    )
    for row in rows:
        print(f"- {row['name']} ({RELATION_LABELS[relation_kind]}) [{row['symbol_key']}]")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
