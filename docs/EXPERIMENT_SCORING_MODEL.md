# Experiment Scoring Model

Scoring version: `adaptive-evidence-gain-score-v1`.

Weight version: `adaptive-evidence-gain-weights-v1`.

All dimensions are normalized to `0..1` before aggregation.

Positive components:

- `uncertainty_reduction`: 0.16
- `evidence_importance`: 0.14
- `market_relevance`: 0.11
- `cross_path_transferability`: 0.10
- `portfolio_value`: 0.11
- `feasibility`: 0.10
- `support_availability`: 0.08
- `user_preference_alignment`: 0.08

Negative components:

- `time_cost`: 0.08
- `monetary_cost`: 0.05
- `complexity`: 0.06
- `accessibility_barrier`: 0.05
- `repetition_penalty`: 0.05
- `evidence_redundancy`: 0.06
- `implementation_risk`: 0.06

Conceptual formula:

```text
priority =
  weighted positive evidence-gain components
  - weighted cost/risk/redundancy components
  + calibration offset
```

Display bands:

- Very strong recommendation
- Strong recommendation
- Moderate recommendation
- Exploratory recommendation
- Insufficient information

The UI displays components and qualitative bands, not false-precision percentages.
