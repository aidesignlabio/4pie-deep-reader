#!/usr/bin/env python3
"""Install and verify the complete 4PIE runtime in .venv."""
import os, platform, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VENV=ROOT/".venv"
SETUP=ROOT/"scripts"/"vedic_engine"/"scripts"/"setup_env.py"
NODE=ROOT/"scripts"/"calculator"/"node"

def run(cmd, cwd=None):
    print("+", " ".join(map(str,cmd)))
    return subprocess.run(list(map(str,cmd)),cwd=cwd).returncode

def venv_python():
    return VENV/("Scripts/python.exe" if platform.system()=="Windows" else "bin/python")

def main():
    if run([sys.executable,SETUP,"--target",VENV]): return 1
    npm=shutil.which("npm.cmd" if platform.system()=="Windows" else "npm") or shutil.which("npm")
    if not npm:
        print("ERROR: Node.js/npm is required for Zi Wei calculation.")
        return 2
    if run([npm,"install","--no-audit","--no-fund"],cwd=NODE): return 2
    py=venv_python()
    if run([py,ROOT/"scripts"/"calculator"/"check_env.py"]): return 3
    if run([py,ROOT/"scripts"/"smoke_test.py"]): return 4
    print(f"4PIE_READY python={py}")
    return 0
if __name__=="__main__": raise SystemExit(main())

