# OrganicAI Compass — System Card

**Release-candidate audit:** 2026-08-24  
**Status:** internal demonstration and controlled UAT candidate; not public-production-ready.  
**Validation status:** technical implementation checks are available; synthetic engineering checks are available where labelled; empirical participant evaluation is pending.

## Purpose and intended users

OrganicAI Compass is a career-exploration and learning-planning prototype for adults who want to structure self-reflection, evidence review, experiments, market/application preparation, and interview practice. It supports decisions; it does not make them for a person, employer, adviser, or institution.

It is not a clinical, psychometric, diagnostic, hiring, employability, personality, honesty, intelligence, mental-health, legal, financial, or labour-market prediction service.

## Main workflow

The user can register, complete a self-report Human Diagnostic, review a Human Potential Map, explore Career Hypotheses, run bounded experiments, review Evidence Passport proposals, plan learning and roadmaps, inspect market/application information, practise interviews, reflect on outcomes, and record a personal decision. My Journey presents this progress without treating an exploratory output as completion or a decision.

## Data and source taxonomy

The product distinguishes **self-report**, **diagnostic interpretation**, **confirmed evidence**, **experiment evidence**, **market**, **employer feedback**, **user observation**, **user interpretation**, **system interpretation**, **system suggestion**, **user decision**, and **synthetic data**. Demo market fixtures and synthetic research records are labelled as such and are not asserted to be current external truth.

## Components and boundaries

| Component | Role | Boundary |
|---|---|---|
| Human Diagnostic and map | Repeatable interpretation of submitted self-report | Exploratory and correctable; not a validated psychometric result. |
| Career hypotheses and experiments | Deterministic, provenance-bearing suggestions and bounded evidence-gain activities | A completion creates a reviewable proposal, never confirmed evidence automatically. |
| Evidence Passport, roadmap and applications | Persisted user-owned records | Authoritative changes require explicit user action or review. |
| Market and application workflows | Source-aware preparation and requirement mapping | Coverage can be demo, cached, partial, or date-bound; no job or hiring result is guaranteed. |
| Interview Journey and Coach | Structured practice, reflection and optional text/voice interaction | No inference of personality, honesty, intelligence, anxiety, cultural fit, or employability from voice or responses. |
| Originality/research tools | Deterministic experiment ranking, Pareto trade-offs, robustness scenarios, and synthetic fixture checks | Exploratory records do not alter a profile, evidence, roadmap, application, or decision state. |
| Optional AI/provider assistance | Explanation, drafting or optional service integration when configured | It is not the authority for scores, confirmations, or user decisions. Disabled/unconfigured services must leave a usable text flow. |

## Deterministic and AI-assisted behavior

The Adaptive Evidence-Gain, Pareto, robustness, and synthetic-fairness modules use recorded deterministic inputs, rule/engine versions, assumptions, limitations, and provenance. AI-assisted text may help explain or draft; it does not silently confirm evidence, choose a career, determine a Pareto front, certify fairness, or change authoritative records.

## Security, privacy, and runtime assumptions

The application relies on authenticated, user-owned resources, origin controls, server-side secrets, and a reachable configured database. It should be deployed with reviewed secrets, transport security, backups, monitoring, a compatible PostgreSQL service, and current migrations. Provider credentials are never documented or exposed to the client.

## Limitations and non-intended uses

- No empirical participant, outcome, psychometric, fairness, or hiring-validity study is recorded.
- Synthetic Fairness Lab results are **SYNTHETIC ONLY — ENGINEERING VALIDATION**, not real-world fairness evidence or certification.
- Robustness outputs are deterministic scenario perturbations, not causal or statistical confidence estimates.
- Market/provider availability and freshness vary by configuration and source coverage.
- The system must not be used to rank applicants, make employment decisions, diagnose people, or represent a prediction of career success.

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md), [USER_CONTROL_AND_MUTATION_BOUNDARIES.md](USER_CONTROL_AND_MUTATION_BOUNDARIES.md), [CLAIM_TO_EVIDENCE_MATRIX.md](CLAIM_TO_EVIDENCE_MATRIX.md), and [ORIGINALITY_TECHNICAL_VALIDATION.md](ORIGINALITY_TECHNICAL_VALIDATION.md).
