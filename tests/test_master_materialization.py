import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCHOOLS=("bazi","ziwei","western","vedic")

def main():
    with tempfile.TemporaryDirectory() as raw:
        case=Path(raw)/"case"; case.mkdir()
        positions={s:{"position":"support"} for s in SCHOOLS}
        master={
            "schema_version":"analysis_master_v1",
            "language":"en",
            "dossiers":{s:{"status":"locked","outcomes":[{"claim":"synthetic"}]} for s in SCHOOLS},
            "adjudication":{"fate_adjudication":[{"domain":"career","school_positions":positions}]},
            "score_input":{"domains":[{
                "domain":f"d{i}","label":f"領域{i}","time_modifier":0,
                "schools":[{"school":s,"support_strength":3,"friction_strength":1,"evidence_quality":.8} for s in SCHOOLS],
                "confidence_components":{"calculation_completeness":90,"rule_specificity":80,"derivation_completeness":80,"independent_support":75,"time_stability":75,"falsifiability":80}
            } for i in range(8)]},
            "fate_packet":{"core_thesis":"synthetic","consequential_judgments":[{"title":"x"}],"school_role_manifest":[{"school":s} for s in SCHOOLS],"consensus_matrix":[{"domain":"career"}],"annual_rulings":[{"year":y,"central_task":"x"} for y in range(2026,2031)]},
            "report_markdown":"# 合成\n\n"+("合成正文。"*800),
        }
        src=case/"analysis_master.json"; src.write_text(json.dumps(master,ensure_ascii=False),encoding="utf-8")
        subprocess.run([sys.executable,str(ROOT/"scripts"/"materialize_analysis.py"),str(src),str(case)],check=True)
        assert all((case/"dossiers"/f"{s}.json").is_file() for s in SCHOOLS)
        assert len(json.loads((case/"domain_scores.json").read_text(encoding="utf-8"))["domains"])==8
        assert json.loads((case/"fate_packet.json").read_text(encoding="utf-8"))["fate_adjudication"]
        assert (case/"report.en.md").is_file()
        print("master_materialization_ok")

if __name__=="__main__": main()
