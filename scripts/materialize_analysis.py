#!/usr/bin/env python3
"""Materialize every production artifact from one canonical agent output."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHOOLS = ("bazi", "ziwei", "western", "vedic")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("master", type=Path)
    ap.add_argument("case_dir", type=Path)
    args = ap.parse_args()
    master = read(args.master)
    if master.get("schema_version") != "analysis_master_v1":
        raise SystemExit("MASTER_SCHEMA_INVALID")
    dossiers = master.get("dossiers", {})
    missing = [school for school in SCHOOLS if not dossiers.get(school, {}).get("outcomes")]
    if missing:
        raise SystemExit(f"MASTER_DOSSIERS_MISSING:{','.join(missing)}")
    adjudication = master.get("adjudication", {})
    rows = adjudication.get("fate_adjudication") or adjudication.get("domains") or []
    if not rows:
        raise SystemExit("MASTER_ADJUDICATION_MISSING")
    packet = dict(master.get("fate_packet") or {})
    packet.setdefault("fate_adjudication", rows)
    report = master.get("report_markdown", "").strip()
    if not report:
        raise SystemExit("MASTER_READER_MISSING")
    case = args.case_dir.resolve()
    for school in SCHOOLS:
        write(case / "dossiers" / f"{school}.json", dossiers[school])
    write(case / "adjudication.json", {"fate_adjudication": rows})
    write(case / "score_input.json", master.get("score_input") or {})
    write(case / "fate_packet.json", packet)
    (case / "report.md").write_text(report + "\n", encoding="utf-8")
    language=master.get("language","zh-TW")
    suffix="en" if language=="en" else "zh-TW"
    (case / f"report.{suffix}.md").write_text(report + "\n", encoding="utf-8")
    packet.setdefault("language",language)
    write(case / "fate_packet.json", packet)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    subprocess.run([
        sys.executable, str(ROOT / "scripts" / "score_domains.py"),
        str(case / "score_input.json"), str(case / "domain_scores.json"),
    ], check=True, env=env)
    print(json.dumps({"status": "materialized", "case_dir": str(case), "schools": 4, "domains": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
