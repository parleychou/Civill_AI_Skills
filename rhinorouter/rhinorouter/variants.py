# -*- coding: utf-8 -*-
"""
RhinoScript COM 参数封送与 VARIANT / SAFEARRAY 转换工具

RhinoScript COM 接口源自 Windows OLE Automation (VBScript 规范)。
Python 的原生 list / tuple 跨进程传递给 win32com 时，由于缺乏类型上下文，
无法自动组装为正确的 SAFEARRAY。本模块提供经过生产环境校验的 5 个数据封送转换函数。
"""

import pythoncom
from win32com.client import VARIANT


def rgb(r: int, g: int, b: int) -> int:
    """计算 RhinoScript 颜色参数 (32-bit Integer / COLORREF)。

    RhinoScript 的 lngColor 参数等价于 VBScript 的 RGB(r, g, b) 函数：
    底 8 位为 R，中 8 位为 G，高 8 位为 B。
    """
    return int(r) | (int(g) << 8) | (int(b) << 16)


def to_flat_variant_r8(*args) -> VARIANT:
    """把坐标或数值打包为一维 Double 数组 (VARIANT VT_ARRAY | VT_R8)。

    适用于 NURBS 曲线/曲面的节点向量 (knots)、权重 (weights) 或平铺的坐标列表。

    调用方式支持：
      to_flat_variant_r8([0, 0, 0, 0.5, 1, 1, 1])          # 传入单列表
      to_flat_variant_r8(0, 0, 0, 0.5, 1, 1, 1)            # 多参数变参
      to_flat_variant_r8([(0,0,0), (10,0,0), (10,10,0)])   # 点列表自动平铺为一维浮点
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        seq = args[0]
    else:
        seq = args
    flat = []
    for item in seq:
        if isinstance(item, (list, tuple)):
            flat.extend(float(x) for x in item)
        else:
            flat.append(float(item))
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)


def to_flat_variant_i4(*args) -> VARIANT:
    """把整数列表打包为一维 Int32 数组 (VARIANT VT_ARRAY | VT_I4)。

    调用方式支持：
      to_flat_variant_i4([1, 2, 3])
      to_flat_variant_i4(1, 2, 3)
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        items = args[0]
    else:
        items = args
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_I4, [int(i) for i in items])


def to_nested_variant_r8(*args) -> VARIANT:
    """把点/向量列表打包为嵌套数组 (VT_ARRAY | VT_VARIANT of VT_ARRAY | VT_R8)。

    用于解决 VBScript 中 Array(Array(x,y,z), ...) 结构在 Python 中的封送。
    适用于所有接收“点数组 / 向量数组 / 平面”的方法，如：
    AddBox, AddPolyline, AddInterpCurve, AddMesh (arrVertices), AddEllipse (arrPlane)。

    调用方式支持：
      to_nested_variant_r8([(0,0,0), (10,0,0), (10,10,0)])
      to_nested_variant_r8((0,0,0), (10,0,0), (10,10,0))
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        items = args[0]
    else:
        items = args
    inner = []
    for item in items:
        inner.append(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(c) for c in item]))
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, inner)


def to_nested_variant_i4(*args) -> VARIANT:
    """把索引列表打包为嵌套整数数组 (VT_ARRAY | VT_VARIANT of VT_ARRAY | VT_I4)。

    用于 AddMesh 的 arrFaceVertices 参数（定义三角面/四边面的顶点索引）。

    调用方式支持：
      to_nested_variant_i4([[0, 1, 2, 2], [0, 2, 3, 3]])
      to_nested_variant_i4([0, 1, 2, 2], [0, 2, 3, 3])
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        items = args[0]
    else:
        items = args
    inner = []
    for item in items:
        inner.append(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_I4, [int(i) for i in item]))
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, inner)
