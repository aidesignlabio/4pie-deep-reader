import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory() as raw:
        case=Path(raw)/"case"; delivery=Path(raw)/"delivery"; qa=case/"pdf_qa"
        qa.mkdir(parents=True)
        (case/"custom-name.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
        (qa/"pdf_qa.json").write_text(json.dumps({"qa_ok":True}),encoding="utf-8")
        subprocess.run([sys.executable,str(ROOT/"scripts"/"package_delivery.py"),str(case),str(delivery)],check=True)
        manifest=json.loads((delivery/"delivery_manifest.json").read_text(encoding="utf-8"))
        assert manifest["source_pdf"]=="custom-name.pdf"
        assert manifest["pdf_qa"]=="passed"
        assert (delivery/"4PIE_Deep_Report.pdf").is_file()
        print("package_delivery_ok")

if __name__=="__main__": main()
