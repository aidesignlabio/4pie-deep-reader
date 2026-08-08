"""Privacy-first four-system calculator CLI."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from engine import calculate_chart, strip_pii
from formatter import format_structured_data

CORE = ["bazi", "ziwei", "western", "vedic"]

def main():
    p=argparse.ArgumentParser(description="Calculate a validated 4PIE chart")
    p.add_argument("--datetime",required=True); p.add_argument("--timezone",required=True)
    p.add_argument("--lat",required=True,type=float); p.add_argument("--lon",required=True,type=float)
    p.add_argument("--gender",required=True); p.add_argument("--as-of")
    p.add_argument("--output",default="chart_data.json"); p.add_argument("--markdown")
    p.add_argument("--include-pii",action="store_true",help="Opt in to retaining raw birth metadata")
    a=p.parse_args()
    chart=calculate_chart(birth_datetime_local=a.datetime,timezone_name=a.timezone,lat=a.lat,lon=a.lon,
        gender=a.gender,as_of=a.as_of,systems=CORE)
    output=chart if a.include_pii else strip_pii(chart)
    path=Path(a.output); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    if a.markdown: Path(a.markdown).write_text(format_structured_data(output),encoding="utf-8")
    print(json.dumps({"output":str(path),**chart["validation_summary"]},ensure_ascii=False))
    return 0 if chart["validation_summary"]["ok"] else 2
if __name__=="__main__": raise SystemExit(main())

