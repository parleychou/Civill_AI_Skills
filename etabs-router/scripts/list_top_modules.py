# -*- coding: utf-8 -*-
"""
查看所有一级模块

用法:
    python list_top_modules.py
"""

import sqlite3
import sqlite3

def connect_db(path):
    """Connect to SQLite database with standard sqlite3 or fallback to vault."""
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        return conn
    except Exception:
        try:
            from PKPMAgent.skill_kit.vault import connect_db as v_connect
            return v_connect(path)
        except Exception as e:
            raise RuntimeError(f"Could not open database at {path}: {e}")

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
