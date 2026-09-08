# -*- coding: utf-8 -*-
"""
RhinoRouter 核心模块自动化单元测试
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rhinorouter.variants import (
    rgb,
    to_flat_variant_r8,
    to_flat_variant_i4,
    to_nested_variant_r8,
    to_nested_variant_i4,
)
from rhinorouter.api_docs import (
    get_top_modules,
    list_module_functions,
    get_function_detail,
    search_functions,
)
from rhinorouter.connector import (
    find_rhino_install_paths,
    find_rhino_process,
)


class TestRhinoRouter(unittest.TestCase):

    def test_rgb(self):
        self.assertEqual(rgb(255, 0, 0), 255)
        self.assertEqual(rgb(0, 255, 0), 65280)
        self.assertEqual(rgb(0, 0, 255), 16711680)

    def test_variants(self):
        v_flat_r8 = to_flat_variant_r8(1, 2, 3)
        self.assertEqual(v_flat_r8.value, [1.0, 2.0, 3.0])

        v_flat_i4 = to_flat_variant_i4([10, 20])
        self.assertEqual(v_flat_i4.value, [10, 20])

        v_nested_r8 = to_nested_variant_r8([(0, 0, 0), (1, 1, 1)])
        self.assertEqual(len(v_nested_r8.value), 2)
        self.assertEqual(v_nested_r8.value[0].value, [0.0, 0.0, 0.0])

        v_nested_i4 = to_nested_variant_i4([[0, 1, 2, 2]])
        self.assertEqual(len(v_nested_i4.value), 1)
        self.assertEqual(v_nested_i4.value[0].value, [0, 1, 2, 2])

    def test_api_database(self):
        modules = get_top_modules()
        self.assertEqual(len(modules), 29)

        funcs = list_module_functions("Curve_Methods", limit=5)
        self.assertEqual(len(funcs), 5)

        detail = get_function_detail("Curve_Methods", "AddCircle")
        self.assertIsNotNone(detail)
        self.assertEqual(detail[0], "AddCircle")

        searched = search_functions("Circle", limit=10)
        self.assertGreater(len(searched), 0)

    def test_system_detection(self):
        paths = find_rhino_install_paths()
        print("\n[Test Info] Detected Rhino installs:", paths)
        proc = find_rhino_process()
        print("[Test Info] Running Rhino process:", proc)


if __name__ == "__main__":
    unittest.main()
