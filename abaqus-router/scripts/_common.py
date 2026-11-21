"""Shared bootstrap for the Abaqus Skill's offline API query scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import _api_docs as docs


def connected_abaqus_version() -> str | None:
    """探测现有 Abaqus 连接，并返回其中的四位版本年份。"""
    try:
        import abaqus
        state = abaqus.connection_state(probe=True)
        if not state.get("bridge_ready"):
            return None
        match = re.search(r"\b(20\d{2})\b", str(state.get("abaqus_version") or ""))
        return match.group(1) if match else None
    except Exception:
        return None

def configure_version(version: str | None) -> Path:
    """选择显式版本或当前连接版本的 API 数据库，禁止猜测版本。"""
    selected_version = version or connected_abaqus_version()
    if not selected_version:
        supported = ", ".join(
            path.stem.removeprefix("abaqus_api_")
            for path in sorted(docs._DB_DIR.glob("abaqus_api_*.db"))
        )
        raise SystemExit(
            "Abaqus API version is required. Connect to Abaqus first or pass "
            "--version YEAR. The documentation database will not guess a "
            f"version. Bundled versions: {supported or 'none'}"
        )
    docs.set_abaqus_version(selected_version)
    db_path = docs.get_abaqus_api_db_path()
    if not db_path.exists():
        requested = (
            f"Abaqus {selected_version}" if selected_version else "the default Abaqus version"
        )
        raise SystemExit(f"No bundled API database for {requested}: {db_path}")
    return db_path
