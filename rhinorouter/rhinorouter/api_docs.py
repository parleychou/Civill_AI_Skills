# -*- coding: utf-8 -*-
"""
RhinoScript 1245 个官方 API 知识库查询接口

直连本地 references/rhinoscript_api.db (SQLite 3 标准数据库)。
"""

import os
import sqlite3
from pathlib import Path


def get_db_path() -> str:
    """获取 rhinoscript_api.db 数据库的绝对路径。"""
    curr = Path(__file__).resolve().parent
    # 优先在 package 同级 references 查找
    db1 = curr.parent / "references" / "rhinoscript_api.db"
    if db1.is_file():
        return str(db1)
    # 兼容直接放置在当前目录
    db2 = curr / "rhinoscript_api.db"
    if db2.is_file():
        return str(db2)
    return str(db1)


def connect_db(db_path: str | None = None) -> sqlite3.Connection:
    """连接到本地 SQLite 知识库。"""
    p = db_path or get_db_path()
    return sqlite3.connect(p)


def get_top_modules(db_path: str | None = None) -> list[tuple[str, str]]:
    """获取所有 29 个顶级 RhinoScript 模块名称与描述。"""
    conn = connect_db(db_path)
    cur = conn.cursor()
    rows = cur.execute("SELECT name, description FROM modules ORDER BY name").fetchall()
    conn.close()
    return rows


def list_module_functions(module: str, limit: int | None = None, db_path: str | None = None) -> list[tuple[str, str]]:
    """获取指定模块包含的所有函数及其简要说明。"""
    conn = connect_db(db_path)
    cur = conn.cursor()
    sql = (
        "SELECT f.name, f.purpose FROM functions f "
        "JOIN modules m ON f.module_id = m.id "
        "WHERE m.name = ? ORDER BY f.name"
    )
    params = (module,)
    if limit:
        sql += " LIMIT ?"
        params = (module, limit)
    rows = cur.execute(sql, params).fetchall()
    conn.close()
    return rows


def get_function_detail(module: str, func: str, db_path: str | None = None):
    """获取指定模块内特定函数的完整签名、说明、参数、返回值与示例。"""
    conn = connect_db(db_path)
    cur = conn.cursor()
    row = cur.execute(
        """SELECT f.name, f.syntax, f.purpose, f.parameters,
                  f.returns, f.example, f.see_also, m.name
           FROM functions f JOIN modules m ON f.module_id = m.id
           WHERE m.name = ? AND f.name = ?""",
        (module, func),
    ).fetchone()
    conn.close()
    return row


def search_functions(keyword: str, limit: int = 20, db_path: str | None = None) -> list[tuple[str, str, str]]:
    """全局搜索包含关键词的函数。"""
    conn = connect_db(db_path)
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
