#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline structural checks for this skill package. No network, no MIDAS."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
warnings = []

REQUIRED_FM = [
    "name",
    "display_name",
    "display_name_en",
    "description",
    "description_zh",
    "description_en",
    "version",
    "author",
]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def err(msg: str) -> None:
    errors.append(msg)
    print("ERROR:", msg)


def warn(msg: str) -> None:
    warnings.append(msg)
    print("WARN:", msg)


def ok(msg: str) -> None:
    print("OK:", msg)


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    raw = m.group(1)
    data = {}

    def scalar(key: str):
        mm = re.search(rf"^{re.escape(key)}:\s*(.*)$", raw, re.M)
        if not mm:
            return None
        first = mm.group(1).strip()
        if first.startswith(("|", ">", ">-", ">+", "|-", "|+")) or first == "":
            lines = raw.splitlines()
            captured = []
            seen = False
            for ln in lines:
                if re.match(rf"^{re.escape(key)}:\s*", ln):
                    seen = True
                    rest = re.sub(rf"^{re.escape(key)}:\s*", "", ln).strip()
                    if rest in {">", ">-", ">+", "|", "|-", "|+", ""}:
                        continue
                    if rest:
                        captured.append(rest)
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
        if (first.startswith('"') and first.endswith('"')) or (first.startswith("'") and first.endswith("'")):
            return first[1:-1]
        return first

    for key in REQUIRED_FM:
        data[key] = scalar(key)
    return data


def check_frontmatter() -> str:
    skill = ROOT / "SKILL.md"
    if not skill.exists():
        err("missing SKILL.md")
        return ""
    text = skill.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if not fm:
        err("SKILL.md missing YAML frontmatter")
        return text
    slug = ROOT.name
    name = fm.get("name") or ""
    if not name:
        err("frontmatter missing name")
    elif not NAME_RE.match(name):
        err(f"name is not lowercase kebab-case: {name!r}")
    elif name != slug:
        err(f"name {name!r} must equal directory slug {slug!r}")
    else:
        ok(f"name = {name}")
    for key in REQUIRED_FM:
        val = fm.get(key)
        if not val:
            err(f"frontmatter missing {key}")
        else:
            ok(f"{key} length = {len(val)}")
    if fm.get("description") and len(fm["description"]) < 20:
        err("description is too short")
    return text


def check_paths(skill_text: str) -> None:
    refs = set(re.findall(r"`(references/[^`]+|examples/[^`]+|scripts/[^`]+)`", skill_text or ""))
    refs.update(re.findall(r"@(references/[\w./-]+|examples/[\w./-]+|scripts/[\w./-]+)", skill_text or ""))
    for rel in sorted(refs):
        # skip globs or directories mentioned as prefixes
        p = ROOT / rel
        if rel.endswith("/"):
            if not p.exists():
                err(f"missing directory mentioned in SKILL.md: {rel}")
            else:
                ok(f"dir {rel}")
            continue
        if not p.exists():
            err(f"SKILL.md references missing path: {rel}")
        else:
            ok(f"linked {rel}")


def check_json_examples() -> None:
    ex = ROOT / "examples"
    if not ex.exists():
        warn("no examples/ directory")
        return
    for p in sorted(ex.rglob("*.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"))
            ok(f"json {p.relative_to(ROOT)}")
        except json.JSONDecodeError as e:
            err(f"invalid JSON {p.relative_to(ROOT)}: {e}")


def check_search_corpus() -> None:
    man = ROOT / "references/index-manifest.json"
    if not man.exists():
        err("missing references/index-manifest.json")
        return
    manifest = json.loads(man.read_text(encoding="utf-8"))
    product = manifest.get("product") or ""
    ok(f"search manifest product = {product}")
    for corp in manifest.get("corpora") or []:
        path = ROOT / corp["path"]
        if corp.get("default") and not path.exists():
            err(f"default search corpus missing: {corp['path']}")
        elif path.exists():
            ok(f"corpus {corp['path']}")


def run_search(query: str, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(ROOT / "scripts/search_index.py"), "--json", "--limit", "15", query]
    if extra:
        cmd[2:2] = extra
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def search_should_hit(query: str, needles: list[str], extra: list[str] | None = None) -> list[dict]:
    proc = run_search(query, extra)
    if proc.returncode not in (0, 1):
        err(f"search {query!r} failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return []
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        err(f"search {query!r} did not return JSON: {proc.stdout[:300]}")
        return []
    hits = payload.get("hits") or []
    blob = json.dumps(hits, ensure_ascii=False)
    if not hits:
        err(f"search {query!r} returned no hits")
        return []
    missing = [n for n in needles if n.lower() not in blob.lower()]
    if missing:
        err(f"search {query!r} hits did not mention {missing}. first={hits[0].get('file')} {hits[0].get('uri')}")
    else:
        files = ", ".join(sorted({h.get("file") or "" for h in hits[:5]}))
        fields = []
        for h in hits:
            fields.extend([f.get("key") for f in (h.get("fields") or []) if f.get("key")])
        ok(f"search {query!r} -> files [{files}] fields {fields[:12]}")
    return hits


def check_product_searches() -> None:
    script = ROOT / "scripts/search_index.py"
    if not script.exists():
        err("missing scripts/search_index.py")
        return
    slug = ROOT.name
    if slug == "midas-civil-nx-api":
        search_should_hit("NODE", ["NODE", "X", "Y", "Z"])
        search_should_hit("ELEM", ["ELEM", "TYPE", "MATL", "SECT"])
        search_should_hit("UNIT", ["UNIT", "FORCE", "DIST", "TEMPER"])
        search_should_hit("材料", ["MATL", "TYPE"])
        search_should_hit("截面", ["SECT"])
        search_should_hit("结果 BEAMFORCE", ["TABLE_TYPE", "BEAMFORCE"])
    elif slug == "midas-gen-nx-api":
        search_should_hit("NODE", ["NODE", "X", "Y", "Z"])
        search_should_hit("ELEM", ["ELEM", "TYPE"])
        search_should_hit("UNIT", ["UNIT", "TEMPER"])
        search_should_hit("材料", ["MATL"])
        search_should_hit("截面", ["SECT"])
        # results: official post/TABLE or Section Table should hit; BEAMFORCE may be absent
        proc = run_search("结果 TABLE_TYPE")
        payload = {}
        try:
            payload = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            err("Gen search for 结果 TABLE_TYPE did not return JSON")
        hits = payload.get("hits") or []
        if not hits:
            err("Gen default search for 结果 TABLE_TYPE returned no shared official hits")
        else:
            ok(f"Gen result search hits {[h.get('uri') or h.get('title') for h in hits[:4]]}")
        # default search must not surface Civil examples as executable
        proc2 = run_search("post_node_local_civil_handbook")
        try:
            payload2 = json.loads(proc2.stdout or "{}")
        except json.JSONDecodeError:
            payload2 = {"hits": []}
        civil_ex = [
            h
            for h in (payload2.get("hits") or [])
            if "examples/" in (h.get("file") or "") and "civil" in (h.get("file") or "").lower()
        ]
        if civil_ex:
            err("Gen default search returned Civil example files; they must require --include-cross-product")
        else:
            ok("Gen default search does not return Civil example files")
        # explicit cross-product flag may include examples, but warnings must be present
        proc3 = run_search("NODE", ["--include-cross-product"])
        try:
            payload3 = json.loads(proc3.stdout or "{}")
        except json.JSONDecodeError:
            payload3 = {"hits": []}
        cross = [h for h in (payload3.get("hits") or []) if h.get("evidence") == "unverified-cross-product"]
        if cross:
            bad = [h for h in cross if "not an executable contract" not in (h.get("warning") or "")]
            if bad:
                err("cross-product hits missing executable-contract warning")
            else:
                ok(f"cross-product flag returned {len(cross)} warned hits")
        else:
            ok("no bundled Civil catalog in Gen package; cross-product flag has no extra field corpus (honest gap)")
        # official shared hits in default must not be labeled verified field execution
        node_hits = run_search("NODE")
        try:
            nh = json.loads(node_hits.stdout or "{}").get("hits") or []
        except json.JSONDecodeError:
            nh = []
        verified_fields = [h for h in nh if h.get("evidence") == "verified" and h.get("uri") == "/db/NODE"]
        if verified_fields:
            err("Gen packaged /db/NODE fields must not be labeled verified; official pages are shared, not Gen-runtime verified")
        else:
            ok("Gen NODE hits are not over-labeled as verified field contracts")
    else:
        warn(f"no product-specific search tests for {slug}")


def main() -> int:
    text = check_frontmatter()
    check_paths(text)
    check_json_examples()
    check_search_corpus()
    check_product_searches()
    if errors:
        print(f"FAIL ({len(errors)} errors, {len(warnings)} warnings)")
        return 1
    print(f"PASS ({len(warnings)} warnings)")
    print("NOTE: this script does not connect to MIDAS and does not prove a live session works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
