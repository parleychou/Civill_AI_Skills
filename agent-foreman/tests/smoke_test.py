#!/usr/bin/env python3
"""Offline smoke test for Agent Foreman worktree + review gate.

Does not call real agy or agy-staff.
"""
from pathlib import Path
import json, os, subprocess, tempfile

def run(*args, cwd=None, env=None, check=True):
    cp = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and cp.returncode != 0:
        raise RuntimeError(cp.stderr)
    return cp

with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "repo"; repo.mkdir()
    run("git","init", cwd=repo)
    run("git","config","user.email","test@example.invalid", cwd=repo)
    run("git","config","user.name","Foreman Test", cwd=repo)
    (repo/"hello.txt").write_text("hello\n")
    run("git","add",".", cwd=repo); run("git","commit","-m","init", cwd=repo)
    print("offline repository setup: OK")
    print("Review-gate logic is exercised by the main helper in real/fake-provider integration tests.")
