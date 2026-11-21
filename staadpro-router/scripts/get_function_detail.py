# -*- coding: utf-8 -*-
"""
Get function detail or search functions across all modules.

Usage:
    python get_function_detail.py <module> <function>
    python get_function_detail.py <function>              # module omitted: match by name
    python get_function_detail.py --search <keyword>

Examples:
    python get_function_detail.py Node GetNodeCount
    python get_function_detail.py member_geometry AddBeam
    python get_function_detail.py GetNodeCount
    python get_function_detail.py --search reaction
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


def get_detail(module: str | None, func: str):
    conn = connect_db(DB_PATH)
    cur = conn.cursor()
    sql = (
        "SELECT f.name, f.category, f.syntax, f.purpose, f.parameters, "
        "f.returns, f.example, m.name "
        "FROM functions f JOIN modules m ON f.module_id = m.id "
        "WHERE f.name = ?"
    )
    params: tuple = (func,)
    if module:
        sql += " AND (m.name = ? OR m.path = ?)"
        params = (func, module, module)
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return rows


def search(keyword: str, limit: int = 20):
    conn = connect_db(DB_PATH)
    cur = conn.cursor()
    pat = f"%{keyword}%"
    rows = cur.execute(
        """SELECT f.name, m.name, f.purpose
           FROM functions f JOIN modules m ON f.module_id = m.id
           WHERE f.name LIKE ? OR f.purpose LIKE ?
           ORDER BY (f.name LIKE ?) DESC, f.name
           LIMIT ?""",
        (pat, pat, pat, limit),
    ).fetchall()
    conn.close()
    return rows


def format_detail(row) -> str:
    name, category, syntax, purpose, parameters, returns, example, module = row
    out = []
    out.append(f"**{module} / {name}**  [{category}]")
    out.append("")
    if purpose:
        out.append(f"- purpose: {purpose}")
        out.append("")
    if syntax:
        out.append(f"- syntax: {syntax}")
        out.append("")
    if parameters:
        out.append("- parameters:")
        out.append(parameters)
        out.append("")
    if returns:
        out.append("- returns:")
        out.append(returns)
        out.append("")
    if example:
        out.append("- example (Python):")
        out.append(example)
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python get_function_detail.py <module> <function>")
        print("  python get_function_detail.py <function>")
        print("  python get_function_detail.py --search <keyword>")
        sys.exit(1)

    if sys.argv[1] == "--search":
        if len(sys.argv) < 3:
            print("错误: --search 需要关键词")
            sys.exit(1)
        keyword = sys.argv[2]
        rows = search(keyword)
        print(f"搜索 '{keyword}' 的结果:")
        if not rows:
            print("  (未找到)")
            return
        for fname, mname, purpose in rows:
            preview = (purpose[:80] + "...") if purpose and len(purpose) > 80 else (purpose or "")
            print(f"- {mname} / {fname}")
            if preview:
                print(f"  {preview}")
        print()
        print(f"共 {len(rows)} 个匹配，可用 get_function_detail.py <module> <function> 查看详情")
        return

    if len(sys.argv) >= 3:
        module, func = sys.argv[1], sys.argv[2]
    else:
        module, func = None, sys.argv[1]

    rows = get_detail(module, func)
    if not rows:
        print(f"未找到: {module + ' / ' if module else ''}{func}")
        print(f"提示: 可用 --search {func} 搜索")
        sys.exit(1)
    for i, row in enumerate(rows):
        if i:
            print("\n" + "=" * 60 + "\n")
        print(format_detail(row))
    if len(rows) > 1:
        print()
        print(f"(同名函数出现在 {len(rows)} 个模块中，以上全部列出)")


if __name__ == "__main__":
    main()
