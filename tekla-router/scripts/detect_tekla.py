# -*- coding: utf-8 -*-
"""Detect the local Tekla Structures runtime and cache its bin directory.

The running process is authoritative.  A valid cache is used only when no
Tekla process is running, which prevents a 2025 cache from selecting the wrong
assemblies after the user has opened Tekla 2026.

The cache lives in the current task workspace.  Both ``python_executor`` and
skill query commands use that workspace as their current working directory, so
each conversation keeps an independent Tekla version context.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - this integration is Windows-only.
    winreg = None


CACHE_FILENAME = "tekla_env.json"
REQUIRED_DLLS = ("Tekla.Structures.Model.dll", "Tekla.Structures.dll")

COMMON_ROOTS = (
    Path(r"C:\Program Files\Tekla Structures"),
    Path(r"C:\Program Files (x86)\Tekla Structures"),
    Path(r"C:\Tekla Structures"),
    Path(r"C:\Tekla"),
    Path(r"D:\Program Files\Tekla Structures"),
    Path(r"D:\Program Files (x86)\Tekla Structures"),
    Path(r"D:\Tekla Structures"),
    Path(r"D:\Tekla"),
    Path(r"E:\Tekla Structures"),
    Path(r"E:\Tekla"),
)


class DetectionError(RuntimeError):
    pass


def cache_path() -> Path:
    """Return the Tekla environment cache in the current task workspace."""
    return Path.cwd() / CACHE_FILENAME


def _assembly_dirs(bin_dir: str | os.PathLike[str]) -> tuple[Path, ...]:
    root = Path(bin_dir)
    runtime = root / "Net48Runtime"
    return (root, runtime) if runtime.is_dir() else (root,)


def is_valid_bin(bin_dir: str | os.PathLike[str] | None) -> bool:
    """A usable bin contains Model and base Structures assemblies.

    Older Tekla releases may keep both assemblies in ``bin`` while newer ones
    keep ``Tekla.Structures.dll`` in ``Net48Runtime``.  Requiring the latter
    directory would incorrectly reject some supported annual versions.
    """
    if not bin_dir:
        return False
    root = Path(bin_dir)
    if not root.is_dir():
        return False
    dirs = _assembly_dirs(root)
    return all(any((folder / dll).is_file() for folder in dirs) for dll in REQUIRED_DLLS)


def infer_version(bin_dir: str | os.PathLike[str]) -> str:
    for part in reversed(Path(bin_dir).parts):
        match = re.search(r"(?<!\d)(20\d{2})(?:\.\d+)?(?!\d)", part)
        if match:
            return match.group(0)
    return "unknown"


def parse_api_year(value: object) -> int | None:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", str(value))
    return int(match.group(1)) if match else None


def _run_paths(command: list[str], timeout: float = 15.0) -> list[Path]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    paths: list[Path] = []
    for raw in completed.stdout.splitlines():
        value = raw.strip().strip('"')
        if value and value.lower().endswith("teklastructures.exe"):
            paths.append(Path(value))
    return paths


def running_bins() -> list[Path]:
    """Return distinct, valid bin directories for running Tekla processes."""
    executables = _run_paths(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-Process -Name TeklaStructures -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty Path -Unique",
        ]
    )
    if not executables:
        executables = _run_paths(
            [
                "wmic",
                "process",
                "where",
                "name='TeklaStructures.exe'",
                "get",
                "ExecutablePath",
            ]
        )

    unique: dict[str, Path] = {}
    for exe in executables:
        candidate = exe.parent
        if is_valid_bin(candidate):
            unique[os.path.normcase(os.path.normpath(str(candidate)))] = candidate
    return list(unique.values())


def detect_from_process() -> Path | None:
    bins = running_bins()
    if len(bins) > 1:
        values = "\n".join(f"- {path}" for path in bins)
        raise DetectionError(
            "检测到多个不同版本的 Tekla 正在运行，无法可靠判断 Open API 将连接哪一个。"
            f"请只保留目标实例后重试：\n{values}"
        )
    return bins[0] if bins else None


def _registry_value_candidates(key) -> list[Path]:
    result: list[Path] = []
    for value_name in ("Bin", "InstallDir", "InstallPath", "Path", ""):
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        if isinstance(value, str) and value.strip():
            path = Path(value.strip().strip('"'))
            result.extend((path, path / "bin", path / "nt", path / "bin" / "x64"))
    return result


def detect_from_registry() -> Path | None:
    if winreg is None:
        return None
    roots = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tekla\Structures"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Tekla\Structures"),
    )
    found: list[Path] = []
    for hive, base in roots:
        try:
            with winreg.OpenKey(hive, base) as root:
                found.extend(_registry_value_candidates(root))
                index = 0
                while True:
                    try:
                        child_name = winreg.EnumKey(root, index)
                        index += 1
                    except OSError:
                        break
                    try:
                        with winreg.OpenKey(root, child_name) as child:
                            found.extend(_registry_value_candidates(child))
                    except OSError:
                        continue
        except OSError:
            continue
    return _newest_valid(found)


def _version_key(path: Path) -> tuple[int, ...]:
    values = re.findall(r"\d+", infer_version(path))
    return tuple(int(value) for value in values) or (0,)


def _newest_valid(candidates) -> Path | None:
    unique: dict[str, Path] = {}
    for raw in candidates:
        path = Path(raw)
        if is_valid_bin(path):
            unique[os.path.normcase(os.path.normpath(str(path)))] = path
    values = sorted(unique.values(), key=_version_key, reverse=True)
    return values[0] if values else None


def detect_from_dirs() -> Path | None:
    found: list[Path] = []
    for root in COMMON_ROOTS:
        if not root.is_dir():
            continue
        for version_dir in root.iterdir():
            if not version_dir.is_dir():
                continue
            found.extend(
                (
                    version_dir / "bin",
                    version_dir / "nt",
                    version_dir / "bin" / "x64",
                )
            )
    return _newest_valid(found)


def load_cache() -> dict | None:
    path = cache_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return data if is_valid_bin(data.get("tekla_bin")) else None


def save_cache(data: dict) -> None:
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def make_result(bin_dir: str | os.PathLike[str], version: str | None = None) -> dict:
    version = version or infer_version(bin_dir)
    result = {
        "tekla_bin": str(Path(bin_dir).resolve()),
        "version": version,
        "detected_at": _datetime.datetime.now().isoformat(timespec="seconds"),
    }
    year = parse_api_year(version)
    if year is not None:
        result["api_year"] = year
    return result


def _manual_path() -> Path | None:
    if not sys.stdin.isatty():
        return None
    value = input("请输入 Tekla bin 目录（直接回车取消）: ").strip().strip('"')
    if not value:
        return None
    path = Path(value)
    if not is_valid_bin(path):
        raise DetectionError(f"无效 Tekla bin：{path}")
    return path


def detect(*, force: bool = False, manual_path: str | None = None, interactive: bool = False) -> dict:
    """Detect Tekla. A running process always wins over cache/installed versions."""
    if manual_path:
        path = Path(manual_path)
        if not is_valid_bin(path):
            raise DetectionError(f"无效 Tekla bin：{path}")
        return make_result(path)

    process_path = detect_from_process()
    if process_path is not None:
        return make_result(process_path)

    if not force:
        cached = load_cache()
        if cached is not None:
            return cached

    path = detect_from_registry() or detect_from_dirs()
    if path is None and interactive:
        path = _manual_path()
    if path is None:
        raise DetectionError(
            "未找到 Tekla。请先启动 Tekla 并打开模型，或使用 --path 指定 bin 目录。"
        )
    return make_result(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检测本机 Tekla Structures 运行时")
    parser.add_argument("--force", action="store_true", help="无运行实例时忽略缓存并重扫安装")
    parser.add_argument("--path", help="手动指定 Tekla bin 目录")
    parser.add_argument("--interactive", action="store_true", help="自动检测失败时允许交互输入")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON")
    args = parser.parse_args(argv)

    try:
        result = detect(force=args.force, manual_path=args.path, interactive=args.interactive)
        save_cache(result)
    except DetectionError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"TEKLA_BIN = {result['tekla_bin']}")
        print(f"版本      = {result['version']}")
        print(f"API 年份  = {result.get('api_year', 'unknown')}")
        print(f"缓存      = {cache_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
