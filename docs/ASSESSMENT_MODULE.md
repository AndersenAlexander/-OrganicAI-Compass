# Human Potential & Career Assessment

## Purpose

The Human Potential & Career Assessment supports self-reflection and career exploration. It is based on self-reported information and deterministic prototype scoring methods. It is not a psychological diagnosis, employment decision, or guarantee of professional success. Final decisions remain with the user.

## Architecture

- The Human Diagnostic remains a five-step guided conversation and now stores resumable, versioned response evidence alongside the generated profile.
- New assessment data is stored in versioned SQLAlchemy entities linked to `profile_id`.
- The backend exposes `/api/v1` assessment endpoints.
- The frontend adds profile-aware routes under `/workspace/:profileId/...`.
- Human Potential Map adds optional assessment layers without replacing the original map.
- Roadmap actions are created only after the user explicitly clicks "Add exploratory action to My Roadmap".

## Human Diagnostic v2

The quick diagnostic preserves these five steps:

1. Interests & Curiosity
2. Fears & Uncertainty
3. Values & Contribution
4. Skills & Learning Style
5. AI Experience

Questions are grouped into a short guided flow rather than presented as a single score-producing test. The flow uses Likert scales, forced choices, scenario choices, limited reflection prompts, priority selection, and confidence ratings. The implementation contains approximately 40 grouped prompts plus multi-row interest, concern, and capability ratings; exact visible item counts can vary when optional reflection fields are skipped.

The optional deep-dive hub links to eight modules:

- Personality Tendencies
- Career Interests
- Work Values
- Motivation & Energy
- Work Style
- Learning & Adaptability
- Decision Style
- AI Collaboration Style

The personality module contains 30 original, balanced Big Five-informed self-reflection items: six prompts per broad dimension, with reverse-coded items. This is an exploratory prototype and is not a validated psychometric instrument.

### Scoring and evidence

Quick Diagnostic scoring is deterministic and follows this pipeline:

`raw answers -> normalized values -> domain summaries -> qualitative interpretation`

The backend owns the calculation. The LLM is not allowed to calculate or mutate scores. It may be used later for a separately labelled explanation step, but the current fallback interpretation is rule-based. Results carry version metadata, confidence/coverage labels, contradiction notes, and source/evidence status.

Self-report, calculated interpretation, and external evidence are separate layers:

- `SELF-REPORT`: what the user selected or wrote;
- `DIAGNOSTIC`: deterministic synthesis of those responses;
- `EVIDENCE`: supporting examples, artifacts, outcomes, or observations, when available.

Missing evidence lowers coverage and produces prompts for confirmation rather than silently increasing confidence. The Human Potential Map uses qualitative language such as emerging signal, early signal, partial coverage, and needs evidence; it does not expose deterministic personality percentages or predictive career certainty.

### Persistence and journey integration

Authenticated users can save an in-progress diagnostic to `/api/v1/diagnostics/draft`, reload it through `/api/v1/diagnostics/current`, and complete it through the versioned completion route. Local draft storage remains a fallback for signed-out continuation. Save & Exit returns to My Journey, where diagnostic completion, map generation, interpretation confirmation, and available deep dives are visible as progression states. Optional deep dives never block quick diagnostic completion.

The server draft is authoritative when both server and local data exist; local storage is offered as a recoverable restore option rather than silently overwriting account data. Draft writes are debounced for normal interaction and also written locally immediately, so refresh, navigation, logout/login, and transient API failures do not discard answers. The persisted journey state machine distinguishes `not_started`, `diagnostic_in_progress`, `map_generated`, and `career_hypotheses_ready`; the next action is derived from those states rather than from navigation alone.

After Human Diagnostic completion, `/api/v1/profiles/{profileId}/career-matches` creates deterministic, persisted exploratory hypotheses when no deeper assessment exists. These records have no assessment session, carry `SELF-REPORT`, `DIAGNOSTIC`, and `MISSING` source metadata, include contradictions and missing-evidence explanations, and create corresponding versioned `CareerHypothesis` rows. Missing evidence is represented as unassessed/unknown, not as low capability. A career experiment may be created from a hypothesis, but `add_to_roadmap` remains false until the user explicitly confirms roadmap insertion.

Deep-dive status is calculated per module from persisted responses (`Not started`, `In progress`, `Completed`), not from the global assessment session status. The Personality Tendencies module remains a 30-item, six-per-dimension, reverse-scored non-clinical self-report; incomplete responses do not produce an overconfident interpretation. Self-report skill rows remain separate from `SkillEvidence` and are never promoted automatically.

### Limitations

The quick diagnostic is self-report and exploratory. It is not clinical, diagnostic, employment-validating, or predictive. RIASEC-inspired interest language is used for orientation only and is not presented as a formal validated RIASEC assessment. Capability confidence is not proof of competence; evidence capture and user confirmation remain necessary.

## Data Model

New persistent entities include:

- `assessment_definitions`, `assessment_modules`, `assessment_items`, `assessment_options`
- `assessment_sessions`, `assessment_responses`, `assessment_scores`
- `personality_results`, `career_interest_results`, `work_value_results`
- `skills_inventory`, `skill_evidence`
- `ai_readiness_results`, `change_readiness_results`
- `career_role_templates`, `career_matches`, `career_match_factors`
- `career_comparisons`, `career_decisions`, `assessment_interpretations`

The current source tree has one Alembic head, `0005_human_diagnostic_v2`, following `0004_provider_operations`. Migration history was audited for duplicate revision identifiers; no duplicate `0005` revision is present in the current tree. If an older branch contains a second `0005_interview_lifecycle` file, it must be reconciled before migration rather than copied into this chain. Development may still use guarded schema creation in local/test contexts, but production-style environments should use reviewed Alembic migrations and verify the source head before startup.

## Assessment Modes

- Quick Assessment: focused self-understanding and broad career-family signals.
- Complete Assessment: all modules, detailed scoring, career matches, comparison support, and roadmap draft actions.
- Evidence-Based Assessment: complete mode plus structured manual evidence fields. Automatic CV parsing is not implemented in this sprint.

## Modules

- Professional Background
- Skills Inventory
- Personality, Work Style & Career Fit
- Career Interests
- Work Values
- AI Literacy & Readiness
- Change Readiness
- Goals & Constraints

## Item Origin and License

Personality and work-style items are original, neutral, Big Five-inspired prototype items created for this project. They are not copied from proprietary questionnaires such as commercial MBTI instruments. They are non-clinical and should not be used for diagnosis, hiring, or employment suitability decisions.

## Scoring

The backend calculates all raw scores deterministically. LLM output is not used to calculate raw personality, interest, skill, AI readiness, or career alignment scores.

Scoring rules:

- Likert items use a 1-5 scale.
- Reverse-scored items use `scaleMax + 1 - value`.
- Visual scores are normalized to 0-100 for presentation only.
- UI labels avoid false precision and use categories such as Strong alignment, Moderate alignment, Exploratory alignment, and Substantial development required.
- Personality labels use neutral language such as stronger current tendency, moderate current preference, lower current preference, or mixed/context-dependent response pattern.
- Self-reported skill level is stored separately from evidence status.

## Career Matching

The prototype career alignment model uses configurable weights:

- skills and transferable skills: 30%
- professional interests: 25%
- work values: 15%
- personality and work style: 15%
- AI readiness: 10%
- feasibility and constraints: 5%

The internal formula is:

Career Alignment = Skills Match + Interest Match + Work Values Match + Work-Style Compatibility + AI Augmentation Opportunity - Skill Gap - Feasibility Barriers.

The role catalogue is curated prototype data, not a universal labour-market model. Initial role families include Human-Centred AI Product Designer, UX Designer for AI Systems, Creative AI Technologist, AI Integration Consultant, Learning Experience Designer, AI Product Manager, RAG Application Developer, Data Analyst, Frontend Developer, Digital Experience Designer, Automation Specialist, Technical Project Manager, and Independent AI Design Service.

## Recommendation Categories

Career matches are grouped into:

- A. Augment Current Profession
- B. Adjacent Professional Roles
- C. Reskilling Opportunities
- D. Entrepreneurship or Independent Work

Every match stores supporting factors, conflicting factors, missing skills, transferable skills, AI opportunities, assumptions, limitations, and factor-level traceability.

## API

Main endpoints:

- `GET /api/v1/assessments`
- `GET /api/v1/assessments/{assessmentId}`
- `POST /api/v1/profiles/{profileId}/assessment-sessions`
- `GET /api/v1/profiles/{profileId}/assessment-sessions/current`
- `POST /api/v1/assessment-sessions/{sessionId}/responses`
- `POST /api/v1/assessment-sessions/{sessionId}/complete`
- `GET /api/v1/profiles/{profileId}/assessment-results`
- `POST /api/v1/profiles/{profileId}/assessment-results/confirm`
- `GET /api/v1/profiles/{profileId}/career-matches`
- `POST /api/v1/profiles/{profileId}/career-comparisons`
- `POST /api/v1/career-matches/{matchId}/save`
- `POST /api/v1/career-matches/{matchId}/reject`
- `POST /api/v1/career-matches/{matchId}/request-alternative`
- `POST /api/v1/career-matches/{matchId}/create-roadmap-draft`
- `DELETE /api/v1/profiles/{profileId}/assessment-data`

## Privacy

Assessment data can be personally meaningful. The implementation includes:

- explicit consent before starting;
- concise purpose and limitation notice;
- profile ownership checks consistent with existing profile APIs;
- clear separation between self-reported responses, calculated scores, and explanations;
- deletion endpoint for assessment data;
- demo data marker and reset support;
- no automatic raw-answer submission to LLM providers.

## Demo Data

Demo Reset restores a complete assessment profile with:

- mixed design and technology background;
- high creative and investigative interests;
- strong learning, autonomy, creativity, and impact values;
- developing-to-operational AI readiness;
- transferable design, communication, systems-thinking, and coordination skills;
- adjacent roles plus at least one reskilling and one entrepreneurship option.

## Tests

Backend:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_assessment_engine.py tests/test_human_diagnostic_v2.py`

Frontend:

- `npm run typecheck`
- `npm test`
- `npm run build`
- `npm run test:e2e -- tests/e2e/human-diagnostic-v2.spec.ts`
- `npm run test:e2e -- tests/e2e/human-diagnostic-full.integration.spec.ts` with an isolated test database and real backend

## Deferred

- Automatic CV parsing.
- Labour-market salary or vacancy ingestion.
- LLM-generated narrative summaries for assessment results.
- Full export UI for assessment data.
- Full visual QA screenshot pack for every requested viewport/theme combination.
