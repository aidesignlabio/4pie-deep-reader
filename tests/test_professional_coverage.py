import json, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_production_case import validate

SCHOOLS=("bazi","ziwei","western","vedic")
def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")

def main():
    with tempfile.TemporaryDirectory() as raw:
        case=Path(raw); positions={s:{"position":"support"} for s in SCHOOLS
        }; domains=[{"domain":f"d{i}","school_positions":positions} for i in range(8)]
        dump(case/"prepare_manifest.json",{"report_mode":"deep"})
        dump(case/"chart_data.json",{"validation_summary":{"ok":True},"systems":{s:{"status":"ok"} for s in SCHOOLS}})
        dump(case/"bazi_l1.json",{"status":"ok","strength_decision":{"status":"verified"},"structure_decision":{"status":"conditional_structure"}})
        dump(case/"adjudication.json",{"fate_adjudication":domains})
        dump(case/"fate_packet.json",{"consequential_judgments":[{} for _ in range(5)],"school_role_manifest":[{} for _ in range(4)],"consensus_matrix":[{} for _ in range(8)],"fate_adjudication":domains,"annual_rulings":[{"year":y} for y in range(2026,2031)]})
        dump(case/"domain_scores.json",{"domains":[{"flow_score":60,"potential_score":70,"friction_score":30,"confidence_score":80} for _ in range(8)]})
        for school in SCHOOLS: dump(case/"dossiers"/f"{school}.json",{"status":"locked","outcomes":[{}, {}, {}]})
        chapters="\n\n".join(f"## 章節{i}\n內容" for i in range(8)); (case/"report.md").write_text("# 報告\n"+chapters+"\n"+("有效分析內容。"*720),encoding="utf-8")
        result=validate(case,2026); assert result["ok"],result["errors"]
        dump(case/"prepare_manifest.json",{"report_mode":"deep","language":"en"})
        mismatch=validate(case,2026); assert any(x.startswith("report:language_mismatch:expected_en") for x in mismatch["errors"])
        dump(case/"prepare_manifest.json",{"report_mode":"deep","language":"zh-TW"})
        dossier=json.loads((case/"dossiers"/"western.json").read_text(encoding="utf-8")); dossier["outcomes"].pop(); dump(case/"dossiers"/"western.json",dossier)
        failed=validate(case,2026); assert "professional_coverage:dossier:western:expected_3:got_2" in failed["errors"]
        print("professional_coverage_ok")

if __name__=="__main__": main()
