# -*- coding: utf-8 -*-
"""
查看所有一级模块

用法:
    python list_top_modules.py
"""

import sqlite3
import sqlite3

def connect_db(path):
    """Connect to SQLite database."""
    return sqlite3.connect(str(path))

import os

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "etabs_api.db")
)


def get_top_modules():
    """获取所有一级模块"""
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    # 从路径提取一级目录
    cur.execute("""
        SELECT DISTINCT
            CASE
                WHEN instr(path, '/') > 0 THEN substr(path, 1, instr(path, '/') - 1)
                ELSE path
            END as group_name
        FROM modules
        ORDER BY group_name
    """)

    modules = [row[0] for row in cur.fetchall()]
    conn.close()
    return modules


def main():
    modules = get_top_modules()
    for i, name in enumerate(modules, 1):
        print(f"- {name}")

if __name__ == "__main__":
    main()
