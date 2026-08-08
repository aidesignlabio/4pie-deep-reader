import json, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_production_case import validate

def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")

def main():
    with tempfile.TemporaryDirectory() as raw:
        case=Path(raw)
        dump(case/"chart_data.json",{"validation_summary":{"ok":True},"systems":{s:{"status":"ok"} for s in ("bazi","ziwei","western","vedic")}})
        dump(case/"bazi_l1.json",{"status":"ok","strength_decision":{"status":"verified"},"structure_decision":{"status":"conditional_structure"}})
        positions={s:{"position":"support"} for s in ("bazi","ziwei","western","vedic")}
        domains=[{"domain":"career","school_positions":positions}]
        dump(case/"adjudication.json",{"fate_adjudication":domains})
        dump(case/"fate_packet.json",{"consequential_judgments":[1],"school_role_manifest":[1],"consensus_matrix":[1],"fate_adjudication":domains,"annual_rulings":[{"year":y} for y in range(2026,2031)]})
        dump(case/"domain_scores.json",{"domains":[{"flow_score":60,"potential_score":70,"friction_score":30,"confidence_score":80} for _ in range(8)]})
        for school in ("bazi","ziwei","western","vedic"): dump(case/"dossiers"/f"{school}.json",{"status":"locked","outcomes":[{"claim":"synthetic"}]})
        headings="\n\n".join(f"## 合成章節{i+1}\n\n可驗證的合成正文。" for i in range(8))
        (case/"report.md").write_text("# 合成測試\n\n"+headings+"\n\n"+("可驗證的合成正文。"*600),encoding="utf-8")
        initial=validate(case,2026); assert initial["ok"], initial["errors"]
        scores=json.loads((case/"domain_scores.json").read_text(encoding="utf-8")); scores["domains"].pop(); dump(case/"domain_scores.json",scores)
        result=validate(case,2026); assert not result["ok"] and "scores:expected_8:got_7" in result["errors"]
        print("production_gate_ok")

if __name__=="__main__": main()
