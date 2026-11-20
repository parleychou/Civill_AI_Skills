# -*- coding: utf-8 -*-
"""Locate a local Tekla Structures bin directory.

A running TeklaStructures process is the authority. The workspace cache is used
only when nothing is running, so a cached 2025 path cannot select assemblies
after the user has opened Tekla 2026. Each task workspace keeps its own cache
because both the executor and this script use that directory as the working
directory.
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
except ImportError:  # pragma: no cover - Windows-only integration.
    winreg = None


CACHE_FILENAME = "tekla_env.json"
REQUIRED_ASSEMBLIES = ("Tekla.Structures.Model.dll", "Tekla.Structures.dll")
SEARCH_ROOTS = (
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
REGISTRY_KEYS = (
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tekla\Structures") if winreg else None,
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Tekla\Structures") if winreg else None,
)
SUPPORTED_YEARS = (2020, 2021, 2022, 2023, 2024, 2025, 2026)


class DetectionError(RuntimeError):
    """Raised when a requested Tekla install cannot be resolved."""


def cache_file() -> Path:
    return Path.cwd() / CACHE_FILENAME


def assembly_dirs(bin_dir: str | os.PathLike[str]) -> tuple[Path, ...]:
    root = Path(bin_dir)
    runtime = root / "Net48Runtime"
    if runtime.is_dir():
        return (root, runtime)
    return (root,)


def is_valid_bin(bin_dir: str | os.PathLike[str] | None) -> bool:
    """True when Model and base Structures assemblies are present.

    Older releases keep both assemblies in ``bin``. Newer releases keep
    ``Tekla.Structures.dll`` under ``Net48Runtime``. Requiring that extra
    directory would reject supported annual versions.
    """
    if not bin_dir:
        return False
    root = Path(bin_dir)
    if not root.is_dir():
        return False
    folders = assembly_dirs(root)
    return all(any((folder / name).is_file() for folder in folders) for name in REQUIRED_ASSEMBLIES)


def version_from_path(bin_dir: str | os.PathLike[str]) -> str:
    for part in reversed(Path(bin_dir).parts):
        match = re.search(r"(?<!\d)(20\d{2})(?:\.\d+)?(?!\d)", part)
        if match:
            return match.group(0)
    return "unknown"


def year_from_text(value: object) -> int | None:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", str(value))
    if not match:
        return None
    return int(match.group(1))


def _command_paths(command: list[str], timeout: float = 15.0) -> list[Path]:
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
    found: list[Path] = []
    for raw in completed.stdout.splitlines():
        value = raw.strip().strip('"')
        if value and value.lower().endswith("teklastructures.exe"):
            found.append(Path(value))
    return found


def running_bins() -> list[Path]:
    executables = _command_paths(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-Process -Name TeklaStructures -ErrorAction SilentlyContinue "
            "| Select-Object -ExpandProperty Path -Unique",
        ]
    )
    if not executables:
        executables = _command_paths(
            ["wmic", "process", "where", "name='TeklaStructures.exe'", "get", "ExecutablePath"]
        )
    unique: dict[str, Path] = {}
    for exe in executables:
        candidate = exe.parent
        if is_valid_bin(candidate):
            unique[os.path.normcase(os.path.normpath(str(candidate)))] = candidate
    return list(unique.values())


def bin_from_process() -> Path | None:
    bins = running_bins()
    if len(bins) > 1:
        listing = "\n".join("- {0}".format(path) for path in bins)
        raise DetectionError(
            "More than one Tekla release is running, so the Open API target is ambiguous. "
            "Leave only the target instance running and retry:\n{0}".format(listing)
        )
    if not bins:
        return None
    return bins[0]


def _registry_paths(key) -> list[Path]:
    found: list[Path] = []
    for value_name in ("Bin", "InstallDir", "InstallPath", "Path", ""):
        try:
            value, _kind = winreg.QueryValueEx(key, value_name)
        except OSError:
            continue
        if isinstance(value, str) and value.strip():
            path = Path(value.strip().strip('"'))
            found.extend((path, path / "bin", path / "nt", path / "bin" / "x64"))
    return found


def _walk_registry(root, found: list[Path]) -> None:
    found.extend(_registry_paths(root))
    index = 0
    while True:
        try:
            child_name = winreg.EnumKey(root, index)
        except OSError:
            return
        index += 1
        try:
            with winreg.OpenKey(root, child_name) as child:
                found.extend(_registry_paths(child))
        except OSError:
            continue


def bin_from_registry() -> Path | None:
    if winreg is None:
        return None
    found: list[Path] = []
    for item in REGISTRY_KEYS:
        if item is None:
            continue
        hive, base = item
        try:
            with winreg.OpenKey(hive, base) as root:
                _walk_registry(root, found)
        except OSError:
            continue
    return newest_valid(found)


def version_sort_key(path: Path) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", version_from_path(path))
    if not numbers:
        return (0,)
    return tuple(int(value) for value in numbers)


def newest_valid(candidates) -> Path | None:
    unique: dict[str, Path] = {}
    for raw in candidates:
        path = Path(raw)
        if is_valid_bin(path):
            unique[os.path.normcase(os.path.normpath(str(path)))] = path
    ordered = sorted(unique.values(), key=version_sort_key, reverse=True)
    if not ordered:
        return None
    return ordered[0]


def bin_from_common_dirs() -> Path | None:
    found: list[Path] = []
    for root in SEARCH_ROOTS:
        if not root.is_dir():
            continue
        for version_dir in root.iterdir():
            if not version_dir.is_dir():
                continue
            found.extend((version_dir / "bin", version_dir / "nt", version_dir / "bin" / "x64"))
    return newest_valid(found)


def read_cache() -> dict | None:
    try:
        data = json.loads(cache_file().read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not is_valid_bin(data.get("tekla_bin")):
        return None
    return data


def save_cache(data: dict) -> None:
    path = cache_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)


def describe_bin(bin_dir: str | os.PathLike[str], version: str | None = None) -> dict:
    version = version or version_from_path(bin_dir)
    result = {
        "tekla_bin": str(Path(bin_dir).resolve()),
        "version": version,
        "detected_at": _datetime.datetime.now().isoformat(timespec="seconds"),
    }
    year = year_from_text(version)
    if year is not None:
        result["api_year"] = year
    return result


def prompt_for_bin() -> Path | None:
    if not sys.stdin.isatty():
        return None
    value = input("Tekla bin directory (press Enter to cancel): ").strip().strip('"')
    if not value:
        return None
    path = Path(value)
    if not is_valid_bin(path):
        raise DetectionError("Not a Tekla bin directory: {0}".format(path))
    return path


def detect(*, force: bool = False, manual_path: str | None = None, interactive: bool = False) -> dict:
    """Resolve a Tekla bin. A running process wins over cache and installed copies."""
    if manual_path:
        path = Path(manual_path)
        if not is_valid_bin(path):
            raise DetectionError("Not a Tekla bin directory: {0}".format(path))
        return describe_bin(path)

    process_path = bin_from_process()
    if process_path is not None:
        return describe_bin(process_path)
    if not force:
        cached = read_cache()
        if cached is not None:
            return cached
    path = bin_from_registry() or bin_from_common_dirs()
    if path is None and interactive:
        path = prompt_for_bin()
    if path is None:
        raise DetectionError(
            "Tekla Structures was not found. Start Tekla and open a model, or pass --path with the bin directory."
        )
    return describe_bin(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Locate a local Tekla Structures runtime")
    parser.add_argument("--force", action="store_true", help="Ignore the cache and scan again")
    parser.add_argument("--path", help="Tekla bin directory")
    parser.add_argument("--interactive", action="store_true", help="Prompt when detection fails")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    parser.add_argument(
        "--require",
        action="store_true",
        help="Exit 2 when Tekla is not installed. The default prints a self-check and exits 0.",
    )
    args = parser.parse_args(argv)
    try:
        result = detect(force=args.force, manual_path=args.path, interactive=args.interactive)
        save_cache(result)
    except DetectionError as exc:
        if args.require or args.path or args.force:
            print("error: {0}".format(exc), file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "status": "not_installed",
                    "self_check": True,
                    "supported_years": list(SUPPORTED_YEARS),
                    "detail": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return 0
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print("TEKLA_BIN = {0}".format(result["tekla_bin"]))
        print("version = {0}".format(result["version"]))
        print("api_year = {0}".format(result.get("api_year", "unknown")))
        print("cache = {0}".format(cache_file()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
