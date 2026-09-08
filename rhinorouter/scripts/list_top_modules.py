# -*- coding: utf-8 -*-
"""
列出所有 29 个顶级 RhinoScript 模块

用法:
    python list_top_modules.py
"""

import os
import sys

# 自动定位上一级目录以导入 rhinorouter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rhinorouter.api_docs import get_top_modules

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    rows = get_top_modules()
    print(f"=== RhinoScript 官方顶级模块列表 (共 {len(rows)} 个) ===\n")
    for name, desc in rows:
        preview = (desc[:200] + "...") if desc and len(desc) > 200 else (desc or "")
        print(f"- {name}")
        if preview:
            print(f"  {preview}")
    print()


if __name__ == "__main__":
    main()
