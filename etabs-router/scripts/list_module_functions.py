# -*- coding: utf-8 -*-
"""
查看指定模块直接包含的函数

用法:
    python list_module_functions.py <module_path> [--limit N]

示例:
    python list_module_functions.py "ETABSv1/cFrameObj Interface/cFrameObj Methods"
    python list_module_functions.py "ETABSv1/cAnalyze Interface/cAnalyze Methods" --limit 20
"""

import sqlite3
import sqlite3

def connect_db(path):
    """Connect to SQLite database."""
    return sqlite3.connect(str(path))

import os
import sys

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "etabs_api.db")
)


def get_module_functions(module_path, limit=None):
    """获取指定模块直接包含的函数
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    if limit:
        cur.execute("""
            SELECT f.name, f.purpose, f.syntax
            FROM functions f
            JOIN modules m ON f.module_id = m.id
            WHERE m.path = ?
            ORDER BY f.name
            LIMIT ?
        """, (module_path, limit))
    else:
        cur.execute("""
            SELECT f.name, f.purpose, f.syntax
            FROM functions f
            JOIN modules m ON f.module_id = m.id
            WHERE m.path = ?
            ORDER BY f.name
        """, (module_path,))
        
    functions = cur.fetchall()
    conn.close()
    return functions


def main():
    if len(sys.argv) < 2:
        print("用法: python list_module_functions.py <module_path> [--limit N]")
        print('示例: python list_module_functions.py "cFrameObj Interface"')
        sys.exit(1)

    module_path = sys.argv[1]
    limit = None

    # 解析 --limit 参数
    if "--limit" in sys.argv:
        limit_idx = sys.argv.index("--limit")
        if limit_idx + 1 < len(sys.argv):
            limit = int(sys.argv[limit_idx + 1])

    result = get_module_functions(module_path, limit)

    
    functions = result
    print(f"模块 '{module_path}' 直接包含的函数：")

    if not functions:
        print("  (该模块无直接包含的函数，请查看其子模块)")
    else:
        for name, purpose, syntax in functions:
            print(f"{name}: {purpose}")

    total = len(functions)
    if limit and total == limit:
        print(f"(显示前 {limit} 个函数，可能还有更多)")
    else:
        print(f"共 {total} 个函数")
    print()


if __name__ == "__main__":
    main()
