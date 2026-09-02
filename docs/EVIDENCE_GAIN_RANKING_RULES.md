# Evidence-Gain Ranking Rules

Rule-set version: `adaptive-evidence-gain-weights-v1`

Algorithm version: `adaptive-evidence-gain-score-v1`

Priority bands:

- High evidence value
- Useful evidence value
- Exploratory value
- Low current feasibility
- Insufficient information

Scores are deterministic decision-support bands, not scientific probabilities. The weighted composite is internal and every component value and weight is returned to the user.

Missing-data behavior:

- missing skill evidence increases uncertainty;
- outdated skill evidence increases recency uncertainty;
- weak evidence is not treated as incapability;
- missing market or job links are exposed as empty arrays or data-quality notes.

Tie-breaking is deterministic by internal score, title and template ID.
