# -*- coding: utf-8 -*-
"""
List functions in a given OpenSTAAD module.

Usage:
    python list_module_functions.py <module> [--limit N]

<module> accepts either the full name or the short path name, e.g.:
    python list_module_functions.py Node
    python list_module_functions.py member_geometry
    python list_module_functions.py "Load: Load Cases" --limit 20
"""

import os
import sys

import sqlite3

def connect_db(path):
    """Connect to SQLite database."""
    return sqlite3.connect(str(path))


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "openstaad_api.db")
)


def list_functions(module: str, limit: int | None = None):
    conn = connect_db(DB_PATH)
    cur = conn.cursor()
    sql = (
        "SELECT f.name, f.category, f.purpose FROM functions f "
        "JOIN modules m ON f.module_id = m.id "
        "WHERE m.name = ? OR m.path = ? "
        "ORDER BY f.category, f.name"
    )
    params: tuple = (module, module)
    if limit:
        sql += " LIMIT ?"
        params = (module, module, limit)
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return rows


def main():
    if len(sys.argv) < 2:
        print("用法: python list_module_functions.py <module> [--limit N]")
        print("示例: python list_module_functions.py Node")
        print("      python list_module_functions.py member_geometry")
        sys.exit(1)

    module = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    rows = list_functions(module, limit)

    print(f"模块 '{module}' 包含的函数:")
    if not rows:
        print("  (未找到，请用 list_top_modules.py 确认模块名)")
        sys.exit(1)
    current_cat = None
    for name, category, purpose in rows:
        if category != current_cat:
            current_cat = category
            print(f"[{category}]")
        print(f"  {name}: {purpose[:120] if purpose else ''}")
    if limit and len(rows) == limit:
        print(f"(显示前 {limit} 个，可能还有更多)")
    else:
        print(f"共 {len(rows)} 个函数")


if __name__ == "__main__":
    main()
