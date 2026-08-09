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
    args = ap.parse_args()
    pdf = args.case_dir / "report.pdf"
    qa = args.case_dir / "pdf-qa" / "pdf_qa.json"
    if not pdf.is_file():
        raise SystemExit("DELIVERY_PDF_MISSING")
    args.delivery_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, args.delivery_dir / "4PIE_Deep_Report.pdf")
    manifest = {"product": "4PIE Deep Report", "files": ["4PIE_Deep_Report.pdf"], "pdf_qa": "passed" if qa.is_file() and json.loads(qa.read_text(encoding="utf-8")).get("qa_ok") else "not_verified"}
    (args.delivery_dir / "delivery_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
