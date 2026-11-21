# -*- coding: utf-8 -*-
"""Retrieve one exact API topic for the detected Tekla version."""

import argparse

from _tekla_db import (
    KIND_LABELS,
    add_version_argument,
    available_years,
    connect_db,
    detail_text,
    find_active_symbol,
    resolve_query_version,
    run_cli,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "symbol_key",
        help="Exact Microsoft Help ID; method overloads must include the complete parameter signature",
    )
    add_version_argument(parser)
    args = parser.parse_args()

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        symbol_key = args.symbol_key
        row = find_active_symbol(conn, bit, symbol_key)
        if row is None:
            raise LookupError(f"Tekla {year} 中不存在 API: {symbol_key}")
        kind_label = KIND_LABELS[row["kind"]]
        if int(row["kind"]) == 10 and row["parent_id"] is not None:
            parent = conn.execute(
                "SELECT kind FROM symbols WHERE id = ?",
                (int(row["parent_id"]),),
            ).fetchone()
            if parent is not None and int(parent["kind"]) == 5:
                kind_label = "enum-member"
        revision_masks = conn.execute(
            "SELECT version_mask FROM revisions WHERE symbol_id = ?",
            (row["id"],),
        ).fetchall()
        mask = 0
        for revision in revision_masks:
            mask |= int(revision["version_mask"])
        availability = available_years(conn, mask)
        body = detail_text(row["detail_blob"])
    finally:
        conn.close()

    print(f"**name: {row['name']}**")
    print(f"- query_version: Tekla {year}")
    print(f"- kind: {kind_label}")
    print(f"- symbol_key: {row['symbol_key']}")
    print(f"- available_versions: {', '.join(map(str, availability))}")
    if row["summary"]:
        print(f"- summary: {row['summary']}")
    if body:
        print()
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
