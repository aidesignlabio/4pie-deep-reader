#!/usr/bin/env python3
"""Unified 4PIE deterministic command launcher."""
import argparse, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
COMMANDS={
    "prepare": ROOT/"prepare_case.py",
    "calculate": ROOT/"calculator"/"run.py",
    "bazi-l1": ROOT/"adjudicate_bazi_l1.py",
    "score": ROOT/"score_domains.py",
    "validate": ROOT/"validate_fate_packet.py",
    "production-check": ROOT/"validate_production_case.py",
    "render": ROOT/"render_production_case.py",
    "render-dashboard": ROOT/"render_apple_pdf.py",
    "privacy": ROOT/"privacy_scan.py",
    "doctor": ROOT/"calculator"/"check_env.py",
    "smoke": ROOT/"smoke_test.py",
    "pdf-qa": ROOT/"qa_pdf.py",
}

def main():
    p=argparse.ArgumentParser(description="4PIE deterministic pipeline launcher")
    p.add_argument("command",choices=COMMANDS)
    p.add_argument("args",nargs=argparse.REMAINDER)
    a=p.parse_args()
    child_env=os.environ.copy()
    child_env["PYTHONIOENCODING"]="utf-8"
    return subprocess.call([sys.executable,str(COMMANDS[a.command]),*a.args],env=child_env)
if __name__=="__main__": raise SystemExit(main())
