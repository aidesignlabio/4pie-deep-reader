#!/usr/bin/env python3
"""Create a shareable delivery folder without private calculation artifacts."""
import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", type=Path)
    ap.add_argument("delivery_dir", type=Path)
    ap.add_argument("--pdf", type=Path, help="PDF to package; defaults to report.pdf or the only PDF in the case directory")
    args = ap.parse_args()
    pdf = args.pdf
    if pdf is None:
        preferred = args.case_dir / "report.pdf"
        candidates = sorted(args.case_dir.glob("*.pdf"))
        if preferred.is_file():
            pdf = preferred
        elif len(candidates) == 1:
            pdf = candidates[0]
        elif not candidates:
            raise SystemExit("DELIVERY_PDF_MISSING: render a PDF or pass --pdf PATH")
        else:
            raise SystemExit("DELIVERY_PDF_AMBIGUOUS: pass --pdf PATH")
    qa_candidates = (args.case_dir / "pdf-qa" / "pdf_qa.json", args.case_dir / "pdf_qa" / "pdf_qa.json")
    qa = next((path for path in qa_candidates if path.is_file()), None)
    if not pdf.is_file():
        raise SystemExit(f"DELIVERY_PDF_MISSING:{pdf}")
    args.delivery_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, args.delivery_dir / "4PIE_Deep_Report.pdf")
    manifest = {"product": "4PIE Deep Report", "source_pdf": pdf.name, "files": ["4PIE_Deep_Report.pdf"], "pdf_qa": "passed" if qa and json.loads(qa.read_text(encoding="utf-8")).get("qa_ok") else "not_verified"}
    (args.delivery_dir / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
