#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline keyword search over this skill package.

Standard library only. No network, no MIDAS connection.
Evidence levels are product-isolated: default Gen search does not treat
Civil handbook or Civil examples as an executable Gen contract.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
MANIFEST_PATH = ROOT / "references" / "index-manifest.json"

LEVEL_ORDER = {
    "verified": 0,
    "shared": 1,
    "civil-handbook": 2,
    "package-docs": 3,
    "unverified-cross-product": 4,
}


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print("ERROR: missing", MANIFEST_PATH.relative_to(ROOT), file=sys.stderr)
        sys.exit(2)
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def tokens(query: str) -> list[str]:
    parts = [p for p in re.split(r"[\s,;|/]+", query.strip()) if p]
    return parts or [query.strip()]


def haystack_of_record(rec: dict) -> str:
    bits = [
        rec.get("title") or "",
        rec.get("input_uri") or "",
        rec.get("input_uri_raw") or "",
        rec.get("menu") or "",
        rec.get("rel") or "",
        rec.get("source_url") or "",
        rec.get("official_url") or "",
        " ".join(rec.get("methods") or []),
        rec.get("notes") or "",
        rec.get("product_hint") or "",
        " ".join(rec.get("keywords") or []),
    ]
    for f in rec.get("fields") or []:
        bits.extend(
            [
                f.get("key") or "",
                f.get("name") or "",
                f.get("type") or "",
                f.get("group") or "",
                f.get("notes") or "",
                " ".join(f.get("enums") or []),
            ]
        )
    for s in rec.get("schema_props") or []:
        bits.extend([s.get("key") or "", s.get("path") or "", s.get("description") or "", str(s.get("type") or "")])
    for ex in rec.get("examples") or []:
        bits.append(ex.get("label") or "")
        body = ex.get("body")
        if body is not None:
            try:
                bits.append(json.dumps(body, ensure_ascii=False))
            except TypeError:
                bits.append(str(body))
    return "\n".join(bits)


def match_score(text: str, terms: list[str]) -> tuple[int, list[str]]:
    low = text.lower()
    hit = []
    score = 0
    for term in terms:
        t = term.lower()
        if t and t in low:
            hit.append(term)
            score += 3 if re.search(r"(?:^|[\s/\"'`\[]|\b)" + re.escape(t) + r"(?:$|[\s/\"'`\],.:]|\b)", low, re.I) else 1
    return score, hit


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        # allow a JSON array or {"records":[...]} as well as jsonl
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "records" in obj:
                return list(obj["records"])
            if isinstance(obj, list):
                return obj
        except json.JSONDecodeError:
            pass
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def iter_text_files(base: Path, pattern: str, excludes: list[str]) -> list[Path]:
    files = sorted(base.glob(pattern)) if pattern else []
    if base.is_file():
        files = [base]
    elif not pattern:
        files = [p for p in base.rglob("*") if p.is_file()]
    out = []
    for p in files:
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if any(re.search(ex, rel) for ex in excludes or []):
            continue
        out.append(p)
    return out


def corpus_rows(manifest: dict, include_cross: bool) -> list[dict]:
    rows = []
    for corp in manifest.get("corpora") or []:
        default = bool(corp.get("default", True))
        level = corp.get("level") or "package-docs"
        if not default and not include_cross:
            continue
        if level == "unverified-cross-product" and not include_cross:
            continue
        rel = corp.get("path")
        if not rel:
            continue
        path = ROOT / rel
        if not path.exists():
            rows.append(
                {
                    "_missing_corpus": True,
                    "title": f"(missing corpus) {rel}",
                    "rel": rel,
                    "evidence": level,
                    "notes": corp.get("missing_note") or "Corpus file is not in this package.",
                }
            )
            continue
        if path.suffix.lower() in {".jsonl", ".json"}:
            for rec in load_jsonl(path):
                item = dict(rec)
                item.setdefault("evidence", level)
                item["_corpus"] = rel
                item["_source_file"] = rel
                rows.append(item)
            continue
        pattern = corp.get("glob") or ("*.md" if path.is_dir() else path.name)
        base = path if path.is_dir() else path.parent
        for fp in iter_text_files(base, pattern if path.is_dir() else fp_name(path, pattern), corp.get("exclude") or []):
            rel_f = str(fp.relative_to(ROOT)).replace("\\", "/")
            try:
                text = fp.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            rows.append(
                {
                    "title": fp.stem,
                    "rel": rel_f,
                    "evidence": level,
                    "_corpus": rel,
                    "_source_file": rel_f,
                    "_text": text,
                }
            )
    return rows


def fp_name(path: Path, pattern: str) -> str:
    return path.name if not pattern else pattern


def field_hits(rec: dict, terms: list[str]) -> list[dict]:
    """Return fields for a matched record: term hits first, then the rest."""
    fields = list(rec.get("fields") or [])
    matched, rest = [], []
    for f in fields:
        blob = " ".join(
            [
                f.get("key") or "",
                f.get("name") or "",
                f.get("type") or "",
                f.get("group") or "",
                f.get("notes") or "",
                " ".join(f.get("enums") or []),
            ]
        )
        score, _ = match_score(blob, terms)
        (matched if score else rest).append(f)
    hits = matched + rest
    if hits:
        return hits
    for s in rec.get("schema_props") or []:
        hits.append(
            {
                "key": s.get("key"),
                "name": s.get("description") or "",
                "type": s.get("type") or "",
                "group": "schema",
            }
        )
    return hits


def snippet(text: str, terms: list[str], width: int = 180) -> str:
    low = text.lower()
    pos = -1
    for term in terms:
        i = low.find(term.lower())
        if i >= 0 and (pos < 0 or i < pos):
            pos = i
    if pos < 0:
        return re.sub(r"\s+", " ", text)[:width]
    start = max(0, pos - 40)
    chunk = text[start : start + width].replace("\n", " ")
    return ("…" if start else "") + chunk


def format_hit(rec: dict, terms: list[str], show_fields: bool) -> str:
    evidence = rec.get("evidence") or "package-docs"
    src = rec.get("_source_file") or rec.get("rel") or ""
    uri = rec.get("input_uri") or rec.get("input_uri_raw") or ""
    title = rec.get("title") or src
    methods = ", ".join(rec.get("methods") or [])
    lines = [
        f"- [{evidence}] {title}",
        f"  file: {src}",
    ]
    if uri:
        lines.append(f"  uri: {uri}" + (f"  methods: {methods}" if methods else ""))
    elif methods:
        lines.append(f"  methods: {methods}")
    official = rec.get("official_url") or rec.get("source_url")
    if official:
        lines.append(f"  source: {official}")
    if rec.get("crawled"):
        lines.append(f"  crawled: {rec.get('crawled')}")
    if evidence == "unverified-cross-product":
        lines.append("  WARNING: unverified cross-product material; not a Gen executable contract.")
    if evidence == "shared":
        lines.append("  note: official NX-series shared documentation; confirm on the current product page before writing.")
    if rec.get("_missing_corpus"):
        lines.append(f"  gap: {rec.get('notes')}")
    fh = field_hits(rec, terms)
    if not fh and rec.get("fields"):
        # Query often matches the endpoint title (e.g. 材料) rather than English field keys.
        fh = rec.get("fields") or []
    if fh:
        shown = []
        for f in fh[:12]:
            key = f.get("key") or "(no key)"
            typ = f.get("type") or ""
            req = f.get("required") or ""
            name = f.get("name") or ""
            enums = f.get("enums") or []
            extra = f" enums={enums}" if enums else ""
            shown.append(f"{key} ({typ} {req}) {name}{extra}".strip())
        lines.append("  fields: " + " | ".join(shown))
        if len(fh) > 12:
            lines.append(f"  fields_omitted: {len(fh) - 12} more")
    elif show_fields and rec.get("fields"):
        keys = [f.get("key") for f in rec["fields"] if f.get("key")]
        lines.append("  field_keys: " + ", ".join(keys[:20]))
    text = rec.get("_text") or haystack_of_record(rec)
    lines.append("  snippet: " + snippet(text, terms))
    return "\n".join(lines)


def search(query: str, include_cross: bool, show_fields: bool, limit: int) -> list[dict]:
    manifest = load_manifest()
    terms = tokens(query)
    rows = corpus_rows(manifest, include_cross=include_cross)
    scored = []
    for rec in rows:
        if rec.get("_missing_corpus"):
            # only show missing optional corpora when explicitly requested
            if include_cross:
                scored.append((0, rec, []))
            continue
        text = rec.get("_text") or haystack_of_record(rec)
        score, which = match_score(text, terms)
        if score:
            bonus_src = " ".join([
                rec.get("title") or "",
                rec.get("input_uri") or "",
                " ".join(rec.get("keywords") or []),
            ])
            b, _ = match_score(bonus_src, terms)
            score += 5 * b
            rec["_matched_terms"] = which
            scored.append((score, rec, which))
    scored.sort(key=lambda x: (-x[0], LEVEL_ORDER.get(x[1].get("evidence") or "", 9), x[1].get("input_uri") or "", x[1].get("title") or ""))
    return [item[1] for item in scored[:limit]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Search this skill package offline for endpoints, fields, and examples."
    )
    ap.add_argument("query", nargs="+", help="Keywords, for example: NODE  or  UNIT TEMPER  or  材料 截面")
    ap.add_argument("--include-cross-product", action="store_true", help="Include unverified cross-product (e.g. Civil) material. Never treat those hits as a Gen write contract.")
    ap.add_argument("--fields", action="store_true", help="Always list field keys when a record has them.")
    ap.add_argument("--json", action="store_true", help="Machine-readable JSON output.")
    ap.add_argument("--limit", type=int, default=25, help="Max hits (default 25).")
    args = ap.parse_args(argv)
    query = " ".join(args.query)
    manifest = load_manifest()
    product = manifest.get("product") or "unknown"
    hits = search(query, include_cross=args.include_cross_product, show_fields=args.fields, limit=args.limit)
    # drop placeholder missing-corpus rows from default
    visible = [h for h in hits if not h.get("_missing_corpus")]
    if args.json:
        out = []
        for h in visible:
            out.append(
                {
                    "title": h.get("title"),
                    "file": h.get("_source_file") or h.get("rel"),
                    "uri": h.get("input_uri"),
                    "methods": h.get("methods") or [],
                    "evidence": h.get("evidence"),
                    "fields": [
                        {k: f.get(k) for k in ("key", "name", "type", "required", "default", "group", "enums") if f.get(k)}
                        for f in field_hits(h, tokens(query))[:20]
                    ],
                    "official_url": h.get("official_url") or h.get("source_url") or "",
                    "warning": "unverified-cross-product; not an executable contract"
                    if h.get("evidence") == "unverified-cross-product"
                    else "",
                }
            )
        json.dump({"product": product, "query": query, "hits": out}, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0 if out else 1
    print(f"product: {product}")
    print(f"query: {query}")
    print(f"include_cross_product: {bool(args.include_cross_product)}")
    print(f"hits: {len(visible)}")
    if product.startswith("gen") and not args.include_cross_product:
        print("default Gen scope: verified + official NX shared only. Civil handbook/examples are excluded.")
    if not visible:
        print("NO HITS in the current search scope.")
        if product.startswith("gen") and not args.include_cross_product:
            print("Gap: this may be absent from Gen-verified / official shared material. Do not invent fields, and do not execute Civil examples as Gen contracts.")
        else:
            print("Gap: no packaged record matched. Do not invent fields.")
        return 1
    for h in visible:
        print(format_hit(h, tokens(query), show_fields=args.fields))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
