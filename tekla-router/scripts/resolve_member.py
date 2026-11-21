# -*- coding: utf-8 -*-
"""Resolve one exact member name across a versioned Tekla type graph."""

from __future__ import annotations

import argparse
from collections import deque

from _tekla_db import (
    KIND_LABELS,
    RELATION_INTERFACE,
    RELATION_LABELS,
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
    parser.add_argument("type", help="Type on which the member will be used")
    parser.add_argument("member", help="Exact member name")
    parser.add_argument(
        "--kind",
        required=True,
        help="method/property/field/event/constructor/operator",
    )
    add_version_argument(parser)
    add_directory_arguments(parser, include_contains=False)
    args = parser.parse_args()
    limit, offset = directory_window(args.limit, args.offset)
    member_kind = kind_from_name(args.kind)

    conn = connect_db()
    try:
        year, bit = resolve_query_version(conn, args.version)
        start_type = find_type(conn, bit, args.type)
        if int(start_type["kind"]) == 5:
            raise ValueError("enumeration 类型请使用 list_enum_members_details.py")

        relation_rows = conn.execute(
            """
            SELECT tr.type_id, tr.target_id, tr.relation_kind,
                   target.symbol_key AS target_key
            FROM type_relations tr
            JOIN symbols target ON target.id = tr.target_id
            WHERE (tr.version_mask & ?) != 0
            ORDER BY tr.relation_kind, target.symbol_key
            """,
            (bit,),
        ).fetchall()
        adjacency: dict[int, list[tuple[int, int, str]]] = {}
        for row in relation_rows:
            adjacency.setdefault(int(row["type_id"]), []).append(
                (int(row["target_id"]), int(row["relation_kind"]), row["target_key"])
            )

        start_id = int(start_type["id"])
        paths: dict[int, tuple[tuple[int, int], tuple[int, ...], tuple[str, ...]]] = {
            start_id: ((0, 0), (), (start_type["symbol_key"],))
        }
        queue: deque[int] = deque([start_id])
        while queue:
            current_id = queue.popleft()
            score, edge_path, key_path = paths[current_id]
            if member_kind == 7:
                continue  # Constructors are never inherited.
            for target_id, relation_kind, target_key in adjacency.get(current_id, []):
                new_edges = (*edge_path, relation_kind)
                new_score = (
                    sum(1 for edge in new_edges if edge == RELATION_INTERFACE),
                    len(new_edges),
                )
                previous = paths.get(target_id)
                if previous is not None and previous[0] <= new_score:
                    continue
                paths[target_id] = (new_score, new_edges, (*key_path, target_key))
                queue.append(target_id)

        reachable_ids = sorted(paths)
        placeholders = ",".join("?" for _ in reachable_ids)
        rows = conn.execute(
            f"""
            SELECT s.parent_id, declaring.symbol_key AS declaring_key,
                   s.kind, s.name, count(*) AS candidate_count,
                   CASE WHEN count(*) = 1 THEN min(s.symbol_key) END AS symbol_key
            FROM symbols s
            JOIN symbols declaring ON declaring.id = s.parent_id
            WHERE s.parent_id IN ({placeholders})
              AND s.kind = ?
              AND s.name = ? COLLATE NOCASE
              AND EXISTS (
                  SELECT 1 FROM revisions r
                  WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
              )
            GROUP BY s.parent_id, declaring.symbol_key, s.kind, s.name COLLATE NOCASE
            """,
            (*reachable_ids, member_kind, args.member, bit),
        ).fetchall()

        results = []
        for row in rows:
            parent_id = int(row["parent_id"])
            score, edge_path, key_path = paths[parent_id]
            results.append((score, key_path, edge_path, row))
        results.sort(key=lambda item: (item[0], item[1]))
        total = len(results)
        page = results[offset : offset + limit]

        if not results:
            searched = sorted(paths.items(), key=lambda item: (item[1][0], item[1][2]))
            keys = [item[1][2][-1] for item in searched[:20]]
            suffix = " ..." if len(searched) > 20 else ""
            raise LookupError(
                f"Tekla {year} 中未找到 {KIND_LABELS[member_kind]} {args.member!r}；"
                f"已检查 {len(searched)} 个可达类型: {' -> '.join(keys)}{suffix}"
            )
    finally:
        conn.close()

    print(f"Resolved {KIND_LABELS[member_kind]} directory")
    print_directory_meta(
        year=year,
        parent_key=start_type["symbol_key"],
        total=total,
        offset=offset,
        count=len(page),
    )
    print(f"- searched_types: {len(paths)}")
    for _score, _key_path, edge_path, row in page:
        via = "self" if not edge_path else ">".join(RELATION_LABELS[edge] for edge in edge_path)
        count = int(row["candidate_count"])
        location = f"declared_on={row['declaring_key']}, via={via}"
        if count == 1:
            print(
                f"- {row['name']} ({KIND_LABELS[member_kind]}, {location}) "
                f"[{row['symbol_key']}]"
            )
        else:
            print(
                f"- {row['name']} ({KIND_LABELS[member_kind]}, overloads={count}, "
                f"{location})"
            )


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
