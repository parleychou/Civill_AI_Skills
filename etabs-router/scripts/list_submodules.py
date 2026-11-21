# -*- coding: utf-8 -*-
"""
列出指定模块下所有子模块（任意层级）

用法:
    python list_submodules.py <module_path>

示例:
    python list_submodules.py "Code"
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


def get_submodules(module_path):
    """获取指定模块下所有子模块（任意层级）"""
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name, path, description
        FROM modules
        WHERE path LIKE ? AND path != ?
        ORDER BY path
    """, (f"{module_path}/%", module_path))

    results = cur.fetchall()
    conn.close()
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python list_submodules.py <module_path>")
        print('示例: python list_submodules.py "Code"')
        sys.exit(1)

    module_path = sys.argv[1]
    submodules = get_submodules(module_path)

    if not submodules:
        print("无子模块")
    else:
        base_depth = module_path.count('/')
        for name, path, desc in submodules:
            depth = path.count('/') - 1 - base_depth
            indent = "  " * depth
            desc_preview = (desc[:50] + "...") if desc and len(desc) > 50 else (desc or "")
            if desc_preview:
                print(f"{indent}- {name} [{path}]")
                print(f"{indent}  {desc_preview}")
            else:
                print(f"{indent}- {name} [{path}]")


if __name__ == "__main__":
    main()
