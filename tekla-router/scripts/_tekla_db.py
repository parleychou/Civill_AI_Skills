# -*- coding: utf-8 -*-
"""Shared read-only helpers for the Tekla API query commands."""

from __future__ import annotations

import re
import json
import sqlite3
import sys
import zlib
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "references" / "tekla_api.db"
ENV_FILENAME = "tekla_env.json"

KIND_LABELS = {
    1: "namespace",
    2: "class",
    3: "interface",
    4: "structure",
    5: "enumeration",
    6: "delegate",
    7: "constructor",
    8: "method",
    9: "property",
    10: "field",
    11: "event",
    12: "operator",
}
TYPE_KINDS = (2, 3, 4, 5, 6)
MEMBER_KINDS = (7, 8, 9, 10, 11, 12)
RELATION_BASE = 1
RELATION_INTERFACE = 2
RELATION_LABELS = {RELATION_BASE: "base", RELATION_INTERFACE: "interface"}
DEFAULT_DIRECTORY_LIMIT = 50
MAX_DIRECTORY_LIMIT = 100

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def environment_path() -> Path:
    """Return the Tekla version cache in the current task workspace."""
    return Path.cwd() / ENV_FILENAME


def connect_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a plain SQLite database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def resolve_version(conn: sqlite3.Connection, value: str) -> tuple[int, int]:
    """Resolve a detected Tekla version string such as 2024.0.3 to year + bit."""
    match = re.search(r"(?<!\d)(20\d{2})(?!\d)", str(value))
    if not match:
        raise ValueError(f"无法从 Tekla 版本信息中解析年份: {value!r}")
    year = int(match.group(1))
    row = conn.execute("SELECT year, bit FROM versions WHERE year = ?", (year,)).fetchone()
    if row is None:
        supported = ", ".join(str(item[0]) for item in conn.execute("SELECT year FROM versions ORDER BY year"))
        raise ValueError(f"数据库不支持 Tekla {year}；可用版本: {supported}")
    return int(row["year"]), int(row["bit"])


def detected_version(value: str | None = None) -> str:
    """Use an explicit value or the environment cache written by the detector."""
    if value is not None and str(value).strip():
        return str(value).strip()
    path = environment_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"当前任务 workspace 中尚未检测 Tekla 版本（{path}）；"
            "请先连接 Tekla、运行 scripts/detect_tekla.py，或显式传 --version"
        ) from exc
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"Tekla 环境缓存不可读：{path}: {exc}") from exc
    for key in ("version", "api_year"):
        candidate = data.get(key)
        if candidate is not None and str(candidate).strip():
            return str(candidate)
    raise ValueError(f"Tekla 环境缓存缺少版本信息：{path}")


def resolve_query_version(
    conn: sqlite3.Connection, value: str | None = None
) -> tuple[int, int]:
    return resolve_version(conn, detected_version(value))


def add_version_argument(parser) -> None:
    parser.add_argument(
        "--version",
        help="Tekla 版本；省略时读取当前任务 workspace 中的 tekla_env.json",
    )


def add_directory_arguments(parser, *, include_contains: bool = True) -> None:
    if include_contains:
        parser.add_argument("--contains", help="只保留名称中包含该文本的目录项")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_DIRECTORY_LIMIT,
        help=f"本页最多返回多少项（1-{MAX_DIRECTORY_LIMIT}）",
    )
    parser.add_argument("--offset", type=int, default=0, help="从第几个目录项开始（从 0 计）")


def directory_window(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > MAX_DIRECTORY_LIMIT:
        raise ValueError(f"--limit 必须在 1-{MAX_DIRECTORY_LIMIT} 之间")
    if offset < 0:
        raise ValueError("--offset 不能小于 0")
    return limit, offset


def print_directory_meta(
    *,
    year: int,
    total: int,
    offset: int,
    count: int,
    parent_key: str | None = None,
) -> None:
    print(f"- query_version: Tekla {year}")
    if parent_key:
        print(f"- parent: {parent_key}")
    print(f"- total: {total}")
    if count:
        print(f"- showing: {offset + 1}-{offset + count}")
    else:
        print("- showing: 0")
    next_offset = offset + count
    if next_offset < total:
        print(f"- next_offset: {next_offset}")


def available_years(conn: sqlite3.Connection, version_mask: int) -> list[int]:
    return [
        int(row["year"])
        for row in conn.execute("SELECT year, bit FROM versions ORDER BY year")
        if version_mask & int(row["bit"])
    ]


def find_namespace(conn: sqlite3.Connection, version_bit: int, value: str) -> sqlite3.Row:
    key = value if value.startswith("N:") else f"N:{value}"
    row = conn.execute(
        """
        SELECT s.*
        FROM symbols s
        WHERE s.symbol_key = ? AND s.kind = 1
          AND EXISTS (
              SELECT 1 FROM revisions r
              WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
          )
        """,
        (key, version_bit),
    ).fetchone()
    if row is None:
        raise LookupError(f"当前 Tekla 版本中没有命名空间: {value}")
    return row


def find_type(conn: sqlite3.Connection, version_bit: int, value: str) -> sqlite3.Row:
    if value.startswith("T:"):
        condition = "s.symbol_key = ?"
        parameter = value
    elif "." in value:
        condition = "s.symbol_key = ?"
        parameter = f"T:{value}"
    else:
        condition = "s.name = ? COLLATE NOCASE"
        parameter = value

    placeholders = ",".join("?" for _ in TYPE_KINDS)
    rows = conn.execute(
        f"""
        SELECT s.*
        FROM symbols s
        WHERE {condition}
          AND s.kind IN ({placeholders})
          AND EXISTS (
              SELECT 1 FROM revisions r
              WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
          )
        ORDER BY s.symbol_key
        """,
        (parameter, *TYPE_KINDS, version_bit),
    ).fetchall()
    if not rows:
        raise LookupError(f"当前 Tekla 版本中没有类型: {value}")
    if len(rows) > 1:
        choices = "\n".join(f"- {row['symbol_key']}" for row in rows[:20])
        raise LookupError(f"类型名 {value!r} 不唯一，请使用完整名称:\n{choices}")
    return rows[0]


def find_container(conn: sqlite3.Connection, version_bit: int, value: str) -> sqlite3.Row:
    """Resolve a namespace or type that can own direct child types."""
    raw = value.strip()
    if not raw:
        raise ValueError("父节点不能为空")

    placeholders = ",".join("?" for _ in TYPE_KINDS)
    if raw.startswith("N:") or raw.startswith("T:"):
        rows = conn.execute(
            f"""
            SELECT s.*
            FROM symbols s
            WHERE s.symbol_key = ?
              AND (s.kind = 1 OR s.kind IN ({placeholders}))
              AND EXISTS (
                  SELECT 1 FROM revisions r
                  WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
              )
            """,
            (raw, *TYPE_KINDS, version_bit),
        ).fetchall()
    else:
        rows = conn.execute(
            f"""
            SELECT s.*
            FROM symbols s
            WHERE (
                    (s.kind = 1 AND s.symbol_key = ?)
                 OR (s.kind IN ({placeholders}) AND (s.symbol_key = ? OR s.name = ? COLLATE NOCASE))
                  )
              AND EXISTS (
                  SELECT 1 FROM revisions r
                  WHERE r.symbol_id = s.id AND (r.version_mask & ?) != 0
              )
            ORDER BY s.symbol_key
            """,
            (f"N:{raw}", *TYPE_KINDS, f"T:{raw}", raw, version_bit),
        ).fetchall()

    if not rows:
        raise LookupError(f"当前 Tekla 版本中没有命名空间或类型父节点: {value}")
    if len(rows) > 1:
        choices = "\n".join(f"- {row['symbol_key']}" for row in rows[:20])
        raise LookupError(f"父节点 {value!r} 不唯一，请使用完整 N:/T: 标识:\n{choices}")
    return rows[0]


def find_active_symbol(conn: sqlite3.Connection, version_bit: int, symbol_key: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT s.*, r.id AS revision_id, r.version_mask, r.summary, r.detail_blob
        FROM symbols s
        JOIN revisions r ON r.symbol_id = s.id
        WHERE s.symbol_key = ? AND (r.version_mask & ?) != 0
        """,
        (symbol_key, version_bit),
    ).fetchone()


def detail_text(detail_blob: bytes) -> str:
    return zlib.decompress(detail_blob).decode("utf-8")


def fts_query(value: str) -> str:
    tokens = re.findall(r"[^\W_]+", value, flags=re.UNICODE)
    if not tokens:
        raise ValueError("搜索词中没有可检索字符")
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens)


def kind_from_name(value: str | None) -> int | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    for kind in MEMBER_KINDS:
        label = KIND_LABELS[kind]
        if normalized == label:
            return kind
    choices = ", ".join(KIND_LABELS[kind] for kind in MEMBER_KINDS)
    raise ValueError(f"未知成员类型 {value!r}；可用值: {choices}")


def type_kind_from_name(value: str) -> int:
    normalized = value.strip().lower()
    aliases = {"enum": "enumeration", "struct": "structure"}
    normalized = aliases.get(normalized, normalized)
    for kind in TYPE_KINDS:
        if normalized == KIND_LABELS[kind]:
            return kind
    choices = ", ".join(KIND_LABELS[kind] for kind in TYPE_KINDS)
    raise ValueError(f"未知类型种类 {value!r}；可用值: {choices}")


def compact_member_signature(type_symbol_key: str, member_symbol_key: str) -> str:
    """Render a directory-only signature from an exact Help ID."""
    member_body = member_symbol_key.split(":", 1)[1]
    type_body = type_symbol_key.split(":", 1)[1]
    prefix = f"{type_body}."
    if member_body.startswith(prefix):
        member_body = member_body[len(prefix) :]
    return member_body.replace(",", ", ")


def run_cli(main) -> int:
    """Render expected lookup/version failures without an implementation traceback."""
    try:
        result = main()
    except (LookupError, ValueError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    return int(result or 0)
