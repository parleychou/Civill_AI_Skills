#!/usr/bin/env python3
from pathlib import Path
import os, shutil, sys
src = Path(__file__).resolve().parent.parent
codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
dst = codex_home / "skills" / "cheap-agent"
if src == dst:
    print(f"cheap-agent is already installed at: {dst}")
    print("Restart Codex so it can rediscover the skill, then run: $cheap-agent")
    raise SystemExit(0)
if dst.exists():
    shutil.rmtree(dst)
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
print(f"Installed cheap-agent to: {dst}")
print("Restart Codex so it can rediscover the skill, then run: $cheap-agent")
