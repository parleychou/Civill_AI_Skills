# -*- coding: utf-8 -*-
"""
RhinoRouter: 专为 AI Agent 与自动化脚本打造的官方 Rhino 3D 连接与建模工具包

功能概览：
  - get_rhino(): 一键连接或启动 Rhino 8/7/6 实例，获取 IRhinoScript 强类型句柄
  - to_nested_variant_r8, to_flat_variant_r8, rgb 等: 解决 COM 数据封送的核心转换函数
  - get_function_detail, search_functions 等: 本地 1245 个官方 API 知识库检索
"""

from .variants import (
    rgb,
    to_flat_variant_r8,
    to_flat_variant_i4,
    to_nested_variant_r8,
    to_nested_variant_i4,
)
from .connector import (
    get_rhino,
    find_rhino_install_paths,
    find_rhino_process,
    load_rhino_modules,
    attach_rhino,
    spawn_rhino,
    clear_gen_py_cache,
)
from .api_docs import (
    get_top_modules,
    list_module_functions,
    get_function_detail,
    search_functions,
)

__version__ = "2.0.0"
__all__ = [
    "get_rhino",
    "rgb",
    "to_flat_variant_r8",
    "to_flat_variant_i4",
    "to_nested_variant_r8",
    "to_nested_variant_i4",
    "find_rhino_install_paths",
    "find_rhino_process",
    "load_rhino_modules",
    "attach_rhino",
    "spawn_rhino",
    "clear_gen_py_cache",
    "get_top_modules",
    "list_module_functions",
    "get_function_detail",
    "search_functions",
]
