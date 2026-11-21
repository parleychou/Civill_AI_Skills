# -*- coding: utf-8 -*-
"""
List all OpenSTAAD API modules.

Usage:
    python list_top_modules.py
"""

import os
import sys

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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "openstaad_api.db")
)


def main():
    conn = connect_db(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT m.name, m.path, m.description, COUNT(f.id) "
        "FROM modules m LEFT JOIN functions f ON f.module_id = m.id "
        "GROUP BY m.id ORDER BY m.name"
    ).fetchall()
    conn.close()

    for name, path, desc, n in rows:
        preview = (desc[:1000] + "...") if desc and len(desc) > 1000 else (desc or "")
        print(f"- {name}  [{path}]  ({n} 函数)")
        if preview:
            print(f"  {preview}")
    print()
    print(f"共 {len(rows)} 个模块。后续命令中模块既可用全名(带引号),也可用方括号里的短名。")


if __name__ == "__main__":
    main()
