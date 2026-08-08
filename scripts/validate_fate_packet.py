#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

DOMAINS = {"career", "wealth", "relationship", "home_family"}
SCHOOLS = {"western", "ziwei", "vedic", "bazi"}
POSITIONS = {"support", "refine", "limit", "oppose", "not_comparable", "not_applicable", "insufficient"}
CONSENSUS = {"high_consensus", "moderate_consensus", "single_school_strong_signal", "conflict", "insufficient"}
BANNED = re.compile(r"找到自己的方法|重新定義身份|資源配置|承載|對齊|內在轉變|模型|系統|邊界課題|成長機會")

def validate(packet):
    errors = []
    transparent = str(packet.get("model_version", "")).startswith("transparent_")
    if transparent:
        manifest = packet.get("school_role_manifest", [])
        manifest_schools = {x.get("school") for x in manifest if isinstance(x, dict)}
        if manifest_schools != SCHOOLS:
            errors.append("school_role_manifest must contain exactly western, ziwei, vedic, bazi")
        for item in manifest:
            for field in ("role_in_run", "method_policy", "verified_modules", "downgraded_modules", "unavailable_modules", "qualified_questions"):
                if field not in item:
                    errors.append(f"manifest {item.get('school')}: missing {field}")
        matrix = packet.get("consensus_matrix", [])
        if len(matrix) < 4:
            errors.append("transparent model requires at least four consensus matrix rows")
        for row in matrix:
            if not row.get("claim_id") or not row.get("plain_language_claim"):
                errors.append("consensus matrix row missing claim_id or plain_language_claim")
            if row.get("consensus_tier") not in CONSENSUS:
                errors.append(f"claim {row.get('claim_id')}: invalid consensus_tier")
            if set(row.get("school_positions", {})) != SCHOOLS:
                errors.append(f"claim {row.get('claim_id')}: school_positions must contain four schools")
    domains = {item.get("domain"): item for item in packet.get("fate_adjudication", [])}
    missing = sorted(DOMAINS - set(domains))
    if missing:
        errors.append("missing required domains: " + ", ".join(missing))
    for name, item in domains.items():
        for field in ("primary_path", "secondary_path", "rejected_path", "favorable_branch", "unfavorable_branch", "failure_rule"):
            if not item.get(field):
                errors.append(f"{name}: missing {field}")
        if not item.get("deciding_conditions"):
            errors.append(f"{name}: missing deciding_conditions")
        if not item.get("activation_periods"):
            errors.append(f"{name}: missing activation_periods")
        subjudgments = item.get("subjudgments", [])
        if subjudgments and len(subjudgments) < 4:
            errors.append(f"{name}: fewer than four subjudgments")
        if transparent:
            if item.get("consensus_tier") not in CONSENSUS:
                errors.append(f"{name}: invalid or missing consensus_tier")
            if item.get("event_certainty") not in {"high", "medium", "low", "not_applicable"}:
                errors.append(f"{name}: invalid or missing event_certainty")
            positions = item.get("school_positions", {})
            if set(positions) != SCHOOLS:
                errors.append(f"{name}: school_positions must contain four schools")
            for school, position in positions.items():
                if not isinstance(position, dict) or position.get("position") not in POSITIONS:
                    errors.append(f"{name}/{school}: invalid position")
                elif not position.get("reason"):
                    errors.append(f"{name}/{school}: missing position reason")
            if not item.get("evidence_chain"):
                errors.append(f"{name}: missing evidence_chain")
            layers = item.get("statement_layers", {})
            for field in ("model_judgment", "reality_projection", "action_guidance", "validation_condition"):
                if not layers.get(field):
                    errors.append(f"{name}: missing statement layer {field}")
    windows = packet.get("timing_windows", [])
    if len(windows) > 5:
        errors.append("more than five timing windows")
    ranks = [w.get("rank") for w in windows]
    if ranks != list(range(1, len(windows) + 1)):
        errors.append("timing windows are not consecutively ranked")
    for w in windows:
        if len(w.get("event_families", [])) > 3:
            errors.append(f"window {w.get('rank')}: more than three event families")
        for field in ("start", "end", "primary_domain", "real_world_carrier", "contrary_signal", "failure_rule"):
            if not w.get(field):
                errors.append(f"window {w.get('rank')}: missing {field}")
        if transparent:
            for field in ("background_period", "sensitivity_window"):
                layer = w.get(field, {})
                if not all(layer.get(x) for x in ("start", "end", "meaning")):
                    errors.append(f"window {w.get('rank')}: incomplete {field}")
            if not w.get("event_carriers"):
                errors.append(f"window {w.get('rank')}: missing event_carriers")
            for transition in w.get("transition_dates", []):
                if transition.get("not_event_date") is not True:
                    errors.append(f"window {w.get('rank')}: transition date must set not_event_date true")
    annual = packet.get("annual_rulings", [])
    for item in annual:
        for field in ("year", "central_task", "strongest_opportunity", "main_downside", "deciding_condition"):
            if not item.get(field):
                errors.append(f"annual {item.get('year')}: missing {field}")
    prose = packet.get("fortune_report", "")
    if isinstance(prose, str):
        found = sorted(set(BANNED.findall(prose)))
        if found:
            errors.append("banned reader abstractions: " + ", ".join(found))
    return {"ok": not errors, "errors": errors, "model_version": packet.get("model_version", "legacy"), "counts": {"domains": len(domains), "timing_windows": len(windows), "annual_rulings": len(annual), "consensus_rows": len(packet.get("consensus_matrix", []))}}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_fate_packet.py fate_packet.json")
    result = validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)

if __name__ == "__main__":
    main()
