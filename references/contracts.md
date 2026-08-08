# Contracts

Set `model_version` to `transparent_v1` or later when using these contracts.

## Bazi L1

```json
{
  "model_version": "bazi_l1_v1",
  "status": "ok|insufficient",
  "input_audit": {
    "missing_fields": [],
    "classification_expected_from_guardrail": "",
    "classification_consistent": true,
    "as_of": "YYYY-MM-DD",
    "age": 0
  },
  "strength_decision": {"status": "verified|insufficient", "value": "", "follow_structure_allowed": false},
  "structure_decision": {"status": "conditional_structure|verified|insufficient", "value": "", "supporting_mechanism": "", "competing_mechanism": ""},
  "useful_element_decision": {"status": "conditional_ranked_candidates|verified|insufficient", "support_candidates": [], "unfavorable_candidates": [], "climate": {}},
  "current_luck_pillar": {},
  "current_luck_contacts": [],
  "annual_activation": [],
  "domain_positions": {}
}
```

## School role manifest

```json
{
  "school": "western|ziwei|vedic|bazi",
  "role_in_run": "",
  "method_policy": {},
  "verified_modules": [],
  "downgraded_modules": [],
  "unavailable_modules": [],
  "qualified_questions": []
}
```

## Native outcome

```json
{
  "claim_id": "",
  "school": "",
  "question": "",
  "time_layer": "natal|long_period|annual|window",
  "applicability": "applicable|not_applicable|insufficient",
  "source_facts": [],
  "evidence_paths": [],
  "native_reasoning": "",
  "primary_path": "",
  "secondary_path": "",
  "rejected_path": "",
  "selection_reason": [],
  "favorable_realization": "",
  "unfavorable_realization": "",
  "natal_permission": [],
  "timing_triggers": [],
  "deciding_conditions": [],
  "failure_rule": "",
  "confidence": "high|medium|low|insufficient"
}
```

## Domain adjudication

```json
{
  "domain": "",
  "question": "",
  "consensus_tier": "high_consensus|moderate_consensus|single_school_strong_signal|conflict|insufficient",
  "consensus_reason": "",
  "event_certainty": "high|medium|low|not_applicable",
  "school_positions": {
    "western": {"position": "support|refine|limit|oppose|not_comparable|not_applicable|insufficient", "reason": "", "claim_ids": [], "evidence_paths": []},
    "ziwei": {"position": "", "reason": "", "claim_ids": [], "evidence_paths": []},
    "vedic": {"position": "", "reason": "", "claim_ids": [], "evidence_paths": []},
    "bazi": {"position": "", "reason": "", "claim_ids": [], "evidence_paths": []}
  },
  "evidence_chain": [],
  "statement_layers": {
    "model_judgment": "",
    "reality_projection": "",
    "action_guidance": "",
    "validation_condition": ""
  },
  "subjudgments": [
    {
      "question": "",
      "ruling": "",
      "alternative": "",
      "selection_reason": [],
      "life_stage_change": "",
      "failure_rule": ""
    }
  ],
  "primary_path": "",
  "secondary_path": "",
  "rejected_path": "",
  "favorable_branch": "",
  "unfavorable_branch": "",
  "deciding_conditions": [],
  "activation_periods": [],
  "concrete_event_families": [],
  "failure_rule": "",
  "confidence": "high|medium|low|insufficient",
  "unresolved": []
}
```

## Annual ruling

```json
{
  "year": 2027,
  "central_task": "",
  "carry_in": "",
  "strongest_opportunity": "",
  "main_downside": "",
  "likely_event_families": [],
  "deciding_condition": "",
  "result_preparing_next_year": "",
  "confidence": "high|medium|low"
}
```

## Timing window

```json
{
  "rank": 1,
  "start": "",
  "end": "",
  "background_period": {"start": "", "end": "", "meaning": "", "evidence_paths": []},
  "sensitivity_window": {"start": "", "end": "", "meaning": "", "evidence_paths": []},
  "transition_dates": [{"date": "", "source_school": "", "meaning": "", "not_event_date": true}],
  "primary_domain": "",
  "secondary_domains": [],
  "event_families": [],
  "real_world_carrier": "",
  "event_carriers": [],
  "supporting_chain": [],
  "contrary_signal": "",
  "failure_rule": "",
  "confidence": "high|medium|low"
}
```

## Consensus matrix row

```json
{
  "claim_id": "",
  "domain": "",
  "question": "",
  "plain_language_claim": "",
  "school_positions": {},
  "consensus_tier": "",
  "consensus_reason": "",
  "event_certainty": "",
  "selected_version": "",
  "rejected_versions": [],
  "unresolved": [],
  "validation_question": ""
}
```
