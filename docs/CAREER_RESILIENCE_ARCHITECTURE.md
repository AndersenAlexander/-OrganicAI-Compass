# OrganicAI Career Resilience Engine

## Contribution Statement

"The principal contribution is an evidence-based career resilience framework in which career recommendations are treated as testable hypotheses. Users complete personalised role experiments, generate structured skill evidence, compare career directions using personal, capability, market and public-support factors, and recalibrate decisions through transparent, user-controlled feedback loops."

## Architecture

The implementation extends the existing assessment, career matching, skill inventory, learning, roadmap, demo, and RAG modules. It does not introduce a duplicate profile system, skill taxonomy, career matching engine, or roadmap store.

New backend domain:

- `app.models.career_resilience`
- `app.services.career_resilience_engine`
- `app.routers.career_resilience`

New frontend domain:

- `src/pages/CareerResiliencePage.tsx`
- `src/api/careerResilienceApi.ts`
- `src/types/careerResilience.ts`

The complete evidence-calibration boundary is documented in [`EVIDENCE_CALIBRATION_LOOP.md`](EVIDENCE_CALIBRATION_LOOP.md). Persistent gap/proposal records are introduced by Alembic revision `0006_evidence_calibration_loop`.

## Career Experiments

The initial catalogue contains 12 experiments across four role families:

- AI Product Designer
- AI Integration Consultant
- RAG Application Developer
- Learning Experience Designer

Experiment modes:

- Guided
- Independent
- Evidence-only

Creating an experiment session does not automatically start it. Adding it to My Roadmap requires explicit confirmation through `add_to_roadmap`.

## Rubric Logic

Rubric scoring is deterministic. Each experiment has criteria for task understanding, deliverable quality, reasoning clarity, role-specific technique, constraints, human-centred considerations, testing or validation, and reflection quality. Ratings use the 0-4 scale:

- 0: Not demonstrated
- 1: Emerging evidence
- 2: Basic evidence
- 3: Competent evidence
- 4: Strong evidence

The LLM may explain results, but must not change scores.

## Evidence Passport

The Evidence Passport aggregates `SkillsInventory`, existing `skill_evidence`, and new evidence source, confidence, and recency records. It separates self-reported evidence from career experiments, portfolio work, professional work, certifications, mentor review, and user-confirmed external evidence.

Course completion alone is labelled as supported evidence. It does not produce practical verification.

Evidence confidence is determined from:

- source strength
- practical relevance
- recency
- specificity
- independent confirmation

The UI uses confidence labels instead of false precision.

## Recalibration

Evaluation first creates a provisional `CareerEvidenceProposal`; it does not mutate the authoritative Evidence Passport. Only an explicit user accept/edit decision promotes the evidence and triggers a recalibration of the linked hypothesis. `career_recalibration_runs` then stores before and after comparison data:

- career alignment
- assumptions
- missing evidence
- uncertainty
- new evidence
- remaining gaps
- what changed the recommendation

Career directions also expose counterfactual factors: what would strengthen and what would weaken the recommendation. These are not guaranteed causal claims.

## Best Supported Path

Supported paths keep four dimensions separate:

- Personal Fit
- Capability Fit
- Market Fit
- Support Fit

The MVP uses a curated Norway demo market snapshot. It does not claim real-time market coverage.

## Norway Support Registry

The support registry is versioned and official-source-only. Initial records include:

- NAV jobseeker registration
- NAV unemployment benefit
- NAV employment status form
- NAV training measures
- NAV work training
- NAV temporary wage subsidy
- NAV qualification programme
- NAV supplemental benefit
- Arbeidstilsynet dismissal guidance

Preliminary screening labels are limited to:

- Potentially relevant
- Possibly relevant
- Additional information required
- Probably not applicable
- Official assessment required

The system must not say that a user is eligible, that NAV will fund a programme, or that a benefit will be paid.

## Support Brief

The Support Application Brief includes employment situation, transferable skills, proposed direction, market relevance, capability gaps, selected training discussion points, proposed experiment, possible support programmes, questions for an adviser, official-source references, and unresolved eligibility questions.

Required disclaimer:

"This document supports preparation for a discussion with the relevant authority. It is not an eligibility decision or legal advice."

## Privacy And Security

Job Loss Mode requires consent before storing job-loss information. Sensitive fields are optional and include explanations. The module avoids automatic authority submissions, automatic benefit applications, raw sensitive data in logs, and frontend secrets.

Support URLs are validated against an official-source allowlist. User evidence URLs are restricted to `http` and `https`.

## RAG

Knowledge Base documents were added for career resilience methodology, evidence-based skills, and Norway job-loss support. Legal and support retrieval should be filtered to approved official-source documents only.

## Migration Status

The project currently uses SQLAlchemy `create_all` for development. The new models are imported before `create_all`. Alembic is present in requirements, but no migration environment is configured in this repository snapshot, so production migration files remain pending.

## Testing Notes

Backend tests cover catalogue retrieval, lifecycle, submission validation, rubric scoring, evidence creation, confidence, recency, recalibration, counterfactuals, supported paths, preliminary support screening, official source validation, profile ownership, and demo reset hooks.

Frontend E2E coverage is added for the new workspace flow with mocked APIs. Full manual QA across all requested viewports should still be completed before claiming production readiness.

## Known Limitations

- Market data is a demo snapshot, not live labour-market intelligence.
- Norway support coverage is curated and incomplete.
- Screening is preliminary and deterministic.
- No automatic file analysis is implemented.
- No production migration file is included.
- No official applications are submitted by the platform.
- The system has not been scientifically validated before a user study.
