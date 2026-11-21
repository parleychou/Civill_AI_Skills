"""Build grounded Abaqus API context from unknown operations and exact symbols.

This is a retrieval tool, not an automatic API translator or validator.  It
returns real Top-K methods/object members and preserves every documented
overload so the LLM can make the final selection with evidence before writing
code.
"""

from __future__ import annotations

import argparse
import re
from typing import Any

from _common import configure_version, docs


def _compact(value: str, limit: int = 220) -> str:
    """压缩连续空白，并按字符上限截断说明文本。"""
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def _argument_lines(items: list[Any], *, descriptions: bool) -> list[str]:
    """把参数契约转换为 Markdown 列表，可选择是否携带参数说明。"""
    if not items:
        return ["- None"]
    lines: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        name = str(item["name"])
        description = _compact(
            str(item.get("description") or item.get("type") or ""),
            180,
        )
        if descriptions and description:
            lines.append(f"- `{name}` — {description}")
        else:
            lines.append(f"- `{name}`")
    return lines or ["- None"]


def _render_contracts(canonical_call: str) -> list[str]:
    """渲染指定规范调用的全部重载契约，避免遗漏有效签名。"""
    contracts = docs.get_callable_contracts(canonical_call)
    if not contracts:
        return ["- No exact contract found in the selected version database."]
    lines: list[str] = []
    for index, contract in enumerate(contracts, 1):
        heading = f"Contract {index}"
        if len(contracts) > 1:
            heading += f" of {len(contracts)} (overload; do not discard)"
        lines.append(f"#### {heading}")
        if contract["purpose"]:
            lines.append(_compact(contract["purpose"], 320))
        if contract["access_path"]:
            lines.append(f"Access: `{contract['access_path']}`")
        lines.append("Required arguments:")
        lines.extend(_argument_lines(contract["required_arguments"], descriptions=True))
        optional = contract["optional_arguments"]
        optional_names = ", ".join(
            f"`{item['name']}`" for item in optional if isinstance(item, dict) and item.get("name")
        )
        lines.append(f"Optional arguments: {optional_names or 'None'}")
        if contract["returns"]:
            lines.append(f"Returns: {_compact(contract['returns'], 280)}")
    return lines


def _render_member_contract(canonical_member: str) -> list[str]:
    """渲染一个属性或 repository 成员的类型、说明和访问路径。"""
    contracts = docs.get_object_member_contracts(canonical_member)
    if not contracts:
        return ["- No exact object-member contract found in the selected database."]
    contract = contracts[0]
    lines = [f"Kind: `{contract['member_kind']}`"]
    if contract["value_type"]:
        lines.append(f"Value type: `{contract['value_type']}`")
    if contract["description"]:
        lines.append(f"Description: {_compact(contract['description'], 360)}")
    if contract["access_paths"]:
        lines.append("Documented access paths:")
        lines.extend(f"- `{path}`" for path in contract["access_paths"])
    return lines


def _render_hint(hint: str, candidate_limit: int) -> list[str]:
    """验证规范 API 符号；未命中时返回有证据的替代候选。"""
    contracts = docs.get_callable_contracts(hint)
    if contracts:
        lines = [f"### VERIFIED hint: `{contracts[0]['canonical_call']}`"]
        lines.extend(_render_contracts(contracts[0]["canonical_call"]))
        return lines

    member_contracts = docs.get_object_member_contracts(hint)
    if member_contracts:
        canonical = member_contracts[0]["canonical_member"]
        lines = [f"### VERIFIED hint: `{canonical}`"]
        lines.extend(_render_member_contract(canonical))
        return lines

    lines = [f"### UNVERIFIED callable/member hint: `{hint}`"]
    lines.append(
        "No exact method, attribute, or repository contract exists in the selected "
        "database. Do not put this hint into executable code merely by changing its "
        "spelling."
    )
    alternatives = docs.find_api_candidates(hint, limit=candidate_limit)
    if alternatives:
        lines.append("Grounded alternatives retrieved from the hint words:")
        for candidate in alternatives:
            lines.append(
                f"- `{candidate['canonical_symbol']}` ({candidate['symbol_kind']}) "
                f"[{candidate['confidence']}; matched: "
                f"{', '.join(candidate['matched_terms']) or 'none'}]"
            )
    return lines


def _render_need(need: str, candidate_limit: int) -> list[str]:
    """检索并渲染一个操作需求的候选、状态及精确契约。"""
    candidates = docs.find_api_candidates(need, limit=candidate_limit)
    lines = [f"### Need: {need}"]
    if not candidates:
        lines.extend(
            (
                "Status: UNRESOLVED",
                (
                    "No grounded method/member candidate was found. Run one precise "
                    "method/member search for this operation; do not invent an API symbol."
                ),
            )
        )
        return lines

    high_confidence = sum(candidate["confidence"] == "HIGH" for candidate in candidates)
    if high_confidence == 1:
        status = "ONE_HIGH_CONFIDENCE_CANDIDATE"
    elif high_confidence > 1:
        status = "AMBIGUOUS_HIGH_CONFIDENCE_CANDIDATES"
    else:
        status = "REVIEW_CANDIDATES"
    lines.append(f"Status: {status}")
    for index, candidate in enumerate(candidates, 1):
        lines.append(
            f"## Candidate {index}: `{candidate['canonical_symbol']}` "
            f"({candidate['symbol_kind']}) "
            f"[{candidate['confidence']}; score={candidate['score']:.1f}; "
            f"matched={', '.join(candidate['matched_terms']) or 'none'}]"
        )
        if candidate["symbol_kind"] == "method":
            if candidate["purpose"]:
                lines.append(_compact(candidate["purpose"], 320))
            lines.extend(_render_contracts(candidate["canonical_call"]))
        else:
            lines.extend(_render_member_contract(candidate["canonical_member"]))
    return lines


def main() -> None:
    """按版本批量检索 needs 和 hints，并输出可供编写脚本的证据包。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--need",
        action="append",
        default=[],
        help=(
            "One atomic operation whose canonical Abaqus symbol is unknown; "
            "include the target object and action, and repeat for the milestone."
        ),
    )
    parser.add_argument(
        "--hint",
        action="append",
        default=[],
        help=(
            "Known canonical Receiver.symbol for a method, attribute, or repository; "
            "repeat for every known API symbol used by the milestone."
        ),
    )
    parser.add_argument("--version", help="Abaqus year, for example 2024")
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Top-K real candidates returned for each need (default: 3)",
    )
    args = parser.parse_args()
    if not args.need and not args.hint:
        parser.error("provide at least one --need or --hint")

    db_path = configure_version(args.version)
    version = db_path.stem.removeprefix("abaqus_api_")
    limit = max(1, min(args.limit, 5))

    output = [
        f"# Abaqus {version} grounded API context",
        "",
        (
            "This bundle supplies evidence, not an automatic final API decision. "
            "Use only exact symbols shown below, keep all method overloads visible, "
            "and let the LLM choose and compose them from the full task context."
        ),
        (
            "Methods, documented attributes, and repositories are grounded in the "
            "selected Abaqus version."
        ),
    ]
    if args.hint:
        output.extend(("", "# Canonical API symbol verification"))
        for hint in args.hint:
            output.extend(("", *_render_hint(hint, limit)))
    if args.need:
        output.extend(("", "# Operation needs"))
        for need in args.need:
            output.extend(("", *_render_need(need, limit)))
    output.extend(
        (
            "",
            "# Handoff rules",
            "- The LLM makes the final selection; candidate rank is not a command.",
            (
                "- A VERIFIED hint has an exact selected-version contract; never use an "
                "UNVERIFIED hint in executable Abaqus code."
            ),
            "- Include result and diagnostic APIs as hints or needs before using them.",
            (
                "- For an UNRESOLVED operation, run one precise get_api_detail.py "
                "--search-calls or --search-members query according to the intended "
                "code shape. If it returns no canonical candidate, stop without "
                "executing the unresolved operation."
            ),
        )
    )
    print("\n".join(output))


if __name__ == "__main__":
    main()
