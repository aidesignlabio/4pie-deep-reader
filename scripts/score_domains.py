#!/usr/bin/env python3
import argparse, json
from pathlib import Path

SCHOOLS = {"bazi", "ziwei", "western", "vedic"}
COMPONENT_WEIGHTS = {
    "calculation_completeness": .30,
    "rule_specificity": .20,
    "derivation_completeness": .20,
    "independent_support": .15,
    "time_stability": .10,
    "falsifiability": .05,
}

def clamp(value, low=0, high=100): return max(low, min(high, value))

def band(value):
    if value < 40: return "constrained"
    if value < 55: return "low"
    if value < 70: return "moderate"
    if value < 85: return "strong"
    return "very_strong"

def score_domain(item):
    rows = item.get("schools", [])
    if {x.get("school") for x in rows} != SCHOOLS:
        raise ValueError(f"{item.get('domain')}: schools must contain exactly {sorted(SCHOOLS)}")
    support = friction = 0.0
    for row in rows:
        s = row.get("support_strength"); f = row.get("friction_strength"); q = row.get("evidence_quality")
        if not isinstance(s, int) or not 0 <= s <= 4: raise ValueError("support_strength must be integer 0..4")
        if not isinstance(f, int) or not 0 <= f <= 4: raise ValueError("friction_strength must be integer 0..4")
        if not isinstance(q, (int, float)) or not 0 <= q <= 1: raise ValueError("evidence_quality must be 0..1")
        support += s * q; friction += f * q
    potential = round(clamp(100 * support / 16))
    friction_score = round(clamp(100 * friction / 16))
    modifier = item.get("time_modifier", 0)
    if not isinstance(modifier, (int, float)) or not -15 <= modifier <= 15:
        raise ValueError("time_modifier must be -15..15")
    flow = round(clamp(50 + .45 * (potential - 50) - .35 * (friction_score - 50) + modifier))
    comps = item.get("confidence_components", {})
    if set(comps) != set(COMPONENT_WEIGHTS): raise ValueError("confidence_components keys do not match contract")
    for key, value in comps.items():
        if not isinstance(value, (int, float)) or not 0 <= value <= 100: raise ValueError(f"{key} must be 0..100")
    confidence = round(sum(comps[k] * w for k, w in COMPONENT_WEIGHTS.items()))
    return {
        "domain": item["domain"], "label": item.get("label") or item["domain"], "flow_score": flow, "flow_band": band(flow),
        "potential_score": potential, "potential_band": band(potential),
        "friction_score": friction_score, "friction_band": band(friction_score),
        "confidence_score": confidence, "confidence_band": band(confidence),
        "time_modifier": modifier, "formula_version": "4pie-score-1.0",
        "confidence_components": comps,
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("output"); args=ap.parse_args()
    data=json.loads(Path(args.input).read_text(encoding="utf-8"))
    result={"score_version":"1.0.0", "domains":[score_domain(x) for x in data.get("domains",[])]}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"output":args.output,"domains":len(result["domains"])},ensure_ascii=False))
if __name__=="__main__": main()
