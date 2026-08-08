import json, subprocess, sys, tempfile
from pathlib import Path
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as d:
        d=Path(d); md=d/"report.md"; packet=d/"packet.json"; scores=d/"scores.json"; out=d/"report.pdf"
        md.write_text("# 測試報告\n\n# 五個重要結論\n\n1. 這是一項可驗證的測試結論。\n\n# 事業深讀\n\n正文分析。\n",encoding="utf-8")
        packet.write_text(json.dumps({"core_thesis":"合成個案主判。","annual_rulings":[{"year":year,"central_task":f"{year}年度主題","strongest_opportunity":"合成機會"} for year in range(2026,2031)]},ensure_ascii=False),encoding="utf-8")
        scores.write_text(json.dumps({"domains":[{"domain":f"domain_{i}","label":f"領域{i+1}","flow_score":60+i,"potential_score":70+i,"friction_score":30+i,"confidence_score":80+i} for i in range(8)]},ensure_ascii=False),encoding="utf-8")
        subprocess.run([sys.executable,str(ROOT/"scripts"/"render_plain_deep_pdf.py"),str(md),str(out),"--packet",str(packet),"--scores",str(scores),"--subject","合成個案"],check=True)
        reader=PdfReader(str(out)); text="\n".join(p.extract_text() or "" for p in reader.pages)
        assert "目錄與閱讀路線" in text
        assert "八領域評分 Dashboard" in text
        assert "時間索引" in text
        assert "四派在本次報告中的角色" not in text
        assert len(reader.pages)>=5
        broken=json.loads(scores.read_text(encoding="utf-8")); broken["domains"].pop(); scores.write_text(json.dumps(broken,ensure_ascii=False),encoding="utf-8")
        failed=subprocess.run([sys.executable,str(ROOT/"scripts"/"render_plain_deep_pdf.py"),str(md),str(out),"--packet",str(packet),"--scores",str(scores),"--subject","合成個案"],capture_output=True,text=True)
        assert failed.returncode!=0 and not out.exists()
        print("plain_renderer_ok")

if __name__=="__main__": main()
