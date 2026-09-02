# Final Demonstration Script

## Preconditions

1. Start the intended PostgreSQL runtime (`organicai_app` on `127.0.0.1:55432`) and confirm a successful database connection.
2. From `backend`, run `alembic current` and confirm the one source head, `0010_alembic_version_capacity`.
3. Start the backend on port 8020 and the configured frontend. Do not use a temporary SQLite override for this demonstration.
4. Use a dedicated, non-demo QA account. Do not display secrets or another user's profile.

## Demonstration flow

1. Register or log in and show the authenticated My Journey start state.
2. Complete a short Human Diagnostic. Open the Human Potential Map and point out that it is an exploratory interpretation with explicit confirmation.
3. Open Career Compatibility, inspect a direction, and start a bounded experiment. Show that the experiment produces a proposal rather than confirmed evidence.
4. Open the Evidence Passport proposal and use the explicit review action. Show source category, confidence/recency and the confirmation boundary.
5. Open roadmap, learning and recommendations. Describe them as user-controlled suggestions, not an automatic plan.
6. In Market/Application, show source/provenance and requirement confirmation before Evidence Lock, materials, or application-stage change.
7. In Interview Journey, show observable practice/reflection feedback. State that the system does not assess personality, honesty, intelligence, anxiety, cultural fit, employability, or hiring likelihood.
8. In Originality/Research, demonstrate one deterministic scenario. State that Pareto and robustness outputs are exploratory and that the fairness lab is **SYNTHETIC ONLY — ENGINEERING VALIDATION**.
9. Open Decision Journal and show that a user decision is separate from a system output.
10. Log out, log in again, and reopen the user-owned profile to demonstrate session persistence. Optionally show a second QA account cannot load the first account's profile.

## What not to claim

Do not claim live-market completeness, prediction of career or hiring outcomes, psychometric validity, fairness certification, empirical effectiveness, or public-production readiness. If an optional provider is unavailable, show its explicit unavailable/disabled state and continue using the text workflow.
