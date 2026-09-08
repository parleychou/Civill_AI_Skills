# -*- coding: utf-8 -*-
"""
获取指定函数的详细签名、用途、参数说明与官方示例，或全局模糊搜索

用法:
    python get_function_detail.py <module> <function>
    python get_function_detail.py --search <keyword>

示例:
    python get_function_detail.py Curve_Methods AddCircle
    python get_function_detail.py --search Circle
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rhinorouter.api_docs import get_function_detail, search_functions

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def format_detail(row) -> str:
    name, syntax, purpose, parameters, returns, example, see_also, module = row
    out = []
    out.append(f"**{module}/{name}**")
    out.append("")
    if purpose:
        out.append(f"- 说明 (purpose): {purpose}")
        out.append("")
    if syntax:
        out.append("- 语法 (syntax):")
        out.append(syntax)
        out.append("")
    if parameters:
        out.append("- 参数说明 (parameters):")
        out.append(parameters)
        out.append("")
    if returns:
        out.append("- 返回值 (returns):")
        out.append(returns)
        out.append("")
    if example:
        out.append("- 官方示例 (VBScript，请按 SKILL.md 规范转为 Python):")
        out.append(example)
        out.append("")
    if see_also:
        out.append(f"- 相关函数 (see_also): {see_also}")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python get_function_detail.py <module> <function>")
        print("  python get_function_detail.py --search <keyword>")
        sys.exit(1)

    if sys.argv[1] == "--search":
        if len(sys.argv) < 3:
            print("错误: --search 需要指定关键词")
            sys.exit(1)
        keyword = sys.argv[2]
        rows = search_functions(keyword)
        print(f"搜索 '{keyword}' 的结果:")
        if not rows:
            print("  (未找到匹配函数)")
            return
        for fname, mname, purpose in rows:
            preview = (purpose[:80] + "...") if purpose and len(purpose) > 80 else (purpose or "")
            print(f"- {mname}/{fname}")
            if preview:
                print(f"  {preview}")
        print(f"\n共 {len(rows)} 个匹配，可用 get_function_detail.py <module> <function> 查看详情")
        return

    if len(sys.argv) < 3:
        print("错误: 需要同时提供 module 和 function 名")
        sys.exit(1)

    module, func = sys.argv[1], sys.argv[2]
    row = get_function_detail(module, func)
    if not row:
        print(f"未找到: {module}/{func}")
        print(f"提示: 可使用 python get_function_detail.py --search {func} 全局搜索")
        sys.exit(1)

    print(format_detail(row))


if __name__ == "__main__":
    main()
