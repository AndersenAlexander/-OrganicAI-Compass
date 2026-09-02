from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException, Request
from fastapi.responses import Response
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.config import get_settings
from app.core.time import to_utc_naive, utc_now_naive as utcnow
from app.database import Base
from app.models.auth_security import AuthSession
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.privacy import (
    DataLifecycleEvent,
    DataSubjectRequest,
    DeletionSuppressionLedgerEntry,
    ExternalProviderRecord,
    PrivacyConsentEvent,
    PrivacyExportArtifact,
    PrivacyPolicyVersion,
    RetentionPolicy,
    UserPrivacySettings,
)
from app.models.user import User
from app.privacy.categories import SECURITY_SECRET_FIELDS
from app.privacy.inventory import personal_data_categories, table_registry, user_inventory_response
from app.services.error_responses import request_id_from_request
from app.services.providers.elevenlabs_privacy import retention_summary as elevenlabs_summary
from app.services.providers.openai_privacy import processing_summary as openai_summary
from app.services.research_readiness import assert_research_ready, research_readiness
from app.services.token_hashing import hash_context, hash_secret

POLICY_VERSION = "2026-privacy-draft-1"


def current_policy(db: Session) -> PrivacyPolicyVersion:
    policy = db.scalar(select(PrivacyPolicyVersion).where(PrivacyPolicyVersion.version == POLICY_VERSION))
    if policy:
        return policy
    document_path = "docs/PRIVACY_ARCHITECTURE.md"
    content = "Technical draft - requires legal review before public deployment."
    policy = PrivacyPolicyVersion(
        version=POLICY_VERSION,
        title="OrganicAI Compass Privacy Technical Draft",
        summary="Technical draft for local privacy lifecycle controls. Requires legal review before public deployment.",
        effective_at=datetime(2026, 7, 27),
        published_at=None,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        document_path=document_path,
        is_current=True,
        created_at=utcnow(),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def ensure_privacy_settings(db: Session, user: User, source: str = "migration") -> UserPrivacySettings:
    settings = db.get(UserPrivacySettings, user.id)
    policy = current_policy(db)
    if settings:
        return settings
    settings = UserPrivacySettings(
        user_id=user.id,
        conversation_history_enabled=True,
        voice_transcript_history_enabled=False,
        voice_audio_storage_enabled=False,
        product_analytics_enabled=False,
        research_participation_enabled=False,
        personalization_enabled=True,
        service_email_enabled=True,
        marketing_email_enabled=False,
        current_policy_version_id=policy.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(settings)
    db.add(
        PrivacyConsentEvent(
            user_id=user.id,
            purpose_key="essential-service",
            action="not-required",
            policy_version_id=policy.id,
            legal_basis_label="essential-service",
            source=source,
            occurred_at=utcnow(),
            metadata_json={"technicalDraft": True},
        )
    )
    db.commit()
    db.refresh(settings)
    return settings


def record_consent_event(
    db: Session,
    user: User,
    *,
    purpose_key: str,
    action: str,
    legal_basis_label: str,
    source: str,
    request: Request | None = None,
    metadata: dict | None = None,
) -> PrivacyConsentEvent:
    policy = current_policy(db)
    event = PrivacyConsentEvent(
        user_id=user.id,
        purpose_key=purpose_key,
        action=action,
        policy_version_id=policy.id,
        legal_basis_label=legal_basis_label,
        source=source,
        occurred_at=utcnow(),
        request_id=request_id_from_request(request),
        session_id=getattr(user, "_auth_session_id", None),
        ip_hash=hash_context(request.client.host if request and request.client else None),
        user_agent_hash=hash_context(request.headers.get("user-agent") if request else None),
        metadata_json=metadata or {},
    )
    db.add(event)
    return event


def preferences_payload(settings: UserPrivacySettings) -> dict:
    return {
        "conversationPersistenceMode": "account-history" if settings.conversation_history_enabled else "ephemeral",
        "voiceTranscriptPersistenceMode": "account-history" if settings.voice_transcript_history_enabled else "ephemeral",
        "voiceAudioStorageEnabled": False,
        "productAnalyticsEnabled": settings.product_analytics_enabled,
        "researchParticipationEnabled": settings.research_participation_enabled,
        "personalizationEnabled": settings.personalization_enabled,
        "serviceEmailEnabled": settings.service_email_enabled,
        "marketingEmailEnabled": settings.marketing_email_enabled,
        "updatedAt": settings.updated_at.isoformat(),
    }


def update_preferences(db: Session, user: User, payload: dict, request: Request | None = None) -> UserPrivacySettings:
    settings = ensure_privacy_settings(db, user)
    if payload.get("researchParticipationEnabled") is True:
        assert_research_ready()
    changes: list[tuple[str, bool, bool]] = []
    mapping = {
        "conversationPersistenceMode": ("conversation_history_enabled", lambda value: value == "account-history", "conversation-history"),
        "voiceTranscriptPersistenceMode": ("voice_transcript_history_enabled", lambda value: value == "account-history", "voice-transcript-history"),
        "productAnalyticsEnabled": ("product_analytics_enabled", bool, "product-analytics"),
        "researchParticipationEnabled": ("research_participation_enabled", bool, "research-participation"),
        "personalizationEnabled": ("personalization_enabled", bool, "personalization"),
        "serviceEmailEnabled": ("service_email_enabled", bool, "service-email"),
        "marketingEmailEnabled": ("marketing_email_enabled", bool, "marketing-email"),
    }
    if payload.get("voiceAudioStorageEnabled"):
        raise HTTPException(status_code=422, detail="Voice audio storage is not available.")
    for key, (attr, caster, purpose) in mapping.items():
        if key not in payload:
            continue
        old = bool(getattr(settings, attr))
        new = bool(caster(payload[key]))
        if old != new:
            setattr(settings, attr, new)
            changes.append((purpose, old, new))
    settings.updated_at = utcnow()
    for purpose, _old, new in changes:
        record_consent_event(
            db,
            user,
            purpose_key=purpose,
            action="granted" if new else "withdrawn",
            legal_basis_label="optional-consent",
            source="privacy-center",
            request=request,
            metadata={"preferenceChanged": True},
        )
    db.commit()
    db.refresh(settings)
    return settings


def summary(db: Session, user: User) -> dict:
    settings = ensure_privacy_settings(db, user)
    categories = personal_data_categories()
    return {
        "policy": {
            "version": current_policy(db).version,
            "title": current_policy(db).title,
            "technicalDraft": True,
            "legalReviewRequired": True,
        },
        "preferences": preferences_payload(settings),
        "categoryCount": len(categories),
        "providerCount": 4,
        "backupDisclosure": "Deletion removes active database rows. Existing backups expire by retention policy and restore workflows must apply the deletion-suppression ledger.",
        "legacyOrphanArchive": "The Task 11 legacy orphan archive remains outside active user export, deletion, research and RAG flows.",
    }


def consent_events(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(PrivacyConsentEvent).where(PrivacyConsentEvent.user_id == user.id).order_by(PrivacyConsentEvent.occurred_at.desc())).all()
    return [
        {
            "id": row.id,
            "purposeKey": row.purpose_key,
            "action": row.action,
            "legalBasisLabel": row.legal_basis_label,
            "source": row.source,
            "occurredAt": row.occurred_at.isoformat(),
        }
        for row in rows
    ]


def requests_for_user(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(DataSubjectRequest).where(DataSubjectRequest.user_id == user.id).order_by(DataSubjectRequest.submitted_at.desc())).all()
    return [
        {
            "id": row.id,
            "type": row.request_type,
            "status": row.status,
            "scope": row.scope_json,
            "submittedAt": row.submitted_at.isoformat(),
            "completedAt": row.completed_at.isoformat() if row.completed_at else None,
            "resultSummary": row.result_summary_json,
        }
        for row in rows
    ]


def provider_summary(db: Session, user: User) -> list[dict]:
    linked = db.scalar(select(func.count()).select_from(ExternalProviderRecord).where(ExternalProviderRecord.user_id == user.id)) or 0
    eleven = elevenlabs_summary()
    openai = openai_summary()
    return [
        {
            "provider": "OpenAI",
            "purpose": "AI response generation, transcription and embeddings when those features are used.",
            "dataCategories": ["conversation-history", "diagnostic-profile", "provider-operational"],
            "retentionStatus": openai["retentionStatus"],
            "deletionCapability": openai["deletionCapability"],
            "connectivity": "configured-unverified" if get_settings().active_openai_api_key else "not-configured",
            "featuresUsed": ["chat-completions", "embeddings", "transcription"],
            "trainingOptInStatus": get_settings().openai_training_opt_in_status,
            "abuseMonitoringMode": get_settings().openai_abuse_monitoring_mode,
            "dataResidencyStatus": get_settings().openai_data_residency_region,
            "dataControlsVerified": bool(get_settings().openai_project_data_controls_verified and get_settings().openai_data_controls_verified_at),
            "transferReviewStatus": "manual-review-required",
            "dpaReviewStatus": "manual-review-required",
            "lastVerifiedDate": get_settings().openai_data_controls_verified_at or None,
        },
        {
            "provider": "ElevenLabs",
            "purpose": "Live voice and optional text-to-speech when configured.",
            "dataCategories": ["conversation-history"],
            "retentionStatus": eleven["retentionStatus"],
            "audioSavingStatus": eleven["audioSavingStatus"],
            "zeroRetentionStatus": eleven["zeroRetentionStatus"],
            "connectivity": "configured-unverified" if get_settings().elevenlabs_api_key and get_settings().elevenlabs_agent_id else "not-configured",
            "agentConfigured": bool(get_settings().elevenlabs_agent_id),
            "webhookSignatureStatus": "configured" if get_settings().elevenlabs_webhook_secret else "not-configured",
            "deletionCapability": eleven["deletionCapability"],
            "linkedRecordCount": linked,
            "transferReviewStatus": "manual-review-required",
            "dpaReviewStatus": "manual-review-required",
            "lastVerifiedDate": None,
        },
        {
            "provider": "Email",
            "purpose": "Transactional account, security and privacy notifications.",
            "dataCategories": ["account-profile", "security-and-operations"],
            "retentionStatus": "operational-events-only",
            "connectivity": "configured-unverified" if get_settings().email_delivery_driver == "smtp" else "not-configured",
            "deliveryDriver": get_settings().email_delivery_driver,
            "senderVerifiedStatus": "manual-review-required",
            "deliveryTrackingStatus": "smtp-acceptance-only",
            "deletionCapability": "not-applicable",
            "transferReviewStatus": "manual-review-required",
            "dpaReviewStatus": "manual-review-required",
            "lastVerifiedDate": None,
        },
        {"provider": "Local PostgreSQL", "purpose": "Active application data store.", "retentionStatus": "configured", "deletionCapability": "active-database-delete", "transferReviewStatus": "not-applicable", "dpaReviewStatus": "not-applicable", "lastVerifiedDate": "2026-07-27"},
        {"provider": "Local file storage", "purpose": "Temporary exports, generated media and local evidence files.", "retentionStatus": "configured", "deletionCapability": "retention-policy-only", "transferReviewStatus": "not-applicable", "dpaReviewStatus": "not-applicable", "lastVerifiedDate": "2026-07-27"},
    ]


def research_summary(db: Session, user: User) -> dict:
    settings = ensure_privacy_settings(db, user)
    readiness = research_readiness()
    enabled = settings.research_participation_enabled and readiness["ready"]
    return {
        "participationEnabled": enabled,
        "pseudonymousSubjectId": hash_secret(f"research:{user.id}")[:24] if enabled else None,
        "directIdentifiersIncluded": False,
        "ephemeralDataExcluded": True,
        "withdrawalAvailable": True,
        "configurationComplete": readiness["ready"],
        "missingFields": readiness["missingFields"],
        "liveRecruitmentEnabled": readiness["liveRecruitmentEnabled"],
        "empiricalDataCollectionEnabled": readiness["empiricalDataCollectionEnabled"],
        "syntheticEvaluationEnabled": readiness["syntheticEvaluationEnabled"],
    }


def reauthenticate(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=403, detail="RECENT_AUTH_REQUIRED")
    session_id = getattr(user, "_auth_session_id", None)
    session = db.get(AuthSession, session_id) if session_id else None
    if session:
        session.last_used_at = utcnow()
    db.commit()


def _safe_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _row_dict(row: dict) -> dict:
    return {key: _safe_value(value) for key, value in row.items() if key not in SECURITY_SECRET_FIELDS and not key.endswith("_hash")}


def export_user_data(db: Session, user: User) -> PrivacyExportArtifact:
    settings = get_settings()
    export_dir = Path(settings.privacy_export_directory).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    request_row = DataSubjectRequest(user_id=user.id, request_type="access", status="completed", scope_json={"format": "zip-json"}, submitted_at=utcnow(), verified_at=utcnow(), processing_started_at=utcnow(), completed_at=utcnow(), result_summary_json={})
    db.add(request_row)
    db.flush()
    payload = {"manifest": {"generatedAt": utcnow().isoformat(), "format": "zip-json", "encryptedAtRest": True, "legacyOrphanArchiveIncluded": False}, "categories": [], "records": {}}
    for category in personal_data_categories():
        payload["categories"].append(category.to_dict())
    for table_name, table in Base.metadata.tables.items():
        rows = []
        if "user_id" in table.c:
            rows = [dict(item._mapping) for item in db.execute(select(table).where(table.c.user_id == user.id)).all()]
        elif table_name == "users":
            rows = [dict(item._mapping) for item in db.execute(select(table).where(table.c.id == user.id)).all()]
        elif table_name == "messages":
            conversation_ids = select(Conversation.id).where(Conversation.user_id == user.id)
            rows = [dict(item._mapping) for item in db.execute(select(table).where(table.c.conversation_id.in_(conversation_ids))).all()]
        if rows:
            payload["records"][table_name] = [_row_dict(row) for row in rows]
    raw_zip = export_dir / f"{request_row.id}.zip"
    with zipfile.ZipFile(raw_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(payload["manifest"], indent=2))
        archive.writestr("personal-data.json", json.dumps(payload, indent=2, default=str))
    key = Fernet.generate_key()
    encrypted = Fernet(key).encrypt(raw_zip.read_bytes())
    raw_zip.unlink(missing_ok=True)
    encrypted_path = export_dir / f"{request_row.id}.zip.enc"
    encrypted_path.write_bytes(encrypted)
    checksum = hashlib.sha256(encrypted).hexdigest()
    artifact = PrivacyExportArtifact(
        user_id=user.id,
        request_id=request_row.id,
        status="ready",
        storage_path=str(encrypted_path),
        encryption_key_hash=hash_secret(key.decode("ascii")),
        checksum_sha256=checksum,
        size_bytes=len(encrypted),
        created_at=utcnow(),
        expires_at=utcnow() + timedelta(hours=settings.privacy_export_expire_hours),
    )
    db.add(artifact)
    db.flush()
    request_row.result_summary_json = {"artifactId": artifact.id, "recordTables": sorted(payload["records"]), "secretValuesIncluded": False}
    db.add(DataLifecycleEvent(user_id=user.id, request_id=request_row.id, event_type="export-generated", resource_type="privacy_export", resource_id_hash=hash_secret(artifact.id), occurred_at=utcnow(), metadata_json={"sizeBytes": len(encrypted)}))
    db.commit()
    db.refresh(artifact)
    return artifact


def export_payload(artifact: PrivacyExportArtifact) -> dict:
    return {
        "id": artifact.id,
        "status": artifact.status,
        "format": artifact.format,
        "createdAt": artifact.created_at.isoformat(),
        "expiresAt": artifact.expires_at.isoformat(),
        "sizeBytes": artifact.size_bytes,
        "checksumSha256": artifact.checksum_sha256,
        "downloadedAt": artifact.downloaded_at.isoformat() if artifact.downloaded_at else None,
    }


def latest_exports(db: Session, user: User) -> list[dict]:
    rows = db.scalars(select(PrivacyExportArtifact).where(PrivacyExportArtifact.user_id == user.id).order_by(PrivacyExportArtifact.created_at.desc())).all()
    return [export_payload(row) for row in rows]


def download_export(db: Session, user: User, artifact_id: str) -> Response:
    artifact = db.get(PrivacyExportArtifact, artifact_id)
    if artifact is None or artifact.user_id != user.id or artifact.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Export not found.")
    if to_utc_naive(artifact.expires_at) <= utcnow():
        artifact.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Export expired.")
    path = Path(artifact.storage_path).resolve()
    root = Path(get_settings().privacy_export_directory).resolve()
    if root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="Export not found.")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != artifact.checksum_sha256:
        raise HTTPException(status_code=409, detail="Export checksum mismatch.")
    artifact.downloaded_at = utcnow()
    db.add(DataLifecycleEvent(user_id=user.id, request_id=artifact.request_id, event_type="export-downloaded", resource_type="privacy_export", resource_id_hash=hash_secret(artifact.id), occurred_at=utcnow(), metadata_json={}))
    db.commit()
    return Response(content=data, media_type="application/octet-stream", headers={"Content-Disposition": 'attachment; filename="organicai-personal-data.zip.enc"', "Cache-Control": "no-store"})


def delete_export(db: Session, user: User, artifact_id: str) -> None:
    artifact = db.get(PrivacyExportArtifact, artifact_id)
    if artifact is None or artifact.user_id != user.id:
        raise HTTPException(status_code=404, detail="Export not found.")
    Path(artifact.storage_path).unlink(missing_ok=True)
    artifact.deleted_at = utcnow()
    artifact.status = "deleted"
    db.commit()


def category_deletion_preview(db: Session, user: User, category_key: str) -> dict:
    categories = {category.key: category for category in personal_data_categories()}
    category = categories.get(category_key)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")
    counts = {}
    for table_name in category.tables:
        table = Base.metadata.tables.get(table_name)
        if table is None:
            continue
        if "user_id" in table.c:
            counts[table_name] = int(db.scalar(select(func.count()).select_from(table).where(table.c.user_id == user.id)) or 0)
        elif table_name == "messages":
            conversation_ids = select(Conversation.id).where(Conversation.user_id == user.id)
            counts[table_name] = int(db.scalar(select(func.count()).select_from(table).where(table.c.conversation_id.in_(conversation_ids))) or 0)
    return {"category": category.to_dict(), "rowCounts": counts, "providerImpact": "provider records may be marked pending when linked objects exist", "requiresConfirmation": True}


def delete_category(db: Session, user: User, category_key: str, confirmation: str) -> dict:
    if confirmation != category_key:
        raise HTTPException(status_code=422, detail="Confirmation does not match.")
    preview = category_deletion_preview(db, user, category_key)
    deleted = {}
    if category_key == "conversation-history":
        conversation_ids = [row[0] for row in db.execute(select(Conversation.id).where(Conversation.user_id == user.id)).all()]
        if conversation_ids:
            deleted["messages"] = db.execute(delete(Message).where(Message.conversation_id.in_(conversation_ids))).rowcount or 0
            deleted["conversations"] = db.execute(delete(Conversation).where(Conversation.id.in_(conversation_ids))).rowcount or 0
    db.add(DataLifecycleEvent(user_id=user.id, event_type="category-deletion", resource_type=category_key, resource_id_hash=hash_secret(category_key), occurred_at=utcnow(), metadata_json={"deleted": deleted, "previewCounts": preview["rowCounts"]}))
    db.commit()
    return {"categoryKey": category_key, "deletedRows": deleted, "providerStatus": "not-requested", "idempotent": True}


def append_suppression_entry(db: Session, *, subject_type: str, subject_id: str, action: str, request_id: str | None = None) -> DeletionSuppressionLedgerEntry:
    previous = db.scalar(select(DeletionSuppressionLedgerEntry).order_by(DeletionSuppressionLedgerEntry.created_at.desc()))
    subject_hash = hash_secret(f"{subject_type}:{subject_id}")
    base = f"{subject_type}|{subject_hash}|{action}|{request_id or ''}|{previous.entry_hash if previous else ''}"
    entry = DeletionSuppressionLedgerEntry(subject_type=subject_type, subject_hash=subject_hash, action=action, request_id=request_id, created_at=utcnow(), previous_entry_hash=previous.entry_hash if previous else None, entry_hash=hash_secret(base), metadata_json={})
    db.add(entry)
    return entry


def request_account_deletion(db: Session, user: User, confirmation: str) -> dict:
    if confirmation != "DELETE MY ORGANICAI ACCOUNT":
        raise HTTPException(status_code=422, detail="Confirmation phrase does not match.")
    grace_until = utcnow() + timedelta(days=get_settings().privacy_account_deletion_grace_days)
    request_row = DataSubjectRequest(user_id=user.id, request_type="account-deletion", status="queued", scope_json={"graceUntil": grace_until.isoformat()}, submitted_at=utcnow(), verified_at=utcnow(), result_summary_json={"graceUntil": grace_until.isoformat()})
    db.add(request_row)
    db.flush()
    db.add(DataLifecycleEvent(user_id=user.id, request_id=request_row.id, event_type="account-deletion-requested", occurred_at=utcnow(), metadata_json={"graceUntil": grace_until.isoformat()}))
    db.commit()
    db.refresh(request_row)
    return {"requestId": request_row.id, "status": request_row.status, "graceUntil": grace_until.isoformat()}


def cancel_account_deletion(db: Session, user: User, request_id: str) -> dict:
    request_row = db.get(DataSubjectRequest, request_id)
    if request_row is None or request_row.user_id != user.id or request_row.request_type != "account-deletion":
        raise HTTPException(status_code=404, detail="Request not found.")
    if request_row.status not in {"queued", "identity-verification-required"}:
        raise HTTPException(status_code=409, detail="Request cannot be cancelled.")
    request_row.status = "cancelled"
    request_row.cancelled_at = utcnow()
    db.add(DataLifecycleEvent(user_id=user.id, request_id=request_row.id, event_type="account-deletion-cancelled", occurred_at=utcnow(), metadata_json={}))
    db.commit()
    return {"requestId": request_row.id, "status": request_row.status}


def execute_account_deletion_fixture(db: Session, user: User, request_id: str) -> dict:
    settings = get_settings()
    if settings.app_env != "test" or not settings.account_deletion_fixture_enabled:
        raise HTTPException(status_code=404, detail="Request not found.")
    if not (user.is_demo or user.email.endswith("@example.test") or user.email.endswith("@fixture.test")):
        raise HTTPException(status_code=403, detail="Fixture execution requires a synthetic fixture user.")
    request_row = db.get(DataSubjectRequest, request_id)
    if request_row is None or request_row.user_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found.")
    if request_row.request_type != "account-deletion" or request_row.status != "queued":
        raise HTTPException(status_code=409, detail="Request is not executable.")
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    user.account_status = "pending_deletion"
    user.email = f"deleted-{hash_secret(user.id)[:16]}@deleted.local"
    user.name = "Deleted account"
    user.auth_version = int(user.auth_version or 1) + 1
    request_row.status = "completed"
    request_row.completed_at = utcnow()
    append_suppression_entry(db, subject_type="user", subject_id=user.id, action="account-deletion-completed", request_id=request_row.id)
    db.add(DataLifecycleEvent(user_id=user.id, request_id=request_row.id, event_type="account-deletion-completed", occurred_at=utcnow(), metadata_json={"tombstone": True, "providerDeletion": "pending-or-manual"}))
    db.commit()
    return {"requestId": request_row.id, "status": "completed", "tombstone": True, "sessionsRevoked": True}


def withdraw_research(db: Session, user: User, request: Request | None = None) -> dict:
    settings = ensure_privacy_settings(db, user)
    settings.research_participation_enabled = False
    settings.updated_at = utcnow()
    record_consent_event(db, user, purpose_key="research-participation", action="withdrawn", legal_basis_label="optional-consent", source="research-flow", request=request, metadata={"futureCollectionDisabled": True})
    db.add(DataLifecycleEvent(user_id=user.id, event_type="research-withdrawn", occurred_at=utcnow(), metadata_json={"directLinkageCleanup": "manual-review-required"}))
    db.commit()
    return {"researchParticipationEnabled": False, "futureResearchCollection": "disabled", "identifiableCleanup": "manual-review-required"}


def retention_dry_run(db: Session) -> dict:
    now = utcnow()
    expired_exports = db.scalar(select(func.count()).select_from(PrivacyExportArtifact).where(PrivacyExportArtifact.expires_at <= now, PrivacyExportArtifact.deleted_at.is_(None))) or 0
    expired_sessions = db.scalar(select(func.count()).select_from(AuthSession).where(AuthSession.expires_at <= now, AuthSession.revoked_at.is_(None))) or 0
    return {"dryRun": True, "expiredExports": int(expired_exports), "expiredAuthSessions": int(expired_sessions), "activeUserContentDeleted": False}


def retention_apply(db: Session) -> dict:
    now = utcnow()
    artifacts = db.scalars(select(PrivacyExportArtifact).where(PrivacyExportArtifact.expires_at <= now, PrivacyExportArtifact.deleted_at.is_(None))).all()
    for artifact in artifacts:
        Path(artifact.storage_path).unlink(missing_ok=True)
        artifact.deleted_at = now
        artifact.status = "expired"
    expired_sessions = db.execute(delete(AuthSession).where(AuthSession.expires_at <= now, AuthSession.revoked_at.is_(None))).rowcount or 0
    db.add(DataLifecycleEvent(event_type="retention-deleted", occurred_at=now, metadata_json={"expiredExports": len(artifacts), "expiredAuthSessions": expired_sessions, "activeUserContentDeleted": False}))
    db.commit()
    return {"dryRun": False, "expiredExports": len(artifacts), "expiredAuthSessions": expired_sessions, "activeUserContentDeleted": False}


def inventory_response() -> dict:
    return user_inventory_response()

