#!/usr/bin/env python3
"""Validate a complete case, then invoke the canonical Plain Deep renderer."""
import argparse, subprocess, sys
from pathlib import Path
from validate_production_case import validate

ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("case_dir",type=Path); ap.add_argument("output",type=Path); ap.add_argument("--start-year",type=int,default=2026); ap.add_argument("--title"); ap.add_argument("--subject",required=True); ap.add_argument("--generated"); ap.add_argument("--language",choices=("zh-TW","en"),default="zh-TW")
    a=ap.parse_args(); result=validate(a.case_dir,a.start_year)
    if not result["ok"]:
        print("PRODUCTION_GATE_FAILED",file=sys.stderr)
        for error in result["errors"]: print(f"- {error}",file=sys.stderr)
        return 2
    title=a.title or ("Destiny Adjudication Report" if a.language=="en" else "命運裁決報告")
    cmd=[sys.executable,str(ROOT/"render_plain_deep_pdf.py"),str(a.case_dir/"report.md"),str(a.output),"--packet",str(a.case_dir/"fate_packet.json"),"--scores",str(a.case_dir/"domain_scores.json"),"--title",title,"--subject",a.subject,"--start-year",str(a.start_year),"--language",a.language]
    if a.generated: cmd += ["--generated",a.generated]
    return subprocess.call(cmd)
if __name__=="__main__": raise SystemExit(main())
