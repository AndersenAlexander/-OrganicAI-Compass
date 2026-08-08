# Human Potential & Career Assessment

## Purpose

The Human Potential & Career Assessment supports self-reflection and career exploration. It is based on self-reported information and deterministic prototype scoring methods. It is not a psychological diagnosis, employment decision, or guarantee of professional success. Final decisions remain with the user.

## Architecture

- Existing Human Diagnostic and profile routes remain unchanged.
- New assessment data is stored in versioned SQLAlchemy entities linked to `profile_id`.
- The backend exposes `/api/v1` assessment endpoints.
- The frontend adds profile-aware routes under `/workspace/:profileId/...`.
- Human Potential Map adds optional assessment layers without replacing the original map.
- Roadmap actions are created only after the user explicitly clicks "Add exploratory action to My Roadmap".

## Data Model

New persistent entities include:

- `assessment_definitions`, `assessment_modules`, `assessment_items`, `assessment_options`
- `assessment_sessions`, `assessment_responses`, `assessment_scores`
- `personality_results`, `career_interest_results`, `work_value_results`
- `skills_inventory`, `skill_evidence`
- `ai_readiness_results`, `change_readiness_results`
- `career_role_templates`, `career_matches`, `career_match_factors`
- `career_comparisons`, `career_decisions`, `assessment_interpretations`

The current project has no Alembic `versions` directory. Development persistence follows the existing `Base.metadata.create_all` pattern. Production should add reviewed migrations before deployment.

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

- `python -m pytest tests/test_assessment_engine.py tests/test_demo_account.py`

Frontend:

- `npm run build`
- `npm run test:e2e -- tests/e2e/assessment-career.spec.ts`

## Deferred

- Automatic CV parsing.
- Labour-market salary or vacancy ingestion.
- Alembic migration files.
- LLM-generated narrative summaries for assessment results.
- Full export UI for assessment data.
- Complete visual QA screenshot pack for all requested viewport sizes.
