#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline self-check for this skill package. Does not call MIDAS, Midashosts, or any network API."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
warnings = []

def err(msg):
    errors.append(msg)
    print("ERROR:", msg)

def warn(msg):
    warnings.append(msg)
    print("WARN:", msg)

def ok(msg):
    print("OK:", msg)

# 1. SKILL.md frontmatter
skill = ROOT / "SKILL.md"
if not skill.exists():
    err("missing SKILL.md")
    print("FAIL")
    sys.exit(1)
text = skill.read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
if not m:
    err("SKILL.md missing YAML frontmatter")
    fm = {}
else:
    fm_raw = m.group(1)
    name = desc = None
    # simple YAML: name: ..., description: ... (possibly folded not used)
    def _fm_scalar(raw: str, key: str):
        # single-line: key: value
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.M)
        if not m:
            return None
        first = m.group(1).strip()
        # folded/literal block scalars
        if first in {">", ">-", ">+", "|", "|-", "|+"} or first == "":
            lines = raw.splitlines()
            captured = []
            seen = False
            for ln in lines:
                if re.match(rf"^{re.escape(key)}:\s*", ln):
                    seen = True
                    continue
                if not seen:
                    continue
                if ln.startswith(" ") or ln.startswith("\t"):
                    captured.append(ln.strip())
                    continue
                if ln.strip() == "" and captured:
                    captured.append("")
                    continue
                break
            return " ".join(x for x in captured if x).strip() or None
        return first

    name = _fm_scalar(fm_raw, "name")
    desc = _fm_scalar(fm_raw, "description")
    if not name:
        err("frontmatter missing name")
    else:
        ok(f"name = {name}")
    if not desc or len(desc) < 20:
        err("frontmatter missing or too short description")
    else:
        ok(f"description length = {len(desc)}")

# 2. relative references in SKILL.md
refs = set(re.findall(r"`(references/[^`]+|examples/[^`]+|scripts/[^`]+)`", text))
# also bare paths
for rel in sorted(refs):
    p = ROOT / rel
    if p.exists():
        ok(f"linked path exists: {rel}")
    else:
        err(f"linked path missing: {rel}")

# required files
required = [
    "README.md",
    "references/sources.md",
    "references/product-scope.md",
    "references/connection-and-safety.md",
    "references/conventions.md",
    "references/endpoint-index.md",
    "references/documents.md",
    "references/modeling.md",
    "references/analysis.md",
    "references/results.md",
    "references/limitations.md",
    "examples/PROVENANCE.md",
    "scripts/verify_offline.py",
]
for rel in required:
    if not (ROOT / rel).exists():
        err(f"required file missing: {rel}")
    else:
        ok(f"required file: {rel}")

# 3. example JSON parse
ex_dir = ROOT / "examples"
json_files = sorted(ex_dir.glob("*.json"))
if not json_files:
    err("no example JSON files")
prov = (ex_dir / "PROVENANCE.md").read_text(encoding="utf-8") if (ex_dir / "PROVENANCE.md").exists() else ""
for p in json_files:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"JSON parse failed: {p.name}: {e}")
        continue
    ok(f"JSON parses: {p.name}")
    if f"`{p.name}`" not in prov and p.name not in prov:
        warn(f"example not mentioned in PROVENANCE.md: {p.name}")
    # placeholder path check
    raw = p.read_text(encoding="utf-8")
    if "C:\\\\MIDAS" in raw or "C:/MIDAS" in raw:
        ok(f"contains handbook placeholder path (must be replaced before use): {p.name}")

# 4. no obvious real secrets in package text
secret_pat = re.compile(r"(mapi-key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,})", re.I)
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix.lower() in {".md", ".json", ".py", ".txt"}:
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "your_api_key_here" in t or "base_url_here" in t:
            ok(f"contains official placeholder only: {p.relative_to(ROOT)}")
        if secret_pat.search(t) and "MAPI-Key" in t and "your_api_key" not in t.lower() and "当前产品" not in t and "<" not in t:
            # only flag if it looks like a literal assigned key
            if re.search(r"MAPI-Key['\"]?\s*:\s*['\"][A-Za-z0-9_\-]{16,}", t):
                err(f"possible literal MAPI-Key value in {p.relative_to(ROOT)}")

# 5. endpoint index non-empty
idx = ROOT / "references" / "endpoint-index.md"
if idx.exists() and len(idx.read_text(encoding="utf-8")) < 1000:
    err("endpoint-index.md unexpectedly small")
elif idx.exists():
    ok(f"endpoint-index.md size = {idx.stat().st_size}")

print("---")
print("LIVE_MIDAS_TESTED: no")
print("NETWORK_CALLS: none")
print(f"ERRORS: {len(errors)}  WARNINGS: {len(warnings)}")
if errors:
    print("FAIL")
    sys.exit(1)
print("PASS")
