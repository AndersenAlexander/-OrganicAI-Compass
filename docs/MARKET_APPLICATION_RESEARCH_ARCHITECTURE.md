# Market-Aware Application Journey And Research Architecture

## Scope

This module extends OrganicAI Compass with a market-aware employment workflow:

1. Profile and Evidence Passport.
2. Market Radar.
3. Job Analyzer.
4. Application Studio.
5. Application Tracker.
6. Outcome recalibration.
7. Research Evaluation export.

Existing modules remain authoritative for profile, skills, evidence, career matching, supported paths, learning, and roadmap behavior.

## Backend Architecture

Core backend files:

- `app/models/market_application.py`
- `app/services/market_application_engine.py`
- `app/routers/market_application.py`

Model groups:

- Labour-market providers, sync cursors, sync runs, job postings, versions, locations, classifications, skill mentions, and language requirements.
- Market preferences, signal runs, and signal results.
- ESCO concepts, labels, mappings, and normalisation runs.
- Job analyses, versions, requirements, corrections, evidence matches, and readiness results.
- Master career profile entries reused by application documents.
- Application documents, sections, claims, evidence links, versions, review events, and exports.
- Job applications, events, stages, contacts, feedback, outcomes, and recalibration runs.
- Research studies, versions, participants, consent, sessions, assignments, questions, responses, interaction metrics, and export runs.

## Provider Boundary

The market provider layer supports:

- `demo`: deterministic fictional Norwegian vacancies.
- `nav_stilling_feed`: backend-only NAV Job Vacancy Feed adapter, disabled by default.
- `future_provider`: reserved adapter placeholder.

Provider health is surfaced through `/api/v1/market/providers/status`. Missing credentials return degraded provider status and do not break the user journey.

NAV implementation notes are based on official documentation checked on 2026-07-21:

- https://navikt.github.io/pam-stilling-feed/
- https://arbeidsplassen.nav.no/vilkar-api

## Readiness Logic

Job readiness is deterministic and label-based:

- Apply now.
- Apply with positioning.
- Prepare first.
- Low current feasibility.
- Insufficient information.

No single market score is produced. Reasons, blockers, and recommended actions are stored with a deterministic version.

## Evidence Lock

Application documents contain reviewable factual claims. Claims can be supported, partially supported, transferable, user-confirmed, unverified, conflicting, or blocked. Blocked claims require safer wording or explicit export acknowledgement.

Exports are local document exports only. The system does not auto-apply and does not make ATS outcome guarantees.

## Research Evaluation

Research Evaluation supports:

- versioned consent;
- withdrawal;
- pre/post/custom Likert and SUS-style questions;
- pseudonymous participants;
- workflow metrics that exclude raw typed personal text;
- JSON plus CSV preview export;
- default exclusion of demo records unless requested.

The export excludes names, email addresses, raw CV text, raw cover-letter text, personal URLs, and national identity numbers.

