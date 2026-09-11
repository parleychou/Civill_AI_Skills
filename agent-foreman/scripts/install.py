#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, shutil
from pathlib import Path

NAME = "agent-foreman"
SRC = Path(__file__).resolve().parent.parent

def copy_to(dst: Path) -> None:
    dst = dst.expanduser().resolve()
    if SRC == dst:
        print(f"{NAME} is already at {dst}")
        return
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    print(f"Installed {NAME} -> {dst}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["codex", "claude", "both", "custom"], default="custom")
    p.add_argument("--dest", default=None, help="Required for --target custom")
    p.add_argument("--legacy-codex", action="store_true", help="Use ~/.codex/skills instead of ~/.agents/skills")
    args = p.parse_args()

    targets = []
    if args.target in {"codex", "both"}:
        if args.legacy_codex:
            home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
            targets.append(home / "skills" / NAME)
        else:
            targets.append(Path.home() / ".agents" / "skills" / NAME)
    if args.target in {"claude", "both"}:
        targets.append(Path.home() / ".claude" / "skills" / NAME)
    if args.target == "custom":
        if not args.dest:
            p.error("--dest is required for --target custom")
        targets.append(Path(args.dest) / NAME if Path(args.dest).name != NAME else Path(args.dest))

    for dst in targets:
        copy_to(dst)

if __name__ == "__main__":
    main()
