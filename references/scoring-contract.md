# Four-dimensional scoring contract v1.0

Scores are comparative reading indices, not empirical probabilities, personal value or guaranteed outcomes.

## Inputs per domain

Each of the four schools provides `support_strength`, `friction_strength` in the integer range 0-4 and `evidence_quality` in the range 0-1. Semantically duplicate claims must be merged before scoring.

## Formulas

```text
Potential = round(100 * sum(support_strength * evidence_quality) / 16)
Friction  = round(100 * sum(friction_strength * evidence_quality) / 16)
Flow      = round(clamp(50 + 0.45*(Potential-50) - 0.35*(Friction-50) + time_modifier, 0, 100))

Confidence = round(
  calculation_completeness * 0.30 +
  rule_specificity         * 0.20 +
  derivation_completeness  * 0.20 +
  independent_support      * 0.15 +
  time_stability           * 0.10 +
  falsifiability           * 0.05
)
```

`time_modifier` is limited to -15 through +15. Natal scores use 0.

## Bands

- 0-39: constrained
- 40-54: low
- 55-69: moderate
- 70-84: strong
- 85-100: very strong

Confidence never changes Potential, Friction or Flow. A high-potential low-confidence result must remain visibly uncertain.

