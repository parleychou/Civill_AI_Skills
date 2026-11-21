# -*- coding: utf-8 -*-
"""Search API documentation but return compact directory candidates only."""

import argparse

from _tekla_db import (
    KIND_LABELS,
    add_directory_arguments,
    add_version_argument,
    connect_db,
    directory_window,
    fts_query,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="API name or English documentation keywords")
    add_version_argument(parser)
    add_directory_arguments(parser, include_contains=False)
    parser.set_defaults(limit=10)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        matches = conn.execute(
            """
            SELECT s.id, s.parent_id, s.kind, s.name, s.symbol_key,
                   parent.symbol_key AS parent_key,
                   bm25(api_fts, 8.0, 5.0, 2.0, 1.0) AS rank
            FROM api_fts
            JOIN revisions r ON r.id = api_fts.rowid
            JOIN symbols s ON s.id = r.symbol_id
            LEFT JOIN symbols parent ON parent.id = s.parent_id
            WHERE api_fts MATCH ? AND (r.version_mask & ?) != 0
            ORDER BY rank, s.symbol_key
            """,
            (fts_query(args.query), bit),
        ).fetchall()

        active_group_counts = {
            (int(row["parent_id"]) if row["parent_id"] is not None else None, int(row["kind"]), row["name"].casefold()):
            int(row["candidate_count"])
            for row in conn.execute(
                """
                SELECT s.parent_id, s.kind, s.name, count(*) AS candidate_count
                FROM symbols s
                WHERE EXISTS (
                    SELECT 1 FROM revisions r
                    WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
                )
                GROUP BY s.parent_id, s.kind, s.name COLLATE NOCASE
                """,
                (bit,),
            )
        }
    finally:
        conn.close()

    groups: dict[tuple[int | None, int, str], dict[str, object]] = {}
    for row in matches:
        key = (
            int(row["parent_id"]) if row["parent_id"] is not None else None,
            int(row["kind"]),
            row["name"].casefold(),
        )
        if key not in groups:
            groups[key] = {
                "kind": int(row["kind"]),
                "name": row["name"],
                "symbol_key": row["symbol_key"],
                "parent_key": row["parent_key"],
                "candidate_count": active_group_counts.get(key, 1),
            }

    grouped_rows = list(groups.values())
    total = len(grouped_rows)
    page = grouped_rows[offset : offset + limit]
    print(f"Search directory for {args.query!r}")
    print_directory_meta(year=year, total=total, offset=offset, count=len(page))
    for row in page:
        kind = int(row["kind"])
        count = int(row["candidate_count"])
        parent = f" parent={row['parent_key']}" if row["parent_key"] else ""
        if count == 1:
            print(
                f"- {row['name']} ({KIND_LABELS[kind]})"
                f" [{row['symbol_key']}]{parent}"
            )
        else:
            print(
                f"- {row['name']} ({KIND_LABELS[kind]}, overloads={count}){parent}"
            )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
