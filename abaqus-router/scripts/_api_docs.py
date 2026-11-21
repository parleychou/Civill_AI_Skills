"""Deterministic navigation of schema-v6 Abaqus API documentation.

``functions.object_name`` preserves the source documentation heading.  Runtime
queries use the separate ``callables`` table, whose canonical identity is the
actual receiver and method, for example ``Part.BaseShellRevolve``.
Documented attributes and repositories use ``object_members`` with identities
such as ``Part.cells`` and ``Mdb.models``.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


_BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

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
  # noqa: E402


_DB_DIR = Path(__file__).parent.parent / "references"
_current_version: str | None = None
_MAX_LIMIT = 100
_METHOD_DETAIL_LIMIT = 12_000
_CALLABLE_ROWS_CACHE: dict[str, list[sqlite3.Row]] = {}
_OBJECT_MEMBER_ROWS_CACHE: dict[str, list[sqlite3.Row]] = {}
_CALLABLE_SELECT = """
SELECT f.*,
       parent.name || '/' || f.object_name AS object_path,
       parent.name AS module_name,
       c.receiver_name,
       c.canonical_call,
       c.access_path AS callable_access_path,
       c.receiver_source
FROM callables c
JOIN functions f ON f.id = c.function_id
JOIN modules parent ON parent.id = f.module_id
"""
_OBJECT_MEMBER_SELECT = """
SELECT om.*,
       parent.name AS module_name,
       om.object_name || '.' || om.name AS canonical_member
FROM object_members om
JOIN modules parent ON parent.id = om.module_id
"""


def set_abaqus_version(version: str | None) -> None:
    """设置后续查询使用的 Abaqus 版本年份。"""
    global _current_version
    _current_version = version


def _get_db_path() -> Path:
    """解析当前版本的数据库路径；未指定时选择最高版本的 v6 数据库。"""
    if _current_version:
        return _DB_DIR / f"abaqus_api_{_current_version}.db"
    candidates = sorted(_DB_DIR.glob("abaqus_api_*.db"), reverse=True)
    for candidate in candidates:
        try:
            conn = connect_db(candidate)
            version = conn.execute(
                "SELECT value FROM db_meta WHERE key = 'schema_version'"
            ).fetchone()
            conn.close()
        except Exception:
            continue
        if version and version[0] == "6":
            return candidate
    return _DB_DIR / "abaqus_api_2024.db"


def get_abaqus_api_db_path() -> Path:
    """返回当前选中的 Abaqus API 数据库路径。"""
    return _get_db_path()


def _get_db() -> sqlite3.Connection:
    """打开 API 数据库并校验其表结构和 schema 版本。"""
    # connect_db handles plaintext development DBs and encrypted packaged DBs.
    conn = connect_db(_get_db_path())
    conn.row_factory = sqlite3.Row
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"modules", "functions", "callables", "object_members"}.issubset(tables):
        conn.close()
        raise RuntimeError(
            f"Unsupported Abaqus API database schema at {_get_db_path()}; "
            "rebuild it with scripts/abaqus_api_docs/build_versioned_db.py"
        )
    module_columns = {row[1] for row in conn.execute("PRAGMA table_info(modules)")}
    function_columns = {row[1] for row in conn.execute("PRAGMA table_info(functions)")}
    schema = conn.execute("SELECT value FROM db_meta WHERE key = 'schema_version'").fetchone()
    if (
        not schema
        or schema[0] != "6"
        or module_columns != {"id", "name", "path", "description"}
        or "object_name" not in function_columns
    ):
        conn.close()
        raise RuntimeError(
            f"Unsupported Abaqus API database schema at {_get_db_path()}; "
            "schema v6 with callable and object-member contracts is required"
        )
    return conn


def _bounded_limit(limit: int) -> int:
    """把调用方给出的结果数量限制在安全区间内。"""
    return max(1, min(int(limit), _MAX_LIMIT))


def _preview(content: str | None, max_len: int = 500) -> str:
    """清理文本首尾空白，并生成不超过指定长度的预览。"""
    if not content:
        return ""
    value = content.strip()
    return value if len(value) <= max_len else value[:max_len].rstrip() + "..."


def _canonical(value: str | None) -> str:
    """统一大小写、空白和空参数后缀，便于宽松比较名称。"""
    value = (value or "").strip().casefold()
    value = re.sub(r"\(\s*\.\.\.\s*\)\s*$", "", value)
    value = re.sub(r"\(\s*\)\s*$", "", value)
    return re.sub(r"\s+", " ", value)


def _purpose_from_content(content: str | None, max_len: int = 220) -> str:
    """从原始文档正文中提取第一段有效用途说明。"""
    if not content:
        return ""
    text = content.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = re.sub(r"^#{3,5}\s+[^\n]+\n+", "", text.strip())
    for paragraph in re.split(r"\n\s*\n", text):
        compact = re.sub(r"\s+", " ", paragraph).strip()
        if compact and not compact.startswith("**"):
            return _preview(compact, max_len)
    return ""


def _row_purpose(row: sqlite3.Row, max_len: int = 220) -> str:
    """优先返回结构化用途字段，缺失时从正文回退提取。"""
    return _preview(row["purpose"], max_len) or _purpose_from_content(row["content"], max_len)


def _json_list(value: str | None) -> list[Any]:
    """把数据库中的 JSON 字符串安全解析为列表，非法值返回空列表。"""
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _all_callable_rows() -> list[sqlite3.Row]:
    """读取当前版本全部可调用契约，并按数据库路径进行进程内缓存。"""
    cache_key = str(_get_db_path().resolve())
    cached = _CALLABLE_ROWS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    conn = _get_db()
    try:
        rows = conn.execute(
            _CALLABLE_SELECT + " ORDER BY c.canonical_call, f.module_priority, f.variant"
        ).fetchall()
    finally:
        conn.close()
    _CALLABLE_ROWS_CACHE[cache_key] = rows
    return rows


def _all_object_member_rows() -> list[sqlite3.Row]:
    """读取当前版本全部属性和 repository 契约，并进行进程内缓存。"""
    cache_key = str(_get_db_path().resolve())
    cached = _OBJECT_MEMBER_ROWS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    conn = _get_db()
    try:
        rows = conn.execute(
            _OBJECT_MEMBER_SELECT + " ORDER BY om.object_name, om.name, parent.name, om.source_url"
        ).fetchall()
    finally:
        conn.close()
    _OBJECT_MEMBER_ROWS_CACHE[cache_key] = rows
    return rows


def _render_arguments(value: str | None) -> list[str]:
    """把数据库中的参数 JSON 渲染为稳定的 Markdown 文本行。"""
    items = _json_list(value)
    if not items:
        return ["None."]
    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        if lines:
            lines.append("")
        lines.append(str(item["name"]))
        lines.append("")
        lines.append(str(item.get("description") or item.get("type") or ""))
    return lines or ["None."]


def _render_method_detail(
    row: sqlite3.Row,
    access_paths: list[str] | None = None,
) -> str:
    """将方法记录渲染为不依赖官方网页布局的稳定契约格式。"""
    parts = [f"##### {row['syntax']}"]
    if (
        "documented_name" in row.keys()
        and row["documented_name"]
        and row["documented_name"] != row["name"]
    ):
        parts.extend(
            (
                "",
                "**Documented heading**",
                str(row["documented_name"]),
            )
        )
    if row["purpose"]:
        parts.extend(("", row["purpose"]))
    parts.extend(("", "**Path**"))
    paths = _json_list(row["access_paths"]) if access_paths is None else access_paths
    if paths:
        parts.extend(str(path) for path in paths)
    else:
        parts.append("None.")
    parts.extend(("", "**Required arguments**", ""))
    parts.extend(_render_arguments(row["required_arguments"]))
    parts.extend(("", "**Optional arguments**", ""))
    parts.extend(_render_arguments(row["optional_arguments"]))
    parts.extend(("", "**Return value**", "", row["returns"] or "None."))
    parts.extend(("", "**Exceptions**", "", row["exceptions"] or "None."))
    if row["notes"]:
        parts.extend(("", "**Table data**", "", row["notes"]))
    return "\n".join(parts)


def _normalize_call(value: str) -> str:
    """移除规范调用末尾的空参数标记和全部空白。"""
    value = value.strip()
    value = re.sub(r"\(\s*\.\.\.\s*\)\s*$", "", value)
    value = re.sub(r"\(\s*\)\s*$", "", value)
    return re.sub(r"\s+", "", value)


_INTENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
}
_GENERIC_ACTIONS = {
    "add",
    "access",
    "build",
    "construct",
    "create",
    "draw",
    "generate",
    "get",
    "make",
    "query",
    "read",
    "return",
    "use",
}
_CHINESE_INTENT_TERMS = {
    "三维": "3d",
    "体积": "volume",
    "创建": "create",
    "可变形": "deformable",
    "实体": "solid",
    "建立": "create",
    "拉伸": "extrude",
    "查询": "query",
    "矩形": "rectangle",
    "绘制": "draw",
    "草图": "sketch",
    "部件": "part",
    "属性": "attribute",
    "仓库": "repository",
    "模型": "model",
    "单元": "cells",
}
_INTENT_ALIASES = {
    "3d": {"3d", "three", "dimensional", "dimensionality", "three_d"},
    "cell": {"cell", "cells"},
    "cells": {"cell", "cells"},
    "construct": {"construct", "constructs", "create", "creates"},
    "create": {"add", "construct", "constructs", "create", "creates", "new"},
    "deformable": {"deformable", "deformable_body"},
    "draw": {"construct", "constructs", "create", "creates", "draw"},
    "extrude": {"extrude", "extruded", "extruding", "extrusion"},
    "part": {"part", "parts"},
    "parts": {"part", "parts"},
    "model": {"model", "models"},
    "models": {"model", "models"},
    "repository": {"repositories", "repository"},
    "attribute": {"attribute", "attributes", "member", "members"},
    "rectangle": {"rectangle", "rectangular"},
    "sketch": {"constrained", "constrainedsketch", "sketch"},
    "solid": {"solid", "solids"},
    "volume": {"volume", "volumetric"},
}


def _split_search_tokens(value: str | None) -> set[str]:
    """将中文术语、英文描述和 CamelCase 标识符拆成意图匹配词元。"""
    text = value or ""
    for chinese, english in _CHINESE_INTENT_TERMS.items():
        text = text.replace(chinese, f" {english} ")
    text = re.sub(r"\b3\s*d\b", " 3d ", text, flags=re.IGNORECASE)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    text = text.casefold().replace("three-dimensional", "3d")
    return {
        token for token in re.findall(r"3d|[a-z][a-z0-9_]*", text) if token not in _INTENT_STOPWORDS
    }


def _intent_groups(query: str) -> list[tuple[str, set[str], bool]]:
    """把查询词元扩展为“原词、别名集合、是否通用动作”的分组。"""
    groups: list[tuple[str, set[str], bool]] = []
    for token in _split_search_tokens(query):
        aliases = set(_INTENT_ALIASES.get(token, {token}))
        groups.append((token, aliases, token in _GENERIC_ACTIONS))
    return sorted(groups, key=lambda item: (item[2], item[0]))


def _field_match(aliases: set[str], tokens: set[str]) -> bool:
    """判断一组意图别名是否命中目标字段词元。"""
    return bool(aliases & tokens)


def _callable_intent_score(
    row: sqlite3.Row,
    groups: list[tuple[str, set[str], bool]],
) -> tuple[float, list[str], int]:
    """计算一个方法变体的意图匹配分数，并返回命中词及有效命中数。

    方法名和接收对象的权重大于普通正文，避免通用动作词把无关 API 排到前面。
    """
    method_tokens = _split_search_tokens(row["name"])
    receiver_tokens = _split_search_tokens(row["receiver_name"])
    canonical_tokens = _split_search_tokens(row["canonical_call"])
    purpose_tokens = _split_search_tokens(row["purpose"])
    content_tokens = _split_search_tokens(row["content"])
    matched: list[str] = []
    meaningful = sum(not generic for _token, _aliases, generic in groups)
    score = 0.0
    meaningful_matched = 0
    generic_matched = 0
    for token, aliases, generic in groups:
        token_score = 0.0
        if _field_match(aliases, method_tokens):
            token_score = 12.0
        elif _field_match(aliases, receiver_tokens):
            # 简单接收对象名（如 Cell、Part、Model）是强证据；复合名称也加分，
            # 但不能仅因包含多个查询词就压过真正的构造方法。
            token_score = 15.0 if len(receiver_tokens) == 1 and token in receiver_tokens else 10.0
        elif _field_match(aliases, canonical_tokens):
            token_score = 6.0
        elif _field_match(aliases, purpose_tokens):
            token_score = 4.0
        elif _field_match(aliases, content_tokens):
            token_score = 1.0
        if not token_score:
            continue
        matched.append(token)
        if generic:
            generic_matched += 1
            token_score *= 0.5
        else:
            meaningful_matched += 1
        score += token_score
    if any(generic for _token, _aliases, generic in groups) and not generic_matched:
        score -= 10.0
    if meaningful and meaningful_matched == meaningful:
        score += 10.0
    elif meaningful_matched:
        score += 2.0 * meaningful_matched
    return score, matched, meaningful_matched


def find_callable_candidates(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """按操作意图检索真实规范调用，返回供模型判断的 Top-K 候选。

    本函数不自动替模型选定 API，而是保留接收对象、重载和契约证据。
    """
    clean = query.strip()
    if not clean:
        return []
    groups = _intent_groups(clean)
    if not groups:
        return []
    rows = _all_callable_rows()

    aggregated: dict[str, dict[str, Any]] = {}
    for row in rows:
        score, matched, meaningful_matched = _callable_intent_score(row, groups)
        if score <= 0:
            continue
        key = str(row["canonical_call"]).casefold()
        candidate = aggregated.get(key)
        if candidate is None:
            candidate = {
                "canonical_call": str(row["canonical_call"]),
                "receiver_name": str(row["receiver_name"]),
                "purpose": _row_purpose(row),
                "score": score,
                "matched_terms": matched,
                "meaningful_matched": meaningful_matched,
                "variant_count": 1,
                "_variant_keys": {(row["source_url"], row["object_name"], int(row["variant"]))},
            }
            aggregated[key] = candidate
            continue
        variant_key = (row["source_url"], row["object_name"], int(row["variant"]))
        candidate["_variant_keys"].add(variant_key)
        candidate["variant_count"] = len(candidate["_variant_keys"])
        if score > candidate["score"]:
            candidate.update(
                purpose=_row_purpose(row),
                score=score,
                matched_terms=matched,
                meaningful_matched=meaningful_matched,
            )

    meaningful_total = sum(not generic for _token, _aliases, generic in groups)
    ranked = sorted(
        aggregated.values(),
        key=lambda item: (
            -int(item["meaningful_matched"] == meaningful_total),
            -float(item["score"]),
            str(item["canonical_call"]).casefold(),
        ),
    )[: _bounded_limit(limit)]
    for candidate in ranked:
        candidate.pop("_variant_keys", None)
        coverage = int(candidate["meaningful_matched"])
        if meaningful_total and coverage == meaningful_total:
            candidate["confidence"] = "HIGH"
        elif coverage >= max(1, meaningful_total - 1):
            candidate["confidence"] = "MEDIUM"
        else:
            candidate["confidence"] = "LOW"
    return ranked


def _member_intent_score(
    row: sqlite3.Row,
    groups: list[tuple[str, set[str], bool]],
    query: str,
) -> tuple[float, list[str], int]:
    """计算对象成员的意图匹配分数，并返回命中词及有效命中数。"""
    member_tokens = _split_search_tokens(row["name"])
    owner_tokens = _split_search_tokens(row["object_name"])
    canonical_tokens = _split_search_tokens(row["canonical_member"])
    value_type_tokens = _split_search_tokens(row["value_type"])
    description_tokens = _split_search_tokens(row["description"])
    kind_tokens = _split_search_tokens(row["member_kind"])
    matched: list[str] = []
    meaningful = sum(not generic for _token, _aliases, generic in groups)
    meaningful_matched = 0
    generic_matched = 0
    score = 0.0
    for token, aliases, generic in groups:
        token_score = 0.0
        if _field_match(aliases, member_tokens):
            token_score = 14.0
        elif _field_match(aliases, owner_tokens):
            token_score = 15.0
        elif _field_match(aliases, kind_tokens):
            token_score = 10.0
        elif _field_match(aliases, canonical_tokens):
            token_score = 7.0
        elif _field_match(aliases, value_type_tokens):
            token_score = 6.0
        elif _field_match(aliases, description_tokens):
            token_score = 2.0
        if not token_score:
            continue
        matched.append(token)
        if generic:
            generic_matched += 1
            token_score *= 0.5
        else:
            meaningful_matched += 1
        score += token_score
    if any(generic for _token, _aliases, generic in groups) and not generic_matched:
        score -= 8.0
    if meaningful and meaningful_matched == meaningful:
        score += 10.0
    elif meaningful_matched:
        score += 2.0 * meaningful_matched
    normalized_query = re.sub(r"\s+", "", query).casefold()
    normalized_member = str(row["canonical_member"]).casefold()
    if normalized_query == normalized_member:
        score += 30.0
    return score, matched, meaningful_matched


def find_object_member_candidates(
    query: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """按意图检索文档中存在的对象属性和 repository 成员。"""
    clean = query.strip()
    if not clean:
        return []
    groups = _intent_groups(clean)
    if not groups:
        return []
    aggregated: dict[str, dict[str, Any]] = {}
    for row in _all_object_member_rows():
        score, matched, meaningful_matched = _member_intent_score(
            row,
            groups,
            clean,
        )
        if score <= 0:
            continue
        key = str(row["canonical_member"]).casefold()
        candidate = aggregated.get(key)
        if candidate is None or score > candidate["score"]:
            aggregated[key] = {
                "canonical_member": str(row["canonical_member"]),
                "object_name": str(row["object_name"]),
                "name": str(row["name"]),
                "member_kind": str(row["member_kind"]),
                "value_type": str(row["value_type"] or ""),
                "description": str(row["description"] or ""),
                "access_paths": _json_list(row["access_paths"]),
                "score": score,
                "matched_terms": matched,
                "meaningful_matched": meaningful_matched,
            }
    meaningful_total = sum(not generic for _token, _aliases, generic in groups)
    ranked = sorted(
        aggregated.values(),
        key=lambda item: (
            -int(item["meaningful_matched"] == meaningful_total),
            -float(item["score"]),
            str(item["canonical_member"]).casefold(),
        ),
    )[: _bounded_limit(limit)]
    for candidate in ranked:
        coverage = int(candidate["meaningful_matched"])
        if meaningful_total and coverage == meaningful_total:
            candidate["confidence"] = "HIGH"
        elif coverage >= max(1, meaningful_total - 1):
            candidate["confidence"] = "MEDIUM"
        else:
            candidate["confidence"] = "LOW"
    return ranked


def get_object_member_contracts(canonical_member: str) -> list[dict[str, Any]]:
    """返回一个精确 ``Object.member`` 标识对应的结构化成员契约。"""
    clean = _normalize_call(canonical_member)
    if not clean or "." not in clean:
        return []
    rows = [
        row
        for row in _all_object_member_rows()
        if str(row["canonical_member"]).casefold() == clean.casefold()
    ]
    contracts: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        key = (str(row["source_url"]), str(row["object_name"]), str(row["name"]))
        if key in seen:
            continue
        seen.add(key)
        contracts.append(
            {
                "canonical_member": str(row["canonical_member"]),
                "module_name": str(row["module_name"]),
                "object_name": str(row["object_name"]),
                "name": str(row["name"]),
                "member_kind": str(row["member_kind"]),
                "value_type": str(row["value_type"] or ""),
                "description": str(row["description"] or ""),
                "access_paths": _json_list(row["access_paths"]),
                "source_kind": str(row["source_kind"]),
            }
        )
    return contracts


def find_api_candidates(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """合并排序当前版本中的方法、属性和 repository 候选。"""
    candidates: list[dict[str, Any]] = []
    for callable_candidate in find_callable_candidates(query, limit=limit * 2):
        item = dict(callable_candidate)
        item["symbol_kind"] = "method"
        item["canonical_symbol"] = item["canonical_call"]
        candidates.append(item)
    for member_candidate in find_object_member_candidates(query, limit=limit * 2):
        item = dict(member_candidate)
        item["symbol_kind"] = item["member_kind"]
        item["canonical_symbol"] = item["canonical_member"]
        candidates.append(item)
    confidence_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(
        candidates,
        key=lambda item: (
            confidence_rank.get(str(item.get("confidence")), 3),
            -float(item["score"]),
            str(item["canonical_symbol"]).casefold(),
        ),
    )[: _bounded_limit(limit)]


def get_object_member_info(canonical_member: str) -> str:
    """将一个精确 ``Object.member`` 属性或 repository 契约渲染为文本。"""
    contracts = get_object_member_contracts(canonical_member)
    if not contracts:
        callable_contracts = get_callable_contracts(canonical_member)
        if callable_contracts:
            canonical_call = callable_contracts[0]["canonical_call"]
            return (
                f"'{canonical_member}' is a callable method, not an object member. "
                "Use scripts/get_api_detail.py "
                f"--call {canonical_call} for the exact contract."
            )
        return (
            f"Object member '{canonical_member}' not found. Use "
            'scripts/get_api_detail.py --search-members "object member words".'
        )
    contract = contracts[0]
    parts = [f"# {contract['canonical_member']}"]
    parts.append(f"Kind: `{contract['member_kind']}`")
    if contract["value_type"]:
        parts.append(f"Value type: `{contract['value_type']}`")
    if contract["description"]:
        parts.append(f"Description: {_preview(contract['description'], 1600)}")
    if contract["access_paths"]:
        parts.append("Access paths:")
        parts.extend(f"- `{path}`" for path in contract["access_paths"])
    return "\n".join(parts)


def search_abaqus_object_members(query: str, limit: int = 10) -> str:
    """按对象或成员用途检索属性和 repository，并渲染候选列表。"""
    candidates = find_object_member_candidates(query, limit=limit)
    if not candidates:
        return f"No documented Abaqus object members match '{query}'."
    parts = [f"Abaqus object members for '{query}' ({len(candidates)} shown):"]
    for index, candidate in enumerate(candidates, 1):
        line = (
            f"[{index}] {candidate['canonical_member']} "
            f"[{candidate['member_kind']}; {candidate['confidence']}; matched: "
            f"{', '.join(candidate['matched_terms']) or 'none'}]"
        )
        if candidate["value_type"]:
            line += f" -> {candidate['value_type']}"
        if candidate["description"]:
            line += f" — {_preview(candidate['description'], 220)}"
        parts.append(line)
    parts.append(
        "\nNext: call scripts/get_api_detail.py --member Object.member for the exact contract."
    )
    return "\n".join(parts)


def get_callable_contracts(canonical_call: str) -> list[dict[str, Any]]:
    """返回一个代码侧规范调用的全部结构化重载契约。"""
    clean = _normalize_call(canonical_call)
    if not clean or "." not in clean:
        return []
    rows = [
        row
        for row in _all_callable_rows()
        if str(row["canonical_call"]).casefold() == clean.casefold()
    ]
    rows.sort(
        key=lambda row: (
            int(row["module_priority"]),
            int(row["variant"]),
            str(row["module_name"]),
            str(row["object_name"]),
        )
    )
    contracts: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()
    for row in rows:
        key = (row["source_url"], row["object_name"], int(row["variant"]))
        if key in seen:
            continue
        seen.add(key)
        contracts.append(
            {
                "canonical_call": str(row["canonical_call"]),
                "receiver_name": str(row["receiver_name"]),
                "module_name": str(row["module_name"]),
                "object_name": str(row["object_name"]),
                "syntax": str(row["syntax"]),
                "purpose": _row_purpose(row),
                "required_arguments": _json_list(row["required_arguments"]),
                "optional_arguments": _json_list(row["optional_arguments"]),
                "returns": str(row["returns"] or ""),
                "access_path": str(row["callable_access_path"] or ""),
            }
        )
    return contracts


def search_abaqus_callables(query: str, limit: int = 10) -> str:
    """按操作意图检索 API，只返回真实的 ``Receiver.method`` 标识。"""
    clean = query.strip()
    if not clean:
        return "Please provide an operation or API intent."
    candidates = find_callable_candidates(clean, limit=limit)
    if not candidates:
        return f"No canonical Abaqus calls match '{query}'."
    parts = [f"Canonical Abaqus calls for '{query}' ({len(candidates)} shown):"]
    for index, candidate in enumerate(candidates, 1):
        line = (
            f"[{index}] {candidate['canonical_call']} "
            f"[{candidate['confidence']}; matched: "
            f"{', '.join(candidate['matched_terms']) or 'none'}]"
        )
        if candidate["purpose"]:
            line += f" — {candidate['purpose']}"
        parts.append(line)
    parts.append(
        "\nNext: call scripts/get_api_detail.py --call Receiver.method for "
        "the exact contract. Do not query documentation object names."
    )
    return "\n".join(parts)


def get_callable_info(canonical_call: str) -> str:
    """按代码侧 ``Receiver.method`` 名称渲染精确方法契约。"""
    clean = _normalize_call(canonical_call)
    if not clean or "." not in clean:
        return "Use a canonical call such as Part.BaseShellRevolve."
    conn = _get_db()
    try:
        rows = conn.execute(
            _CALLABLE_SELECT
            + " WHERE lower(c.canonical_call) = lower(?) "
            + "ORDER BY f.module_priority, f.variant, parent.name, f.object_name",
            (clean,),
        ).fetchall()
        if not rows:
            partial = conn.execute(
                "SELECT DISTINCT canonical_call FROM callables "
                "WHERE lower(canonical_call) LIKE lower(?) "
                "ORDER BY canonical_call LIMIT 10",
                (f"%{clean}%",),
            ).fetchall()
            if partial:
                choices = "\n".join(f"- {row[0]}" for row in partial)
                return (
                    f"Canonical call '{canonical_call}' not found. "
                    f"Choose one exact call:\n{choices}"
                )
            return (
                f"Canonical call '{canonical_call}' not found. Use "
                'scripts/get_api_detail.py --search-calls "operation words".'
            )

        # Import-module aliases can point to the same source contract.  Keep
        # real overloads, but avoid repeating identical documentation rows.
        unique: list[sqlite3.Row] = []
        seen: set[tuple[str, str, int]] = set()
        for row in rows:
            key = (
                row["source_url"],
                row["object_name"],
                int(row["variant"]),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)

        parts = [f"# {unique[0]['canonical_call']}"]
        for index, row in enumerate(unique, 1):
            if len(unique) > 1:
                parts.append(f"\n## Variant {index}")
            parts.extend(
                (
                    f"\nReceiver: `{row['receiver_name']}`",
                    f"Source documentation: `{row['module_name']} > {row['object_name']}`",
                    _render_method_detail(
                        row,
                        [row["callable_access_path"]] if row["callable_access_path"] else [],
                    ),
                )
            )
        return _preview("\n\n".join(parts), _METHOD_DETAIL_LIMIT)
    finally:
        conn.close()
