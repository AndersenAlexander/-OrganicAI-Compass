import json
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.database import SessionLocal, check_database_connection, dispose_database_engine, get_database_migration_status, init_db
from app.routers import advanced, assessments, auth, career_resilience, chat, conversations, demo, diagnostics, elevenlabs_llm, innovation_extension, interview_journey, learning, market_application, originality_research, privacy, profile_tools, profiles, rag, recommendations, research, roadmap, system_operations, users, voice, webhooks
from app.services.error_responses import error_response, request_id_from_request
from app.services.http_middleware import (
    RateLimitMiddleware,
    RequestBodyLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    StructuredLoggingMiddleware,
    configure_logging,
)
from app.services.telemetry import OpenTelemetryMiddleware, emit_validation_span, flush_telemetry
from app.services.runtime_configuration import assert_startup_configuration, check_runtime_configuration, failed_required_categories
from app.services.metrics import prometheus_text, set_database_metrics

settings = get_settings()

logger = logging.getLogger("organicai.lifecycle")


def _log_lifecycle(event_type: str, **extra: object) -> None:
    record = json.dumps(
        {
            "event_type": event_type,
            "service": settings.otel_service_name,
            "environment": settings.app_env,
            **extra,
        },
        separators=(",", ":"),
    )
    logger.info(record)
    print(record, flush=True)


def _emit_database_validation_span(operation: str) -> None:
    emit_validation_span(
        "SQLAlchemy " + operation.upper(),
        {
            "db.system": "postgresql" if settings.database_url.startswith("postgresql") else "sqlite",
            "db.operation": operation.upper(),
        },
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    _log_lifecycle("application_startup_started")
    assert_startup_configuration(settings)
    init_db()
    if settings.demo_account_enabled:
        from app.services.demo_seed_service import ensure_demo
        with SessionLocal() as db:
            ensure_demo(db, reset=settings.demo_reset_on_startup)
    emit_validation_span("application.startup", {"lifecycle.event": "startup"})
    _log_lifecycle("application_startup_completed")
    try:
        yield
    finally:
        _log_lifecycle("application_shutdown_started")
        _log_lifecycle("provider_client_shutdown_completed", registered_clients=0, closed_clients=0)
        _log_lifecycle("telemetry_flush_started")
        flushed = flush_telemetry(timeout_seconds=5)
        _log_lifecycle("telemetry_flush_completed", flushed_spans=flushed)
        dispose_database_engine()
        _log_lifecycle("database_pool_disposed")
        _log_lifecycle("application_shutdown_completed")


app = FastAPI(title=settings.app_name, version=settings.app_version or "0.0.0", lifespan=lifespan)

app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(OpenTelemetryMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_host_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Retry-After"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else None
    code = None
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 409:
        code = "CONFLICT"
    elif exc.status_code == 413:
        code = "REQUEST_TOO_LARGE"
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
    elif exc.status_code == 429:
        code = "RATE_LIMITED"
    elif exc.status_code == 503:
        code = "SERVICE_UNAVAILABLE"
    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=detail,
        headers={key: str(value) for key, value in (exc.headers or {}).items()},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = None
    if settings.app_env != "production":
        details = [{"loc": item.get("loc"), "msg": item.get("msg"), "type": item.get("type")} for item in exc.errors()[:5]]
    return error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="The request contains invalid data.",
        details=details,
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, _exc: SQLAlchemyError):
    return error_response(
        request,
        status_code=503,
        code="DATABASE_UNAVAILABLE",
        message="The database is temporarily unavailable.",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, _exc: Exception):
    return error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="The server could not complete the request.",
    )

app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(elevenlabs_llm.router, prefix="/api/elevenlabs", tags=["elevenlabs custom llm"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(demo.auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(privacy.router, prefix="/api/privacy", tags=["privacy"])
if settings.app_env == "test":
    from app.routers import test_fixtures

    app.include_router(test_fixtures.router, prefix="/api", tags=["test fixtures"])
app.include_router(system_operations.router, prefix="/api/system", tags=["system operations"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
app.include_router(roadmap.router, prefix="/api/roadmap", tags=["roadmap"])
app.include_router(roadmap.api_router, prefix="/api", tags=["roadmap adaptation"])
app.include_router(rag.router, prefix="/api/rag", tags=["rag"])
app.include_router(research.router, prefix="/api/admin/research", tags=["research"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(profile_tools.router, prefix="/api", tags=["profile tools"])
app.include_router(advanced.router, prefix="/api", tags=["advanced"])
app.include_router(assessments.router, prefix="/api/v1", tags=["assessments"])
app.include_router(learning.router, prefix="/api/v1", tags=["learning"])
app.include_router(career_resilience.router, prefix="/api/v1", tags=["career resilience"])
app.include_router(market_application.router, prefix="/api/v1", tags=["market application"])
app.include_router(interview_journey.router, prefix="/api/v1", tags=["interview journey"])
app.include_router(innovation_extension.router, prefix="/api/v1", tags=["innovation extension"])
app.include_router(originality_research.router, prefix="/api/v1", tags=["originality research"])
if settings.demo_account_enabled:
    app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
app.mount("/media", StaticFiles(directory="app/media"), name="media")

@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
async def health(request: Request) -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
        "version": settings.app_version,
        "requestId": request_id_from_request(request),
    }


@app.get("/health/live")
async def health_live(request: Request) -> dict[str, str]:
    return {
        "status": "live",
        "environment": settings.app_env,
        "version": settings.app_version,
        "requestId": request_id_from_request(request),
    }


@app.get("/health/ready")
async def health_ready(request: Request):
    report = check_runtime_configuration(settings)
    db_status = check_database_connection()
    _emit_database_validation_span("select")
    checked_out = available_connections = overflow = 0
    try:
        pool = SessionLocal.kw["bind"].pool
        checked_out = int(pool.checkedout()) if hasattr(pool, "checkedout") else 0
        size = int(pool.size()) if hasattr(pool, "size") else 0
        overflow = int(pool.overflow()) if hasattr(pool, "overflow") else 0
        available_connections = max(0, size - checked_out)
    except Exception:
        checked_out = available_connections = overflow = 0
    set_database_metrics(
        available=db_status.reachable,
        checked_out=checked_out,
        available_connections=available_connections,
        overflow=overflow,
    )
    migration_status = get_database_migration_status(settings) if settings.db_require_migration_head else None
    db_ready = db_status.reachable
    migration_ready = migration_status is None or migration_status.current

    if report.ready and db_ready and migration_ready:
        return {
            "status": "ready",
            "environment": settings.app_env,
            "version": settings.app_version,
            "database": {
                "dialect": db_status.dialect,
                "reachable": db_status.reachable,
                "migrationState": migration_status.migration_state if migration_status else "not_required",
            },
            "requestId": request_id_from_request(request),
        }
    failed = failed_required_categories(report)
    if not db_ready and "database" not in failed:
        failed.append("database")
    if not migration_ready and "database_migration" not in failed:
        failed.append("database_migration")
    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "environment": settings.app_env,
            "failedChecks": sorted(failed),
            "database": {
                "dialect": db_status.dialect,
                "reachable": db_status.reachable,
                "migrationState": migration_status.migration_state if migration_status else "not_required",
            },
            "requestId": request_id_from_request(request),
        },
        headers={"X-Request-ID": request_id_from_request(request)},
    )


@app.get("/internal/metrics")
async def internal_metrics() -> PlainTextResponse:
    if not settings.prometheus_metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics are disabled.")
    return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")


def _require_staging_validation() -> None:
    if settings.app_env not in {"staging", "test"}:
        raise HTTPException(status_code=404, detail="Validation endpoint is not available.")


@app.get("/api/system/validation/forbidden")
async def validation_forbidden() -> None:
    _require_staging_validation()
    raise HTTPException(status_code=403, detail="Synthetic validation access is forbidden.")


@app.get("/api/system/validation/slow")
async def validation_slow(request: Request, duration_seconds: float = 5.0):
    _require_staging_validation()
    duration = min(max(duration_seconds, 0.1), 20.0)
    trace_id, span_id = emit_validation_span(
        "validation.synthetic_long_running",
        {
            "validation.operation": "synthetic_long_running",
            "http.route": "/api/system/validation/slow",
        },
    )
    try:
        await asyncio.sleep(duration)
        status = "completed"
    except asyncio.CancelledError:
        status = "cancelled"
        raise
    return {
        "status": status,
        "durationSeconds": duration,
        "requestId": request_id_from_request(request),
        "traceIdSample": trace_id[:12],
        "spanIdSample": span_id[:8],
    }


@app.get("/api/system/version")
async def system_version() -> dict[str, str]:
    return {
        "appVersion": settings.app_version,
        "buildCommit": settings.build_commit or "unavailable",
        "buildTimestamp": settings.build_timestamp,
        "buildEnvironment": settings.build_environment or settings.app_env,
        "provenanceStatus": "complete" if settings.build_commit and settings.build_commit != "unavailable" else "incomplete",
    }


def require_diagnostics_access(x_diagnostics_token: str | None) -> None:
    if not settings.integration_diagnostics_enabled:
        raise HTTPException(status_code=404, detail="Integration diagnostics are disabled.")
    if settings.app_env == "production":
        configured = settings.diagnostic_access_token or ""
        if not configured or x_diagnostics_token != configured:
            raise HTTPException(status_code=403, detail="Diagnostics access is restricted.")


def _read_local_json(path: Path) -> dict | None:
    try:
        if not path.exists() or not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _release_gate_persistence_status() -> dict[str, object]:
    backup_dir = Path(settings.db_backup_directory.strip() or "./backups/database")
    pre_activation_backup_verified = any(backup_dir.glob("organicai-app-pre-activation-*.manifest.json"))
    clean_manifest = _read_local_json(Path("data/organicai-clean.manifest.json"))
    archive_report = _read_local_json(Path("../reports/database-integrity/final-orphan-archive-verification.json"))
    original_proof = _read_local_json(Path("../reports/database-integrity/original-sqlite-post-activation-proof.json"))
    reconciliation = _read_local_json(Path("../reports/database-integrity/final-data-reconciliation.json"))
    data_loss = None
    if reconciliation:
        data_loss = int(reconciliation.get("lostActiveRows") or 0) + int(reconciliation.get("lostArchivedRows") or 0)
    return {
        "preActivationBackupVerified": pre_activation_backup_verified,
        "rollbackFallbackAvailable": bool(clean_manifest and clean_manifest.get("suitableForRollback")),
        "legacyOriginalPreserved": bool(original_proof and not original_proof.get("changedDuringTask11_4")),
        "legacyOrphanArchiveVerified": bool(archive_report and archive_report.get("verificationPassed")),
        "legacyDataLoss": data_loss,
        "originalDatabaseRole": "immutable evidence",
    }


@app.get("/api/system/configuration")
async def system_configuration(
    request: Request,
    x_diagnostics_token: str | None = Header(default=None, alias="X-Diagnostics-Token"),
):
    require_diagnostics_access(x_diagnostics_token)
    report = check_runtime_configuration(settings)
    return {
        **report.model_dump(mode="json"),
        "requestId": request_id_from_request(request),
    }


@app.get("/api/system/persistence")
async def system_persistence(
    request: Request,
    x_diagnostics_token: str | None = Header(default=None, alias="X-Diagnostics-Token"),
):
    require_diagnostics_access(x_diagnostics_token)
    db_status = check_database_connection()
    migration_status = get_database_migration_status(settings)
    backup_dir = settings.db_backup_directory.strip()
    latest_backup_available = False
    if backup_dir:
        latest_backup_available = any(Path(backup_dir).glob("*.manifest.json"))
    return {
        "driver": db_status.dialect,
        "reachable": db_status.reachable,
        "schemaVersion": migration_status.current_revision,
        "headVersion": migration_status.head_revision,
        "migrationState": migration_status.migration_state,
        "productionPostgresRequired": settings.database_require_postgres_in_production,
        "pool": {
            "enabled": db_status.dialect != "sqlite",
            "sizeConfigured": settings.db_pool_size if db_status.dialect != "sqlite" else None,
            "prePing": settings.db_pool_pre_ping,
        },
        "backup": {
            "directoryConfigured": bool(backup_dir),
            "latestBackupAvailable": latest_backup_available,
            "retentionDays": settings.db_backup_retention_days,
        },
        "integrity": {
            "lastCheckStatus": "not_run",
        },
        "releaseGate": _release_gate_persistence_status(),
        "requestId": request_id_from_request(request),
    }
