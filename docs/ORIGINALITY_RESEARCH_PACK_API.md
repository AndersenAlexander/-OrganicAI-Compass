# Originality Research Pack API

Adaptive experiments:

- `POST /api/v1/profiles/{profileId}/adaptive-experiments/analyse`
- `GET /api/v1/profiles/{profileId}/adaptive-experiments`
- `GET /api/v1/adaptive-experiments/{recommendationId}`
- `POST /api/v1/adaptive-experiments/{recommendationId}/accept`
- `POST /api/v1/adaptive-experiments/{recommendationId}/reject`
- `POST /api/v1/adaptive-experiments/{recommendationId}/save`
- `POST /api/v1/adaptive-experiments/{recommendationId}/start`
- `POST /api/v1/adaptive-experiments/{recommendationId}/outcome`
- `GET /api/v1/adaptive-experiments/{recommendationId}/alternatives`

Transition simulator:

- `GET /api/v1/transition-simulations/presets`
- `POST /api/v1/profiles/{profileId}/transition-simulations`
- `GET /api/v1/profiles/{profileId}/transition-simulations`
- `GET /api/v1/transition-simulations/{simulationId}`
- `POST /api/v1/transition-simulations/{simulationId}/run`
- `POST /api/v1/transition-simulations/{simulationId}/scenarios`
- `GET /api/v1/transition-simulations/{simulationId}/pareto-front`
- `POST /api/v1/transition-simulations/{simulationId}/compare`
- `POST /api/v1/transition-paths/{pathId}/decision-journal`
- `POST /api/v1/transition-paths/{pathId}/propose-roadmap`

Robustness and fairness:

- `POST /api/v1/profiles/{profileId}/recommendation-robustness`
- `GET /api/v1/profiles/{profileId}/recommendation-robustness`
- `GET /api/v1/recommendation-robustness/{runId}`
- `GET /api/v1/recommendation-robustness/{runId}/dependencies`
- `POST /api/v1/research/fairness-audits`
- `GET /api/v1/research/fairness-audits`
- `GET /api/v1/research/fairness-audits/{auditId}`
- `GET /api/v1/recommendation-system-card`
- `GET /api/v1/recommendation-system-card.json`

Research evaluation:

- `POST /api/v1/research/originality-sessions`
- `POST /api/v1/research/originality-sessions/{sessionId}/baseline`
- `POST /api/v1/research/originality-sessions/{sessionId}/experimental`
- `POST /api/v1/research/originality-sessions/{sessionId}/feedback`
- `GET /api/v1/research/originality-sessions/{sessionId}/results`
