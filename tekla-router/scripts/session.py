# -*- coding: utf-8 -*-
"""Attach this worker to a Tekla Structures process that is already open.

Assemblies stay loaded for the life of the worker. A second Tekla year cannot
be loaded in the same process. Callers should reuse a live model handle instead
of constructing another session.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
_LOCATOR_SPEC = importlib.util.spec_from_file_location(
    "_tekla_install_locator", SCRIPT_DIR / "find_install.py"
)
if _LOCATOR_SPEC is None or _LOCATOR_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("The Tekla install locator could not be initialized.")
_locator = importlib.util.module_from_spec(_LOCATOR_SPEC)
sys.modules.setdefault(_LOCATOR_SPEC.name, _locator)
_LOCATOR_SPEC.loader.exec_module(_locator)


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
REQUIRED_ASSEMBLIES = {"Tekla.Structures.dll", "Tekla.Structures.Model.dll"}

_loaded_bin: str | None = None
_dll_handles: list[object] = []
_dll_paths: set[str] = set()
_loaded_assemblies: dict[str, str] = {}


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
    return _locator.detect(force=force, manual_path=bin_path)


def supported_years() -> tuple[int, ...]:
    return _locator.SUPPORTED_YEARS


def _search_dirs(bin_dir: str) -> tuple[Path, ...]:
    return _locator.assembly_dirs(bin_dir)


def _prepare_search(bin_dir: str) -> tuple[Path, ...]:
    directories = _search_dirs(bin_dir)
    for directory in reversed(directories):
        value = str(directory)
        if value not in sys.path:
            sys.path.insert(0, value)
    if hasattr(os, "add_dll_directory"):
        for directory in directories:
            normalized = _normal(directory)
            if normalized not in _dll_paths:
                _dll_handles.append(os.add_dll_directory(str(directory)))
                _dll_paths.add(normalized)
    return directories


def _start_clr():
    try:
        from pythonnet import load

        try:
            load("netfx")
        except RuntimeError as exc:
            text = str(exc).lower()
            if "already" not in text and "initialized" not in text:
                raise
        import clr
    except Exception as exc:
        raise RuntimeError("Could not initialize pythonnet / .NET Framework: {0}".format(exc)) from exc
    return clr


def load_assemblies(bin_dir: str) -> dict[str, str]:
    """Load the annual Tekla assemblies once in this worker."""
    global _loaded_bin
    normalized = _normal(bin_dir)
    if _loaded_bin is not None and _normal(_loaded_bin) != normalized:
        raise RuntimeError(
            "This worker already loaded a different Tekla CLR version, and .NET assemblies cannot be unloaded in-process. "
            "Leave only the target Tekla release running, start a new task, and connect again."
        )
    directories = _prepare_search(bin_dir)
    clr = _start_clr()
    for name in ASSEMBLIES:
        if name in _loaded_assemblies:
            continue
        path = next((folder / name for folder in directories if (folder / name).is_file()), None)
        if path is None:
            if name in REQUIRED_ASSEMBLIES:
                raise RuntimeError("Tekla installation is missing required assembly: {0}".format(name))
            continue
        try:
            clr.AddReference(str(path))
        except Exception as exc:
            raise RuntimeError("Failed to load Tekla assembly {0}: {1}".format(path, exc)) from exc
        _loaded_assemblies[name] = str(path)
    _loaded_bin = str(Path(bin_dir).resolve())
    return dict(_loaded_assemblies)


def _year_in_version(version: str) -> int:
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", version)
    if not match:
        raise RuntimeError("Could not read a release year from the Tekla version string: {0!r}".format(version))
    return int(match.group(1))


def connect_tekla(*, force_detect: bool = False, bin_path: str | None = None) -> TeklaSession:
    """Connect to the Tekla instance that is already running in this worker."""
    environment = detect_tekla(force=force_detect, bin_path=bin_path)
    assemblies = load_assemblies(environment["tekla_bin"])
    try:
        from Tekla.Structures import TeklaStructuresInfo
        from Tekla.Structures.Model import Model
    except Exception as exc:
        raise RuntimeError("Could not import Tekla namespaces: {0}".format(exc)) from exc

    model = Model()
    if not model.GetConnectionStatus():
        raise RuntimeError("Tekla is not connected. Start Tekla Structures and open a model, then retry.")

    program_version = str(TeklaStructuresInfo.GetCurrentProgramVersion())
    api_year = _year_in_version(program_version)
    years = supported_years()
    if api_year not in years:
        available = ", ".join(str(year) for year in years)
        raise RuntimeError(
            "This skill supports Tekla Structures releases {0}. "
            "The connected release is {1}. "
            "Look up members for other releases at https://developer.tekla.com/tekla-structures/api-reference.".format(
                available, api_year
            )
        )
    detected_year = environment.get("api_year")
    if detected_year is not None and int(detected_year) != api_year:
        raise RuntimeError(
            "Assembly path year {0} does not match the connected instance {1}. "
            "Close the other Tekla release and retry in a new task.".format(
                detected_year, program_version
            )
        )
    environment["version"] = program_version
    environment["api_year"] = api_year
    _locator.save_cache(environment)
    return TeklaSession(
        model=model,
        tekla_bin=environment["tekla_bin"],
        program_version=program_version,
        api_year=api_year,
        loaded_assemblies=tuple(assemblies),
    )


if __name__ == "__main__":
    import json

    status_info = {
        "status": "ready",
        "self_check": True,
        "module": "session",
        "supported_years": list(supported_years()),
        "assemblies": list(ASSEMBLIES),
        "required_assemblies": list(REQUIRED_ASSEMBLIES),
        "description": "Tekla Open API CLR session manager and assembly loader.",
    }
    print(json.dumps(status_info, ensure_ascii=False))

