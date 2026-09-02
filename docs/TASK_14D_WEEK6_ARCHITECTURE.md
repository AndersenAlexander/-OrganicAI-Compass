# Task 14D Week 6 Architecture

## Backend

Week 6 extends the existing `originality_research` boundary:

- models: `backend/app/models/originality_research.py`
- service: `backend/app/services/originality_research_engine.py`
- routes: `backend/app/routers/originality_research.py`
- tests: `backend/tests/test_originality_research_engine.py`

The implementation reuses:

- Career Hypotheses and Evidence Passport from `career_resilience`;
- Application Readiness, Job Analyzer and Market Radar records from `market_application`;
- Career Encyclopedia and Decision Journal from `innovation_extension`;
- Roadmap proposal and action records from `roadmap_adaptation`.

## Persistence

No new table family was introduced. Week 6 outputs are linked through existing run/result records:

- `AdaptiveExperimentRecommendation` -> `AdaptiveExperimentRun`
- `CareerTransitionPath` -> `CareerTransitionSimulation`
- `RecommendationRobustnessRun`
- `FairnessAuditRun`
- `RecommendationSystemCardVersion`

Historical outputs are not silently recalculated. Recalculation creates a new run or simulation.

## Frontend

`OriginalityResearchPage.tsx` provides:

- Adaptive Evidence-Gain Experiments;
- Career Transition Simulator and Pareto chart;
- Recommendation Robustness Lab;
- Synthetic Fairness Lab;
- Recommendation System Card;
- provenance trace display.

Routes include `/workspace/:profileId/adaptive-experiments`, `/workspace/:profileId/transition-simulator`, `/workspace/:profileId/recommendation-robustness`, `/workspace/:profileId/synthetic-fairness-lab`, `/about/recommendation-system-card` and `/research/robustness-lab`.

## Boundaries

The layer is deterministic decision support. It is not a career predictor, hiring-probability estimator, employability score, psychological assessment, official forecast, optimisation oracle or automated decision-maker.
