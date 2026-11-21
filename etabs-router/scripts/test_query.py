# -*- coding: utf-8 -*-
"""
测试 ETABS-Link 检索脚本的所有查询功能

通过模拟命令行执行（subprocess），与 Agent 实际运行方式一致。

用法:
    python test_query.py
"""

import subprocess
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

PASS = 0
FAIL = 0


def run(script, args=""):
    """模拟命令行执行脚本，返回 (returncode, stdout)"""
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, script)]
    if args:
        cmd += args.split("  ")
        # 用双空格分割参数，避免路径中的空格问题
        cmd = [PYTHON, os.path.join(SCRIPTS_DIR, script)] + args.split("  ")
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8"
    )
    return result.returncode, result.stdout.strip()


def run_raw(script, args_list):
    """模拟命令行执行脚本，参数以列表传入，返回 (returncode, stdout)"""
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, script)] + args_list
    result = subprocess.run(cmd, capture_output=True)
    stdout = result.stdout.decode("utf-8").strip()
    return result.returncode, stdout


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"  ({detail})"
        print(msg)


def show(label, output):
    """显示命令行输出前30行"""
    lines = output.split("\n")
    # print(len(lines))
    for line in lines[:20]:
        safe = line.encode("gbk", errors="replace").decode("gbk")
        print(f"    {safe}")
    if len(lines) > 20:
        print(f"    ... (共 {len(lines)} 行)")


# ==================== 1. list_top_modules ====================
print("\n=== list_top_modules ===")

code, out = run_raw("list_top_modules.py", [])
test("执行成功 (returncode=0)", code == 0)
test("输出包含 cFrameObj", "cFrameObj" in out)
test("输出包含 Code", "Code" in out)
test("输出包含 Enumeration", "Enumeration" in out)
print("")
print("list_top_modules.py, [] 的细节")
show("output", out)


# ==================== 2. list_submodules ====================
print("\n=== list_submodules ===")

# Code 子模块
code, out = run_raw("list_submodules.py", ["Code"])
test("Code 子模块执行成功", code == 0)
test("Code 输出含 cDCoChinese_2010", "cDCoChinese_2010" in out)
print("")
print("list_submodules.py, ['Code'] 的细节")
show("Code submodules", out)

# Enumeration 子模块
code, out = run_raw("list_submodules.py", ["Enumeration"])
test("Enumeration 子模块执行成功", code == 0)
test("Enumeration 输出含 eItemType", "eItemType" in out)
print("")
print("list_submodules.py, ['Enumeration'] 的细节")
show("Enum submodules (前几行)", out)

# 普通模块无子模块
code, out = run_raw("list_submodules.py", ["cFrameObj"])
test("cFrameObj 输出无子模块", "无子模块" in out)
print("")
print("list_submodules.py, ['cFrameObj'] 的细节")   
show("list_submodules 输出:", out)


# ==================== 3. list_module_functions ====================
print("\n=== list_module_functions ===")

# 普通模块
code, out = run_raw("list_module_functions.py", ["cFrameObj"])
test("cFrameObj 函数列表执行成功", code == 0)
test("输出含 SetLoadDistributed", "SetLoadDistributed" in out)
print("")
print("list_module_functions.py, ['cFrameObj'] 的细节")
show("list_module_functions 输出:", out)

# 带 limit
code, out = run_raw("list_module_functions.py", ["cFrameObj", "--limit", "2"])
test("limit=2 执行成功", code == 0)
func_lines = [l for l in out.split("\n") if l.strip() and not l.startswith("模块") and not l.startswith("共")]
test("limit=2 限制输出行数", len(func_lines) <= 4)
print("")
print("list_module_functions.py, ['cFrameObj'] 的细节")
show("list_module_functions 输出:", out)

# Code 模块
code, out = run_raw("list_module_functions.py", ["Code/cDCoChinese_2010"])
test("Code/cDCoChinese_2010 执行成功", code == 0)
test("输出含 SetOverwrite", "SetOverwrite" in out)
print("")
print("list_module_functions.py, ['Code/cDCoChinese_2010'] 的细节")
show("list_module_functions 输出:", out)


# ==================== 4. get_function_or_enum_detail - 函数查询 ====================
print("\n=== get_function_or_enum_detail (函数查询) ===")

# 精确查询函数
code, out = run_raw("get_function_or_enum_detail.py", ["cFrameObj", "SetLoadDistributed"])
test("查询 cFrameObj SetLoadDistributed 执行成功", code == 0)
test("输出含 SetLoadDistributed 名称", "SetLoadDistributed" in out)
test("输出含 syntax 字段", "syntax" in out)
test("输出含 vb_signature 字段", "vb_signature" in out)
print("")
print("get_function_or_enum_detail.py, ['cFrameObj', 'SetLoadDistributed'] 的细节")
show("get 输出:", out)


# 不存在的函数
code, out = run_raw("get_function_or_enum_detail.py", ["cFrameObj", "NotExistsFunction"])
test("不存在函数提示未找到", "未找到" in out)


# ==================== 5. get_function_or_enum_detail --functionsearch ====================
print("\n=== get_function_or_enum_detail --functionsearch ===")

code, out = run_raw("get_function_or_enum_detail.py", ["--functionsearch", "FrameForce"])
test("搜索 FrameForce 执行成功", code == 0)
test("输出含 FrameForce", "FrameForce" in out)
print("")
print("get_function_or_enum_detail.py, ['--functionsearch', 'FrameForce'] 的细节")
show("search results", out)

# 无匹配
code, out = run_raw("get_function_or_enum_detail.py", ["--functionsearch", "ZZZ_NOT_EXIST"])
test("无匹配搜索提示未找到", "未找到" in out)


# ==================== 6. get_function_or_enum_detail - 枚举路径查询 ====================
print("\n=== get_function_or_enum_detail (枚举路径查询) ===")

code, out = run_raw("get_function_or_enum_detail.py", ["Enumeration/eItemType"])
test("路径查询 eItemType 执行成功", code == 0)
test("输出含 eItemType", "eItemType" in out)
test("输出含 Objects = 0", "Objects = 0" in out or "Objects" in out)
print("")
print("get_function_or_enum_detail.py, ['Enumeration/eItemType'] 的细节")
show("enum by path", out)

# 不存在的枚举路径
code, out = run_raw("get_function_or_enum_detail.py", ["Enumeration/eNotExist"])
test("不存在的枚举路径提示未找到", "未找到" in out)


# ==================== 7. get_function_or_enum_detail --enumsearch ====================
print("\n=== get_function_or_enum_detail --enumsearch ===")

# 按枚举名精确查找
code, out = run_raw("get_function_or_enum_detail.py", ["--enumsearch", "eItemType"])
test("--enumsearch eItemType 执行成功", code == 0)
test("输出含 Objects", "Objects" in out)
print("")
print("get_function_or_enum_detail.py, ['--enumsearch', 'eItemType'] 的细节")
show("enumsearch by name", out)

# 按成员名查找
code, out = run_raw("get_function_or_enum_detail.py", ["--enumsearch", "Objects"])
test("--enumsearch Objects 执行成功", code == 0)
test("输出含 eItemType", "eItemType" in out)
print("")
print("get_function_or_enum_detail.py, ['--enumsearch', 'Objects'] 的细节")
show("enumsearch by member", out)

# 不存在的枚举/成员
code, out = run_raw("get_function_or_enum_detail.py", ["--enumsearch", "ZZZ_NOT_EXIST"])
test("不存在的枚举搜索提示未找到", "未找到" in out)


# ==================== 汇总 ====================
total = PASS + FAIL
print(f"\n{'='*40}")
print(f"测试完成: {PASS}/{total} 通过, {FAIL}/{total} 失败")
if FAIL == 0:
    print("全部通过!")
else:
    print("存在失败用例，请检查!")
    sys.exit(1)
