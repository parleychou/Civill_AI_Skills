"""01_query_api_database.py
示例 1：查询本地 RhinoScript 1245 个官方 API 知识库。

无需启动 Rhino 软件，直接基于 references/rhinoscript_api.db 执行离线结构化检索：
- 检索所有 29 个顶级模块
- 模块函数清单列举
- 单函数完整签名、参数、返回值与官方示例提取
- 关键词模糊搜索
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from rhinorouter import (
    get_top_modules,
    list_module_functions,
    get_function_detail,
    search_functions,
)


def main():
    print("=== RhinoScript 官方 API 知识库检索示例 ===\n")

    # 1. 查询 29 个顶级模块
    modules = get_top_modules()
    print(f"[1. 顶级模块总览] 共 {len(modules)} 个模块:")
    for name, desc in modules[:8]:
        short_desc = (desc[:60] + "...") if desc and len(desc) > 60 else (desc or "无描述")
        print(f"  - {name}: {short_desc}")
    print(f"  ... (还有 {len(modules) - 8} 个模块)\n")

    # 2. 列出 Curve_Methods 模块的前 10 个函数
    mod_name = "Curve_Methods"
    funcs = list_module_functions(mod_name, limit=10)
    print(f"[2. {mod_name} 模块函数样例] (展示前 {len(funcs)} 个):")
    for fname, purpose in funcs:
        p_short = (purpose[:50] + "...") if purpose and len(purpose) > 50 else (purpose or "")
        print(f"  - {fname}: {p_short}")
    print()

    # 3. 查看 AddBox 详细签名与参数
    detail = get_function_detail("Surface_and_Polysurface_Methods", "AddBox")
    if detail:
        fname, syntax, purpose, parameters, returns, example, see_also, mname = detail
        print(f"[3. 详细函数文档: {mname}.{fname}]")
        print(f"  说明: {purpose}")
        print(f"  语法:\n    {syntax}")
        print(f"  参数说明:\n    {parameters}")
        print(f"  返回值: {returns}")
    print()

    # 4. 全局搜索包含 'Mesh' 的核心方法
    keyword = "Mesh"
    results = search_functions(keyword, limit=6)
    print(f"[4. 全局搜索关键词 '{keyword}'] 找到前 {len(results)} 条匹配:")
    for fname, mname, purpose in results:
        p_short = (purpose[:40] + "...") if purpose and len(purpose) > 40 else (purpose or "")
        print(f"  - [{mname}] {fname}: {p_short}")


if __name__ == "__main__":
    main()
