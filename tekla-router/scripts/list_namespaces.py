# -*- coding: utf-8 -*-
"""List every namespace available in one Tekla version."""

import argparse

from _tekla_db import (
    add_version_argument,
    connect_db,
    print_directory_meta,
    resolve_query_version,
    run_cli,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    add_version_argument(parser)
    args = parser.parse_args()

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        rows = conn.execute(
            """
            SELECT s.name, s.symbol_key
            FROM symbols s
            WHERE s.kind = 1
              AND EXISTS (
                  SELECT 1 FROM revisions r
                  WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
              )
            ORDER BY s.name COLLATE NOCASE
            """,
            (bit,),
        ).fetchall()
    finally:
        conn.close()

    print("Namespace directory")
    print_directory_meta(year=year, total=len(rows), offset=0, count=len(rows))
    for row in rows:
        print(f"- {row['name']} [{row['symbol_key']}]")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
