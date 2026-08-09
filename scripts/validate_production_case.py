#!/usr/bin/env python3
"""Hard production gate: no PDF unless every 4PIE artifact is complete."""
import argparse, json
from pathlib import Path

SCHOOLS=("bazi","ziwei","western","vedic")
SCORE_KEYS=("flow_score","potential_score","friction_score","confidence_score")

def load(path, errors):
    if not path.is_file(): errors.append(f"missing:{path.name}"); return None
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: errors.append(f"invalid_json:{path.name}:{exc}"); return None

def score_rows(scores):
    return (scores or {}).get("domains") or (scores or {}).get("natal_dimensions") or []

def validate(case_dir, start_year):
    errors=[]
    chart=load(case_dir/"chart_data.json",errors)
    bazi=load(case_dir/"bazi_l1.json",errors)
    adjudication=load(case_dir/"adjudication.json",errors)
    packet=load(case_dir/"fate_packet.json",errors)
    scores=load(case_dir/"domain_scores.json",errors)
    report=case_dir/"report.md"
    if not report.is_file(): errors.append("missing:report.md")

    if chart:
        if not chart.get("validation_summary",{}).get("ok"): errors.append("chart_validation:not_ok")
        systems=chart.get("systems",{})
        for school in SCHOOLS:
            if systems.get(school,{}).get("status")!="ok": errors.append(f"core_system:{school}:not_ok")
    if bazi:
        if bazi.get("status")!="ok": errors.append("bazi_l1:not_ok")
        if bazi.get("strength_decision",{}).get("status")!="verified": errors.append("bazi_strength:not_verified")
        if bazi.get("structure_decision",{}).get("status") not in ("verified","conditional_structure"): errors.append("bazi_structure:not_adjudicated")

    dossier_dir=case_dir/"dossiers"
    for school in SCHOOLS:
        dossier=load(dossier_dir/f"{school}.json",errors)
        if dossier and dossier.get("status") not in ("locked","approved","ok"):
            errors.append(f"dossier:{school}:not_locked")
        if dossier and not dossier.get("outcomes"):
            errors.append(f"dossier:{school}:no_outcomes")

    if adjudication:
        rows=adjudication.get("fate_adjudication") or adjudication.get("domains") or []
        if not rows: errors.append("adjudication:no_domains")
        for row in rows:
            positions=row.get("school_positions",{})
            for school in SCHOOLS:
                position=positions.get(school,{}); position=position.get("position") if isinstance(position,dict) else position
                if position in (None,"insufficient"): errors.append(f"adjudication:{row.get('domain','unknown')}:{school}:incomplete")

    if packet:
        required=("consequential_judgments","school_role_manifest","consensus_matrix","fate_adjudication","annual_rulings")
        for key in required:
            if not packet.get(key): errors.append(f"packet:{key}:missing_or_empty")
        years=[int(x.get("year")) for x in packet.get("annual_rulings",[]) if str(x.get("year","")).isdigit()]
        expected=list(range(start_year,start_year+5))
        if not all(year in years for year in expected): errors.append(f"annual_years:expected:{expected}:got:{years}")

    rows=score_rows(scores)
    if len(rows)!=8: errors.append(f"scores:expected_8:got_{len(rows)}")
    for index,row in enumerate(rows):
        for key in SCORE_KEYS:
            value=row.get(key,row.get("fortune_score") if key=="flow_score" else None)
            if not isinstance(value,(int,float)) or not 0<=value<=100: errors.append(f"scores:{index}:{key}:invalid")

    mode="legacy"
    manifest=case_dir/"prepare_manifest.json"
    if manifest.is_file():
        try: mode=json.loads(manifest.read_text(encoding="utf-8")).get("input",{}).get("mode") or json.loads(manifest.read_text(encoding="utf-8")).get("report_mode") or "deep"
        except Exception: pass
    if report.is_file():
        text=report.read_text(encoding="utf-8")
        titles=[line for line in text.splitlines() if line.startswith("# ")]
        chapters=[line for line in text.splitlines() if line.startswith("## ")]
        chapter_count=max(0,len(titles)-1)+len(chapters)
        if not titles or chapter_count<8: errors.append("report:requires_title_and_at_least_8_chapters")
        minimum={"standard":3500,"deep":7000,"legacy":5000}[mode]
        if len(text.strip())<minimum: errors.append(f"report:too_short_for_{mode}:{len(text.strip())}<{minimum}")
    return {"ok":not errors,"errors":errors,"case_dir":str(case_dir),"start_year":start_year}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("case_dir",type=Path); ap.add_argument("--start-year",type=int,default=2026); ap.add_argument("--output",type=Path)
    a=ap.parse_args(); result=validate(a.case_dir,a.start_year)
    if a.output: a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False)); raise SystemExit(0 if result["ok"] else 2)

if __name__=="__main__": main()
