# -*- coding: utf-8 -*-
"""Tekla pythonnet runtime used inside a PKPMAgent per-thread exec worker."""

from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DB_PATH = SKILL_DIR / "references" / "tekla_api.db"

_DETECT_SPEC = importlib.util.spec_from_file_location(
    "_pkpmagent_detect_tekla", SCRIPT_DIR / "detect_tekla.py"
)
if _DETECT_SPEC is None or _DETECT_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("无法加载 Tekla 检测模块")
_detect_module = importlib.util.module_from_spec(_DETECT_SPEC)
sys.modules.setdefault(_DETECT_SPEC.name, _detect_module)
_DETECT_SPEC.loader.exec_module(_detect_module)


ASSEMBLIES = (
    "Tekla.Structures.dll",
    "Tekla.Structures.Datatype.dll",
    "Tekla.Structures.Geometry3d.Compatibility.dll",
    "Tekla.Structures.Model.dll",
    "Tekla.Structures.Catalogs.dll",
    "Tekla.Structures.Plugins.dll",
    "Tekla.Structures.Dialog.dll",
    "Tekla.Structures.Analysis.dll",
    "Tekla.Structures.Drawing.dll",
)

_LOADED_BIN: str | None = None
_DLL_DIRECTORY_HANDLES: list[object] = []
_DLL_DIRECTORY_PATHS: set[str] = set()
_LOADED_ASSEMBLIES: dict[str, str] = {}


@dataclass(frozen=True)
class TeklaSession:
    model: object
    tekla_bin: str
    program_version: str
    api_year: int
    loaded_assemblies: tuple[str, ...]


def _normal(path: str | os.PathLike[str]) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def detect_tekla(*, force: bool = False, bin_path: str | None = None) -> dict:
    return _detect_module.detect(force=force, manual_path=bin_path)


def _connect_db() -> sqlite3.Connection:
    try:
        import sqlite3

def connect_db(path):
    """Connect to SQLite database with standard sqlite3 or fallback to vault."""
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        return conn
    except Exception:
        try:
            from PKPMAgent.skill_kit.vault import connect_db as v_connect
            return v_connect(path)
        except Exception as e:
            raise RuntimeError(f"Could not open database at {path}: {e}")

    except ImportError:
        uri = DB_PATH.resolve().as_uri() + "?mode=ro"
        return sqlite3.connect(uri, uri=True)
    return connect_db(DB_PATH)


def supported_years() -> tuple[int, ...]:
    conn = _connect_db()
    try:
        return tuple(int(row[0]) for row in conn.execute("SELECT year FROM versions ORDER BY year"))
    finally:
        conn.close()


def _assembly_dirs(bin_dir: str) -> tuple[Path, ...]:
    root = Path(bin_dir)
    runtime = root / "Net48Runtime"
    return (root, runtime) if runtime.is_dir() else (root,)


def _configure_search_paths(bin_dir: str) -> tuple[Path, ...]:
    directories = _assembly_dirs(bin_dir)
    for directory in reversed(directories):
        value = str(directory)
        if value not in sys.path:
            sys.path.insert(0, value)
    if hasattr(os, "add_dll_directory"):
        for directory in directories:
            normalized = _normal(directory)
            if normalized not in _DLL_DIRECTORY_PATHS:
                _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(directory)))
                _DLL_DIRECTORY_PATHS.add(normalized)
    return directories


def load_assemblies(bin_dir: str) -> dict[str, str]:
    """Load the annual Tekla assemblies once in the current worker process."""
    global _LOADED_BIN
    normalized = _normal(bin_dir)
    if _LOADED_BIN is not None and _normal(_LOADED_BIN) != normalized:
        raise RuntimeError(
            "当前 work 线程已经加载另一版 Tekla CLR 程序集，.NET 程序集无法在进程内卸载。"
            "请在只运行目标 Tekla 版本后新建一个任务，再连接。"
        )
    directories = _configure_search_paths(bin_dir)

    try:
        from pythonnet import load

        try:
            load("netfx")
        except RuntimeError as exc:
            # pythonnet reports this when another module has already initialized CLR.
            if "already" not in str(exc).lower() and "initialized" not in str(exc).lower():
                raise
        import clr
    except Exception as exc:
        raise RuntimeError(f"无法初始化 pythonnet/.NET Framework：{exc}") from exc

    for name in ASSEMBLIES:
        if name in _LOADED_ASSEMBLIES:
            continue
        path = next((folder / name for folder in directories if (folder / name).is_file()), None)
        if path is None:
            # Model and base Structures are detector requirements. Other API areas are
            # optional in customized installations and should not block model access.
            if name in ("Tekla.Structures.dll", "Tekla.Structures.Model.dll"):
                raise RuntimeError(f"Tekla 安装缺少必需程序集：{name}")
            continue
        try:
            clr.AddReference(str(path))
        except Exception as exc:
            raise RuntimeError(f"加载 Tekla 程序集失败：{path}: {exc}") from exc
        _LOADED_ASSEMBLIES[name] = str(path)

    _LOADED_BIN = str(Path(bin_dir).resolve())
    return dict(_LOADED_ASSEMBLIES)


def _program_year(version: str) -> int:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", version)
    if not match:
        raise RuntimeError(f"无法从 Tekla 返回值解析年度版本：{version!r}")
    return int(match.group(1))


def connect_tekla(*, force_detect: bool = False, bin_path: str | None = None) -> TeklaSession:
    """Connect to the already-running Tekla instance in the current worker."""
    environment = detect_tekla(force=force_detect, bin_path=bin_path)
    assemblies = load_assemblies(environment["tekla_bin"])

    try:
        from Tekla.Structures import TeklaStructuresInfo
        from Tekla.Structures.Model import Model
    except Exception as exc:
        raise RuntimeError(f"Tekla 命名空间导入失败：{exc}") from exc

    model = Model()
    if not model.GetConnectionStatus():
        raise RuntimeError("无法连接 Tekla：请确认 Tekla 已运行且模型已经打开")

    program_version = str(TeklaStructuresInfo.GetCurrentProgramVersion())
    api_year = _program_year(program_version)
    years = supported_years()
    if api_year not in years:
        available = ", ".join(map(str, years))
        raise RuntimeError(f"API 文档库不支持 Tekla {api_year}；可用版本：{available}")

    detected_year = environment.get("api_year")
    if detected_year is not None and int(detected_year) != api_year:
        raise RuntimeError(
            f"程序集路径年份 {detected_year} 与已连接实例 {program_version} 不一致；"
            "请关闭其他 Tekla 版本并在新任务中重试"
        )

    environment["version"] = program_version
    environment["api_year"] = api_year
    _detect_module.save_cache(environment)
    return TeklaSession(
        model=model,
        tekla_bin=environment["tekla_bin"],
        program_version=program_version,
        api_year=api_year,
        loaded_assemblies=tuple(assemblies),
    )
