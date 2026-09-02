# OrganicAI Compass 0.9.0-rc.2

Date: 2026-08-20

`0.9.0-rc.2` is the validated local dissertation release candidate after Task 16B and Week 7 stabilisation. It integrates Task 16A RIASEC-inspired Career Interests into the accepted RC1 lineage while preserving the Task 15A-15E architecture and acceptance boundaries. The current classification is **Stable Internal Release Candidate**; public production readiness is not claimed.

## Baseline

- RC1 baseline branch: `release/task13c-local-production-rehearsal`
- RC1 baseline commit: `7215f9a92671e8050f99d38d39fc699634631e18`
- Task 16A branch: `feature/task16a-riasec-career-interests`
- Task 16A commit: `909f1daec73cdec192e8a855103cae5e11a02ef7`
- RC2 version: `0.9.0-rc.2`
- Browser extension version: `0.1.0`
- Alembic head: `0009_collaboration_traceability_extensions`

## Task 16A Motivation

Task 16A reviewed whether Natural Discovery already represented the six RIASEC-inspired vocational-interest dimensions. The gap audit found Investigative, Artistic and Social coverage adequate, Realistic, Enterprising and Conventional coverage weak, and no dimension fully missing.

The minimal accepted change adds one lightweight Natural Discovery subsection with six direct current-preference items. This avoids question explosion while improving intentional coverage of:

- Realistic
- Investigative
- Artistic
- Social
- Enterprising
- Conventional

## Scoring Model

The rule-set version is `riasec-career-interests-v1`.

Scoring is deterministic. Direct 1-5 preference responses map to 0-100 dimension scores, produce transparent bands, and generate a current-interest pattern. Legacy Natural Discovery signals may provide lower-confidence derived context when direct answers are unavailable. The model does not use population norms and does not claim clinical, psychometric or employment-prediction validity.

## Human Potential Integration

Human Potential now presents Career Interests as a distinct profile card and map layer. The wording frames results as current career-interest patterns for reflection and exploration.

Career Interests remain distinct from:

- Current Capabilities
- Evidence
- Development Opportunities
- Constraints

## Relationship To Natural Fit

RIASEC-inspired Career Interests contribute only to Natural Fit and vocational-interest interpretation. They do not directly alter Capability Fit, Evidence Strength, Transition Feasibility, Market Fit or Support Fit.

Career Hypothesis explanations may use RIASEC signals as one contributor, for example by stating that Artistic and Investigative interest signals contribute to Natural Fit. They must not state that RIASEC proves an ideal career or guarantees success.

## Regression Results

Task 16B reran safe backend, frontend, E2E, Alembic, source-safety and archive validation gates. Week 7 then reran the feature-frozen regression scope. Full historical logs and summaries are stored in `evidence/task16b/`; the current consolidated result is in [WEEK7_STABILISATION_RELEASE_REPORT.md](WEEK7_STABILISATION_RELEASE_REPORT.md).

Results:

- Backend full local regression: `215 passed`, `5 skipped`, `85 warnings`.
- Route authorization audit: `0` blocking findings, `257` advisory findings.
- Frontend unit: `54 passed`.
- Frontend typecheck: pass.
- Frontend production build: pass with existing Vite large-chunk advisory.
- Browser extension build: pass; component version remains `0.1.0`.
- Playwright frontend-only regression: `144 passed`; real-user managed-server assertions passed but Windows teardown remains documented as a harness limitation.
- Alembic heads: one head, `0009_collaboration_traceability_extensions`; fresh full and incremental upgrades passed.
- Source safety blockers: `0`.
- Archive forbidden findings: `0`.
- Archive blocking secret findings: `0`.

The validation boundary excludes live OpenAI, ElevenLabs, NAV, ESCO, email and cloud-provider calls.

## Source Archive

The source archive is created outside the repository at:

```text
C:\Users\achid\AppData\Local\Temp\organicai-task16b\OrganicAI-Compass-source-final-0.9.0-rc.2.zip
```

The final entry count, byte size and SHA-256 are recorded in `evidence/task16b/release-manifest-rc2.json` and `evidence/task16b/archive-scan.json`.

## Limitations

- RIASEC-inspired Career Interests are not a validated psychometric RIASEC instrument.
- No population-norm, clinical, personality-diagnosis, hiring, or guaranteed-career claims are made.
- Role mappings and downstream explanations are deterministic prototype decision-support rules.
- Public production deployment remains unvalidated.
- Empirical participant evaluation remains `PENDING / NOT EXECUTED`.
- NAV/live market and voice provider acceptance remain provider-dependent.
- PostgreSQL validation is not required solely for Task 16A because no migration was added; disposable PostgreSQL may be rerun separately when the local environment is healthy.

## Future Work

- Empirical participant evaluation of the career-interest interpretation.
- Broader role catalogue review.
- Professional accessibility audit.
- Penetration testing.
- Legal/privacy review.
- Public production deployment validation.
- Live provider acceptance for OpenAI, ElevenLabs, NAV, ESCO, email and cloud infrastructure.
