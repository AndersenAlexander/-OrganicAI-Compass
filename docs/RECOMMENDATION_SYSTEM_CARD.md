# Recommendation System Card

Version: `recommendation-system-card-v1`.

Purpose: decision support for evidence-calibrated career exploration and transition planning.

Intended users:

- OrganicAI Compass users.
- Research evaluators.
- Career advisers reviewing user-approved selected context.

Excluded uses:

- Employment guarantees.
- Psychological diagnosis.
- Automated hiring decisions.
- Benefit eligibility decisions.

Deterministic services:

- `adaptive-evidence-gain-score-v1`
- `career-transition-objectives-v1`
- `recommendation-robustness-v1`
- `synthetic-fairness-audit-v1`

AI-assisted components may explain outputs or draft reflection prompts, but authoritative scores, weights, Pareto sorting, robustness metrics, and fairness audit statuses are deterministic.

Validation status: implemented for MVP evaluation; not scientifically validated.

Human oversight:

- no automatic career direction change
- no automatic evidence change
- no automatic roadmap mutation
- no automatic Decision Journal outcome rewrite
