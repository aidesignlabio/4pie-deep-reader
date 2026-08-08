import json, subprocess, sys, tempfile
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
SCHOOLS=("bazi","ziwei","western","vedic")
def dump(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")

def main():
    with tempfile.TemporaryDirectory() as raw:
        case=Path(raw)/"case"; output=Path(raw)/"report.pdf"; qa=Path(raw)/"qa"
        dump(case/"chart_data.json",{"validation_summary":{"ok":True},"systems":{s:{"status":"ok"} for s in SCHOOLS}})
        dump(case/"bazi_l1.json",{"status":"ok","strength_decision":{"status":"verified"},"structure_decision":{"status":"conditional_structure"}})
        positions={s:{"position":"support"} for s in SCHOOLS}; domains=[{"domain":"career","school_positions":positions}]
        dump(case/"adjudication.json",{"fate_adjudication":domains})
        dump(case/"fate_packet.json",{"core_thesis":"所有內容均為合成測試。","consequential_judgments":[{"title":"合成裁決"}],"school_role_manifest":[{"school":s} for s in SCHOOLS],"consensus_matrix":[{"domain":"career"}],"fate_adjudication":domains,"annual_rulings":[{"year":y,"central_task":f"{y}合成主題","strongest_opportunity":"合成機會"} for y in range(2026,2031)]})
        dump(case/"domain_scores.json",{"domains":[{"label":f"合成領域{i+1}","flow_score":60+i,"potential_score":70+i,"friction_score":30+i,"confidence_score":80+i} for i in range(8)]})
        for school in SCHOOLS: dump(case/"dossiers"/f"{school}.json",{"status":"locked","outcomes":[{"claim":"synthetic"}]})
        chapters="\n\n".join(f"# 合成章節{i+1}\n\n"+("這是用於驗證版式與完整流程的合成正文。"*45) for i in range(8))
        (case/"report.md").write_text("# 合成測試報告\n\n"+chapters,encoding="utf-8")
        subprocess.run([sys.executable,str(ROOT/"scripts"/"render_production_case.py"),str(case),str(output),"--subject","合成個案","--generated","2026-08-08"],check=True)
        subprocess.run([sys.executable,str(ROOT/"scripts"/"qa_pdf.py"),str(output),"--output-dir",str(qa)],check=True)
        reader=PdfReader(str(output)); text="\n".join(p.extract_text() or "" for p in reader.pages)
        assert len(reader.pages)>4 and "2026-2030 時間索引" in text and "八領域評分 Dashboard" in text
        assert json.loads((qa/"pdf_qa.json").read_text(encoding="utf-8"))["qa_ok"]
        print("production_render_ok")

if __name__=="__main__": main()
