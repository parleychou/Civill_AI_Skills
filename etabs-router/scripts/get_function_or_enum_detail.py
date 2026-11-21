# -*- coding: utf-8 -*-
"""
获取函数详细信息，支持枚举查询。

用法:
    根据路径和函数名查找函数信息用法:
    get_function_or_enum_detail.py <module_path> <function_name>
    仅提供函数名搜索函数用法:
    get_function_or_enum_detail.py --functionsearch <function_name>
    根据路径查找枚举信息用法:
    get_function_or_enum_detail.py <module_path>
    根据枚举名查找枚举信息用法:
    get_function_or_enum_detail.py --enumsearch <enum_name>
示例:
    get_function_or_enum_detail.py "cFrameObj" SetLoadDistributed
    get_function_or_enum_detail.py --functionsearch FrameForce
    get_function_or_enum_detail.py "Enumeration/eTemplateType Enumeration"
    get_function_or_enum_detail.py --enumsearch eItemType
    get_function_or_enum_detail.py --enumsearch Objects
"""

import sqlite3
import sqlite3

def connect_db(path):
    """Connect to SQLite database."""
    return sqlite3.connect(str(path))

import os
import sys
import json

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "references", "etabs_api.db")
)


def get_function_detail(module_path, func_name):
    """通过模块路径 + 函数名精确查询
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT f.name, f.syntax, f.vb_signature, f.purpose,
               f.parameters, f.remarks, f.example, f.see_also
        FROM functions f
        JOIN modules m ON f.module_id = m.id
        WHERE m.path = ? AND f.name = ?
    """, (module_path, func_name))

    result = cur.fetchone()
    conn.close()
    if result:
        return ("function",) + result
    return None



def search_function(keyword, limit=10):
    """按关键词搜索函数（用于只知函数名时）

    返回格式: [(module_path, (name, syntax, vb_signature, purpose, parameters, remarks, example, see_also)), ...]
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT m.path, f.name, f.syntax, f.vb_signature, f.purpose,
               f.parameters, f.remarks, f.example, f.see_also
        FROM functions f
        JOIN modules m ON f.module_id = m.id
        WHERE f.name LIKE ? OR f.purpose LIKE ?
        ORDER BY m.path, f.name
        LIMIT ?
    """, (f"%{keyword}%", f"%{keyword}%", limit))

    results = [(row[0], row[1:]) for row in cur.fetchall()]
    conn.close()
    return results


def get_enum_detail_by_enum_name(enum_name):
    """通过枚举名直接查询该枚举的全部成员

    返回格式: {"enum_name": {"member_name": "member_value", ...}}
    未找到返回空字典 {}
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT member_name, member_value
        FROM enumerations
        WHERE enum_name = ?
        ORDER BY member_value
    """, (enum_name,))

    members = {mn: str(mv) for mn, mv in cur.fetchall()}
    conn.close()

    if members:
        return {enum_name: members}
    return {}


def get_enum_detail_by_module(module_path):
    """通过模块路径查询该枚举的全部成员

    返回格式: {"enum_name": {"member_name": "member_value", ...}}
    未找到返回空字典 {}
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT e.enum_name, e.member_name, e.member_value
        FROM enumerations e
        JOIN modules m ON e.module_id = m.id
        WHERE m.path = ?
        ORDER BY e.member_value
    """, (module_path,))

    results = {}
    for enum_name, member_name, member_value in cur.fetchall():
        results.setdefault(enum_name, {})[member_name] = str(member_value)

    conn.close()
    return results


def search_enum(member_name):
    """通过成员名查找其所属枚举

    返回格式: {"enum_name": {"member_name": "member_value", ...}, ...}
    如果多个枚举包含该成员，全部返回
    """
    conn = connect_db(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT e.enum_name, e.member_name, e.member_value
        FROM enumerations e
        WHERE e.member_name = ?
        ORDER BY e.enum_name
    """, (member_name,))

    results = {}
    for enum_name, mn, mv in cur.fetchall():
        if enum_name not in results:
            # 查询该枚举的全部成员
            cur.execute("""
                SELECT member_name, member_value
                FROM enumerations
                WHERE enum_name = ?
                ORDER BY member_value
            """, (enum_name,))
            results[enum_name] = {m: str(v) for m, v in cur.fetchall()}

    conn.close()
    return results


def format_output(result):
    """格式化输出函数详情"""
    name, syntax, vb_signature, purpose, parameters, remarks, example, see_also = result

    output = []
    output.append(f"**function_name:{name}**")
    output.append("")
    if syntax:
        output.append(f"- syntax:{syntax}")
        output.append("")

    if vb_signature:
        output.append(f"- vb_signature:{vb_signature}")
        output.append("")

    if purpose:
        output.append(f"- purpose:{purpose}")
        output.append("")

    if parameters:
        output.append(f"- parameters:{parameters}")
        output.append("")

    if remarks:
        output.append(f"- remarks:{remarks}")
        output.append("")

    if example:
        output.append(f"- example:")
        output.append(example)
        output.append("")
    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("根据路径和函数名查找函数信息用法:")
        print("  get_function_or_enum_detail.py <module_path> <function_name>")
        print("仅提供函数名搜索函数用法:")
        print("  get_function_or_enum_detail.py --functionsearch <function_name>")
        print("根据路径查找枚举信息用法:")
        print("  get_function_or_enum_detail.py <module_path>")
        print("根据枚举名查找枚举信息用法:")
        print("  get_function_or_enum_detail.py --enumsearch <enum_name>")
        print()
        print("示例:")
        print('  get_function_or_enum_detail.py "cFrameObj" SetLoadDistributed')
        print('  get_function_or_enum_detail.py --functionsearch FrameForce')
        print('  get_function_or_enum_detail.py "Enumeration/eTemplateType Enumeration"')
        print('  get_function_or_enum_detail.py --enumsearch eItemType')
        print('  get_function_or_enum_detail.py --enumsearch Objects')
        sys.exit(1)

    if sys.argv[1] == "--functionsearch":
        keyword = sys.argv[2]
        results = search_function(keyword)

        if not results:
            print(f"未找到匹配的函数: {keyword}")
        else:
            for module_path, func_data in results:
                print(f"** module_path:{module_path}**:")
                print(format_output(func_data))
                print()
            print(f"共找到 {len(results)} 个匹配函数")

    elif sys.argv[1] == "--enumsearch":
        name = sys.argv[2]
        # 先按枚举名精确查找
        results = get_enum_detail_by_enum_name(name)
        if results:
            for enum_name, members in results.items():
                print(f"**{enum_name}**:")
                for member_name, member_value in members.items():
                    print(f"  {member_name} = {member_value}")
            total = sum(len(m) for m in results.values())
            print(f"\n共 {total} 个成员")
        else:
            # 按成员名查找
            results = search_enum(name)
            if results:
                for enum_name, members in results.items():
                    print(f"**{enum_name}**:")
                    for member_name, member_value in members.items():
                        print(f"  {member_name} = {member_value}")
                total = sum(len(m) for m in results.values())
                print(f"\n共 {total} 个成员")
            else:
                print(f"未找到枚举或成员: {name}")

    else:
        module_path = sys.argv[1]

        if len(sys.argv) >= 3:
            # 模式1: module_path + func_name，查函数详情
            func_name = sys.argv[2]
            result = get_function_detail(module_path, func_name)

            if not result:
                print(f"未找到函数: {func_name} (模块: {module_path})")
            else:
                print(format_output(result[1:]))
        else:
            # 模式3: 只传 module_path，查枚举
            results = get_enum_detail_by_module(module_path)

            if results:
                for enum_name, members in results.items():
                    print(f"**{enum_name}**:")
                    for member_name, member_value in members.items():
                        print(f"  {member_name} = {member_value}")
                total = sum(len(m) for m in results.values())
                print(f"\n共 {total} 个成员")
            else:
                print(f"未找到枚举: {module_path}")


if __name__ == "__main__":
    main()
