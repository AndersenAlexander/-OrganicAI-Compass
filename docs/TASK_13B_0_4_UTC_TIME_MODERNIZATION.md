# Task 13B.0.4 UTC Time Modernization

Status: Passed locally.

## Objective

Project-owned UTC timestamp generation was moved away from direct `datetime.utcnow()` use and into a centralized utility while preserving the current database schema, public API timestamp shapes, and PostgreSQL/SQLite behavior.

## Inventory Before Remediation

Application runtime code:

- `assessment_engine.py`, `career_resilience_engine.py`, `learning_engine.py`, `market_application_engine.py`, `interview_journey_engine.py`, `innovation_extension_engine.py`, `originality_research_engine.py`
- `live_voice_metadata.py`, `profile_generation.py`, `provider_registry.py`, `recommendation_engine.py`, `roadmap_adaptation.py`
- `routers/learning.py`, `routers/roadmap.py`, `routers/test_fixtures.py`, `routers/webhooks.py`

SQLAlchemy model defaults:

- `assessment.py`, `auth_security.py`, `career_resilience.py`, `conversation.py`, `diagnostic.py`, `fear_transform.py`, `innovation_extension.py`, `interview_journey.py`, `learning.py`, `market_application.py`, `message.py`, `originality_research.py`, `privacy.py`, `profile.py`, `provider_operations.py`, `rag_observability.py`, `recommendation.py`, `roadmap.py`, `roadmap_adaptation.py`, `user.py`

Authentication and JWT:

- `auth/dependencies.py`, `auth/security.py`, `services/auth_service.py`

Privacy, retention, and workers:

- `privacy/service.py`, `services/operational_workers.py`, `scripts/worker_retry_dead_letter_drill.py`

API serialization and diagnostics:

- Existing public response fields continue using the same ISO string shape by default.
- Diagnostic/report timestamp helpers now use the shared aware UTC utility.

Tests and fixtures:

- `test_innovation_extension_engine.py`, `test_live_voice_conversation.py`, `test_release_gate_persistence.py`, `test_task12c_operational_privacy.py`

Third-party warnings:

- Remaining deprecation warnings are from `backend/.venv/Lib/site-packages/jose/jwt.py`, where `python-jose` calls `datetime.utcnow()` internally.

## Compatibility Strategy

Selected strategy: B, preserve legacy naive UTC storage.

Evidence:

- Existing Alembic migrations use plain `sa.DateTime()` with no `timezone=True`.
- Model declarations use `DateTime` without timezone-aware configuration.
- No schema migration was required or created.

Implementation:

- `utc_now()` returns timezone-aware UTC via `datetime.now(UTC)`.
- `utc_now_naive()` is the explicit persistence-boundary helper for existing naive `DateTime` columns.
- `ensure_utc()` treats legacy naive datetimes as UTC and normalizes aware values to UTC.
- `to_utc_naive()` normalizes values before comparisons or persistence when legacy naive storage is required.
- `utc_isoformat()` defaults to the existing naive ISO string shape, with an explicit `include_offset=True` option for aware output.
- `parse_utc_datetime()` parses `Z`, offset-aware, and legacy naive strings as UTC.

Public API timestamp fields were not changed from `2026-01-01T10:00:00` to `2026-01-01T10:00:00+00:00` or `Z`.

## Files Modified

- `backend/app/core/__init__.py`
- `backend/app/core/time.py`
- `backend/app/auth/dependencies.py`
- `backend/app/auth/security.py`
- `backend/app/db/health.py`
- `backend/app/models/assessment.py`
- `backend/app/models/auth_security.py`
- `backend/app/models/career_resilience.py`
- `backend/app/models/conversation.py`
- `backend/app/models/diagnostic.py`
- `backend/app/models/fear_transform.py`
- `backend/app/models/innovation_extension.py`
- `backend/app/models/interview_journey.py`
- `backend/app/models/learning.py`
- `backend/app/models/market_application.py`
- `backend/app/models/message.py`
- `backend/app/models/originality_research.py`
- `backend/app/models/privacy.py`
- `backend/app/models/profile.py`
- `backend/app/models/provider_operations.py`
- `backend/app/models/rag_observability.py`
- `backend/app/models/recommendation.py`
- `backend/app/models/roadmap.py`
- `backend/app/models/roadmap_adaptation.py`
- `backend/app/models/user.py`
- `backend/app/privacy/service.py`
- `backend/app/routers/learning.py`
- `backend/app/routers/roadmap.py`
- `backend/app/routers/test_fixtures.py`
- `backend/app/routers/webhooks.py`
- `backend/app/scripts/create_task11_fixture.py`
- `backend/app/scripts/prune_database_backups.py`
- `backend/app/scripts/validate_openai_provider.py`
- `backend/app/scripts/worker_retry_dead_letter_drill.py`
- `backend/app/services/assessment_engine.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/career_resilience_engine.py`
- `backend/app/services/database_admin.py`
- `backend/app/services/database_immutability.py`
- `backend/app/services/http_middleware.py`
- `backend/app/services/innovation_extension_engine.py`
- `backend/app/services/interview_journey_engine.py`
- `backend/app/services/learning_engine.py`
- `backend/app/services/legacy_orphan_analysis.py`
- `backend/app/services/live_voice_metadata.py`
- `backend/app/services/market_application_engine.py`
- `backend/app/services/operational_workers.py`
- `backend/app/services/originality_research_engine.py`
- `backend/app/services/profile_generation.py`
- `backend/app/services/provider_registry.py`
- `backend/app/services/recommendation_engine.py`
- `backend/app/services/roadmap_adaptation.py`
- `backend/app/services/runtime_configuration.py`
- `backend/app/services/sqlite_to_postgres.py`
- `backend/tests/test_innovation_extension_engine.py`
- `backend/tests/test_live_voice_conversation.py`
- `backend/tests/test_release_gate_persistence.py`
- `backend/tests/test_task12c_operational_privacy.py`
- `backend/tests/test_utc_time_modernization.py`

## Warning Delta

- Before remediation: `148 passed`, `5 deselected`, `34869 warnings`.
- After remediation: `158 passed`, `5 deselected`, `55 warnings`.
- Warning reduction: `34814`.
- Remaining project-owned `datetime.utcnow()` warnings: none observed.
- Remaining third-party warnings: `55` from `python-jose` at `backend/.venv/Lib/site-packages/jose/jwt.py:311`.

No global `DeprecationWarning` suppression was added.

## Validation

- Compile checks: `python -m compileall -q app tests` passed.
- UTC/auth/privacy/worker targeted suite: `25 passed`, `28 warnings` from `python-jose`.
- Business-service suite: `41 passed`.
- Full backend suite: `158 passed`, `5 deselected`, `55 warnings`.
- PostgreSQL preparation: passed.
- Alembic head: `0004_provider_operations`.
- Schema drift: `0`.
- PostgreSQL marker suite: `5 passed`, `0 failed`, `0 skipped`, `158 deselected`.
- Timeout/hang: none observed.
- Staging `/health`: `ok`.
- Staging `/health/ready`: `ready`, PostgreSQL reachable, `migrationState=current`.

## Evidence Files

- `evidence/task13b04/backend-warnings-before.txt`
- `evidence/task13b04/backend-warnings-after-final.txt`
- `evidence/task13b04/backend-warning-details-after-always.txt`
- `evidence/task13b04/postgres-prepare-after-utc-final.txt`
- `evidence/task13b04/postgres-marker-after-utc-final.txt`
- `evidence/task13b04/staging-health-final.json`
- `evidence/task13b04/staging-ready-final.json`

## Security and Data Safety

- PostgreSQL URLs in evidence are redacted.
- `.env.postgres-test` was not written to reports or source archives.
- No Docker volume, staging database, staging credential, user account data, or non-disposable database was deleted or recreated.
- PostgreSQL preparation recreated only the disposable `organicai_task13b03_test` database.

## Remaining Limitations

- `python-jose` still emits `datetime.utcnow()` deprecation warnings internally. This is third-party-owned and was not patched in `.venv`.
- Public timestamp serialization remains legacy naive ISO format by design. A future API version can introduce explicit `+00:00`/`Z` timestamps with frontend contract tests.
