#!/usr/bin/env python3
"""Resumable one-calculation preparation stage for a 4PIE report."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_compact_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(value, depth=0):
    """Remove bulky diagnostics while retaining every interpretation-grade field."""
    if depth > 12:
        return value
    if isinstance(value, dict):
        blocked = {"raw", "debug", "trace", "stdout", "stderr", "formatted_report"}
        return {k: compact(v, depth + 1) for k, v in value.items() if k not in blocked}
    if isinstance(value, list):
        return [compact(v, depth + 1) for v in value]
    return value


def input_contract(args: argparse.Namespace) -> dict:
    return {
        "datetime": args.datetime,
        "timezone": args.timezone,
        "lat": args.lat,
        "lon": args.lon,
        "gender": args.gender,
        "as_of": args.as_of,
        "start_year": args.start_year,
    }


def fingerprint(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run(command: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(command, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)


def valid_chart(path: Path) -> bool:
    try:
        chart = load_json(path)
        return bool(chart.get("validation_summary", {}).get("ok")) and all(
            chart.get("systems", {}).get(school, {}).get("status") == "ok"
            for school in ("bazi", "ziwei", "western", "vedic")
        )
    except Exception:
        return False


def valid_bazi(path: Path) -> bool:
    try:
        data = load_json(path)
        return data.get("status") == "ok" and data.get("strength_decision", {}).get("status") == "verified"
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and cache one complete 4PIE calculation bundle")
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--datetime", required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--gender", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--start-year", type=int, default=2026)
    parser.add_argument("--mode", choices=("standard", "deep"), default="deep")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--stop-after", choices=("chart",), help=argparse.SUPPRESS)
    args = parser.parse_args()

    case_dir = args.case_dir.resolve()
    case_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = case_dir / "prepare_manifest.json"
    state_path = case_dir / "run_state.json"
    chart_path = case_dir / "chart_data.json"
    structured_path = case_dir / "structured_data.md"
    bazi_path = case_dir / "bazi_l1.json"
    bundle_path = case_dir / "analysis_bundle.json"
    context_path = case_dir / "analysis_context.json"
    contract = input_contract(args)
    contract_hash = fingerprint(contract)

    if manifest_path.is_file():
        old = load_json(manifest_path)
        if old.get("input_hash") != contract_hash and not args.force:
            raise SystemExit("CASE_INPUT_MISMATCH: choose a new case directory or pass --force")
    manifest = {
        "schema_version": "prepare_v1",
        "input_hash": contract_hash,
        "input": contract,
        "report_mode": args.mode,
        "policy": {
            "single_natal_calculation": True,
            "annual_full_chart_recalculation": "prohibited",
            "annual_source": "chart_data systems plus bazi_l1.annual_activation",
            "divisional_sensitivity": "on_demand_only_when_reader_uses_d9_d10_ul",
        },
    }
    write_json(manifest_path, manifest)

    state = load_json(state_path) if state_path.is_file() else {"schema_version": "run_state_v1", "stages": {}}
    stages = state.setdefault("stages", {})
    if args.force or not valid_chart(chart_path):
        run([
            sys.executable, str(ROOT / "scripts" / "calculator" / "run.py"),
            "--datetime", args.datetime, "--timezone", args.timezone,
            "--lat", str(args.lat), "--lon", str(args.lon), "--gender", args.gender,
            "--as-of", args.as_of, "--output", str(chart_path), "--markdown", str(structured_path),
        ])
        stages["chart"] = {"status": "complete", "reused": False}
    else:
        stages["chart"] = {"status": "complete", "reused": True}
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(state_path, state)
    if args.stop_after == "chart":
        print(json.dumps({"status": "stopped_for_resume_test", "stage": "chart", "case_dir": str(case_dir)}))
        return 75

    if args.force or not valid_bazi(bazi_path):
        run([
            sys.executable, str(ROOT / "scripts" / "adjudicate_bazi_l1.py"),
            str(chart_path), str(bazi_path), "--as-of", args.as_of, "--strict",
        ])
        stages["bazi_l1"] = {"status": "complete", "reused": False}
    else:
        stages["bazi_l1"] = {"status": "complete", "reused": True}

    chart = load_json(chart_path)
    bazi_l1 = load_json(bazi_path)
    bundle = {
        "schema_version": "analysis_bundle_v1",
        "input_hash": contract_hash,
        "chart_id": chart.get("chart_id"),
        "start_year": args.start_year,
        "requested_years": list(range(args.start_year, args.start_year + 5)),
        "chart_data": chart,
        "bazi_l1": bazi_l1,
        "execution_policy": manifest["policy"],
        "agent_next_step": "Create all four dossiers, adjudication, score_input, fate_packet and report.md in one analysis pass; do not recalculate charts.",
    }
    write_json(bundle_path, bundle)
    context = {
        "schema_version": "analysis_context_v1",
        "input_hash": contract_hash,
        "chart_id": chart.get("chart_id"),
        "report_mode": args.mode,
        "reader_length": {"standard": [3500, 5500], "deep": [7000, 10000]}[args.mode],
        "requested_years": bundle["requested_years"],
        "professional_gate": {
            "four_native_dossiers": True,
            "competing_versions_per_major_claim": 2,
            "cross_school_positions_required": True,
            "falsifiable_revision_condition": True,
            "no_core_downgrades": True,
        },
        "systems": compact(chart.get("systems", {})),
        "bazi_l1": compact(bazi_l1),
        "validation_summary": chart.get("validation_summary", {}),
        "agent_next_step": "Read this file once; write analysis_master.json once; run materialize. Do not hand-write duplicate artifacts.",
    }
    write_compact_json(context_path, context)
    stages["analysis_bundle"] = {"status": "complete", "reused": False}
    state["status"] = "analysis_ready"
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(state_path, state)
    print(json.dumps({"status": "analysis_ready", "case_dir": str(case_dir), "context": str(context_path), "chart_reused": stages["chart"]["reused"], "bazi_reused": stages["bazi_l1"]["reused"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
