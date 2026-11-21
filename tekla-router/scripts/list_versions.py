# -*- coding: utf-8 -*-
"""List Tekla product years available in the bundled API database."""

from _tekla_db import connect_db, run_cli


def main() -> None:
    conn = connect_db()
    try:
        rows = conn.execute("SELECT year, api_count FROM versions ORDER BY year").fetchall()
    finally:
        conn.close()
    for row in rows:
        print(f"- {row['year']}: {row['api_count']} API entries")


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
