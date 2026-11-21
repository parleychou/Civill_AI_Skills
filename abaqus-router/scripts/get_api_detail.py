"""Fetch one exact Abaqus API contract or perform one intent search."""

from __future__ import annotations

import argparse

from _common import configure_version, docs


def main() -> None:
    """解析命令行查询方式，并输出一个精确契约或一组意图候选。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--call", help="Exact code-facing call, e.g. Part.BaseShellRevolve")
    parser.add_argument("--search-calls", help="Find canonical calls by operation intent")
    parser.add_argument("--member", help="Exact object member, e.g. Part.cells")
    parser.add_argument("--search-members", help="Find attributes/repositories by intent")
    parser.add_argument("--version", help="Abaqus year, for example 2024 or 2026")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    selected = sum(
        bool(value)
        for value in (
            args.call,
            args.search_calls,
            args.member,
            args.search_members,
        )
    )
    if selected != 1:
        parser.error("provide exactly one of --call, --search-calls, --member, or --search-members")

    configure_version(args.version)
    if args.call:
        result = docs.get_callable_info(args.call)
    elif args.member:
        result = docs.get_object_member_info(args.member)
    elif args.search_calls:
        result = docs.search_abaqus_callables(args.search_calls, limit=args.limit)
    else:
        result = docs.search_abaqus_object_members(args.search_members, limit=args.limit)
    print(result)


if __name__ == "__main__":
    main()
