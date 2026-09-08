# -*- coding: utf-8 -*-
"""
Rhino 官方 COM 自动化连接器与进程生命周期管理

支持：
  1. 自动检测本地已安装的 Rhino 8 / 7 / 6 版本
  2. 优先复用当前运行的 Rhino 实例，自动过滤并清理 -Embedding 僵尸进程
  3. 实例未运行时以独立进程模式启动，并轮询窗口可见性以确保 COM 注册就绪
  4. 加载官方 TypeLib 并导出强类型 IRhinoInterface / IRhinoScript 接口
"""

import os
import re
import sys
import time
import shutil
import winreg
import subprocess
import pythoncom
import win32gui
import win32process
import win32com
import win32com.client
from win32com.client import gencache, makepy, selecttlb
from win32com.client.gencache import EnsureModule

# Rhino 官方 COM TypeLib GUID 定义
_RHINO_TLB = "{8C16E736-D2B9-409D-80DE-CECFBFBC90F6}"       # Rhino.tlb
_SCRIPT_TLB = "{75B1E1B4-8CAA-43C3-975E-373504024FDB}"      # RhinoScript.tlb

_TYPE_E_LIBNOTREGISTERED = -2147319779  # 0x8002801D
_TYPE_E_CANTLOADLIBRARY = -2147312566   # 0x80029C4A


def find_process(name: str) -> list[tuple[int, str | None, str | None, list[str] | None]]:
    """查找指定名称的所有进程。

    Args:
        name: 进程名（如 "rhino.exe"）

    Returns:
        每项为 (进程ID, 进程工作目录, 可执行文件路径, 命令行参数)
    """
    import psutil
    target = name.lower()
    matches = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == target:
                p = psutil.Process(proc.info["pid"])
                try:
                    cwd = p.cwd()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cwd = None
                try:
                    exe = p.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    exe = None
                try:
                    cmdline = p.cmdline()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = None
                matches.append((proc.info["pid"], cwd, exe, cmdline))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches


def kill_process(pid: int) -> str | None:
    """终止指定 PID 的进程。成功返回 None，失败返回错误字符串。"""
    import psutil
    try:
        proc = psutil.Process(pid)
        proc.kill()
        proc.wait(timeout=3)
        return None
    except Exception as e:
        return str(e)


def find_rhino_install_paths() -> list[tuple[str, str]]:
    r"""从 Windows 注册表查找系统中所有真实存在的 Rhino 安装路径。

    排查卸载与升级留下的幽灵键（键值为空或目标目录已被删除），
    使用 System\Rhino.exe 真实存在性作为校验条件。

    Returns:
        按版本号从高到低排序的 [(version_str, install_path), ...]
    """
    results = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\McNeel\Rhinoceros") as rk:
            i = 0
            while True:
                try:
                    ver_key = winreg.EnumKey(rk, i)
                    i += 1
                    try:
                        with winreg.OpenKey(rk, f"{ver_key}\\Install") as ik:
                            path = None
                            for val_name in ("InstallPath", "Path", "InstallDir"):
                                try:
                                    path, _ = winreg.QueryValueEx(ik, val_name)
                                    if path:
                                        break
                                except OSError:
                                    pass
                            if not path:
                                continue
                            if not os.path.isfile(os.path.join(path, "System", "Rhino.exe")):
                                continue
                            ver = None
                            try:
                                ver, _ = winreg.QueryValueEx(ik, "Version")
                            except OSError:
                                ver = ver_key
                            results.append((ver, path))
                    except OSError:
                        pass
                except OSError:
                    break
    except OSError:
        pass

    def _parse_version(v):
        try:
            return tuple(int(x) for x in re.findall(r"\d+", v))
        except Exception:
            return (0,)

    results.sort(key=lambda x: _parse_version(x[0]), reverse=True)
    return results


def find_rhino_process() -> tuple[int | None, str | None, str | None, list[str] | None]:
    """查找用户正在使用的真实 Rhino 进程。

    自动检测并清理带有 -Embedding 参数的残留自动化僵尸进程，
    返回第一个正常启动的 Rhino 进程信息。
    """
    procs = find_process("rhino.exe")
    for pid, cwd, exe, cmdline in procs:
        is_embedding = False
        if cmdline:
            is_embedding = any("-embedding" in arg.lower() for arg in cmdline)
        if is_embedding:
            kill_process(pid)
        else:
            return pid, cwd, exe, cmdline
    return None, None, None, None


def clear_gen_py_cache():
    """清理 pywin32 gencache 磁盘缓存并重建内存索引。"""
    gen_path = getattr(win32com, "__gen_path__", None)
    if gen_path and os.path.isdir(gen_path):
        try:
            shutil.rmtree(gen_path, ignore_errors=True)
        except Exception:
            pass
    try:
        gencache.Rebuild()
    except Exception:
        pass


def module_from_tlb_file(tlb_path: str):
    """直接从 .tlb 文件生成并返回 makepy 强类型模块，绕过注册表依赖。"""
    tlb = pythoncom.LoadTypeLib(tlb_path)
    guid, lcid, _syskind, major, minor, _flags = tlb.GetLibAttr()
    try:
        mod = gencache.GetModuleForTypelib(str(guid), lcid, major, minor)
        if mod is not None:
            return mod
    except Exception:
        pass
    spec = selecttlb.TypelibSpec(tlb_path)
    makepy.GenerateChildFromTypeLibSpec(spec)
    return gencache.GetModuleForTypelib(str(guid), lcid, major, minor)


def modules_from_tlb_files(install_dir: str):
    """从 Rhino 安装目录定位 Rhino.tlb 与 RhinoScript.tlb 并返回模块。"""
    def _locate(filename: str) -> str:
        candidates = [
            os.path.join(install_dir, "System", filename),
            os.path.join(install_dir, "Plug-ins", filename),
            os.path.join(install_dir, filename),
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        for root, _, files in os.walk(install_dir):
            for f in files:
                if f.lower() == filename.lower():
                    return os.path.join(root, f)
        raise FileNotFoundError(f"未在 Rhino 安装目录 {install_dir} 中找到 {filename}")

    rhino_tlb = _locate("Rhino.tlb")
    script_tlb = _locate("RhinoScript.tlb")
    return module_from_tlb_file(rhino_tlb), module_from_tlb_file(script_tlb)


def load_rhino_modules(version: int, install_dir: str | None = None):
    """加载指定版本的 Rhino COM TypeLib，返回 (rhino_mod, script_mod)。"""
    try:
        rhino_mod = EnsureModule(_RHINO_TLB, 0, version, 0)
        script_mod = EnsureModule(_SCRIPT_TLB, 0, version, 0)
        return rhino_mod, script_mod
    except Exception as e:
        hresult = getattr(e, "hresult", None)
        if hresult in (_TYPE_E_LIBNOTREGISTERED, _TYPE_E_CANTLOADLIBRARY):
            if install_dir:
                return modules_from_tlb_files(install_dir)
            raise
        clear_gen_py_cache()
        try:
            rhino_mod = EnsureModule(_RHINO_TLB, 0, version, 0)
            script_mod = EnsureModule(_SCRIPT_TLB, 0, version, 0)
            return rhino_mod, script_mod
        except Exception:
            if install_dir:
                return modules_from_tlb_files(install_dir)
            raise


def wait_for_rhino_window(pid: int, timeout: float = 120.0) -> bool:
    """轮询直到指定 PID 拥有一个带标题的可见顶层窗口（代表 COM 消息循环就绪）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = False

        def _enum(hwnd, _):
            nonlocal found
            if win32gui.IsWindowVisible(hwnd):
                _, w_pid = win32process.GetWindowThreadProcessId(hwnd)
                if w_pid == pid:
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        found = True
                        return False
            return True

        try:
            win32gui.EnumWindows(_enum, None)
        except Exception:
            pass
        if found:
            return True
        time.sleep(0.5)
    return False


def spawn_rhino(install_dir: str, timeout: float = 120.0) -> int:
    """以独立进程方式启动 Rhino 并等待顶层窗口出现。"""
    exe = os.path.join(install_dir, "System", "Rhino.exe")
    flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen([exe], creationflags=flags, close_fds=True)
    if not wait_for_rhino_window(p.pid, timeout=timeout):
        raise TimeoutError(f"Rhino (PID {p.pid}) 已启动，但在 {timeout} 秒内未检测到可见顶层窗口。")
    return p.pid


def attach_rhino(version: int):
    """通过 Dispatch 附着到已运行的 Rhino COM 实例。"""
    progids = [
        f"Rhino.Application.{version}",
        f"Rhino.Interface.{version}",
        "Rhino.Application",
        "Rhino.Interface",
    ]
    for progid in progids:
        try:
            dispatch = win32com.client.Dispatch(progid)
            if dispatch:
                return dispatch
        except Exception:
            continue
    return None


def get_rhino(auto_spawn: bool = True, timeout: float = 60.0):
    """获取 Rhino 应用实例与 RhinoScript 脚本接口。

    参数:
        auto_spawn: 当无运行中的 Rhino 进程时，是否自动启动新实例 (默认 True)
        timeout: 启动新实例时的窗口等待超时时间 (秒)

    返回值:
        成功: (rhino, script, version) 元组
              - rhino: IRhinoInterface / IRhinoApplication 实例
              - script: 包含 1245 个官方 API 的 IRhinoScript 实例
              - version: int 主版本号（如 8, 7, 6）
        失败: 错误描述字符串
    """
    installs = find_rhino_install_paths()
    if not installs:
        return "未在系统中检测到有效的 Rhino 安装（未找到有效注册表项或 Rhino.exe 文件）。"

    path_to_ver = {}
    for ver_str, install_path in installs:
        norm = os.path.normcase(os.path.abspath(install_path)).rstrip("\\/")
        path_to_ver[norm] = ver_str

    pid, _, exe, _ = find_rhino_process()
    version = None
    install_dir = None

    if pid is not None and exe:
        exe_norm = os.path.normcase(os.path.abspath(exe))
        for path_prefix, ver in path_to_ver.items():
            if exe_norm.startswith(path_prefix):
                try:
                    version = int(ver.split(".")[0])
                    install_dir = path_prefix
                    break
                except ValueError:
                    pass

    if version is None:
        ver_str, install_dir = installs[0]
        try:
            version = int(ver_str.split(".")[0])
        except ValueError:
            version = 8

    try:
        rhino_mod, script_mod = load_rhino_modules(version, install_dir)
    except Exception as e:
        return f"加载 Rhino {version} TypeLib 失败: {e}"

    if pid is None:
        if not auto_spawn:
            return "未检测到正在运行的 Rhino 进程。请先打开 Rhino，或在调用时设置 auto_spawn=True 自动拉起实例。"
        try:
            pid = spawn_rhino(install_dir, timeout=timeout)
        except Exception as e:
            return f"启动 Rhino 进程失败: {e}"

    dispatch = attach_rhino(version)
    if dispatch is None:
        return f"无法连接到 Rhino {version} COM 接口 (Dispatch 附着失败)。"

    try:
        rhino = getattr(rhino_mod, "IRhinoInterface", getattr(rhino_mod, "RhinoInterface", None))(dispatch)
        if rhino is None:
            rhino = dispatch
    except Exception:
        rhino = dispatch

    try:
        script_disp = rhino.GetScriptObject()
        script = getattr(script_mod, "IRhinoScript", getattr(script_mod, "RhinoScript", None))(script_disp)
        if script is None:
            script = script_disp
    except Exception as e:
        return f"获取 RhinoScript 接口失败: {e}"

    return rhino, script, version
