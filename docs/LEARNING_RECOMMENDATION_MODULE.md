# Personalised Learning Path Module

## Purpose

The module recommends learning actions after a user has completed the assessment, reviewed career directions, selected or saved a target direction, and has skill-gap data. It is decision support for professional learning, not a guarantee of reskilling success or employment.

## Architecture

- Career context comes from `CareerMatch` and `CareerRoleTemplate`.
- Current skills come from `SkillsInventory`; self-reported skills are not treated as verified.
- Role requirements are compared with current levels by `learning_engine.py`.
- Skill gaps become `LearningObjective` records.
- Resources come from `LearningResource` records seeded by the curated catalogue.
- Provider adapters are defined through `LearningProviderAdapter`; external APIs are optional and disabled by default.
- Recommendations are ranked deterministically and stored with `LearningRecommendationFactor` rows.
- Roadmap conversion creates normal `RoadmapAction` rows with `source_type="learning_resource"` only after explicit confirmation.

## Added Data Models

- `LearningProvider`
- `LearningResource`
- `LearningResourceVersion`
- `LearningResourceSkill`
- `LearningResourceObjective`
- `LearningResourceVerification`
- `LearningPreferences`
- `SkillGapAnalysis`
- `SkillGapItem`
- `LearningObjective`
- `LearningRecommendationRun`
- `LearningRecommendation`
- `LearningRecommendationFactor`
- `LearningResourceFeedback`
- `LearningPath`
- `LearningPathPhase`
- `LearningPathItem`
- `PracticalProject`
- `RoadmapLearningAction`
- `LearningResourceComparison`
- `ExternalProviderCache`

## Catalogue

The MVP catalogue contains 53 stored resource records across internal resources, official documentation, online courses, interactive tutorials, YouTube playlist entry points, Udemy courses, practical projects, portfolio projects, professional interviews, workshops, and job-description analysis exercises.

Unknown metadata remains null or is presented as "Not provided", "Not verified", or "Check provider page". Affiliate status never improves ranking.

## Provider Strategy

Stage 1 is implemented:

- internal curated catalogue;
- manually curated official documentation;
- manually curated YouTube playlist entry points;
- manually curated Udemy and other course links;
- deterministic filtering and ranking;
- verification metadata;
- roadmap integration.

Stages deferred:

- YouTube Data API metadata refresh;
- Udemy official API integration;
- automatic external search;
- real-time price, rating, playlist, or availability refresh.

No unauthorised scraping is implemented.

## Skill-Gap Method

For each selected role requirement, the engine records:

- current level;
- target level;
- gap size;
- importance;
- evidence status;
- required or optional status;
- AI augmentation possibility;
- prerequisites;
- gap status;
- priority label.

Gap statuses include No gap, Small gap, Moderate gap, Significant gap, Missing prerequisite, and Evidence required.

Priority labels are Essential, High priority, Recommended, Supplementary, and Optional. Internal numeric scores are traceability aids, not scientific precision.

## Ranking Weights

Prototype weights:

- skill-gap relevance: 30%;
- level compatibility: 15%;
- learning-objective coverage: 15%;
- source quality: 10%;
- language fit: 8%;
- time fit: 7%;
- budget fit: 5%;
- practical evidence value: 5%;
- freshness: 3%;
- format preference: 2%.

The weights are transparent prototype defaults, not scientifically validated universal constants.

## AI Responsibility Boundary

Deterministic code:

- selects career context;
- calculates gaps;
- creates learning objectives from templates;
- filters resources;
- ranks resources;
- stores factors;
- creates roadmap actions only after confirmation.

AI may:

- explain a stored recommendation;
- suggest ordering;
- compare stored resources;
- draft a weekly plan from retrieved resources.

AI must not:

- invent courses, URLs, providers, prices, ratings, instructors, or availability;
- change deterministic ranking;
- claim guaranteed career outcomes.

## API

Main endpoints under `/api/v1`:

- `GET /learning/providers`
- `GET /learning/resources`
- `GET /learning/resources/{resourceId}`
- `GET|PUT /profiles/{profileId}/learning-preferences`
- `POST|GET /profiles/{profileId}/skill-gap-analysis`
- `POST|GET /profiles/{profileId}/learning-recommendations`
- `POST /learning-recommendations/{recommendationId}/save`
- `POST /learning-recommendations/{recommendationId}/reject`
- `POST /learning-recommendations/{recommendationId}/feedback`
- `POST /learning-recommendations/{recommendationId}/alternative`
- `POST /learning-recommendations/{recommendationId}/add-to-roadmap`
- `POST|GET /profiles/{profileId}/learning-resource-comparisons`
- `GET /profiles/{profileId}/learning-path`
- `POST /profiles/{profileId}/learning-path/generate`
- `PUT /profiles/{profileId}/learning-path`
- `POST /learning-path-items/{itemId}/progress`
- `DELETE /profiles/{profileId}/learning-data`

## Frontend Routes

- `/workspace/:profileId/learning`
- `/workspace/:profileId/learning/recommendations`
- `/workspace/:profileId/learning/compare`
- `/workspace/:profileId/learning/preferences`
- `/workspace/:profileId/learning/progress`

The routes reuse active profile handling and avoid `undefined`, `null`, or empty profile IDs.

## Environment Variables

External APIs are off by default:

```env
LEARNING_RESOURCE_EXTERNAL_SEARCH_ENABLED=false
YOUTUBE_API_ENABLED=false
YOUTUBE_API_KEY=
YOUTUBE_REGION_CODE=US
YOUTUBE_DEFAULT_LANGUAGE=en
UDEMY_API_ENABLED=false
UDEMY_CLIENT_ID=
UDEMY_CLIENT_SECRET=
UDEMY_AFFILIATE_ID=
LEARNING_RESOURCE_CACHE_TTL_SECONDS=86400
LEARNING_RESOURCE_REQUEST_TIMEOUT_SECONDS=10
```

Secrets are backend-only and must never be exposed in frontend bundles.

## Security And Privacy

- External URL validation rejects unsafe schemes such as `javascript:`.
- External API calls are backend-only.
- Provider failures are cached as non-blocking errors.
- Recommendation explanations are derived from stored resource and factor data.
- Users can reject resources, request alternatives, record feedback, and delete learning recommendation history.
- Demo data is separated from real user data.

## Schema Status

The project currently uses SQLAlchemy `create_all` in development. No Alembic migration directory is present, so this module preserves development compatibility and documents the production migration need. Production use would require Alembic migration files, operational monitoring, real auth hardening, and provider access reviews.

## Tests

Backend tests cover catalogue sync, unsafe URL rejection, no-career-selected state, skill-gap generation, objective generation, deterministic ranking, factor traceability, filtering, feedback recalibration, provider failure fallback, roadmap confirmation, learning path generation, and profile ownership.

Frontend E2E covers a mocked demo flow from career compatibility to learning recommendations, comparison, roadmap confirmation, progress evidence, demo reset, and no undefined or null links.
