#!/usr/bin/env python3
"""End-to-end synthetic four-system calculation; contains no real subject data."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    with tempfile.TemporaryDirectory() as d:
        out=Path(d)/"chart.json"
        cmd=[sys.executable,str(ROOT/"scripts"/"calculator"/"run.py"),
             "--datetime","2000-01-01 12:00","--timezone","UTC","--lat","0","--lon","0",
             "--gender","F","--as-of","2026-01-01","--output",str(out)]
        result=subprocess.run(cmd,capture_output=True,text=True,env=os.environ.copy(),timeout=180)
        if result.returncode:
            print(result.stdout); print(result.stderr,file=sys.stderr); return result.returncode
        data=json.loads(out.read_text(encoding="utf-8"))
        systems=data.get("systems",{})
        expected={"bazi","ziwei","western","vedic"}
        if set(systems)!=expected: raise AssertionError(f"systems={set(systems)}")
        bad={k:v.get("status") for k,v in systems.items() if v.get("status")!="ok"}
        if bad: raise AssertionError(f"core failures={bad}")
        if not data.get("validation_summary",{}).get("ok"): raise AssertionError("validation_summary.ok is false")
        print("FOUR_SYSTEM_SMOKE_OK")
    return 0
if __name__=="__main__": raise SystemExit(main())

