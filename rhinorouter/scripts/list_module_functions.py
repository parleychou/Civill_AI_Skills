# -*- coding: utf-8 -*-
"""
列出指定 RhinoScript 模块中的函数列表

用法:
    python list_module_functions.py <module_name> [--limit N]

示例:
    python list_module_functions.py Curve_Methods
    python list_module_functions.py Surface_and_Polysurface_Methods --limit 20
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rhinorouter.api_docs import list_module_functions

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("用法: python list_module_functions.py <module_name> [--limit N]")
        print("示例: python list_module_functions.py Curve_Methods")
        sys.exit(1)

    module = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    rows = list_module_functions(module, limit)
    print(f"模块 '{module}' 包含的函数:")
    if not rows:
        print("  (未找到，请用 list_top_modules.py 确认模块名)")
        sys.exit(1)

    for name, purpose in rows:
        print(f"- {name}: {purpose}")

    if limit and len(rows) == limit:
        print(f"\n(显示前 {limit} 个，可能还有更多)")
    else:
        print(f"\n共 {len(rows)} 个函数")


if __name__ == "__main__":
    main()
