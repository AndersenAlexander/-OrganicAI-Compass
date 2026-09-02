# Originality Research Pack Architecture

The Originality and Research Innovation Pack adds three connected, academically evaluable modules:

- Adaptive Evidence-Gain Experiment Engine
- Career Transition Pareto Simulator
- Recommendation Robustness and Fairness Lab

The workflow treats career recommendations as testable hypotheses. It reuses Career Hypotheses, Evidence Passport, Career Experiments, Career Encyclopedia, Learning Path, Supported Paths, Market Radar, Decision Journal, Demo Mode, Reset Demo, and the existing research-export boundary.

Implemented behavior:

- Deterministic experiment scoring with explicit score components and versioned weights.
- Deterministic Pareto non-dominated sorting over transition paths.
- User-specific robustness runs over non-sensitive variables.
- Synthetic-only fairness audits.
- Recommendation System Card as API and accessible UI route.
- Research originality sessions requiring explicit consent.

Planned behavior:

- Production migrations if the project adopts Alembic.
- Broader scenario history pagination.
- Additional synthetic fairness fixture sets reviewed by domain experts.
- Empirical evaluation and statistical analysis after participant data exists.

Core routes:

- `/workspace/:profileId/adaptive-experiments`
- `/workspace/:profileId/adaptive-experiments/:recommendationId`
- `/workspace/:profileId/transition-simulator`
- `/workspace/:profileId/transition-simulator/:simulationId`
- `/workspace/:profileId/recommendation-robustness`
- `/research/robustness-lab`
- `/about/recommendation-system-card`

The system does not automatically change career direction, Evidence Passport, My Roadmap, applications, or Decision Journal outcomes.
