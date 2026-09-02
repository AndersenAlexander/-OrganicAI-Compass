# Originality Research Pack Testing

Backend targeted tests:

- `backend/.venv/Scripts/python.exe -m pytest tests/test_originality_research_engine.py -q`

Frontend unit tests:

- `frontend/npm.cmd run test`

Frontend E2E:

- `frontend/$env:PLAYWRIGHT_FRONTEND_ONLY='true'; npm.cmd run test:e2e -- tests/e2e/originality-research.spec.ts`

Covered behavior:

- deterministic adaptive score components and bands
- alternatives and rejection reasons
- no automatic roadmap mutation
- expected versus actual evidence gain
- Pareto non-dominated sorting
- dominated-path visibility
- scenario comparison
- Decision Journal path export
- robustness matrix and dependencies
- synthetic-only fairness audit
- Recommendation System Card
- consent-gated research sessions

Lint is unavailable until the project adds a frontend `lint` script.
