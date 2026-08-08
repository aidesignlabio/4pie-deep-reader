#!/usr/bin/env python3
"""Install and verify the complete 4PIE runtime in .venv."""
import os, platform, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VENV=ROOT/".venv"
SETUP=ROOT/"scripts"/"vedic_engine"/"scripts"/"setup_env.py"
NODE=ROOT/"scripts"/"calculator"/"node"
FONT_DIR=ROOT/"assets"/"fonts"
FONT_FILE=FONT_DIR/"NotoSansTC-Variable.ttf"
FONT_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"

def run(cmd, cwd=None):
    print("+", " ".join(map(str,cmd)))
    return subprocess.run(list(map(str,cmd)),cwd=cwd).returncode

def venv_python():
    return VENV/("Scripts/python.exe" if platform.system()=="Windows" else "bin/python")

def ensure_font():
    """Install the release-pinned Traditional Chinese font locally."""
    if FONT_FILE.is_file() and FONT_FILE.stat().st_size > 1_000_000:
        print(f"FONT_READY path={FONT_FILE}")
        return 0
    FONT_DIR.mkdir(parents=True,exist_ok=True)
    partial=FONT_FILE.with_suffix(".download")
    try:
        print(f"+ download {FONT_URL}")
        urllib.request.urlretrieve(FONT_URL,partial)
        if partial.stat().st_size <= 1_000_000:
            raise RuntimeError("downloaded font is unexpectedly small")
        partial.replace(FONT_FILE)
        print(f"FONT_READY path={FONT_FILE}")
        return 0
    except Exception as exc:
        partial.unlink(missing_ok=True)
        print(f"ERROR: unable to install Traditional Chinese font: {exc}")
        return 1

def main():
    if run([sys.executable,SETUP,"--target",VENV]): return 1
    if ensure_font(): return 5
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
