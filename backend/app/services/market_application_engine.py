from __future__ import annotations

import csv
import hashlib
import html
import ipaddress
import json
import re
import socket
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.core.time import utc_now_naive
from io import StringIO
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.assessment import CareerMatch, SkillEvidence, SkillsInventory
from app.models.career_resilience import CareerHypothesis, SkillEvidenceConfidence, SkillRecency
from app.models.innovation_extension import BrowserJobCapture
from app.models.market_application import (
    ApplicationContact,
    ApplicationDocument,
    ApplicationDocumentVersion,
    ApplicationFeedback,
    ApplicationOutcome,
    ApplicationRecalibrationRun,
    ApplicationStageRecord,
    CareerProfileEntry,
    DocumentClaim,
    DocumentClaimEvidenceLink,
    DocumentReviewEvent,
    DocumentSection,
    EscoConcept,
    EscoLabel,
    EscoMapping,
    JobAnalysis,
    JobAnalysisCorrection,
    JobAnalysisVersion,
    JobApplication,
    JobApplicationEvent,
    JobClassification,
    JobLanguageRequirement,
    JobLocation,
    JobPosting,
    JobPostingVersion,
    JobReadinessResult,
    JobRequirement,
    JobRequirementEvidenceMatch,
    JobSkillMention,
    LabourMarketProviderRecord,
    LabourMarketSyncCursor,
    LabourMarketSyncRun,
    MarketRadarPreference,
    MarketSignalResult,
    MarketSignalRun,
    MasterCareerProfile,
    ResearchAssignment,
    ResearchConsent,
    ResearchExportRun,
    ResearchInteractionMetric,
    ResearchParticipant,
    ResearchQuestion,
    ResearchResponse,
    ResearchSession,
    ResearchStudy,
    ResearchStudyVersion,
    SkillNormalisationRun,
)
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.services.career_resilience_engine import evidence_passport

MARKET_APPLICATION_VERSION = "market-application-v1"
DEMO_MARKET_VERSION = "demo-labour-market-no-v1"
NAV_STILLING_DOC_URL = "https://navikt.github.io/pam-stilling-feed/"
NAV_TERMS_URL = "https://arbeidsplassen.nav.no/vilkar-api"
NAV_DOC_CHECKED_DATE = "2026-07-21"
ESCO_NORMALISATION_VERSION = "esco-normalisation-v1"
RESEARCH_CONSENT_VERSION = "research-consent-v1"
RESEARCH_EXPORT_VERSION = "research-export-v1"
MAX_PASTED_AD_CHARS = 24000
MAX_URL_RESPONSE_BYTES = 1_000_000
MARKET_COVERAGE_MINIMUM = 3
REQUIREMENT_TYPES = {"mandatory", "preferred", "unclear"}
REQUIREMENT_CATEGORIES = {
    "skills",
    "soft_skills",
    "tools_technologies",
    "domain_knowledge",
    "language",
    "education",
    "experience",
    "portfolio",
    "certifications",
    "work_authorisation",
}
FRESHNESS_THRESHOLDS_DAYS = {
    "Fresh": 3,
    "Recently updated": 14,
    "Aging": 30,
}
PROVIDER_STATES = {"LIVE", "CACHED", "DEMO", "UNAVAILABLE", "PARTIAL", "STALE"}
JOB_SOURCE_TYPES = {
    "live_provider": "Live provider data",
    "cached_provider": "Cached provider data",
    "demo_fixture": "Deterministic demo data",
    "imported_market_vacancy": "Imported market vacancy",
    "pasted_job_ad": "Pasted user content",
    "browser_capture": "Browser-captured user content",
    "browser_capture_confirmed": "User-confirmed browser capture",
}

READINESS_LABELS = {
    "Strong evidence coverage",
    "Mixed evidence coverage",
    "Evidence gaps to address",
    "Eligibility or evidence blockers",
    "Insufficient information",
    "Evidence or capability information incomplete",
}

CLAIM_STATUSES = {
    "Supported",
    "Partially supported",
    "Transferable",
    "User-confirmed",
    "Unverified",
    "Conflicting",
    "Blocked",
}

APPLICATION_STATUSES = {
    "Saved",
    "Analysing",
    "Preparing",
    "Ready",
    "Applied",
    "Recruiter screening",
    "Interview 1",
    "Interview 2",
    "Technical or case stage",
    "Portfolio stage",
    "Final interview",
    "Reference check",
    "Offer",
    "Rejected",
    "Withdrawn",
    "Closed",
    "Unknown",
    "Draft",
    "Ready",
    "Screening",
    "Interview",
    "Final",
    "Archived",
}

APPLICATION_STATUS_ALIASES = {
    "DRAFT": "Draft",
    "READY": "Ready",
    "APPLIED": "Applied",
    "SCREENING": "Screening",
    "INTERVIEW": "Interview",
    "FINAL": "Final",
    "OFFER": "Offer",
    "REJECTED": "Rejected",
    "WITHDRAWN": "Withdrawn",
    "ARCHIVED": "Archived",
}


def _application_status(value: str | None, default: str = "Preparing") -> str:
    raw = str(value or default).strip()
    return APPLICATION_STATUS_ALIASES.get(raw.upper(), raw)

SKILL_ALIASES = {
    "ux": "ux_ui",
    "ui": "ux_ui",
    "user experience": "ux_ui",
    "interaction design": "interaction_design",
    "accessibility": "accessibility",
    "universal design": "accessibility",
    "responsible ai": "responsible_ai",
    "ethical ai": "responsible_ai",
    "human-centred ai": "human_centred_ai",
    "human centered ai": "human_centred_ai",
    "explainability": "explainability",
    "ai evaluation": "evaluation",
    "evaluation": "evaluation",
    "rag": "rag_fundamentals",
    "retrieval": "rag_fundamentals",
    "api": "apis",
    "apis": "apis",
    "python": "software_development",
    "typescript": "software_development",
    "react": "software_development",
    "fastapi": "apis",
    "database": "databases",
    "sql": "databases",
    "workflow": "workflow_analysis",
    "automation": "automation",
    "change management": "change_management",
    "stakeholder": "stakeholder_analysis",
    "communication": "communication",
    "facilitation": "facilitation",
    "teaching": "teaching",
    "instructional design": "instructional_design",
    "learning design": "instructional_design",
    "writing": "writing",
    "research": "research",
    "systems thinking": "systems_thinking",
    "privacy": "privacy_reasoning",
    "security": "security_reasoning",
    "documentation": "documentation",
    "quality assurance": "quality_assurance",
    "testing": "testing",
    "product thinking": "product_thinking",
}

TRANSFERABLE_SKILLS = {
    "product_thinking": ["ux_ui", "systems_thinking", "communication"],
    "responsible_ai": ["human_centred_ai", "critical_thinking", "privacy_reasoning"],
    "workflow_analysis": ["systems_thinking", "planning", "coordination"],
    "rag_fundamentals": ["apis", "software_development", "databases"],
    "instructional_design": ["teaching", "communication", "writing"],
    "evaluation": ["critical_thinking", "quality_assurance", "research"],
    "automation": ["ai_tools", "planning", "systems_thinking"],
}

APPROVED_AD_HOSTS = {
    "pam-stilling-feed.nav.no",
    "arbeidsplassen.nav.no",
    "www.arbeidsplassen.nav.no",
}


def _demo_marker(profile: Profile | None) -> bool:
    return bool(profile and (profile.id == "demo-profile" or str(profile.user_id or "").startswith("demo")))


def _now() -> datetime:
    return utc_now_naive()


def _dt(value: str | datetime | None) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        return parsed.replace(tzinfo=None)
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _date(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _freshness(value: datetime | None, *, now: datetime | None = None) -> dict[str, Any]:
    """Classify freshness from a stored source timestamp, never render time alone."""
    if not value:
        return {
            "label": "Unknown",
            "timestamp": None,
            "age_days": None,
            "basis": "No provider/source timestamp was supplied.",
        }
    current = now or _now()
    age_days = max(0, (current - value).total_seconds() / 86400)
    if age_days <= FRESHNESS_THRESHOLDS_DAYS["Fresh"]:
        label = "Fresh"
    elif age_days <= FRESHNESS_THRESHOLDS_DAYS["Recently updated"]:
        label = "Recently updated"
    elif age_days <= FRESHNESS_THRESHOLDS_DAYS["Aging"]:
        label = "Aging"
    else:
        label = "Stale"
    return {
        "label": label,
        "timestamp": value.isoformat(),
        "age_days": round(age_days, 1),
        "basis": "Provider/source timestamp",
    }


def _source_classification(*, provider: str, demo_marker: bool, input_type: str | None = None) -> str:
    if demo_marker or provider == "demo":
        return "demo_fixture"
    if input_type in JOB_SOURCE_TYPES:
        return input_type
    return "live_provider"


def _canonical_job_key(event: dict[str, Any]) -> str:
    """Stable duplicate group key while retaining each provider record."""
    source_url = str(event.get("source_url") or "").strip().lower().rstrip("/")
    if source_url:
        return "url:" + _hash({"url": source_url})[:32]
    identity = "|".join(
        _clean_text(str(event.get(key) or ""), 255).lower()
        for key in ("title", "employer", "municipality", "city", "country")
    )
    return "identity:" + _hash({"identity": identity})[:32]


def _job_source_provenance(db: Session, row: JobPosting) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(JobPosting).where(JobPosting.canonical_job_key == row.canonical_job_key)
    ).all() if row.canonical_job_key else [row]
    provenance: list[dict[str, Any]] = []
    for item in rows:
        provenance.append(
            {
                "job_id": item.id,
                "provider": item.provider,
                "provider_id": item.external_job_id,
                "source_url": item.source_url,
                "source_type": _source_classification(provider=item.provider, demo_marker=item.demo_marker),
                "last_provider_update": _date(item.last_provider_update),
                "freshness": _freshness(item.last_provider_update),
                "title": item.title,
                "location": ", ".join(part for part in [item.city, item.municipality, item.country] if part),
            }
        )
    return provenance


def _demo_mode_requested(profile: Profile | None, filters: dict[str, Any] | None) -> bool:
    """API callers must opt into demo fixtures; legacy service callers stay compatible."""
    if filters is not None and "demo_mode" in filters:
        return bool(filters.get("demo_mode"))
    # Direct service callers predate the explicit API flag and historically
    # expected the deterministic fixture feed to be available in tests and
    # local workflows. HTTP callers always receive an explicit demo_mode key.
    return True


def _provider_state(row: dict[str, Any]) -> str:
    if row.get("provider_type") == "demo":
        return "DEMO"
    if row.get("reachable") and row.get("enabled"):
        return "LIVE"
    if row.get("last_successful_sync"):
        freshness = _freshness(_dt(row.get("last_successful_sync")))
        return "CACHED" if freshness["label"] != "Stale" else "STALE"
    return "UNAVAILABLE"


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "item"


def _hash(payload: dict[str, Any]) -> str:
    clean = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def _clean_text(value: str | None, limit: int = MAX_PASTED_AD_CHARS) -> str:
    text = re.sub(r"<script.*?</script>", " ", value or "", flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _profile_languages(profile: Profile) -> list[str]:
    data = profile.data or {}
    text = " ".join(str(item) for item in [data.get("goals_languages"), data.get("language_profile"), data.get("languages")] if item)
    langs = []
    for language in ["English", "Norwegian", "Romanian"]:
        if language.lower() in text.lower():
            langs.append(language)
    return langs or ["English"]


def _normalise_skill_phrase(phrase: str) -> str:
    lower = re.sub(r"[^a-z0-9 +#.-]+", " ", phrase.lower())
    for alias, skill_id in SKILL_ALIASES.items():
        if alias in lower:
            return skill_id
    return _slug(phrase)


def _skill_label(skill_id: str) -> str:
    special = {"ux": "UX", "ui": "UI", "ai": "AI", "rag": "RAG", "api": "API"}
    return " ".join(special.get(part, part.capitalize()) for part in skill_id.split("_"))


def _safe_external_url(url: str | None) -> bool:
    if not url:
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_supported_ad_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in APPROVED_AD_HOSTS:
        raise ValueError("Only explicitly supported NAV/Arbeidsplassen advertisement URLs are allowed.")
    host = parsed.hostname or ""
    if host in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Localhost URLs are not allowed.")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Private IP URLs are not allowed.")
    except ValueError:
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
            raise
    try:
        for result in socket.getaddrinfo(host, None):
            address = result[4][0]
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise ValueError("URLs resolving to private networks are not allowed.")
    except socket.gaierror:
        raise ValueError("URL host could not be resolved safely.")


def _fetch_supported_url(url: str, timeout: int = 10) -> str:
    _validate_supported_ad_url(url)
    request = Request(url, headers={"Accept": "text/html,application/json"})
    with urlopen(request, timeout=timeout) as response:  # nosec - guarded by allowlist/private-IP checks.
        content_type = response.headers.get("content-type", "")
        if not any(kind in content_type for kind in ["text/html", "application/json", "text/plain"]):
            raise ValueError("Unsupported content type for advertisement URL.")
        data = response.read(MAX_URL_RESPONSE_BYTES + 1)
        if len(data) > MAX_URL_RESPONSE_BYTES:
            raise ValueError("Advertisement response exceeds configured size limit.")
        return _clean_text(data.decode("utf-8", errors="replace"))


def _provider_row(db: Session, provider_id: str = "demo") -> LabourMarketProviderRecord:
    settings = get_settings()
    row = db.get(LabourMarketProviderRecord, provider_id)
    if not row:
        row = LabourMarketProviderRecord(id=provider_id, provider_name=provider_id, display_name="Demo labour-market provider" if provider_id == "demo" else "NAV Job Vacancy Feed")
    if provider_id == "demo":
        row.provider_type = "demo"
        row.base_url = None
        row.enabled = True
        row.configured = True
        row.reachable = True
        row.status = "ready"
        row.degraded_reason = ""
        row.error_state = ""
        row.fallback_state = "demo_fixture"
        row.coverage_notes = "Deterministic fictional fixtures only; not complete market coverage."
    else:
        configured = bool(settings.nav_stilling_feed_token and settings.nav_stilling_feed_base_url)
        live_enabled = bool(settings.labour_market_live_enabled and settings.nav_stilling_feed_enabled)
        row.provider_type = "nav_stilling_feed"
        row.base_url = settings.nav_stilling_feed_base_url
        row.enabled = live_enabled
        row.configured = configured
        row.reachable = False
        row.status = "configured" if live_enabled and configured else "disabled"
        row.degraded_reason = "" if live_enabled and configured else "Live Norwegian labour-market data is not enabled. The current results use a curated demonstration dataset and must not be interpreted as current market coverage."
        row.error_state = "" if live_enabled and configured else row.degraded_reason
        row.fallback_state = "none"
        row.coverage_notes = "Coverage depends on the configured NAV feed and its returned window."
    row.documentation_url = NAV_STILLING_DOC_URL
    row.documentation_checked_date = NAV_DOC_CHECKED_DATE
    row.metadata_json = {
        "terms_url": NAV_TERMS_URL,
        "old_public_feed_used": False,
        "credentials_backend_only": True,
        "source_classification": "demo_fixture" if provider_id == "demo" else "live_provider",
    }
    db.add(row)
    db.flush()
    return row


def _cursor_row(db: Session, provider_id: str) -> LabourMarketSyncCursor:
    row = db.scalar(select(LabourMarketSyncCursor).where(LabourMarketSyncCursor.provider_id == provider_id, LabourMarketSyncCursor.cursor_key == "default"))
    if not row:
        row = LabourMarketSyncCursor(provider_id=provider_id, cursor_key="default", cursor_status="not_started")
        db.add(row)
        db.flush()
    return row


def demo_job_catalogue() -> list[dict[str, Any]]:
    # Keep the curated demo dataset useful as time moves on. The day-level
    # anchor makes repeated syncs deterministic while preventing every active
    # demonstration vacancy from expiring after the original fixture date.
    now = _now()
    today_anchor = datetime(now.year, now.month, now.day, 9, 0, 0) - timedelta(days=7)
    base = max(datetime(2026, 7, 21, 9, 0, 0), today_anchor)
    municipalities = [
        ("Oslo", "Oslo", "Oslo", "hybrid"),
        ("Bergen", "Vestland", "Bergen", "on-site"),
        ("Trondheim", "Trondelag", "Trondheim", "hybrid"),
        ("Stavanger", "Rogaland", "Stavanger", "remote"),
        ("Tromso", "Troms", "Tromso", "hybrid"),
    ]
    families = [
        ("AI Product Designer", ["ux_ui", "human_centred_ai", "responsible_ai", "accessibility", "evaluation"], "Product and design"),
        ("AI Integration Consultant", ["workflow_analysis", "automation", "stakeholder_analysis", "privacy_reasoning", "communication"], "Consulting and adoption"),
        ("RAG Application Developer", ["rag_fundamentals", "apis", "software_development", "databases", "quality_assurance"], "Software and AI engineering"),
        ("Learning Experience Designer", ["instructional_design", "ai_literacy", "writing", "facilitation", "assessment_design"], "Learning and enablement"),
    ]
    employers = [
        "Fjord Insight Labs AS",
        "Nordlys Learning Studio AS",
        "Oslo Human Systems AS",
        "Viken Workflow Partners AS",
        "Bergen Knowledge Tools AS",
        "Trondheim Source Systems AS",
        "Stavanger Civic AI AS",
        "Tromso Design Futures AS",
        "Aurora Product Lab AS",
        "Havn Data Cooperative AS",
        "Lysning Digital AS",
        "Myr Learning AS",
        "Kyst Automation Studio AS",
        "Granitt AI Services AS",
        "Solheim Experience Lab AS",
        "Fictional Municipality Innovation Unit",
        "Bridgeway Responsible Tech AS",
        "Northstar Portfolio Systems AS",
        "Varde Learning Systems AS",
        "Skog Product Research AS",
    ]
    rows: list[dict[str, Any]] = []
    for index in range(20):
        family, skills, domain = families[index % len(families)]
        city, county, municipality, work_mode = municipalities[index % len(municipalities)]
        published = base - timedelta(days=(index % 8) * 4 + (index // 8) * 35)
        expires = base + timedelta(days=21 + (index % 5) * 7)
        if index == 18:
            expires = base - timedelta(days=2)
        if index == 19:
            expires = base - timedelta(days=20)
        active = index < 18
        norwegian_required = index % 5 in {1, 4}
        language_requirements = ["English"] + (["Norwegian Bokmal"] if norwegian_required else ["Norwegian useful"])
        title_prefix = ["Junior", "Associate", "Practical", "Human-centred", "Evidence-focused"][index % 5]
        title = f"{title_prefix} {family}"
        description = (
            f"{employers[index]} seeks a {family} for {domain.lower()} work in {municipality}. "
            f"Mandatory requirements include {skills[0].replace('_', ' ')}, {skills[1].replace('_', ' ')}, and clear communication. "
            f"Preferred requirements include {skills[2].replace('_', ' ')}, portfolio evidence, and experience with AI-assisted workflows. "
            f"Language requirements: {'Norwegian and English' if norwegian_required else 'English, Norwegian useful'}. "
            "The advertisement is fictional demo data and is not a real vacancy."
        )
        rows.append(
            {
                "provider": "demo",
                "external_job_id": f"demo-job-{index + 1:02d}",
                "source_url": f"https://arbeidsplassen.nav.no/stillinger/stilling/demo-job-{index + 1:02d}",
                "provider_event_id": f"demo-event-{index + 1:02d}",
                "event_type": "upsert" if active else "expired",
                "title": title,
                "employer": employers[index],
                "description": description,
                "publication_time": published,
                "expiry_time": expires,
                "last_provider_update": published + timedelta(days=2),
                "is_active": active,
                "inactive_reason": "" if active else "expired",
                "employment_type": "Permanent" if index % 3 else "Temporary project",
                "full_time_part_time": "Full-time" if index % 4 else "Part-time possible",
                "work_mode": work_mode,
                "country": "Norway",
                "county": county,
                "municipality": municipality,
                "city": city,
                "coordinates": {},
                "language_requirements": language_requirements,
                "experience_requirements": ["0-2 years", "portfolio evidence"] if index % 2 else ["2+ years useful", "practical project evidence"],
                "education_requirements": ["Relevant education or equivalent practical evidence"],
                "occupation_classifications": [{"level1": domain, "level2": family}],
                "esco_classifications": [],
                "styrk_classifications": [],
                "extracted_skills": skills,
                "career_families": [family],
                "original_provider_metadata": {"fictional": True, "demo_index": index + 1},
                "source_version": DEMO_MARKET_VERSION,
                "historical_retention_allowed": True,
                "demo_marker": True,
            }
        )
    return rows


def _job_snapshot(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": event.get("provider", "demo"),
        "external_job_id": event["external_job_id"],
        "title": event.get("title", ""),
        "employer": event.get("employer", ""),
        "description": event.get("description", ""),
        "publication_time": _date(_dt(event.get("publication_time"))),
        "expiry_time": _date(_dt(event.get("expiry_time"))),
        "last_provider_update": _date(_dt(event.get("last_provider_update"))),
        "is_active": bool(event.get("is_active", True)),
        "inactive_reason": event.get("inactive_reason", ""),
        "employment_type": event.get("employment_type", ""),
        "full_time_part_time": event.get("full_time_part_time", ""),
        "work_mode": event.get("work_mode", ""),
        "country": event.get("country", "Norway"),
        "county": event.get("county", ""),
        "municipality": event.get("municipality", ""),
        "city": event.get("city", ""),
        "language_requirements": event.get("language_requirements", []),
        "experience_requirements": event.get("experience_requirements", []),
        "education_requirements": event.get("education_requirements", []),
        "occupation_classifications": event.get("occupation_classifications", []),
        "esco_classifications": event.get("esco_classifications", []),
        "styrk_classifications": event.get("styrk_classifications", []),
        "extracted_skills": event.get("extracted_skills", []),
        "career_families": event.get("career_families", []),
        "source_version": event.get("source_version", DEMO_MARKET_VERSION),
    }


def upsert_job_event(db: Session, event: dict[str, Any]) -> tuple[JobPosting | None, str]:
    if not event.get("external_job_id"):
        raise ValueError("Provider event is missing external_job_id.")
    provider = event.get("provider", "demo")
    snapshot = _job_snapshot(event)
    content_hash = _hash(snapshot)
    canonical_key = _canonical_job_key(event)
    row = db.scalar(select(JobPosting).where(JobPosting.provider == provider, JobPosting.external_job_id == event["external_job_id"]))
    action = "created"
    if row and row.content_hash == content_hash:
        return row, "unchanged"
    if not row:
        row = JobPosting(provider=provider, external_job_id=event["external_job_id"], title=event.get("title", "Untitled vacancy"))
        db.add(row)
        db.flush()
    else:
        action = "updated"
    row.source_url = event.get("source_url") or row.source_url or ""
    row.provider_event_id = event.get("provider_event_id")
    row.event_type = event.get("event_type", "upsert")
    row.title = event.get("title", row.title)
    row.employer = event.get("employer", "")
    row.description = _clean_text(event.get("description"), 50000)
    row.publication_time = _dt(event.get("publication_time"))
    row.expiry_time = _dt(event.get("expiry_time"))
    row.last_provider_update = _dt(event.get("last_provider_update")) or _now()
    row.is_active = bool(event.get("is_active", True)) and (row.expiry_time is None or row.expiry_time >= _now())
    row.inactive_reason = event.get("inactive_reason") or ("expired" if row.expiry_time and row.expiry_time < _now() else "")
    row.employment_type = event.get("employment_type", "")
    row.full_time_part_time = event.get("full_time_part_time", "")
    row.work_mode = event.get("work_mode", "unspecified")
    row.country = event.get("country", "Norway")
    row.county = event.get("county", "")
    row.municipality = event.get("municipality", "")
    row.city = event.get("city", "")
    row.coordinates_json = event.get("coordinates") or {}
    row.language_requirements_json = event.get("language_requirements") or []
    row.experience_requirements_json = event.get("experience_requirements") or []
    row.education_requirements_json = event.get("education_requirements") or []
    row.occupation_classifications_json = event.get("occupation_classifications") or []
    row.esco_classifications_json = event.get("esco_classifications") or []
    row.styrk_classifications_json = event.get("styrk_classifications") or []
    row.extracted_skills_json = event.get("extracted_skills") or []
    row.career_families_json = event.get("career_families") or []
    row.original_provider_metadata_json = event.get("original_provider_metadata") or {}
    row.source_version = event.get("source_version", DEMO_MARKET_VERSION)
    row.historical_retention_allowed = bool(event.get("historical_retention_allowed", True))
    row.content_hash = content_hash
    row.canonical_job_key = canonical_key
    row.source_provenance_json = [
        {
            "provider": provider,
            "provider_id": row.external_job_id,
            "source_url": row.source_url,
            "source_type": _source_classification(provider=provider, demo_marker=bool(event.get("demo_marker", False))),
            "last_provider_update": _date(row.last_provider_update),
        }
    ]
    row.demo_marker = bool(event.get("demo_marker", False))
    row.updated_at = _now()
    db.flush()
    db.add(JobPostingVersion(job_id=row.id, provider_event_id=row.provider_event_id, event_type=row.event_type, content_hash=content_hash, snapshot_json=snapshot))
    db.execute(delete(JobLocation).where(JobLocation.job_id == row.id))
    db.execute(delete(JobClassification).where(JobClassification.job_id == row.id))
    db.execute(delete(JobSkillMention).where(JobSkillMention.job_id == row.id))
    db.execute(delete(JobLanguageRequirement).where(JobLanguageRequirement.job_id == row.id))
    db.add(JobLocation(job_id=row.id, country=row.country, county=row.county, municipality=row.municipality, city=row.city, coordinates_json=row.coordinates_json))
    for classification in row.occupation_classifications_json:
        db.add(JobClassification(job_id=row.id, classification_type="occupation", code=str(classification.get("code", "")), label=str(classification.get("level2") or classification.get("name") or ""), source=provider, metadata_json=classification))
    for skill in row.extracted_skills_json:
        mapping = normalise_skill(db, skill)
        db.add(
            JobSkillMention(
                job_id=row.id,
                original_phrase=skill,
                normalised_skill_id=mapping["normalised_skill_id"],
                normalised_label=mapping["preferred_label"] or _skill_label(mapping["normalised_skill_id"] or _slug(skill)),
                esco_uri=mapping.get("esco_uri"),
                requirement_type="observed",
                confidence=mapping["confidence"],
                extraction_method="provider_or_demo_metadata",
                source_excerpt=skill,
            )
        )
    for language in row.language_requirements_json:
        requirement_type = "mandatory" if "norwegian" in str(language).lower() and "useful" not in str(language).lower() else "preferred"
        db.add(JobLanguageRequirement(job_id=row.id, language=str(language), requirement_type=requirement_type, source_excerpt=str(language)))
    db.flush()
    return row, action


def sync_demo_labour_market(db: Session) -> dict[str, Any]:
    provider = _provider_row(db, "demo")
    cursor = _cursor_row(db, provider.id)
    run = LabourMarketSyncRun(provider_id=provider.id, status="started", cursor_before_json={"status": cursor.cursor_status}, demo_marker=True)
    db.add(run)
    db.flush()
    counts = Counter()
    errors = []
    for event in demo_job_catalogue():
        try:
            row, action = upsert_job_event(db, event)
            counts[action] += 1
            if row and not row.is_active:
                counts["inactive"] += 1
        except Exception as error:
            counts["errors"] += 1
            errors.append({"external_job_id": event.get("external_job_id"), "error": str(error)})
    cursor.cursor_status = "ready"
    cursor.latest_event_timestamp = max((_dt(item.get("last_provider_update")) or _now()) for item in demo_job_catalogue())
    cursor.next_url = None
    cursor.next_id = None
    cursor.metadata_json = {"provider": "demo", "dataset_version": DEMO_MARKET_VERSION}
    run.status = "completed" if not errors else "completed_with_errors"
    run.completed_at = _now()
    run.fetched_count = len(demo_job_catalogue())
    run.created_count = counts["created"]
    run.updated_count = counts["updated"]
    run.inactive_count = counts["inactive"]
    run.error_count = counts["errors"]
    run.error_json = errors
    run.cursor_after_json = {"status": cursor.cursor_status, "latest_event_timestamp": _date(cursor.latest_event_timestamp)}
    provider.last_successful_fetch = run.completed_at if run.status == "completed" else provider.last_successful_fetch
    provider.freshness_timestamp = cursor.latest_event_timestamp
    provider.error_state = "" if run.status == "completed" else "; ".join(error.get("error", "") for error in errors)
    provider.fallback_state = "demo_fixture"
    db.commit()
    return sync_run_public(run)


class LabourMarketProvider:
    provider_id = "base"

    def health_check(self, db: Session) -> dict[str, Any]:
        raise NotImplementedError

    def sync_events(self, db: Session) -> dict[str, Any]:
        raise NotImplementedError

    def get_provider_metadata(self, db: Session) -> dict[str, Any]:
        row = _provider_row(db, self.provider_id)
        return provider_public(db, row)


class DemoLabourMarketProvider(LabourMarketProvider):
    provider_id = "demo"

    def health_check(self, db: Session) -> dict[str, Any]:
        return provider_public(db, _provider_row(db, "demo"))

    def sync_events(self, db: Session) -> dict[str, Any]:
        return sync_demo_labour_market(db)


class NavStillingFeedProvider(LabourMarketProvider):
    provider_id = "nav_stilling_feed"

    def health_check(self, db: Session) -> dict[str, Any]:
        settings = get_settings()
        row = _provider_row(db, self.provider_id)
        if settings.labour_market_live_enabled and settings.nav_stilling_feed_enabled and settings.nav_stilling_feed_token:
            row.status = "configured"
            row.configured = True
            row.degraded_reason = "Configured but not contacted during ordinary health checks."
        db.commit()
        return provider_public(db, row)

    def sync_events(self, db: Session) -> dict[str, Any]:
        settings = get_settings()
        row = _provider_row(db, self.provider_id)
        cursor = _cursor_row(db, row.id)
        run = LabourMarketSyncRun(provider_id=row.id, status="failed", cursor_before_json={"next_url": cursor.next_url, "status": cursor.cursor_status})
        db.add(run)
        db.flush()
        if not settings.labour_market_live_enabled or not settings.nav_stilling_feed_enabled or not settings.nav_stilling_feed_token:
            run.error_count = 1
            run.error_json = [{"message": "NAV stilling-feed credentials are missing or live mode is disabled."}]
            row.degraded_reason = "Live Norwegian labour-market data is not enabled. The current results use a curated demonstration dataset and must not be interpreted as current market coverage."
            cursor.cursor_status = "disabled"
            run.completed_at = _now()
            db.commit()
            return sync_run_public(run)
        try:
            feed_url = cursor.next_url or "/api/v1/feed"
            url = urljoin(settings.nav_stilling_feed_base_url.rstrip("/") + "/", feed_url.lstrip("/"))
            request = Request(url, headers={"Accept": "application/json", "Authorization": f"Bearer {settings.nav_stilling_feed_token}"})
            if cursor.last_modified:
                request.add_header("If-Modified-Since", cursor.last_modified)
            if cursor.etag:
                request.add_header("If-None-Match", cursor.etag)
            with urlopen(request, timeout=settings.nav_stilling_feed_request_timeout_seconds) as response:  # nosec - configured backend provider endpoint.
                page = json.loads(response.read(MAX_URL_RESPONSE_BYTES).decode("utf-8"))
                cursor.etag = response.headers.get("ETag")
                cursor.last_modified = response.headers.get("Last-Modified")
            fetched = 0
            inactive = 0
            for item in page.get("items", [])[: settings.nav_stilling_feed_sync_batch_size]:
                fetched += 1
                feed_entry = item.get("_feed_entry") or {}
                status = str(feed_entry.get("status") or "").upper()
                event = {
                    "provider": row.id,
                    "external_job_id": feed_entry.get("uuid") or item.get("id"),
                    "provider_event_id": item.get("id"),
                    "event_type": "delete" if status != "ACTIVE" else "upsert",
                    "title": feed_entry.get("title") or item.get("title") or "NAV vacancy",
                    "employer": feed_entry.get("businessName") or "",
                    "municipality": feed_entry.get("municipal") or "",
                    "description": item.get("content_text") or "",
                    "last_provider_update": feed_entry.get("sistEndret") or item.get("date_modified"),
                    "is_active": status == "ACTIVE",
                    "inactive_reason": "" if status == "ACTIVE" else "inactive_or_deleted_at_provider",
                    "source_url": urljoin(settings.nav_stilling_feed_base_url, item.get("url") or ""),
                    "source_version": "nav-stilling-feed",
                    "historical_retention_allowed": False,
                    "demo_marker": False,
                }
                _, action = upsert_job_event(db, event)
                if action in {"created", "updated"}:
                    run.created_count += 1 if action == "created" else 0
                    run.updated_count += 1 if action == "updated" else 0
                if status != "ACTIVE":
                    inactive += 1
            cursor.next_url = page.get("next_url")
            cursor.next_id = page.get("next_id")
            cursor.latest_event_timestamp = _now()
            cursor.cursor_status = "ready"
            run.status = "completed"
            run.fetched_count = fetched
            run.inactive_count = inactive
            run.cursor_after_json = {"next_url": cursor.next_url, "next_id": cursor.next_id}
            row.reachable = True
            row.status = "available"
            row.last_successful_fetch = run.completed_at
            row.freshness_timestamp = cursor.latest_event_timestamp
            row.error_state = ""
            row.fallback_state = "none"
        except Exception as error:
            run.error_count = 1
            run.error_json = [{"message": str(error)}]
            cursor.cursor_status = "failed"
            row.reachable = False
            row.status = "degraded"
            row.degraded_reason = str(error)
            row.error_state = str(error)
            row.fallback_state = "cached_provider" if cursor.latest_event_timestamp else "none"
        run.completed_at = _now()
        db.commit()
        return sync_run_public(run)


class FutureProviderAdapter(LabourMarketProvider):
    provider_id = "future_provider"

    def health_check(self, db: Session) -> dict[str, Any]:
        return {"provider": self.provider_id, "enabled": False, "status": "not_implemented"}

    def sync_events(self, db: Session) -> dict[str, Any]:
        raise ValueError("FutureProviderAdapter is reserved and not enabled.")


def provider_public(db: Session, row: LabourMarketProviderRecord) -> dict[str, Any]:
    active_count = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.provider == row.id, JobPosting.is_active.is_(True))) or 0
    inactive_count = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.provider == row.id, JobPosting.is_active.is_(False))) or 0
    cursor = _cursor_row(db, row.id)
    last_success = db.scalar(select(LabourMarketSyncRun).where(LabourMarketSyncRun.provider_id == row.id, LabourMarketSyncRun.status == "completed").order_by(LabourMarketSyncRun.completed_at.desc()))
    last_failed = db.scalar(select(LabourMarketSyncRun).where(LabourMarketSyncRun.provider_id == row.id, LabourMarketSyncRun.status.in_(["failed", "completed_with_errors"])).order_by(LabourMarketSyncRun.completed_at.desc()))
    return {
        "id": row.id,
        "provider_name": row.provider_name,
        "display_name": row.display_name,
        "provider_type": row.provider_type,
        "enabled": row.enabled,
        "configured": row.configured,
        "reachable": row.reachable,
        "status": row.status,
        "base_url": row.base_url,
        "documentation_url": row.documentation_url,
        "documentation_checked_date": row.documentation_checked_date,
        "degraded_mode_reason": row.degraded_reason,
        "degraded_reason": row.degraded_reason,
        "active_local_records": active_count,
        "inactive_records": inactive_count,
        "last_successful_sync": _date(last_success.completed_at) if last_success else None,
        "last_failed_sync": _date(last_failed.completed_at) if last_failed else None,
        "latest_event_timestamp": _date(cursor.latest_event_timestamp),
        "current_cursor_status": cursor.cursor_status,
        "cursor": {"next_url": cursor.next_url, "next_id": cursor.next_id, "etag": cursor.etag, "last_modified": cursor.last_modified},
        "metadata": row.metadata_json or {},
        "availability": _provider_state({"provider_type": row.provider_type, "reachable": row.reachable, "enabled": row.enabled, "last_successful_sync": _date(last_success.completed_at) if last_success else None}),
        "provider_state": _provider_state({"provider_type": row.provider_type, "reachable": row.reachable, "enabled": row.enabled, "last_successful_sync": _date(last_success.completed_at) if last_success else None}),
        "last_successful_fetch": _date(row.last_successful_fetch or (last_success.completed_at if last_success else None)),
        "freshness_timestamp": _date(row.freshness_timestamp or (last_success.completed_at if last_success else None)),
        "freshness": _freshness(row.freshness_timestamp or (last_success.completed_at if last_success else None)),
        "error_state": row.error_state or (last_failed.error_json[0].get("message", "") if last_failed and last_failed.error_json else ""),
        "fallback_state": row.fallback_state,
        "coverage_notes": row.coverage_notes,
        "source_classification": "demo_fixture" if row.provider_type == "demo" else "live_provider",
        "updated_at": row.updated_at.isoformat(),
    }


def _provider_public_readonly(db: Session, row: LabourMarketProviderRecord | None, provider_id: str) -> dict[str, Any]:
    settings = get_settings()
    active_count = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.provider == provider_id, JobPosting.is_active.is_(True))) or 0
    inactive_count = db.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.provider == provider_id, JobPosting.is_active.is_(False))) or 0
    cursor = db.scalar(select(LabourMarketSyncCursor).where(LabourMarketSyncCursor.provider_id == provider_id, LabourMarketSyncCursor.cursor_key == "default"))
    last_success = db.scalar(select(LabourMarketSyncRun).where(LabourMarketSyncRun.provider_id == provider_id, LabourMarketSyncRun.status == "completed").order_by(LabourMarketSyncRun.completed_at.desc()))
    last_failed = db.scalar(select(LabourMarketSyncRun).where(LabourMarketSyncRun.provider_id == provider_id, LabourMarketSyncRun.status.in_(["failed", "completed_with_errors"])).order_by(LabourMarketSyncRun.completed_at.desc()))

    if row:
        provider_name = row.provider_name
        display_name = row.display_name
        provider_type = row.provider_type
        enabled = row.enabled
        configured = row.configured
        reachable = row.reachable
        status = row.status
        base_url = row.base_url
        degraded_reason = row.degraded_reason
        metadata = row.metadata_json or {}
        updated_at = row.updated_at.isoformat()
    elif provider_id == "demo":
        provider_name = "demo"
        display_name = "Demo labour-market provider"
        provider_type = "demo"
        enabled = True
        configured = True
        reachable = active_count > 0
        status = "ready" if active_count > 0 else "not_seeded"
        base_url = None
        degraded_reason = "" if active_count > 0 else "Demo labour-market data has not been synchronized yet."
        metadata = {"terms_url": NAV_TERMS_URL, "old_public_feed_used": False, "credentials_backend_only": True}
        updated_at = None
    else:
        configured = bool(settings.nav_stilling_feed_token and settings.nav_stilling_feed_base_url)
        live_enabled = bool(settings.labour_market_live_enabled and settings.nav_stilling_feed_enabled)
        provider_name = provider_id
        display_name = "NAV Job Vacancy Feed"
        provider_type = "nav_stilling_feed"
        enabled = live_enabled
        reachable = False
        status = "configured" if live_enabled and configured else "disabled"
        base_url = settings.nav_stilling_feed_base_url
        degraded_reason = "" if live_enabled and configured else "Live Norwegian labour-market data is not enabled. The current results use a curated demonstration dataset and must not be interpreted as current market coverage."
        metadata = {"terms_url": NAV_TERMS_URL, "old_public_feed_used": False, "credentials_backend_only": True}
        updated_at = None

    return {
        "id": provider_id,
        "provider_name": provider_name,
        "display_name": display_name,
        "provider_type": provider_type,
        "enabled": enabled,
        "configured": configured,
        "reachable": reachable,
        "status": status,
        "base_url": base_url,
        "documentation_url": NAV_STILLING_DOC_URL,
        "documentation_checked_date": NAV_DOC_CHECKED_DATE,
        "degraded_mode_reason": degraded_reason,
        "degraded_reason": degraded_reason,
        "active_local_records": active_count,
        "inactive_records": inactive_count,
        "last_successful_sync": _date(last_success.completed_at) if last_success else None,
        "last_failed_sync": _date(last_failed.completed_at) if last_failed else None,
        "latest_event_timestamp": _date(cursor.latest_event_timestamp) if cursor else None,
        "current_cursor_status": cursor.cursor_status if cursor else "not_started",
        "cursor": {
            "next_url": cursor.next_url if cursor else None,
            "next_id": cursor.next_id if cursor else None,
            "etag": cursor.etag if cursor else None,
            "last_modified": cursor.last_modified if cursor else None,
        },
        "metadata": metadata,
        "availability": _provider_state({"provider_type": provider_type, "reachable": reachable, "enabled": enabled, "last_successful_sync": _date(last_success.completed_at) if last_success else None}),
        "provider_state": _provider_state({"provider_type": provider_type, "reachable": reachable, "enabled": enabled, "last_successful_sync": _date(last_success.completed_at) if last_success else None}),
        "last_successful_fetch": _date((row.last_successful_fetch if row else None) or (last_success.completed_at if last_success else None)),
        "freshness_timestamp": _date((row.freshness_timestamp if row else None) or (last_success.completed_at if last_success else None)),
        "freshness": _freshness((row.freshness_timestamp if row else None) or (last_success.completed_at if last_success else None)),
        "error_state": (row.error_state if row else "") or (last_failed.error_json[0].get("message", "") if last_failed and last_failed.error_json else degraded_reason),
        "fallback_state": (row.fallback_state if row else ("demo_fixture" if provider_id == "demo" else "none")),
        "coverage_notes": (row.coverage_notes if row else ("Deterministic fictional fixtures only; not complete market coverage." if provider_id == "demo" else "Coverage depends on the configured NAV feed and its returned window.")),
        "source_classification": "demo_fixture" if provider_id == "demo" else "live_provider",
        "updated_at": updated_at,
    }


def providers_status(db: Session) -> dict[str, Any]:
    settings = get_settings()
    nav = db.get(LabourMarketProviderRecord, "nav_stilling_feed")
    demo = db.get(LabourMarketProviderRecord, "demo")
    warning = ""
    if not settings.nav_stilling_feed_enabled or not settings.labour_market_live_enabled:
        warning = "Live NAV feed is disabled or missing backend credentials; demo labour-market data is available."
    return {
        "documentation_checked_date": NAV_DOC_CHECKED_DATE,
        "nav_documentation_url": NAV_STILLING_DOC_URL,
        "nav_terms_url": NAV_TERMS_URL,
        "old_public_feed_used": False,
        "active_provider": "demo" if not settings.labour_market_live_enabled else settings.labour_market_provider,
        "requested_provider": settings.labour_market_provider,
        "demo_mode_required": not bool(settings.labour_market_live_enabled and settings.nav_stilling_feed_enabled and settings.nav_stilling_feed_token),
        "live_enabled": bool(settings.labour_market_live_enabled and settings.nav_stilling_feed_enabled and settings.nav_stilling_feed_token),
        "warning": warning,
        "providers": [_provider_public_readonly(db, demo, "demo"), _provider_public_readonly(db, nav, "nav_stilling_feed")],
    }


def sync_run_public(row: LabourMarketSyncRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "provider_id": row.provider_id,
        "status": row.status,
        "started_at": row.started_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "fetched_count": row.fetched_count,
        "created_count": row.created_count,
        "updated_count": row.updated_count,
        "inactive_count": row.inactive_count,
        "error_count": row.error_count,
        "errors": row.error_json or [],
        "cursor_before": row.cursor_before_json or {},
        "cursor_after": row.cursor_after_json or {},
    }


def normalise_skill(db: Session, phrase: str) -> dict[str, Any]:
    settings = get_settings()
    normalised = _normalise_skill_phrase(phrase)
    if settings.esco_provider == "disabled":
        mapping = EscoMapping(
            original_phrase=phrase,
            normalised_phrase=normalised,
            preferred_label=_skill_label(normalised),
            concept_type="skill",
            provider="disabled",
            confidence="unnormalised",
            status="fallback_raw_term",
        )
        db.add(mapping)
        db.flush()
        return {
            "original_phrase": phrase,
            "normalised_skill_id": normalised,
            "preferred_label": mapping.preferred_label,
            "esco_uri": None,
            "confidence": "unnormalised",
            "status": "fallback_raw_term",
            "provider": "disabled",
        }
    local_map = {
        "ux_ui": ("https://data.europa.eu/esco/skill/ux-ui-demo", "user interface design"),
        "software_development": ("https://data.europa.eu/esco/skill/software-development-demo", "software development"),
        "communication": ("https://data.europa.eu/esco/skill/communication-demo", "communicate with others"),
        "instructional_design": ("https://data.europa.eu/esco/skill/instructional-design-demo", "instructional design"),
        "accessibility": ("https://data.europa.eu/esco/skill/accessibility-demo", "accessibility"),
    }
    if settings.esco_provider == "local" and normalised in local_map:
        uri, label = local_map[normalised]
        concept = db.scalar(select(EscoConcept).where(EscoConcept.esco_uri == uri))
        if not concept:
            concept = EscoConcept(esco_uri=uri, preferred_label=label, concept_type="skill", taxonomy_version="local-demo-esco-v1", provider="local")
            db.add(concept)
            db.flush()
            db.add(EscoLabel(concept_id=concept.id, language="en", label=label, label_type="preferred"))
            db.add(EscoLabel(concept_id=concept.id, language="nb", label=label, label_type="alternative"))
        mapping = EscoMapping(
            original_phrase=phrase,
            normalised_phrase=normalised,
            concept_id=concept.id,
            esco_uri=uri,
            preferred_label=label,
            alternative_labels_json=[phrase],
            concept_type="skill",
            taxonomy_version=concept.taxonomy_version,
            provider="local",
            confidence="mapped",
            status="mapped",
        )
        db.add(mapping)
        db.flush()
        return {
            "original_phrase": phrase,
            "normalised_skill_id": normalised,
            "preferred_label": label,
            "esco_uri": uri,
            "confidence": "mapped",
            "status": "mapped",
            "provider": "local",
        }
    status = "ambiguous" if "design" in phrase.lower() else "fallback_raw_term"
    mapping = EscoMapping(
        original_phrase=phrase,
        normalised_phrase=normalised,
        preferred_label=_skill_label(normalised),
        provider=settings.esco_provider,
        confidence="ambiguous" if status == "ambiguous" else "unnormalised",
        status=status,
    )
    db.add(mapping)
    db.flush()
    return {
        "original_phrase": phrase,
        "normalised_skill_id": normalised,
        "preferred_label": mapping.preferred_label,
        "esco_uri": None,
        "confidence": mapping.confidence,
        "status": status,
        "provider": settings.esco_provider,
    }


def normalise_skill_terms(db: Session, phrases: list[str]) -> dict[str, Any]:
    run = SkillNormalisationRun(provider=get_settings().esco_provider, input_count=len(phrases), version=ESCO_NORMALISATION_VERSION)
    db.add(run)
    mappings = [normalise_skill(db, phrase) for phrase in phrases]
    run.mapped_count = sum(1 for item in mappings if item["status"] == "mapped")
    run.ambiguous_count = sum(1 for item in mappings if item["status"] == "ambiguous")
    run.fallback_count = sum(1 for item in mappings if item["status"] == "fallback_raw_term")
    run.status = "completed"
    run.metadata_json = {"startup_required": False, "silent_replacement": False}
    db.commit()
    return {"id": run.id, "provider": run.provider, "status": run.status, "mappings": mappings}


def esco_status(db: Session) -> dict[str, Any]:
    settings = get_settings()
    return {
        "provider": settings.esco_provider,
        "enabled": settings.esco_provider != "disabled",
        "base_url": settings.esco_base_url if settings.esco_provider == "web" else None,
        "startup_required": False,
        "fallback": "Raw extracted terms are retained and marked unnormalised when ESCO is unavailable.",
        "cached_mappings": db.scalar(select(func.count()).select_from(EscoMapping)) or 0,
    }


def _evidence_by_skill(db: Session, profile_id: str) -> dict[str, dict[str, Any]]:
    passport = evidence_passport(db, profile_id)
    return {item["skill_id"]: item for item in passport.get("skills", [])}


def _first_evidence_id(skill: dict[str, Any] | None) -> str | None:
    if not skill:
        return None
    sources = skill.get("evidence_sources") or []
    return sources[0].get("id") if sources else None


def _coverage_for_job(db: Session, profile_id: str, job: JobPosting) -> dict[str, Any]:
    evidence = _evidence_by_skill(db, profile_id)
    required = [_normalise_skill_phrase(skill) for skill in (job.extracted_skills_json or [])]
    covered = []
    partial = []
    missing = []
    for skill_id in required:
        row = evidence.get(skill_id)
        if not row:
            missing.append(skill_id)
        elif row.get("strongest_evidence_label") in {"Practically verified", "Demonstrated", "Supported"} or row.get("evidence_confidence") in {"Strong evidence", "Multiple supporting sources"}:
            covered.append(skill_id)
        else:
            partial.append(skill_id)
    return {
        "covered": covered,
        "partial": partial,
        "missing": missing,
        "coverage_label": "Strong coverage" if len(covered) >= max(1, len(required) - 1) else "Partial coverage" if covered or partial else "Limited coverage",
    }


def _job_recommendation(db: Session, profile: Profile, job: JobPosting) -> dict[str, Any]:
    coverage = _coverage_for_job(db, profile.id, job)
    languages = _profile_languages(profile)
    norwegian_required = any("norwegian" in str(item).lower() and "useful" not in str(item).lower() for item in (job.language_requirements_json or []))
    language_blocker = norwegian_required and not any("norwegian" in item.lower() for item in languages)
    if not job.description.strip():
        label = "Insufficient information"
    elif language_blocker:
        label = "Eligibility or evidence blockers"
    elif coverage["covered"] and not coverage["partial"] and not coverage["missing"]:
        label = "Strong evidence coverage"
    elif len(coverage["covered"]) + len(coverage["partial"]) >= max(1, len(job.extracted_skills_json or []) // 2):
        label = "Mixed evidence coverage"
    elif coverage["missing"] and job.expiry_time and job.expiry_time > _now() + timedelta(days=10):
        label = "Evidence gaps to address"
    else:
        label = "Eligibility or evidence blockers"
    return {
        "recommendation_status": label,
        "career_relevance": ", ".join(job.career_families_json or []),
        "required_evidence_coverage": coverage["coverage_label"],
        "missing_evidence": [_skill_label(item) for item in coverage["missing"]],
        "language_or_eligibility_blockers": ["Norwegian appears mandatory and is not confirmed in the profile."] if language_blocker else [],
        "deterministic_reasons": [
            f"{len(coverage['covered'])} required skills have stronger evidence.",
            f"{len(coverage['missing'])} required skills need evidence.",
        ],
    }


def job_public(db: Session, row: JobPosting, profile: Profile | None = None) -> dict[str, Any]:
    recommendation = _job_recommendation(db, profile, row) if profile else {}
    coverage = _coverage_for_job(db, profile.id, row) if profile else None
    location = ", ".join([part for part in [row.city, row.municipality, row.country] if part])
    source_timestamp = row.last_provider_update or row.publication_time or row.ingested_at
    freshness = _freshness(source_timestamp)
    latest_analysis = db.scalar(
        select(JobAnalysis).where(JobAnalysis.job_id == row.id, *( [JobAnalysis.profile_id == profile.id] if profile else [] )).order_by(JobAnalysis.updated_at.desc())
    )
    provenance = _job_source_provenance(db, row)
    return {
        "id": row.id,
        "provider": row.provider,
        "external_job_id": row.external_job_id,
        "source_url": row.source_url if row.is_active else None,
        "provider_event_id": row.provider_event_id,
        "event_type": row.event_type,
        "title": row.title,
        "employer": row.employer,
        "description": row.description,
        "publication_time": _date(row.publication_time),
        "expiry_time": _date(row.expiry_time),
        "last_provider_update": _date(row.last_provider_update),
        "is_active": row.is_active,
        "inactive_reason": row.inactive_reason,
        "employment_type": row.employment_type,
        "full_time_part_time": row.full_time_part_time,
        "work_mode": row.work_mode,
        "country": row.country,
        "county": row.county,
        "municipality": row.municipality,
        "city": row.city,
        "location": location or row.country,
        "language_requirements": row.language_requirements_json or [],
        "languages": [str(item).split()[0] for item in (row.language_requirements_json or [])],
        "experience_requirements": row.experience_requirements_json or [],
        "education_requirements": row.education_requirements_json or [],
        "occupation_classifications": row.occupation_classifications_json or [],
        "esco_classifications": row.esco_classifications_json or [],
        "styrk_classifications": row.styrk_classifications_json or [],
        "extracted_skills": row.extracted_skills_json or [],
        "skills": row.extracted_skills_json or [],
        "career_families": row.career_families_json or [],
        "provider_freshness": freshness["label"] if row.is_active else f"Inactive: {row.inactive_reason or 'provider inactive'}",
        "freshness": freshness,
        "freshness_timestamp": freshness["timestamp"],
        "source_excerpt": row.description[:420],
        "import_timestamp": _date(row.ingested_at),
        "source_type": _source_classification(provider=row.provider, demo_marker=row.demo_marker),
        "source_classification": JOB_SOURCE_TYPES[_source_classification(provider=row.provider, demo_marker=row.demo_marker)],
        "provider_status": provider_public(db, _provider_row(db, row.provider)),
        "analysis_status": latest_analysis.status if latest_analysis else "not_analysed",
        "canonical_job_key": row.canonical_job_key,
        "source_provenance": provenance,
        "deduplication": {"key": row.canonical_job_key, "source_count": len(provenance), "sources_preserved": True},
        "source_version": row.source_version,
        "content_hash": row.content_hash,
        "demo_marker": row.demo_marker,
        "coverage": {
            "covered_count": len(coverage["covered"]) + len(coverage["partial"]),
            "missing_count": len(coverage["missing"]),
            "total_count": len(coverage["covered"]) + len(coverage["partial"]) + len(coverage["missing"]),
            "covered_skills": [_skill_label(item) for item in coverage["covered"] + coverage["partial"]],
            "missing_skills": [_skill_label(item) for item in coverage["missing"]],
            "label": coverage["coverage_label"],
        } if coverage else None,
        "recommendation": {
            "readiness_label": recommendation.get("recommendation_status", "Needs analysis"),
            "reason": "; ".join(recommendation.get("deterministic_reasons", [])),
            "missing_skills": recommendation.get("missing_evidence", []),
            "covered_skills": [_skill_label(item) for item in (coverage["covered"] + coverage["partial"])] if coverage else [],
        } if recommendation else None,
        **recommendation,
    }


def _filtered_jobs(db: Session, filters: dict[str, Any] | None = None) -> list[JobPosting]:
    filters = filters or {}
    demo_mode = bool(filters.get("demo_mode")) if "demo_mode" in filters else True
    if demo_mode:
        sync_demo_labour_market(db)
    query = select(JobPosting).where(JobPosting.is_active.is_(True))
    if demo_mode:
        query = query.where(JobPosting.demo_marker.is_(True), JobPosting.provider == "demo")
    else:
        query = query.where(JobPosting.demo_marker.is_(False))
    provider = filters.get("provider")
    if provider:
        query = query.where(JobPosting.provider == provider)
    country = filters.get("country")
    if country:
        query = query.where(JobPosting.country == country)
    municipality = filters.get("municipality") or filters.get("municipality_or_region")
    if municipality:
        query = query.where(JobPosting.municipality.ilike(f"%{municipality}%"))
    county = filters.get("county")
    if county:
        query = query.where(JobPosting.county.ilike(f"%{county}%"))
    minimum_publication_date = _dt(filters.get("minimum_publication_date"))
    if minimum_publication_date:
        query = query.where(JobPosting.publication_time >= minimum_publication_date)
    rows = db.scalars(query.order_by(JobPosting.publication_time.desc(), JobPosting.title)).all()
    work_mode_values = filters.get("work_modes") or ([filters["work_mode"]] if filters.get("work_mode") else [])
    career_family_values = filters.get("career_families") or ([filters["career_family"]] if filters.get("career_family") else [])
    employment_type_values = filters.get("employment_types") or ([filters["employment_type"]] if filters.get("employment_type") else [])
    language_values = filters.get("preferred_languages") or filters.get("languages") or ([filters["language"]] if filters.get("language") else [])
    work_modes = {str(item).lower() for item in work_mode_values if item}
    career_families = {str(item).lower() for item in career_family_values if item}
    employment_types = {str(item).lower() for item in employment_type_values if item}
    languages = {str(item).lower() for item in language_values if item}
    excluded_employers = {str(item).lower() for item in filters.get("excluded_employers", []) if item}
    excluded_keywords = {str(item).lower() for item in filters.get("excluded_keywords", []) if item}
    text_query = str(filters.get("query") or "").strip().lower()
    role_title = str(filters.get("role_title") or filters.get("title") or "").strip().lower()
    seniority = str(filters.get("seniority") or filters.get("experience_level") or "").strip().lower()
    limit = int(filters.get("limit") or 50)
    result = []
    for row in rows:
        haystack = f"{row.title} {row.employer} {row.description}".lower()
        if text_query and text_query not in haystack:
            continue
        if role_title and role_title not in row.title.lower():
            continue
        if work_modes and row.work_mode.lower() not in work_modes:
            continue
        if career_families:
            row_family_values = {item.lower() for item in (row.career_families_json or [])}
            row_family_values.update(_slug(item) for item in (row.career_families_json or []))
            if not any(value in row_family_values or any(value in row_value for row_value in row_family_values) for value in career_families):
                continue
        if employment_types and row.employment_type.lower() not in employment_types:
            continue
        if languages:
            row_languages = {str(value).lower() for value in (row.language_requirements_json or [])}
            if not any(language in row_language for language in languages for row_language in row_languages):
                continue
        if seniority:
            experience_text = " ".join(str(value).lower() for value in (row.experience_requirements_json or []))
            if experience_text and seniority not in experience_text:
                continue
            if not experience_text:
                continue
        if row.employer.lower() in excluded_employers:
            continue
        if any(keyword in haystack for keyword in excluded_keywords):
            continue
        result.append(row)
    deduplicated: list[JobPosting] = []
    seen: set[str] = set()
    for row in result:
        key = row.canonical_job_key or row.id
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(row)
    return deduplicated[: max(1, min(limit, 100))]


def _distribution(values: list[str]) -> list[dict[str, Any]]:
    counts = Counter(value or "Unspecified" for value in values)
    return [{"label": key, "count": count} for key, count in counts.most_common()]


def _trend_label(observed: int, previous: int, sufficient: bool, continuity_ok: bool) -> str:
    if not continuity_ok:
        return "Data continuity incomplete"
    if not sufficient:
        return "Insufficient coverage"
    if observed > previous * 1.15:
        return "Observed more often in the current sample"
    if observed < previous * 0.85:
        return "Observed less often than the comparison sample"
    return "Appears repeatedly in available data"


def calculate_market_signals(db: Session, profile: Profile | None = None, window_days: int = 30, demo_mode: bool | None = None) -> dict[str, Any]:
    if demo_mode is None:
        # Preserve the legacy service-level default. The router passes an
        # explicit value so production API calls never fall back implicitly.
        demo_mode = True
    provider_id = "demo" if demo_mode else get_settings().labour_market_provider
    if demo_mode:
        sync_demo_labour_market(db)
    provider_status = provider_public(db, _provider_row(db, provider_id))
    now = _now()
    observed_start = now - timedelta(days=window_days)
    previous_start = observed_start - timedelta(days=window_days)
    run = MarketSignalRun(
        profile_id=profile.id if profile else None,
        provider=provider_id,
        observation_window_days=window_days,
        comparison_window_days=window_days,
        provider_status_json=provider_status,
        source_metadata_json={"source": JOB_SOURCE_TYPES["demo_fixture"] if demo_mode else JOB_SOURCE_TYPES["live_provider"], "trend_language": "observed_sample_only"},
        demo_marker=_demo_marker(profile),
        source_window_start=observed_start,
        source_window_end=now,
    )
    db.add(run)
    db.flush()
    jobs = db.scalars(select(JobPosting).where(JobPosting.provider == provider_id)).all()
    skill_counts_observed: Counter[str] = Counter()
    skill_counts_previous: Counter[str] = Counter()
    observed_job_count = 0
    previous_job_count = 0
    for job in jobs:
        published = job.publication_time or now
        target = skill_counts_observed if published >= observed_start else skill_counts_previous if previous_start <= published < observed_start else None
        if target is skill_counts_observed:
            observed_job_count += 1
        elif target is skill_counts_previous:
            previous_job_count += 1
        if target is not None:
            for skill in job.extracted_skills_json or []:
                target[_normalise_skill_phrase(skill)] += 1
    labels = set(skill_counts_observed) | set(skill_counts_previous)
    if demo_mode:
        labels |= {"responsible_ai", "ux_ui", "quantum_ai_governance"}
    results = []
    for skill in sorted(labels):
        observed = skill_counts_observed[skill]
        previous = skill_counts_previous[skill]
        continuity_ok = provider_status["current_cursor_status"] == "ready"
        sufficient = observed + previous >= MARKET_COVERAGE_MINIMUM
        if skill == "quantum_ai_governance":
            sufficient = False
        label = _trend_label(observed, previous, sufficient, continuity_ok)
        result = MarketSignalResult(
            run_id=run.id,
            signal_type="skill_frequency",
            label=_skill_label(skill),
            trend_label=label,
            observation_count=observed,
            comparison_count=previous,
            confidence_label="Moderate" if sufficient and continuity_ok else "Limited",
            limitations_json=[
                "Trend labels describe only the available local dataset.",
            "The result is not a hiring prediction or future-growth claim.",
            f"Coverage: {observed} of {observed_job_count} vacancies in the observation window mention this skill." if observed_job_count else "Insufficient coverage: no vacancies were available in the observation window.",
        ],
            factor_json={
                "observation_window": f"{window_days} days",
                "comparison_window": f"previous {window_days} days",
                "source": "local_job_index",
                "last_update": provider_status["latest_event_timestamp"],
                "sample_count": observed_job_count,
                "comparison_sample_count": previous_job_count,
            },
        )
        result.coverage_label = f"{observed} of {observed_job_count} sampled vacancies" if observed_job_count else "Insufficient coverage"
        result.source_window_json = {
            "observed_start": observed_start.isoformat(),
            "observed_end": now.isoformat(),
            "comparison_start": previous_start.isoformat(),
            "comparison_end": observed_start.isoformat(),
            "sample_count": observed_job_count,
            "comparison_sample_count": previous_job_count,
        }
        db.add(result)
        results.append(result)
    run.sample_count = observed_job_count
    run.coverage_sufficient = observed_job_count >= MARKET_COVERAGE_MINIMUM
    run.coverage_label = "Sufficient observed sample" if run.coverage_sufficient else "Insufficient coverage"
    db.commit()
    return {
        "id": run.id,
        "status": run.status,
        "observation_window_days": window_days,
        "comparison_window_days": window_days,
        "coverage": {"sample_count": observed_job_count, "comparison_sample_count": previous_job_count, "minimum_observations": MARKET_COVERAGE_MINIMUM, "sufficient": observed_job_count >= MARKET_COVERAGE_MINIMUM},
        "provider_status": provider_status,
        "results": [market_signal_public(item) for item in results],
    }


def market_signal_public(row: MarketSignalResult) -> dict[str, Any]:
    return {
        "id": row.id,
        "signal_type": row.signal_type,
        "label": row.label,
        "trend_label": row.trend_label,
        "observation_count": row.observation_count,
        "comparison_count": row.comparison_count,
        "confidence_label": row.confidence_label,
        "limitations": row.limitations_json or [],
        "factor": row.factor_json or {},
        "coverage_label": row.coverage_label,
        "source_window": row.source_window_json or {},
        "coverage": {
            "observed_count": row.observation_count,
            "sample_count": (row.factor_json or {}).get("sample_count", 0),
            "comparison_count": row.comparison_count,
            "label": row.coverage_label,
        },
    }


def upsert_market_preferences(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("user_confirmed_storage"):
        raise ValueError("User confirmation is required before storing market-radar preferences.")
    selected_hypothesis_id = payload.get("selected_hypothesis_id")
    if selected_hypothesis_id and not db.scalar(select(CareerHypothesis).where(CareerHypothesis.id == selected_hypothesis_id, CareerHypothesis.profile_id == profile.id)):
        raise PermissionError("Selected career hypothesis does not belong to this profile.")
    row = db.scalar(select(MarketRadarPreference).where(MarketRadarPreference.profile_id == profile.id).order_by(MarketRadarPreference.updated_at.desc()))
    if not row:
        row = MarketRadarPreference(profile_id=profile.id, user_id=profile.user_id, demo_marker=_demo_marker(profile))
    row.country = payload.get("country") or row.country or "Norway"
    row.county = payload.get("county") or ""
    row.municipality = payload.get("municipality") or ""
    row.commuting_area = payload.get("commuting_area") or ""
    row.radius_km = payload.get("radius_km")
    row.work_modes_json = payload.get("work_modes") or []
    row.preferred_languages_json = payload.get("preferred_languages") or []
    row.employment_types_json = payload.get("employment_types") or []
    row.full_time_part_time_json = payload.get("full_time_part_time") or []
    row.career_families_json = payload.get("career_families") or []
    row.selected_hypothesis_id = selected_hypothesis_id
    row.minimum_publication_date = payload.get("minimum_publication_date")
    row.experience_level = payload.get("experience_level") or ""
    row.role_title = payload.get("role_title") or ""
    row.excluded_employers_json = payload.get("excluded_employers") or []
    row.excluded_keywords_json = payload.get("excluded_keywords") or []
    row.relocation_preference = payload.get("relocation_preference") or ""
    row.user_confirmed_storage = True
    row.updated_at = _now()
    db.add(row)
    db.commit()
    return market_preferences_public(row)


def market_preferences_public(row: MarketRadarPreference) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "country": row.country,
        "county": row.county,
        "municipality": row.municipality,
        "commuting_area": row.commuting_area,
        "radius_km": row.radius_km,
        "work_modes": row.work_modes_json or [],
        "preferred_languages": row.preferred_languages_json or [],
        "employment_types": row.employment_types_json or [],
        "full_time_part_time": row.full_time_part_time_json or [],
        "career_families": row.career_families_json or [],
        "selected_hypothesis_id": row.selected_hypothesis_id,
        "minimum_publication_date": row.minimum_publication_date,
        "experience_level": row.experience_level,
        "role_title": row.role_title,
        "excluded_employers": row.excluded_employers_json or [],
        "excluded_keywords": row.excluded_keywords_json or [],
        "relocation_preference": row.relocation_preference,
        "user_confirmed_storage": row.user_confirmed_storage,
        "updated_at": row.updated_at.isoformat(),
    }


def market_radar(db: Session, profile: Profile, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    filters = dict(filters or {})
    demo_mode = _demo_mode_requested(profile, filters)
    filters.setdefault("demo_mode", demo_mode)
    saved_preferences = db.scalar(select(MarketRadarPreference).where(MarketRadarPreference.profile_id == profile.id).order_by(MarketRadarPreference.updated_at.desc()))
    base_filters = market_preferences_public(saved_preferences) if saved_preferences else {"country": "Norway"}
    merged_filters = {**base_filters, **filters}
    jobs = _filtered_jobs(db, merged_filters)
    provider_id = "demo" if demo_mode else get_settings().labour_market_provider
    provider = provider_public(db, _provider_row(db, provider_id))
    nav_status = provider_public(db, _provider_row(db, "nav_stilling_feed"))
    provider_status_response = providers_status(db)
    job_cards = [job_public(db, job, profile) for job in jobs]
    skills = [skill for job in jobs for skill in (job.extracted_skills_json or [])]
    hypotheses = db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.status == "active").order_by(CareerHypothesis.updated_at.desc())).all()
    evidence = _evidence_by_skill(db, profile.id)
    recurring_skills = [{"skill_id": _normalise_skill_phrase(skill), "skill_label": _skill_label(_normalise_skill_phrase(skill)), "count": count} for skill, count in Counter(skills).most_common(12)]
    coverage = []
    for item in recurring_skills:
        passport_item = evidence.get(item["skill_id"])
        coverage.append(
            {
                **item,
                "evidence_confidence": passport_item.get("evidence_confidence") if passport_item else "Missing evidence",
                "strongest_evidence": passport_item.get("strongest_evidence_label") if passport_item else "None",
                "recency": passport_item.get("recency") if passport_item else {"status": "Unknown", "refresh_recommendation": "Add evidence before relying on this skill."},
            }
        )
    signals = calculate_market_signals(db, profile, demo_mode=demo_mode)
    market_uncertainties = [
        "Market results are limited to the provider and source window shown above.",
        "Trend labels describe observed records in the current sample only.",
        "No result is a hiring prediction or complete Norwegian job-market coverage.",
    ]
    if not demo_mode and not provider_status_response.get("live_enabled"):
        market_uncertainties.insert(0, "Provider unavailable. Deterministic demo fixtures are hidden until Demo Mode is explicitly selected.")
    recurring_requirements = sorted(signals["results"], key=lambda item: item["observation_count"], reverse=True)[:10]
    emerging_observed_requirements = [item for item in recurring_requirements if item["trend_label"] not in {"Insufficient coverage", "Data continuity incomplete"}][:6]
    geographical_distribution = _distribution([job.municipality or job.county or "Unspecified" for job in jobs])
    language_distribution = _distribution([str(lang) for job in jobs for lang in (job.language_requirements_json or [])])
    return {
        "profile_id": profile.id,
        "provider_status": provider,
        "provider_status_response": provider_status_response,
        "nav_provider_status": nav_status,
        "preferences": market_preferences_public(saved_preferences) if saved_preferences else None,
        "source_classification": JOB_SOURCE_TYPES["demo_fixture"] if demo_mode else JOB_SOURCE_TYPES["live_provider"],
        "data_source": JOB_SOURCE_TYPES["demo_fixture"] if demo_mode else JOB_SOURCE_TYPES["live_provider"],
        "data_coverage": "Fictional demo records for Norway; not complete market coverage." if demo_mode else (provider.get("coverage_notes") or "No provider coverage is currently available."),
        "live_disabled_message": nav_status.get("degraded_mode_reason"),
        "last_sync": provider.get("last_successful_sync"),
        "freshness": provider.get("freshness"),
        "provider_state": provider.get("provider_state"),
        "coverage": signals.get("coverage"),
        "demo_mode": demo_mode,
        "demo_data_hidden": not demo_mode,
        "filters": merged_filters,
        "saved_filters": merged_filters,
        "current_opportunities": job_cards,
        "active_jobs": job_cards,
        "matching_active_jobs": len(job_cards),
        "recurring_job_titles": _distribution([job.title for job in jobs]),
        "recurring_skills": recurring_skills,
        "language_requirements": language_distribution,
        "experience_requirements": _distribution([str(item) for job in jobs for item in (job.experience_requirements_json or [])]),
        "work_mode_distribution": _distribution([job.work_mode for job in jobs]),
        "geographical_distribution": geographical_distribution,
        "location_language": {"municipalities": geographical_distribution, "languages": language_distribution},
        "active_career_hypotheses": [{"id": item.id, "title": item.title, "statement": item.statement, "uncertainty_label": item.uncertainty_label} for item in hypotheses],
        "related_career_directions": sorted({family for job in jobs for family in (job.career_families_json or [])}),
        "evidence_coverage": coverage,
        "market_signals": signals["results"],
        "signal_run": {
            "id": signals["id"],
            "status": signals["status"],
            "coverage_label": signals.get("coverage", {}).get("sufficient") and ("Deterministic demo sample" if demo_mode else "Provider sample") or "Insufficient coverage",
            "source_metadata": {"source": JOB_SOURCE_TYPES["demo_fixture"] if demo_mode else JOB_SOURCE_TYPES["live_provider"], "trend_language": "observed_sample_only", "coverage": signals.get("coverage")},
            "created_at": signals.get("provider_status", {}).get("freshness_timestamp") or _now().isoformat(),
        },
        "recurring_requirements": recurring_requirements,
        "emerging_observed_requirements": emerging_observed_requirements,
        "market_uncertainties": market_uncertainties,
        "limitations": market_uncertainties,
        "sections": [
            "Current opportunities",
            "Recurring requirements",
            "Emerging observed requirements",
            "Evidence coverage",
            "Location and language",
            "Market limitations",
        ],
    }


def list_jobs(db: Session, profile: Profile | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [job_public(db, row, profile) for row in _filtered_jobs(db, filters)]


def get_job(db: Session, job_id: str, profile: Profile | None = None) -> dict[str, Any]:
    row = db.get(JobPosting, job_id)
    if not row:
        raise LookupError("Job posting not found")
    return job_public(db, row, profile)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+|;", text)
    return [_clean_text(part, 800) for part in parts if len(_clean_text(part, 800)) >= 8]


def _requirement_category(sentence: str) -> str:
    lower = sentence.lower()
    if any(word in lower for word in ["language", "english", "norwegian", "norsk", "engelsk"]):
        return "language"
    if any(word in lower for word in ["certificate", "certification", "certified", "certifikat"]):
        return "certifications"
    if any(word in lower for word in ["communication", "collaboration", "teamwork", "stakeholder", "facilitation", "leadership"]):
        return "soft_skills"
    if any(word in lower for word in ["degree", "education", "bachelor", "master", "utdanning"]):
        return "education"
    if any(word in lower for word in ["experience", "years", "erfaring"]):
        return "experience"
    if any(word in lower for word in ["portfolio", "case", "project"]):
        return "portfolio"
    if any(word in lower for word in ["authorisation", "authorization", "work permit", "residence"]):
        return "work_authorisation"
    if any(word in lower for word in ["react", "python", "api", "rag", "sql", "tool", "technology"]):
        return "tools_technologies"
    if any(word in lower for word in ["responsible", "domain", "health", "education", "public sector"]):
        return "domain_knowledge"
    return "skills"


def _requirement_type(sentence: str) -> str:
    lower = sentence.lower()
    if any(word in lower for word in ["preferred", "nice to have", "useful", "advantage", "onskelig"]):
        return "preferred"
    if any(word in lower for word in ["mandatory", "required", "must", "krav", "ma ", "ma ha"]):
        return "mandatory"
    return "unclear"


def _requirement_segments(sentence: str) -> list[str]:
    """Keep mixed mandatory/preferred clauses distinct without inventing requirements."""
    markers = list(re.finditer(r"\b(?:mandatory\s+requirements?|required\s+requirements?|preferred\s+requirements?|nice\s+to\s+have|useful|advantage)\b", sentence, re.IGNORECASE))
    if len(markers) < 2:
        return [sentence]
    segments = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(sentence)
        segment = sentence[marker.start():end].strip(" ,:;-")
        if segment:
            segments.append(segment)
    return segments


def _extract_responsibilities(text: str) -> list[str]:
    responsibilities = []
    for sentence in _sentences(text):
        lower = sentence.lower()
        if any(marker in lower for marker in ["responsibilities", "responsible for", "you will", "your role", "role includes", "ansvar"]):
            if sentence not in responsibilities:
                responsibilities.append(sentence)
    return responsibilities[:12]


def _extract_requirements(text: str, job: JobPosting | None = None) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, sentence in enumerate(_sentences(text)):
        for segment in _requirement_segments(sentence):
            lower = segment.lower()
            if not any(word in lower for word in ["required", "mandatory", "must", "preferred", "experience", "language", "portfolio", "skill", "knowledge", "certification", "certificate", "degree", "education", "krav", "onskelig"]):
                continue
            canonical = re.sub(r"\s+", " ", lower).strip(" .")
            if canonical in seen:
                continue
            seen.add(canonical)
            category = _requirement_category(segment)
            requirement_type = _requirement_type(segment)
            normalised = None
            if category in {"skills", "soft_skills", "tools_technologies", "domain_knowledge", "portfolio"}:
                normalised = _normalise_skill_phrase(segment)
            requirements.append(
                {
                    "requirement_text": segment,
                    "requirement_category": category,
                    "requirement_type": requirement_type,
                    "source_excerpt": segment[:300],
                    "source_location": f"sentence:{index + 1}",
                    "extraction_method": "deterministic_text_rules",
                    "confidence": "medium",
                    "normalised_skill_id": normalised,
                }
            )
    if job and not requirements:
        for index, skill in enumerate(job.extracted_skills_json or []):
            requirements.append(
                {
                    "requirement_text": f"Demonstrate {_skill_label(_normalise_skill_phrase(skill))}.",
                    "requirement_category": "skills",
                    "requirement_type": "mandatory" if index < 2 else "preferred",
                    "source_excerpt": skill,
                    "source_location": "provider_metadata",
                    "extraction_method": "provider_metadata_fallback",
                    "confidence": "medium",
                    "normalised_skill_id": _normalise_skill_phrase(skill),
                }
            )
    return requirements[:30]


def create_job_analysis(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    job = db.get(JobPosting, payload.get("job_id")) if payload.get("job_id") else None
    capture = db.get(BrowserJobCapture, payload.get("capture_id")) if payload.get("capture_id") else None
    if capture and capture.profile_id != profile.id:
        raise PermissionError("Browser capture does not belong to this profile")
    if capture and capture.status not in {"Confirmed", "Analysed"}:
        raise ValueError("Browser-captured content must be explicitly confirmed before analysis.")
    input_type = payload.get("input_type") or ("saved_job" if job else "browser_capture_confirmed" if capture else "pasted_text")
    source_type = {
        "saved_job": "imported_market_vacancy",
        "imported_job": "imported_market_vacancy",
        "pasted_text": "pasted_job_ad",
        "url": "imported_market_vacancy",
        "supported_source_url": "imported_market_vacancy",
        "browser_capture": "browser_capture",
        "browser_capture_confirmed": "browser_capture_confirmed",
    }.get(input_type, input_type or "pasted_job_ad")
    text = ""
    source_url = job.source_url if job else capture.source_url if capture else payload.get("source_url")
    if job:
        text = job.description
        source_type = "imported_market_vacancy"
    elif capture:
        text = capture.sanitised_text or capture.selected_text
        source_type = "browser_capture_confirmed"
    elif source_url:
        text = _fetch_supported_url(source_url, timeout=get_settings().nav_stilling_feed_request_timeout_seconds)
        input_type = "supported_source_url"
        source_type = "imported_market_vacancy"
    else:
        text = _clean_text(payload.get("text") or payload.get("pasted_text") or "")
    if not text.strip() and not job:
        raise ValueError("Provide an imported job, supported URL, or advertisement text.")
    if len(text) > MAX_PASTED_AD_CHARS:
        raise ValueError("Advertisement text exceeds the configured request-size limit.")
    capture_fields = (capture.confirmed_fields_json or {}) if capture else {}
    title = payload.get("title") or capture_fields.get("title") or (job.title if job else "Pasted job advertisement")
    organisation = payload.get("organisation") or capture_fields.get("employer") or (job.employer if job else "")
    title = title or (job.title if job else "Pasted job advertisement")
    organisation = organisation or (job.employer if job else "")
    # A source may be imported or capture-confirmed without making extracted
    # requirements authoritative. That requires a separate user review step.
    confirmed = False
    analysis = JobAnalysis(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_id=job.id if job else None,
        input_type=input_type,
        source_type=source_type,
        source_url=source_url or (job.source_url if job else None),
        title=title,
        organisation=organisation,
        location=", ".join(part for part in ([job.municipality, job.country] if job else [payload.get("location", "")]) if part),
        deadline=_date(job.expiry_time) if job else payload.get("deadline"),
        raw_text_excerpt=text[:2000],
        source_metadata_json={
            "source_type": source_type,
            "source_label": JOB_SOURCE_TYPES.get(source_type, source_type),
            "source_url": source_url or (job.source_url if job else None),
            "provider": job.provider if job else None,
            "provider_id": job.external_job_id if job else None,
            "capture_id": capture.id if capture else None,
            "canonical_source_type": "BROWSER_CAPTURE" if capture else None,
            "content_hash": _hash({"text": text, "source_url": source_url or ""}),
            "user_confirmed": confirmed,
        },
        user_confirmed=confirmed,
        user_confirmed_at=_now() if confirmed else None,
        structured_output_json={
            "responsibilities": _extract_responsibilities(text),
            "application_documents": ["CV", "Cover letter"],
            "deadline": _date(job.expiry_time) if job else payload.get("deadline"),
                "source": input_type,
            "source_type": source_type,
            "categories": ["responsibilities", "mandatory_requirements", "preferred_requirements", "education", "experience", "tools", "language", "certifications", "soft_skills", "working_conditions"],
        },
        uncertainties_json=["User should review extracted requirements before relying on them."],
        demo_marker=_demo_marker(profile) or bool(job and job.demo_marker),
    )
    db.add(analysis)
    db.flush()
    for index, item in enumerate(_extract_requirements(text, job)):
        db.add(
            JobRequirement(
                analysis_id=analysis.id,
                profile_id=profile.id,
                requirement_text=item["requirement_text"],
                requirement_category=item["requirement_category"],
                requirement_type=item["requirement_type"],
                source_excerpt=item["source_excerpt"],
                source_location=item["source_location"],
                extraction_method=item["extraction_method"],
                confidence=item["confidence"],
                normalised_skill_id=item.get("normalised_skill_id"),
                extracted_requirement_type=item["requirement_type"],
                extracted_requirement_category=item["requirement_category"],
                extraction_timestamp=_now(),
                job_analysis_version=analysis.extraction_version,
                order_index=index,
            )
        )
    db.add(JobAnalysisVersion(analysis_id=analysis.id, version_number=1, snapshot_json={"title": title, "input_type": input_type, "source_type": source_type, "source_url": source_url, "raw_text_excerpt": text[:2000]}, change_reason="Initial deterministic extraction.", version_kind="extraction", edited_by_user=False))
    db.commit()
    return job_analysis_public(db, analysis)


def require_analysis(db: Session, analysis_id: str, profile: Profile | None = None) -> JobAnalysis:
    row = db.get(JobAnalysis, analysis_id)
    if not row:
        raise LookupError("Job analysis not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Job analysis does not belong to this profile")
    return row


def update_requirement(db: Session, requirement: JobRequirement, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    before = requirement_public(db, requirement)
    if payload.get("requirement_text") is not None:
        requirement.requirement_text = _clean_text(payload["requirement_text"], 1200)
    if payload.get("requirement_category"):
        category = str(payload["requirement_category"]).strip().lower()
        if category not in REQUIREMENT_CATEGORIES:
            raise ValueError("Unsupported requirement category.")
        requirement.requirement_category = category
    if payload.get("requirement_type"):
        requirement_type = str(payload["requirement_type"]).strip().lower()
        if requirement_type not in REQUIREMENT_TYPES:
            raise ValueError("Requirement type must be mandatory, preferred, or unclear.")
        requirement.requirement_type = requirement_type
    if payload.get("user_confirmation_state"):
        confirmation_state = str(payload["user_confirmation_state"]).strip().lower()
        if confirmation_state not in {"needs_review", "confirmed", "rejected"}:
            raise ValueError("Unsupported requirement confirmation state.")
        requirement.user_confirmation_state = confirmation_state
    if payload.get("status"):
        status = str(payload["status"]).strip().lower()
        if status not in {"active", "rejected"}:
            raise ValueError("Unsupported requirement status.")
        requirement.status = status
    if payload.get("normalised_skill_id") is not None:
        requirement.normalised_skill_id = payload["normalised_skill_id"]
    edited_fields = {"requirement_text", "requirement_category", "requirement_type", "normalised_skill_id"}.intersection(payload)
    if edited_fields:
        requirement.user_edited = True
    action = str(payload.get("action") or "").lower()
    if action in {"accept", "confirm", "edit", "reject", "reclassify"}:
        requirement.confirmation_action = {"accept": "accepted", "confirm": "accepted", "edit": "edited", "reject": "rejected", "reclassify": "reclassified"}[action]
        requirement.user_confirmation_state = "confirmed" if action != "reject" else "rejected"
        requirement.confirmed_at = _now()
        requirement.confirmed_by = user_id
        if action == "reject":
            requirement.status = "rejected"
    elif payload.get("user_confirmation_state") == "confirmed":
        requirement.confirmation_action = "accepted" if not edited_fields else "edited"
        requirement.confirmed_at = _now()
        requirement.confirmed_by = user_id
    analysis = db.get(JobAnalysis, requirement.analysis_id)
    if analysis:
        active_requirements = db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis.id, JobRequirement.status != "rejected")).all()
        review_complete = bool(active_requirements) and all(item.user_confirmation_state == "confirmed" for item in active_requirements)
        # Requirement-level decisions remain review records until the user
        # explicitly confirms the complete requirement set.
        analysis.user_confirmed = False
        analysis.user_confirmed_at = None
        if analysis.status == "confirmed":
            analysis.status = "analysed"
        previous_version = db.scalar(select(func.max(JobAnalysisVersion.version_number)).where(JobAnalysisVersion.analysis_id == analysis.id)) or 0
        db.add(JobAnalysisVersion(
            analysis_id=analysis.id,
            version_number=previous_version + 1,
            snapshot_json={"requirement_id": requirement.id, "requirement": requirement_public(db, requirement), "review_complete": review_complete, "analysis_user_confirmed": False},
            change_reason="User reviewed an extracted job requirement.",
            version_kind="user_review",
            edited_by_user=True,
        ))
    requirement.updated_at = _now()
    db.add(
        JobAnalysisCorrection(
            analysis_id=requirement.analysis_id,
            requirement_id=requirement.id,
            profile_id=requirement.profile_id,
            correction_type="user_correction",
            before_json=before,
            after_json=requirement_public(db, requirement),
            user_id=user_id,
        )
    )
    db.commit()
    return requirement_public(db, requirement)


def confirm_job_analysis(db: Session, analysis: JobAnalysis, user_id: str | None = None) -> dict[str, Any]:
    requirements = db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis.id)).all()
    active = [item for item in requirements if item.status != "rejected"]
    if active and not all(item.user_confirmation_state == "confirmed" for item in active):
        raise ValueError("Every active extracted requirement must be accepted, edited, reclassified, or rejected before analysis confirmation.")
    if not requirements:
        raise ValueError("There are no extracted requirements to confirm.")
    analysis.user_confirmed = True
    analysis.user_confirmed_at = _now()
    analysis.status = "confirmed"
    previous_version = db.scalar(select(func.max(JobAnalysisVersion.version_number)).where(JobAnalysisVersion.analysis_id == analysis.id)) or 0
    db.add(JobAnalysisVersion(
        analysis_id=analysis.id,
        version_number=previous_version + 1,
        snapshot_json={"analysis_id": analysis.id, "requirements": [requirement_public(db, item) for item in requirements], "user_confirmed": True},
        change_reason="User confirmed authoritative job requirements.",
        version_kind="user_confirmation",
        edited_by_user=True,
    ))
    db.commit()
    return job_analysis_public(db, analysis)


def requirement_public(db: Session, row: JobRequirement) -> dict[str, Any]:
    matches = db.scalars(select(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.requirement_id == row.id).order_by(JobRequirementEvidenceMatch.created_at.desc())).all()
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "requirement_text": row.requirement_text,
        "classification": row.requirement_category,
        "requirement_category": row.requirement_category,
        "requirement_type": row.requirement_type,
        "extracted_requirement_type": row.extracted_requirement_type,
        "extracted_requirement_category": row.extracted_requirement_category,
        "source_excerpt": row.source_excerpt,
        "source_location": row.source_location,
        "extraction_method": row.extraction_method,
        "confidence": row.confidence,
        "user_confirmation_state": row.user_confirmation_state,
        "user_edited": row.user_edited,
        "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None,
        "confirmation_action": row.confirmation_action,
        "extraction_timestamp": row.extraction_timestamp.isoformat() if row.extraction_timestamp else None,
        "job_analysis_version": row.job_analysis_version,
        "normalised_skill_id": row.normalised_skill_id,
        "esco_uri": row.esco_uri,
        "status": row.status,
        "matches": [evidence_match_public(db, item) for item in matches],
    }


def evidence_match_public(db: Session, row: JobRequirementEvidenceMatch) -> dict[str, Any]:
    evidence = db.get(SkillEvidence, row.evidence_id) if row.evidence_id else None
    return {
        "id": row.id,
        "requirement_id": row.requirement_id,
        "evidence_id": row.evidence_id,
        "evidence_type": row.evidence_type,
        "evidence_strength": row.evidence_strength,
        "evidence_status": row.evidence_status,
        "evidence_source": {
            "label": evidence.title,
            "type": evidence.evidence_type,
            "verification_status": evidence.verification_status,
        } if evidence else None,
        "match_category": row.match_category,
        "recency_label": row.recency_label,
        "gap": row.gap,
        "possible_transferable_evidence": row.transferable_evidence_json or [],
        "user_confirmation": row.user_confirmation_state,
        "recommended_action": row.recommended_action,
        "deterministic_reason": row.deterministic_reason,
    }


def _evidence_status(passport_item: dict[str, Any] | None) -> str:
    if not passport_item:
        return "NOT ASSESSED"
    recency = (passport_item.get("recency") or {}).get("status", "Unknown")
    if str(recency).lower() in {"outdated", "stale", "needs refresh"}:
        return "OUTDATED"
    sources = passport_item.get("evidence_sources") or []
    if not sources:
        return "SELF_REPORT ONLY"
    if any(str(item.get("verification_status", "")).lower() in {"conflicting", "disputed"} for item in sources):
        return "CONFLICTING"
    strongest = str(passport_item.get("strongest_evidence_label") or "").lower()
    if strongest in {"practically verified", "demonstrated", "supported"}:
        return "CONFIRMED EVIDENCE"
    return "PARTIAL EVIDENCE"


def _match_category(evidence_status: str, requirement_type: str) -> tuple[str, str]:
    if evidence_status == "CONFIRMED EVIDENCE":
        return "Strong evidence", "Use this confirmed evidence only if the user confirms its relevance to the role."
    if evidence_status == "PARTIAL EVIDENCE":
        return "Partial evidence", "Position this as partial evidence and avoid claiming full scope."
    if evidence_status == "SELF_REPORT ONLY":
        return "Self-report only", "Treat this as a self-report until a dated artifact or independent confirmation exists."
    if evidence_status == "OUTDATED":
        return "Outdated evidence", "Refresh the evidence before relying on this requirement."
    if evidence_status == "CONFLICTING":
        return "Conflicting evidence", "Resolve the conflicting records before using this claim."
    if evidence_status == "NOT ASSESSED":
        return "Capability not yet assessed", "No corresponding capability signal or Evidence Passport record is available. Treat this as an assessment gap, not as missing evidence."
    if requirement_type == "unclear":
        return "User confirmation required", "Clarify whether this extracted item is mandatory, preferred, or not a requirement."
    return "Missing evidence", "Create or link evidence before using this requirement as a factual application claim."


def match_analysis_evidence(db: Session, analysis: JobAnalysis) -> dict[str, Any]:
    db.execute(delete(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.analysis_id == analysis.id))
    passport = _evidence_by_skill(db, analysis.profile_id)
    rows = db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis.id, JobRequirement.status == "active").order_by(JobRequirement.order_index)).all()
    created = []
    for req in rows:
        skill_id = req.normalised_skill_id or _normalise_skill_phrase(req.requirement_text)
        passport_item = passport.get(skill_id)
        transferable = []
        for transferable_id in TRANSFERABLE_SKILLS.get(skill_id, []):
            if transferable_id in passport:
                transferable.append({"skill_id": transferable_id, "skill_label": _skill_label(transferable_id), "evidence_confidence": passport[transferable_id].get("evidence_confidence")})
        evidence_id = _first_evidence_id(passport_item)
        if not analysis.user_confirmed or req.user_confirmation_state != "confirmed":
            evidence_status = "NOT ASSESSED"
            category = "Needs user confirmation"
            action = "Confirm the complete requirement set before using this extracted item for authoritative evidence mapping or readiness."
        else:
            evidence_status = _evidence_status(passport_item)
            category, action = _match_category(evidence_status, req.requirement_type)
        if req.user_confirmation_state == "confirmed" and evidence_status == "MISSING" and transferable:
            category = "Transferable evidence"
            action = "Use transferable evidence carefully and avoid claiming direct experience."
        match = JobRequirementEvidenceMatch(
            requirement_id=req.id,
            analysis_id=analysis.id,
            profile_id=analysis.profile_id,
            evidence_id=evidence_id,
            evidence_type=(passport_item.get("strongest_evidence_label") if passport_item else ""),
            evidence_strength=(passport_item.get("evidence_confidence") if passport_item else "Not assessed"),
            evidence_status=evidence_status,
            match_category=category,
            recency_label=(passport_item.get("recency", {}).get("status") if passport_item else "Unknown"),
            gap=(
                "" if evidence_status in {"CONFIRMED EVIDENCE", "PARTIAL EVIDENCE"}
                else f"No corresponding capability signal or Evidence Passport record is available for {_skill_label(skill_id)}."
                if evidence_status == "NOT ASSESSED"
                else f"No direct confirmed evidence for {_skill_label(skill_id)}."
            ),
            transferable_evidence_json=transferable,
            recommended_action=action,
            deterministic_reason=f"Matched requirement skill '{skill_id}' against Evidence Passport records. No AI-generated evidence was used.",
        )
        db.add(match)
        created.append(match)
    db.commit()
    return {"analysis_id": analysis.id, "matches": [evidence_match_public(db, item) for item in created]}


def calculate_job_readiness(db: Session, analysis: JobAnalysis) -> dict[str, Any]:
    matches = db.scalars(select(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.analysis_id == analysis.id)).all()
    if not matches:
        match_analysis_evidence(db, analysis)
        matches = db.scalars(select(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.analysis_id == analysis.id)).all()
    requirements = {row.id: row for row in db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis.id, JobRequirement.status != "rejected")).all()}
    pending_confirmation = [row for row in requirements.values() if row.user_confirmation_state != "confirmed"]
    analysis_confirmation_pending = bool(requirements) and not analysis.user_confirmed
    supported_count = partial_count = missing_count = outdated_count = unknown_count = 0
    unsupported_claims_risk: list[str] = []
    source_limitations = [
        "Readiness reflects confirmed requirements and available Evidence Passport records only.",
        "It is not an ATS score, recruiter score, interview probability, or hiring prediction.",
    ]
    if not requirements:
        label = "Insufficient information"
        reasons = ["No job requirements were extracted."]
        blockers = []
        actions = ["Add a clearer job description or import a job from the local index."]
        readiness_level = "Needs clarification"
    elif pending_confirmation or analysis_confirmation_pending:
        label = "Insufficient information"
        readiness_level = "Needs clarification"
        reasons = [
            f"{len(pending_confirmation)} extracted requirements still need user confirmation." if pending_confirmation else "Requirement-level review is complete.",
            "System extraction is not authoritative until the user confirms the complete requirement set.",
        ]
        blockers = [item.requirement_text for item in pending_confirmation] or ["Confirm the reviewed requirement set to make it authoritative."]
        actions = ["Review each requirement, preserve the source excerpt, then explicitly confirm the analysis before mapping evidence."]
    else:
        mandatory = [match for match in matches if requirements.get(match.requirement_id) and requirements[match.requirement_id].requirement_type == "mandatory"]
        supported_count = sum(1 for match in matches if match.evidence_status == "CONFIRMED EVIDENCE")
        partial_count = sum(1 for match in matches if match.evidence_status in {"PARTIAL EVIDENCE", "Transferable evidence"})
        missing_count = sum(1 for match in matches if match.evidence_status == "MISSING")
        outdated_count = sum(1 for match in matches if match.evidence_status == "OUTDATED")
        unknown_count = sum(1 for match in matches if match.evidence_status in {"SELF_REPORT ONLY", "CONFLICTING", "NOT ASSESSED"})
        unsupported_claims_risk = [requirements[match.requirement_id].requirement_text for match in matches if match.evidence_status in {"MISSING", "SELF_REPORT ONLY", "CONFLICTING", "OUTDATED"}]
        mandatory_missing = [match for match in mandatory if match.evidence_status in {"MISSING", "SELF_REPORT ONLY", "CONFLICTING", "OUTDATED"}]
        mandatory_not_assessed = [match for match in mandatory if match.evidence_status == "NOT ASSESSED"]
        mandatory_transferable = [match for match in mandatory if match.match_category == "Transferable evidence"]
        unclear = [match for match in matches if requirements.get(match.requirement_id) and requirements[match.requirement_id].requirement_type == "unclear"]
        if any(requirements[match.requirement_id].requirement_category == "work_authorisation" and match.match_category != "Strong evidence" for match in mandatory):
            label = "Eligibility or evidence blockers"
            readiness_level = "Low"
        elif mandatory_not_assessed:
            label = "Evidence or capability information incomplete"
            readiness_level = "Needs clarification"
        elif mandatory_missing:
            label = "Evidence gaps to address"
            readiness_level = "Low"
        elif mandatory_transferable or any(match.match_category == "Partial evidence" for match in matches):
            label = "Mixed evidence coverage"
            readiness_level = "Moderate"
        elif unclear:
            label = "Evidence or capability information incomplete"
            readiness_level = "Needs clarification"
        else:
            label = "Strong evidence coverage"
            readiness_level = "High"
        blockers = [requirements[match.requirement_id].requirement_text for match in mandatory_missing]
        reasons = [
            f"{supported_count} confirmed requirements have supporting evidence.",
            f"{partial_count} requirements have partial or transferable evidence.",
            f"{missing_count} requirements are missing evidence; {outdated_count} are outdated; {unknown_count} are self-report only, conflicting, or not assessed.",
        ]
        actions = ["Review extracted requirements and confirm classifications.", "Use only evidence-linked claims in CV and cover letter."]
        if mandatory_missing:
            actions.append("Create or link evidence before relying on the affected requirement as a factual application claim.")
    row = JobReadinessResult(
        analysis_id=analysis.id,
        profile_id=analysis.profile_id,
        readiness_label=label,
        reasons_json=reasons,
        blockers_json=blockers,
        recommended_actions_json=actions,
        supported_count=supported_count,
        partial_count=partial_count,
        missing_count=missing_count,
        outdated_count=outdated_count,
        unknown_count=unknown_count,
        unsupported_claims_risk_json=unsupported_claims_risk,
        source_limitations_json=source_limitations,
        formula_version="job-readiness-v2",
    )
    db.add(row)
    db.commit()
    result = readiness_public(row)
    result["readiness_level"] = readiness_level
    result["requires_user_confirmation"] = bool(pending_confirmation or analysis_confirmation_pending)
    result["explanation"] = {
        "supported_requirements": supported_count,
        "partial_requirements": partial_count,
        "missing_evidence": missing_count,
        "outdated_evidence": outdated_count,
        "unknowns": unknown_count,
        "unsupported_claims_risk": unsupported_claims_risk,
        "source_limitations": source_limitations,
    }
    return result


def readiness_public(row: JobReadinessResult) -> dict[str, Any]:
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "readiness_label": row.readiness_label,
        "reasons": row.reasons_json or [],
        "blockers": row.blockers_json or [],
        "recommended_actions": row.recommended_actions_json or [],
        "readiness_level": {
            "Strong evidence coverage": "High",
            "Mixed evidence coverage": "Moderate",
            "Evidence gaps to address": "Low",
            "Eligibility or evidence blockers": "Low",
            "Evidence or capability information incomplete": "Needs clarification",
            "Insufficient information": "Needs clarification",
            "Apply now": "High",
            "Apply with positioning": "Moderate",
            "Prepare first": "Low",
            "Low current feasibility": "Low",
        }.get(row.readiness_label, "Needs clarification"),
        "supported_count": row.supported_count,
        "partial_count": row.partial_count,
        "missing_count": row.missing_count,
        "outdated_count": row.outdated_count,
        "unknown_count": row.unknown_count,
        "unsupported_claims_risk": row.unsupported_claims_risk_json or [],
        "source_limitations": row.source_limitations_json or [],
        "explanation": {"supported_requirements": row.supported_count, "partial_requirements": row.partial_count, "missing_evidence": row.missing_count, "outdated_evidence": row.outdated_count, "unknowns": row.unknown_count, "unsupported_claims_risk": row.unsupported_claims_risk_json or [], "source_limitations": row.source_limitations_json or []},
        "requires_user_confirmation": row.readiness_label == "Insufficient information" and any("confirmation" in str(item).lower() for item in (row.reasons_json or [])),
        "formula_version": row.formula_version,
        "deterministic_version": row.deterministic_version,
        "created_at": row.created_at.isoformat(),
    }


def job_analysis_public(db: Session, row: JobAnalysis) -> dict[str, Any]:
    requirements = db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == row.id).order_by(JobRequirement.order_index)).all()
    readiness = db.scalar(select(JobReadinessResult).where(JobReadinessResult.analysis_id == row.id).order_by(JobReadinessResult.created_at.desc()))
    job = db.get(JobPosting, row.job_id) if row.job_id else None
    latest_version = db.scalar(select(JobAnalysisVersion).where(JobAnalysisVersion.analysis_id == row.id).order_by(JobAnalysisVersion.version_number.desc()))
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "job_id": row.job_id,
        "input_type": row.input_type,
        "source_type": row.source_type,
        "source_url": row.source_url,
        "title": row.title,
        "organisation": row.organisation,
        "location": row.location,
        "deadline": row.deadline,
        "raw_text_excerpt": row.raw_text_excerpt,
        "source_metadata": row.source_metadata_json or {},
        "user_confirmed": row.user_confirmed,
        "user_confirmed_at": row.user_confirmed_at.isoformat() if row.user_confirmed_at else None,
        "structured_output": row.structured_output_json or {},
        "uncertainties": row.uncertainties_json or [],
        "ambiguous_statements": [req.requirement_text for req in requirements if req.requirement_type == "unclear"],
        "status": row.status,
        "extraction_version": row.extraction_version,
        "analysis_version": latest_version.version_number if latest_version else 1,
        "requirements": [requirement_public(db, item) for item in requirements],
        "readiness": readiness_public(readiness) if readiness else None,
        "job": job_public(db, job) if job else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_job_analyses(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(JobAnalysis).where(JobAnalysis.profile_id == profile_id).order_by(JobAnalysis.updated_at.desc())).all()
    return [job_analysis_public(db, row) for row in rows]


def ensure_master_career_profile(db: Session, profile: Profile) -> dict[str, Any]:
    row = db.scalar(select(MasterCareerProfile).where(MasterCareerProfile.profile_id == profile.id).order_by(MasterCareerProfile.updated_at.desc()))
    if not row:
        data = profile.data or {}
        row = MasterCareerProfile(
            profile_id=profile.id,
            user_id=profile.user_id,
            professional_summary=(data.get("primary_archetype", {}) or {}).get("summary", "") if isinstance(data.get("primary_archetype"), dict) else "",
            language_profile_json=_profile_languages(profile),
            portfolio_links_json=[],
            source_metadata_json={"origin": "OrganicAI profile, Evidence Passport, and career experiments"},
            demo_marker=_demo_marker(profile),
        )
        db.add(row)
        db.flush()
        passport = evidence_passport(db, profile.id)
        for skill in passport.get("skills", [])[:12]:
            db.add(
                CareerProfileEntry(
                    master_profile_id=row.id,
                    profile_id=profile.id,
                    entry_type="skill",
                    title=skill["skill_label"],
                    description=f"{skill['evidence_confidence']} - {skill['strongest_evidence_label']}",
                    origin="evidence_passport",
                    source_id=skill["skill_id"],
                    user_confirmation_state="needs_review",
                    evidence_relationship_json=skill.get("evidence_sources", []),
                    inclusion_permission="requires_confirmation",
                )
            )
        db.commit()
    entries = db.scalars(select(CareerProfileEntry).where(CareerProfileEntry.master_profile_id == row.id).order_by(CareerProfileEntry.entry_type, CareerProfileEntry.title)).all()
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "status": row.status,
        "professional_summary": row.professional_summary,
        "language_profile": row.language_profile_json or [],
        "portfolio_links": row.portfolio_links_json or [],
        "version": row.version,
        "entries": [
            {
                "id": item.id,
                "entry_type": item.entry_type,
                "title": item.title,
                "description": item.description,
                "origin": item.origin,
                "source_id": item.source_id,
                "user_confirmation_state": item.user_confirmation_state,
                "inclusion_permission": item.inclusion_permission,
                "evidence_relationship": item.evidence_relationship_json or [],
            }
            for item in entries
        ],
    }


def _claim_status_from_text(text: str, linked_count: int = 0, user_confirmed: bool = False) -> tuple[str, str, str, bool]:
    lower = text.lower()
    blocked_patterns = [
        r"\bproduction-ready\b",
        r"\bdeployed at scale\b",
        r"\bguaranteed\b",
        r"\bats-approved\b",
        r"\b10 years\b",
        r"\bexpert in every\b",
        r"\benterprise ai transformation\b",
        r"\bcross-functional team of\s+\d+\b",
        r"\b(?:increased|grew|generated|delivered)\s+(?:revenue|sales|profit).*?\b\d+(?:\.\d+)?%",
    ]
    if any(re.search(pattern, lower) for pattern in blocked_patterns):
        return (
            "Blocked",
            "No matching evidence was found for an exaggerated or high-risk factual claim.",
            "I am interested in contributing to responsible AI work where my documented evidence is relevant.",
            True,
        )
    if linked_count >= 2:
        return "Supported", "Multiple evidence links support this claim.", "", False
    if linked_count == 1:
        return "Partially supported", "One evidence link supports part of this claim.", "", False
    if user_confirmed:
        return "User-confirmed", "The user explicitly confirmed this factual claim; stronger evidence is still preferable.", "", False
    if any(word in lower for word in ["transferable", "adjacent", "related"]):
        return "Transferable", "The claim is framed as transferable evidence rather than direct employment evidence.", "", False
    return "Unverified", "No linked evidence currently supports this claim.", "Rephrase to describe confirmed project or learning evidence.", False


def _support_state(claim_type: str, status: str, user_confirmed: bool = False) -> str:
    if claim_type in {"motivation", "intent", "intentional_language"}:
        return "MOTIVATIONAL"
    if status == "Supported":
        return "SUPPORTED"
    if status in {"Partially supported", "Transferable"}:
        return "PARTIALLY_SUPPORTED"
    if status == "User-confirmed" or user_confirmed:
        return "SELF_REPORT_ONLY"
    if status in {"Blocked", "Conflicting"}:
        return "UNSUPPORTED" if status == "Blocked" else "NEEDS_REVIEW"
    return "NEEDS_REVIEW"


def _create_section(db: Session, document: ApplicationDocument, section_type: str, title: str, content: str, order: int) -> DocumentSection:
    section = DocumentSection(document_id=document.id, profile_id=document.profile_id, section_type=section_type, title=title, content=content, order_index=order)
    db.add(section)
    db.flush()
    return section


def _create_claim(db: Session, document: ApplicationDocument, section: DocumentSection | None, text: str, claim_type: str, evidence_id: str | None = None) -> DocumentClaim:
    linked_count = 1 if evidence_id else 0
    status, reason, safer, blocked = _claim_status_from_text(text, linked_count=linked_count)
    claim = DocumentClaim(
        document_id=document.id,
        section_id=section.id if section else None,
        profile_id=document.profile_id,
        claim_text=text,
        claim_type=claim_type,
        status=status,
        safer_alternative=safer,
        deterministic_reason=reason,
        blocked_for_export=blocked,
        support_state=_support_state(claim_type, status),
        generated_by="deterministic_template",
        user_confirmation_state="needs_review",
    )
    db.add(claim)
    db.flush()
    if evidence_id:
        db.add(DocumentClaimEvidenceLink(claim_id=claim.id, document_id=document.id, profile_id=document.profile_id, evidence_id=evidence_id, confidence=status))
    return claim


def create_application_document(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    analysis = require_analysis(db, payload["job_analysis_id"], profile) if payload.get("job_analysis_id") else None
    doc_type = payload.get("document_type") or "cv"
    if doc_type not in {"cv", "cover_letter"}:
        raise ValueError("Unsupported application document type.")
    ensure_master_career_profile(db, profile)
    document = ApplicationDocument(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_analysis_id=analysis.id if analysis else None,
        document_type=doc_type,
        title=payload.get("title") or (f"{doc_type.replace('_', ' ').title()} for {analysis.title}" if analysis else f"{doc_type.replace('_', ' ').title()} draft"),
        language=payload.get("language") or "en",
        variant=payload.get("variant") or "concise",
        demo_marker=_demo_marker(profile),
        source_metadata_json={
            "ai_may_assist": True,
            "evidence_lock_required": True,
            "auto_apply": False,
            "ats_guarantee": False,
            "source_profile_version": "profile-current",
            "source_job_analysis_version": analysis.extraction_version if analysis else "",
            "source_evidence_version": "evidence-passport-v1",
            "requirements_user_confirmed": bool(analysis and analysis.user_confirmed) if analysis else None,
        },
        source_profile_version="profile-current",
        source_job_analysis_version=analysis.extraction_version if analysis else "",
        source_evidence_version="evidence-passport-v1",
    )
    db.add(document)
    db.flush()
    # Do not map extracted requirements into application claims before the
    # user confirms them. A pre-confirmation document is only a draft and is
    # never represented as evidence-locked.
    matches = match_analysis_evidence(db, analysis)["matches"] if analysis and analysis.user_confirmed else []
    supported = [match for match in matches if match["match_category"] in {"Strong evidence", "Partial evidence"} and match.get("evidence_id")]
    confirmed_requirements = db.scalars(
        select(JobRequirement).where(
            JobRequirement.analysis_id == analysis.id,
            JobRequirement.status == "active",
            JobRequirement.user_confirmation_state == "confirmed",
        ).order_by(JobRequirement.order_index)
    ).all() if analysis and analysis.user_confirmed else []
    requirement_labels = [item.requirement_text for item in confirmed_requirements[:6]]
    job_label = ""
    if analysis:
        job_label = f"{analysis.title}{f' at {analysis.organisation}' if analysis.organisation else ''}"
    requirement_summary = "; ".join(requirement_labels) or "No confirmed requirement wording is available yet."
    if doc_type == "cv":
        summary_content = f"Job-specific draft for {job_label}. Confirmed requirements are treated as evidence targets, not as claims of existing experience." if job_label else "Evidence-based career transition profile focused on human-centred AI and practical product work."
        competencies_content = requirement_summary if job_label else "Evidence-linked skills"
        summary = _create_section(db, document, "professional_summary", "Professional Summary", summary_content, 1)
        competencies = _create_section(db, document, "core_competencies", "Confirmed Requirements To Address", competencies_content, 2)
        _create_claim(db, document, summary, "Developed and locally evaluated AI-enabled web application prototypes with documented limitations.", "project_evidence", supported[0]["evidence_id"] if supported else None)
        _create_claim(db, document, competencies, "Developed production-ready AI systems.", "unsupported_seniority")
        _create_section(db, document, "projects", "Relevant Projects", f"Select only documented project, experiment, or portfolio evidence relevant to: {requirement_summary}" if job_label else "Selected career experiments and portfolio-style evidence only. No employment outcome is implied.", 3)
        _create_section(db, document, "education", "Education", "Education and training entries should be user-confirmed before export.", 4)
    else:
        intro_content = f"I am interested in contributing to the {job_label} role. This draft refers only to the confirmed requirement set." if job_label else "I am applying because the role connects practical evidence, responsible AI, and user-centred product work."
        evidence_content = f"Confirmed role requirements to address: {requirement_summary}" if job_label else "Two or three examples should be selected from linked Evidence Passport records."
        intro = _create_section(db, document, "reason_for_applying", "Reason for Applying", intro_content, 1)
        evidence = _create_section(db, document, "evidence_examples", "Evidence-Based Examples", evidence_content, 2)
        _create_claim(db, document, intro, f"I am interested in contributing to the {job_label} role." if job_label else "The role connects to my confirmed interest in human-centred AI and practical product evidence.", "motivation", supported[0]["evidence_id"] if supported else None)
        _create_claim(db, document, evidence, f"I can discuss transferable evidence in relation to these confirmed requirements: {requirement_summary}" if job_label else "I can contribute with transferable design, AI-literacy, and evaluation evidence.", "transferable_evidence", supported[0]["evidence_id"] if supported else None)
        _create_claim(db, document, evidence, "I have deep company-specific knowledge of your internal roadmap.", "fabricated_company_knowledge")
    db.flush()
    calculate_document_readiness(db, document)
    create_document_version(db, document, "Initial job-specific document version.")
    db.commit()
    return document_public(db, document)


def document_public(db: Session, row: ApplicationDocument) -> dict[str, Any]:
    sections = db.scalars(select(DocumentSection).where(DocumentSection.document_id == row.id).order_by(DocumentSection.order_index)).all()
    claims = db.scalars(select(DocumentClaim).where(DocumentClaim.document_id == row.id).order_by(DocumentClaim.created_at)).all()
    versions = db.scalars(select(ApplicationDocumentVersion).where(ApplicationDocumentVersion.document_id == row.id).order_by(ApplicationDocumentVersion.version_number.desc())).all()
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "job_analysis_id": row.job_analysis_id,
        "job_application_id": row.job_application_id,
        "document_type": row.document_type,
        "title": row.title,
        "language": row.language,
        "variant": row.variant,
        "status": row.status,
        "evidence_lock_status": row.evidence_lock_status,
        "readiness_status": row.readiness_status,
        "source_profile_version": row.source_profile_version,
        "source_job_analysis_version": row.source_job_analysis_version,
        "source_evidence_version": row.source_evidence_version,
        "user_edited_at": row.user_edited_at.isoformat() if row.user_edited_at else None,
        "export_warning_acknowledged": row.export_warning_acknowledged,
        "sections": [section_public(item) for item in sections],
        "claims": [claim_public(db, item) for item in claims],
        "versions": [{"id": item.id, "version_number": item.version_number, "warnings": item.warnings_json or [], "version_kind": item.version_kind, "source_profile_version": item.source_profile_version, "source_job_analysis_version": item.source_job_analysis_version, "source_evidence_version": item.source_evidence_version, "evidence_lock_state": item.evidence_lock_state, "edited_by_user": item.edited_by_user, "created_at": item.created_at.isoformat()} for item in versions],
        "source_metadata": row.source_metadata_json or {},
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def section_public(row: DocumentSection) -> dict[str, Any]:
    return {
        "id": row.id,
        "section_type": row.section_type,
        "title": row.title,
        "content": row.content,
        "include_in_export": row.include_in_export,
        "order_index": row.order_index,
    }


def claim_public(db: Session, row: DocumentClaim) -> dict[str, Any]:
    links = db.scalars(select(DocumentClaimEvidenceLink).where(DocumentClaimEvidenceLink.claim_id == row.id)).all()
    return {
        "id": row.id,
        "document_id": row.document_id,
        "section_id": row.section_id,
        "claim_text": row.claim_text,
        "claim_type": row.claim_type,
        "status": row.status,
        "safer_alternative": row.safer_alternative,
        "deterministic_reason": row.deterministic_reason,
        "user_confirmation_state": row.user_confirmation_state,
        "blocked_for_export": row.blocked_for_export,
        "support_state": row.support_state,
        "generated_by": row.generated_by,
        "edited_by_user": row.edited_by_user,
        "version": row.claim_version,
        "timestamp": row.updated_at.isoformat(),
        "evidence_links": [
            {
                "id": link.id,
                "evidence_type": link.evidence_type,
                "evidence_id": link.evidence_id,
                "source_id": link.source_id,
                "relationship": link.relationship,
                "confidence": link.confidence,
            }
            for link in links
        ],
    }


def list_application_documents(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(ApplicationDocument).where(ApplicationDocument.profile_id == profile_id).order_by(ApplicationDocument.updated_at.desc())).all()
    return [document_public(db, row) for row in rows]


def get_document(db: Session, document_id: str, profile: Profile | None = None) -> ApplicationDocument:
    row = db.get(ApplicationDocument, document_id)
    if not row:
        raise LookupError("Application document not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Application document does not belong to this profile")
    return row


def create_document_version(db: Session, document: ApplicationDocument, reason: str = "Manual version save.") -> dict[str, Any]:
    existing_count = db.scalar(select(func.count()).select_from(ApplicationDocumentVersion).where(ApplicationDocumentVersion.document_id == document.id)) or 0
    snapshot = document_public(db, document)
    warnings = [claim["claim_text"] for claim in snapshot["claims"] if claim["blocked_for_export"] or claim["status"] in {"Blocked", "Unverified"}]
    user_edited = reason.lower().startswith(("manual", "user", "edited"))
    version = ApplicationDocumentVersion(document_id=document.id, profile_id=document.profile_id, version_number=existing_count + 1, snapshot_json={"reason": reason, "document": snapshot}, warnings_json=warnings, version_kind="user_edited" if user_edited else "generated", source_profile_version=document.source_profile_version, source_job_analysis_version=document.source_job_analysis_version, source_evidence_version=document.source_evidence_version, evidence_lock_state=document.evidence_lock_status, edited_by_user=user_edited)
    db.add(version)
    db.commit()
    return {"id": version.id, "version_number": version.version_number, "warnings": warnings, "created_at": version.created_at.isoformat()}


def add_document_claim(db: Session, document: ApplicationDocument, payload: dict[str, Any]) -> dict[str, Any]:
    section = db.get(DocumentSection, payload.get("section_id")) if payload.get("section_id") else None
    if section and section.document_id != document.id:
        raise ValueError("Section does not belong to this document.")
    claim = _create_claim(db, document, section, payload.get("claim_text") or "", payload.get("claim_type") or "manual", payload.get("evidence_id"))
    db.commit()
    calculate_document_readiness(db, document)
    return claim_public(db, claim)


def update_document_claim(db: Session, claim: DocumentClaim, payload: dict[str, Any]) -> dict[str, Any]:
    claim.edited_by_user = True
    claim.claim_version += 1
    if payload.get("claim_text") is not None:
        claim.claim_text = _clean_text(payload["claim_text"], 1200)
    if payload.get("safer_alternative") is not None:
        claim.safer_alternative = payload["safer_alternative"]
    requested_status = payload.get("status")
    if requested_status and requested_status not in CLAIM_STATUSES:
        raise ValueError("Unsupported Evidence Lock claim status.")
    if requested_status in {"Supported", "Partially supported", "Transferable"}:
        raise ValueError("Evidence Lock computes support from linked Evidence Passport records; link evidence instead of setting a support status.")
    requested_confirmation = payload.get("user_confirmation_state")
    if requested_confirmation and requested_confirmation not in {"needs_review", "confirmed"}:
        raise ValueError("Unsupported Evidence Lock confirmation state.")
    if requested_status == "User-confirmed":
        requested_confirmation = "confirmed"
    if requested_confirmation:
        claim.user_confirmation_state = requested_confirmation
    linked_count = db.scalar(select(func.count()).select_from(DocumentClaimEvidenceLink).where(DocumentClaimEvidenceLink.claim_id == claim.id)) or 0
    status, reason, safer, blocked = _claim_status_from_text(claim.claim_text, linked_count=linked_count, user_confirmed=claim.user_confirmation_state == "confirmed")
    claim.status = status
    claim.deterministic_reason = reason
    if safer:
        claim.safer_alternative = safer
    claim.blocked_for_export = blocked
    claim.support_state = _support_state(claim.claim_type, claim.status, claim.user_confirmation_state == "confirmed")
    claim.updated_at = _now()
    db.add(DocumentReviewEvent(document_id=claim.document_id, claim_id=claim.id, profile_id=claim.profile_id, event_type="claim_updated", event_json={"payload_keys": list(payload.keys())}))
    db.commit()
    document = db.get(ApplicationDocument, claim.document_id)
    if document:
        document.user_edited_at = _now()
        calculate_document_readiness(db, document)
    return claim_public(db, claim)


def confirm_document_claim(db: Session, claim: DocumentClaim) -> dict[str, Any]:
    claim.edited_by_user = True
    claim.claim_version += 1
    claim.user_confirmation_state = "confirmed"
    if claim.status == "Unverified":
        claim.status = "User-confirmed"
        claim.deterministic_reason = "The user explicitly confirmed the factual claim. It remains separate from stronger evidence."
    claim.blocked_for_export = claim.status == "Blocked"
    claim.support_state = _support_state(claim.claim_type, claim.status, True)
    db.add(DocumentReviewEvent(document_id=claim.document_id, claim_id=claim.id, profile_id=claim.profile_id, event_type="claim_confirmed", event_json={"status": claim.status}))
    db.commit()
    document = db.get(ApplicationDocument, claim.document_id)
    if document:
        calculate_document_readiness(db, document)
    return claim_public(db, claim)


def link_claim_evidence(db: Session, claim: DocumentClaim, payload: dict[str, Any]) -> dict[str, Any]:
    evidence_id = payload.get("evidence_id")
    evidence = db.get(SkillEvidence, evidence_id) if evidence_id else None
    if not evidence:
        raise LookupError("Evidence not found")
    inventory = db.get(SkillsInventory, evidence.skill_inventory_id)
    if not inventory or inventory.profile_id != claim.profile_id:
        raise PermissionError("Evidence does not belong to this profile")
    claim.edited_by_user = True
    claim.claim_version += 1
    link = DocumentClaimEvidenceLink(
        claim_id=claim.id,
        document_id=claim.document_id,
        profile_id=claim.profile_id,
        evidence_id=evidence.id,
        relationship=payload.get("relationship") or "supports",
        confidence=evidence.verification_status,
    )
    db.add(link)
    status, reason, safer, blocked = _claim_status_from_text(claim.claim_text, linked_count=1)
    claim.status = "Supported" if evidence.verification_status in {"demonstrated", "practically_verified", "supported"} else status
    claim.deterministic_reason = reason
    if safer:
        claim.safer_alternative = safer
    claim.blocked_for_export = blocked and claim.status == "Blocked"
    claim.support_state = _support_state(claim.claim_type, claim.status, claim.user_confirmation_state == "confirmed")
    db.add(DocumentReviewEvent(document_id=claim.document_id, claim_id=claim.id, profile_id=claim.profile_id, event_type="evidence_linked", event_json={"evidence_id": evidence.id}))
    db.commit()
    document = db.get(ApplicationDocument, claim.document_id)
    if document:
        calculate_document_readiness(db, document)
    return claim_public(db, claim)


def require_claim(db: Session, claim_id: str, profile: Profile | None = None) -> DocumentClaim:
    claim = db.get(DocumentClaim, claim_id)
    if not claim:
        raise LookupError("Document claim not found")
    if profile and claim.profile_id != profile.id:
        raise PermissionError("Document claim does not belong to this profile")
    return claim


def calculate_document_readiness(db: Session, document: ApplicationDocument) -> dict[str, Any]:
    claims = db.scalars(select(DocumentClaim).where(DocumentClaim.document_id == document.id)).all()
    blocked = [claim for claim in claims if claim.status == "Blocked" or claim.blocked_for_export or claim.support_state == "UNSUPPORTED"]
    unverified = [claim for claim in claims if claim.status == "Unverified" or claim.support_state == "NEEDS_REVIEW"]
    self_report = [claim for claim in claims if claim.support_state == "SELF_REPORT_ONLY"]
    motivational = [claim for claim in claims if claim.support_state == "MOTIVATIONAL"]
    if blocked:
        status = "Needs evidence"
        lock = "Blocked claims present"
    elif unverified:
        status = "Needs review"
        lock = "Unverified claims present"
    elif claims:
        status = "Ready for user submission"
        lock = "Evidence locked"
    else:
        status = "Draft"
        lock = "No claims reviewed"
    document.readiness_status = status
    document.evidence_lock_status = lock
    document.updated_at = _now()
    db.commit()
    return {"document_id": document.id, "readiness_status": status, "evidence_lock_status": lock, "blocked_claims": [claim_public(db, item) for item in blocked], "unverified_claims": [claim_public(db, item) for item in unverified], "self_report_claims": [claim_public(db, item) for item in self_report], "motivational_claims": [claim_public(db, item) for item in motivational], "factual_claims_reviewed": len(claims) - len(motivational), "unsupported_claims_risk": [claim_public(db, item) for item in blocked + unverified]}


def export_document(db: Session, document: ApplicationDocument, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    readiness = calculate_document_readiness(db, document)
    if (readiness["blocked_claims"] or readiness["unverified_claims"]) and not payload.get("confirm_blocked_claim_export"):
        raise ValueError("Unsupported or unreviewed claims require explicit warning acknowledgement before export.")
    if readiness["blocked_claims"] or readiness["unverified_claims"]:
        document.export_warning_acknowledged = True
    snapshot = document_public(db, document)
    html_sections = "".join(f"<section><h2>{html.escape(section['title'])}</h2><p>{html.escape(section['content'])}</p></section>" for section in snapshot["sections"] if section["include_in_export"])
    printable = f"<article class='application-document {document.document_type}'><h1>{html.escape(document.title)}</h1>{html_sections}</article>"
    db.commit()
    return {
        "document_id": document.id,
        "export_format": payload.get("export_format") or "html_json",
        "printable_html": printable,
        "structured_json": snapshot,
        "pdf_available": False,
        "warnings": readiness["blocked_claims"],
        "ats_guarantee": False,
        "auto_apply": False,
    }


def save_job_for_profile(db: Session, profile: Profile, job: JobPosting) -> dict[str, Any]:
    if not job.is_active:
        raise ValueError("Inactive or expired job postings cannot be saved as active opportunities.")
    existing = db.scalar(select(JobApplication).where(JobApplication.profile_id == profile.id, JobApplication.job_id == job.id).order_by(JobApplication.updated_at.desc()))
    if existing:
        return application_public(db, existing)
    app = JobApplication(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_id=job.id,
        title=job.title,
        organisation=job.employer,
        source=job.provider,
        deadline=_date(job.expiry_time),
        status="Saved",
        next_action="Run Job Analyzer before preparing application documents.",
        demo_marker=_demo_marker(profile) or job.demo_marker,
    )
    db.add(app)
    db.flush()
    db.add(JobApplicationEvent(application_id=app.id, profile_id=profile.id, event_type="saved_job", to_status="Saved", description="Job saved by user. No application was submitted."))
    db.commit()
    return application_public(db, app)


def create_application(db: Session, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    analysis = require_analysis(db, payload["job_analysis_id"], profile) if payload.get("job_analysis_id") else None
    if analysis and not analysis.user_confirmed:
        raise ValueError("Confirm the job requirements before creating an application tracker record linked to this analysis.")
    job = db.get(JobPosting, payload.get("job_id")) if payload.get("job_id") else (db.get(JobPosting, analysis.job_id) if analysis and analysis.job_id else None)
    career_match = db.get(CareerMatch, payload.get("career_match_id")) if payload.get("career_match_id") else None
    if payload.get("career_match_id") and (not career_match or career_match.profile_id != profile.id):
        raise PermissionError("Career hypothesis match does not belong to this profile")
    status = _application_status(payload.get("status"), "Preparing")
    if status not in APPLICATION_STATUSES:
        raise ValueError("Unsupported application status")
    for document_key in ("cv_document_id", "cover_letter_document_id"):
        if payload.get(document_key):
            document = get_document(db, payload[document_key], profile)
            if analysis and document.job_analysis_id not in {None, analysis.id}:
                raise ValueError("Application document is linked to a different job analysis.")
    readiness_snapshot = calculate_job_readiness(db, analysis) if analysis else {}
    evidence_snapshot = evidence_passport(db, profile.id)
    # Saving a market job creates the canonical tracker record first.  Creating
    # its analysed application later must enrich that record rather than create
    # a second application for the same persisted job identity.
    existing = (
        db.scalar(
            select(JobApplication)
            .where(JobApplication.profile_id == profile.id, JobApplication.job_id == job.id)
            .order_by(JobApplication.updated_at.desc(), JobApplication.created_at.desc())
        )
        if job
        else None
    )
    if existing:
        before_status = existing.status
        changed = False
        if analysis and existing.job_analysis_id != analysis.id:
            existing.job_analysis_id = analysis.id
            existing.confirmed_job_analysis_version = analysis.extraction_version
            existing.readiness_snapshot_json = readiness_snapshot
            existing.evidence_snapshot_json = evidence_snapshot
            changed = True
        for document_key in ("cv_document_id", "cover_letter_document_id"):
            if payload.get(document_key) and not getattr(existing, document_key):
                setattr(existing, document_key, payload[document_key])
                changed = True
        # The explicit conversion from a saved opportunity to an application
        # tracker record may advance the initial placeholder status.  Later
        # user-controlled statuses and notes are never overwritten by retries.
        if existing.status == "Saved" and status != "Saved":
            existing.status = status
            changed = True
        if payload.get("notes") and not existing.notes:
            existing.notes = payload["notes"]
            changed = True
        if payload.get("next_action") and not existing.next_action:
            existing.next_action = payload["next_action"]
            changed = True
        if changed:
            existing.updated_at = _now()
            db.add(
                JobApplicationEvent(
                    application_id=existing.id,
                    profile_id=profile.id,
                    event_type="linked_job_analysis",
                    from_status=before_status,
                    to_status=existing.status,
                    description="Existing application tracker record linked to the user-confirmed Job Analyzer result. User-entered application data was preserved.",
                )
            )
            db.commit()
        return application_public(db, existing)
    app = JobApplication(
        profile_id=profile.id,
        user_id=profile.user_id,
        job_id=job.id if job else None,
        job_analysis_id=analysis.id if analysis else None,
        career_match_id=payload.get("career_match_id"),
        cv_document_id=payload.get("cv_document_id"),
        cover_letter_document_id=payload.get("cover_letter_document_id"),
        title=payload.get("title") or (analysis.title if analysis else job.title if job else "Manual application"),
        organisation=payload.get("organisation") or (analysis.organisation if analysis else job.employer if job else ""),
        source=payload.get("source") or (job.provider if job else "manual"),
        application_date=payload.get("application_date"),
        deadline=payload.get("deadline") or (_date(job.expiry_time) if job else None),
        status=status,
        contacts_json=payload.get("contacts") or [],
        notes=payload.get("notes") or "",
        next_action=payload.get("next_action") or "Complete readiness review before user submission.",
        confirmed_job_analysis_version=(analysis.extraction_version if analysis else ""),
        readiness_snapshot_json=readiness_snapshot,
        evidence_snapshot_json=evidence_snapshot,
        demo_marker=_demo_marker(profile) or bool(job and job.demo_marker),
    )
    db.add(app)
    db.flush()
    db.add(JobApplicationEvent(application_id=app.id, profile_id=profile.id, event_type="created", to_status=status, description="Application tracker record created. The platform did not submit an application."))
    db.commit()
    return application_public(db, app)


def require_application(db: Session, application_id: str, profile: Profile | None = None) -> JobApplication:
    app = db.get(JobApplication, application_id)
    if not app:
        raise LookupError("Application not found")
    if profile and app.profile_id != profile.id:
        raise PermissionError("Application does not belong to this profile")
    return app


def update_application(db: Session, app: JobApplication, payload: dict[str, Any]) -> dict[str, Any]:
    before = app.status
    if payload.get("status"):
        payload_status = _application_status(payload["status"])
        if payload_status not in APPLICATION_STATUSES:
            raise ValueError("Unsupported application status")
        app.status = payload_status
    if payload.get("notes") is not None:
        app.notes = payload["notes"]
    if payload.get("next_action") is not None:
        app.next_action = payload["next_action"]
    if payload.get("application_date") is not None:
        app.application_date = payload["application_date"]
    if payload.get("contacts") is not None:
        app.contacts_json = payload["contacts"]
    app.updated_at = _now()
    if before != app.status:
        db.add(JobApplicationEvent(application_id=app.id, profile_id=app.profile_id, event_type="status_change", from_status=before, to_status=app.status, description=payload.get("description") or "Status updated by user."))
    db.commit()
    return application_public(db, app)


def add_application_event(db: Session, app: JobApplication, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    event = JobApplicationEvent(
        application_id=app.id,
        profile_id=app.profile_id,
        event_type=payload.get("event_type") or "note",
        from_status=payload.get("from_status") or "",
        to_status=payload.get("to_status") or app.status,
        description=payload.get("description") or "",
        event_metadata_json=payload.get("metadata") or {},
        created_by=user_id,
    )
    db.add(event)
    db.commit()
    return application_event_public(event)


def add_application_stage(db: Session, app: JobApplication, payload: dict[str, Any]) -> dict[str, Any]:
    stage = ApplicationStageRecord(
        application_id=app.id,
        profile_id=app.profile_id,
        stage_type=payload.get("stage_type") or "recruiter",
        scheduled_date=payload.get("scheduled_date"),
        preparation_notes=payload.get("preparation_notes") or "",
        probable_questions_json=payload.get("probable_questions") or _stage_questions(payload.get("stage_type") or "recruiter"),
        selected_evidence_json=payload.get("selected_evidence") or [],
        user_reflection=payload.get("user_reflection") or "",
        result=payload.get("result") or "",
        feedback=payload.get("feedback") or "",
    )
    db.add(stage)
    previous = app.status
    if payload.get("application_status"):
        next_status = _application_status(payload["application_status"])
        if next_status not in APPLICATION_STATUSES:
            raise ValueError("Unsupported application status")
        app.status = next_status
    db.flush()
    db.add(JobApplicationEvent(application_id=app.id, profile_id=app.profile_id, event_type="stage_added", from_status=previous, to_status=app.status, description=f"Stage recorded: {stage.stage_type}. Application status changes only when explicitly selected."))
    db.commit()
    return stage_public(stage)


def _status_for_stage(stage_type: str) -> str:
    mapping = {
        "recruiter": "Recruiter screening",
        "hiring_manager": "Interview 1",
        "technical": "Technical or case stage",
        "case": "Technical or case stage",
        "portfolio": "Portfolio stage",
        "final": "Final interview",
        "negotiation": "Offer",
    }
    return mapping.get(stage_type, "Recruiter screening")


def _stage_questions(stage_type: str) -> list[str]:
    return [
        "Which evidence proves the most relevant requirement?",
        "What uncertainty should be stated honestly?",
        f"What would a {stage_type} interviewer need to verify?",
    ]


def record_application_outcome(db: Session, app: JobApplication, payload: dict[str, Any]) -> dict[str, Any]:
    outcome = ApplicationOutcome(
        application_id=app.id,
        profile_id=app.profile_id,
        outcome=payload.get("outcome") or "Unknown",
        outcome_date=payload.get("outcome_date"),
        employer_feedback=payload.get("employer_feedback") or "",
        feedback_confirmed=bool(payload.get("feedback_confirmed", False)),
        user_interpretation=payload.get("user_interpretation") or "",
        ai_interpretation=payload.get("ai_interpretation") or "",
        observed_data_json={
            "status_before": app.status,
            "stages_reached": [stage.stage_type for stage in db.scalars(select(ApplicationStageRecord).where(ApplicationStageRecord.application_id == app.id)).all()],
        },
    )
    db.add(outcome)
    previous = app.status
    outcome_status = _application_status(outcome.outcome, outcome.outcome)
    if outcome_status in APPLICATION_STATUSES:
        app.status = outcome_status
    elif outcome.outcome.lower() == "rejected":
        app.status = "Rejected"
    elif outcome.outcome.lower() == "offer":
        app.status = "Offer"
    db.flush()
    db.add(JobApplicationEvent(application_id=app.id, profile_id=app.profile_id, event_type="outcome_recorded", from_status=previous, to_status=app.status, description=f"Outcome recorded: {outcome.outcome}."))
    db.commit()
    return outcome_public(outcome)


def recalibrate_from_application(db: Session, app: JobApplication) -> dict[str, Any]:
    applications = db.scalars(select(JobApplication).where(JobApplication.profile_id == app.profile_id)).all()
    outcomes = db.scalars(select(ApplicationOutcome).where(ApplicationOutcome.profile_id == app.profile_id)).all()
    response_count = sum(1 for item in applications if item.status in {"Recruiter screening", "Interview 1", "Interview 2", "Technical or case stage", "Offer"})
    suggestions = [
        {
            "suggestion_type": "strengthen_evidence",
            "label": "Strengthen missing evidence before the next application.",
            "requires_user_confirmation": True,
        },
        {
            "suggestion_type": "revise_positioning",
            "label": "Review CV positioning for roles that produced recruiter responses in the recorded sample.",
            "requires_user_confirmation": True,
        },
    ]
    if response_count:
        suggestions.insert(0, {"suggestion_type": "target_role_signal", "label": "Applications reaching recruiter stages may indicate better positioning in the recorded sample.", "requires_user_confirmation": True})
    run = ApplicationRecalibrationRun(
        application_id=app.id,
        profile_id=app.profile_id,
        status="suggested",
        observed_data_json={"applications_recorded": len(applications), "outcomes_recorded": len(outcomes), "recruiter_or_later_count": response_count},
        user_interpretation_json={"note": "User interpretation remains separate from observed data."},
        ai_interpretation_json={"note": "No causal hiring claims are made."},
        suggestions_json=suggestions,
        roadmap_changes_require_confirmation=True,
        demo_marker=app.demo_marker,
    )
    db.add(run)
    db.commit()
    return recalibration_public(run)


def application_event_public(row: JobApplicationEvent) -> dict[str, Any]:
    return {
        "id": row.id,
        "event_type": row.event_type,
        "from_status": row.from_status,
        "to_status": row.to_status,
        "description": row.description,
        "metadata": row.event_metadata_json or {},
        "created_at": row.created_at.isoformat(),
    }


def stage_public(row: ApplicationStageRecord) -> dict[str, Any]:
    return {
        "id": row.id,
        "stage_type": row.stage_type,
        "scheduled_date": row.scheduled_date,
        "preparation_notes": row.preparation_notes,
        "probable_questions": row.probable_questions_json or [],
        "selected_evidence": row.selected_evidence_json or [],
        "user_reflection": row.user_reflection,
        "result": row.result,
        "feedback": row.feedback,
        "created_at": row.created_at.isoformat(),
    }


def outcome_public(row: ApplicationOutcome) -> dict[str, Any]:
    return {
        "id": row.id,
        "application_id": row.application_id,
        "outcome": row.outcome,
        "outcome_date": row.outcome_date,
        "employer_feedback": row.employer_feedback if row.feedback_confirmed else "",
        "feedback_confirmed": row.feedback_confirmed,
        "user_interpretation": row.user_interpretation,
        "ai_interpretation": row.ai_interpretation,
        "observed_data": row.observed_data_json or {},
        "created_at": row.created_at.isoformat(),
    }


def recalibration_public(row: ApplicationRecalibrationRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "application_id": row.application_id,
        "interview_id": getattr(row, "interview_id", None),
        "status": row.status,
        "observed_data": row.observed_data_json or {},
        "user_interpretation": row.user_interpretation_json or {},
        "ai_interpretation": row.ai_interpretation_json or {},
        "suggestions": row.suggestions_json or [],
        "roadmap_changes_require_confirmation": row.roadmap_changes_require_confirmation,
        "accepted_by_user": row.accepted_by_user,
        "user_decision": getattr(row, "user_decision", "PENDING"),
        "before": getattr(row, "before_state_json", {}) or {},
        "after": getattr(row, "after_state_json", {}) or {},
        "source": getattr(row, "source_label", "Application recalibration"),
        "limitation": getattr(row, "limitation", "One recorded outcome is limited evidence and does not determine career fit."),
        "version": row.version,
        "created_at": row.created_at.isoformat(),
    }


def application_public(db: Session, row: JobApplication) -> dict[str, Any]:
    events = db.scalars(select(JobApplicationEvent).where(JobApplicationEvent.application_id == row.id).order_by(JobApplicationEvent.created_at)).all()
    stages = db.scalars(select(ApplicationStageRecord).where(ApplicationStageRecord.application_id == row.id).order_by(ApplicationStageRecord.created_at)).all()
    outcome = db.scalar(select(ApplicationOutcome).where(ApplicationOutcome.application_id == row.id).order_by(ApplicationOutcome.created_at.desc()))
    recalibration = db.scalar(select(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.application_id == row.id).order_by(ApplicationRecalibrationRun.created_at.desc()))
    job = db.get(JobPosting, row.job_id) if row.job_id else None
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "job_id": row.job_id,
        "job_analysis_id": row.job_analysis_id,
        "career_match_id": row.career_match_id,
        "cv_document_id": row.cv_document_id,
        "cover_letter_document_id": row.cover_letter_document_id,
        "title": row.title,
        "organisation": row.organisation,
        "source": row.source,
        "application_date": row.application_date,
        "deadline": row.deadline,
        "status": row.status,
        "contacts": row.contacts_json or [],
        "notes": row.notes,
        "next_action": row.next_action,
        "confirmed_job_analysis_version": row.confirmed_job_analysis_version,
        "readiness_snapshot": row.readiness_snapshot_json or {},
        "evidence_snapshot": row.evidence_snapshot_json or {},
        "application_stage": row.status,
        "stage_options": ["DRAFT", "READY", "APPLIED", "SCREENING", "INTERVIEW", "FINAL", "OFFER", "REJECTED", "WITHDRAWN", "ARCHIVED"],
        "roadmap_action_id": row.roadmap_action_id,
        "auto_submitted": False,
        "events": [application_event_public(item) for item in events],
        "stages": [stage_public(item) for item in stages],
        "outcome": outcome_public(outcome) if outcome else None,
        "recalibration": recalibration_public(recalibration) if recalibration else None,
        "job": job_public(db, job) if job else None,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_applications(db: Session, profile_id: str) -> list[dict[str, Any]]:
    rows = db.scalars(select(JobApplication).where(JobApplication.profile_id == profile_id).order_by(JobApplication.updated_at.desc())).all()
    return [application_public(db, row) for row in rows]


def _research_questions() -> list[dict[str, Any]]:
    constructs = [
        ("career_decision_clarity", "I understand which career direction I should test next."),
        ("perceived_control", "I feel in control of my career decision process."),
        ("recommendation_usefulness", "The recommendations feel useful for my situation."),
        ("actionability", "I can identify concrete next actions."),
        ("strength_understanding", "I understand which strengths are supported by evidence."),
        ("skill_gap_understanding", "I understand which skill gaps need evidence."),
        ("confidence_calibration", "My confidence feels appropriately calibrated to the evidence."),
        ("trust_uncertainty", "The system communicates uncertainty in a trustworthy way."),
        ("perceived_workload", "The workflow workload feels manageable."),
        ("intention_to_act", "I intend to take a concrete action after this workflow."),
    ]
    questions = []
    for index, (construct, prompt) in enumerate(constructs, 1):
        questions.append({"id": f"rq-{construct}", "construct": construct, "prompt": prompt, "instrument_type": "custom_likert", "order_index": index})
    sus_prompts = [
        "I think that I would like to use this system frequently.",
        "I found the system unnecessarily complex.",
        "I thought the system was easy to use.",
        "I found the various functions in this system were well integrated.",
    ]
    for index, prompt in enumerate(sus_prompts, 1):
        questions.append({"id": f"sus-{index}", "construct": "sus", "prompt": prompt, "instrument_type": "sus", "order_index": 100 + index})
    return questions


def ensure_research_study(db: Session, demo: bool = False) -> dict[str, Any]:
    study_id = "organicai-market-journey-demo-study" if demo else None
    row = db.get(ResearchStudy, study_id) if study_id else db.scalar(select(ResearchStudy).where(ResearchStudy.demo_marker.is_(False)).order_by(ResearchStudy.created_at.desc()))
    if not row:
        row = ResearchStudy(
            id=study_id,
            title="OrganicAI Market-Aware Career Guidance Evaluation",
            study_mode="experimental",
            status="draft",
            research_question="Does integrating labour-market evidence, practical skill evidence, and application-outcome feedback produce more actionable and better-calibrated career guidance than assessment-based recommendations alone?",
            contribution_statement="The extended OrganicAI Compass platform connects evidence-based career experimentation with local labour-market intelligence, job-specific evidence mapping, evidence-locked application documents, employment outcome tracking, and iterative recommendation recalibration. The system is designed to support transparent and user-controlled career decisions rather than automate hiring or predict employment outcomes.",
            demo_marker=demo,
        )
        db.add(row)
        db.flush()
        db.add(ResearchStudyVersion(study_id=row.id, version_number=1, protocol_json=research_protocol()))
        for item in _research_questions():
            db.add(ResearchQuestion(study_id=row.id, scale_min=1, scale_max=5, scale_label="1 strongly disagree to 5 strongly agree", question_version="research-question-v1", active=True, **item))
        db.commit()
    return research_study_public(db, row)


def research_protocol() -> dict[str, Any]:
    return {
        "study_modes": ["baseline", "experimental", "crossover", "usability-only"],
        "baseline_workflow": ["Assessment", "Career recommendation", "Learning resources"],
        "experimental_workflow": ["Assessment", "Career hypothesis", "Career experiment", "Evidence Passport", "Market analysis", "Application preparation", "Recalibration"],
        "random_assignment_enabled": False,
        "no_empirical_results_claimed": True,
        "consent_version": RESEARCH_CONSENT_VERSION,
    }


def research_study_public(db: Session, row: ResearchStudy) -> dict[str, Any]:
    questions = db.scalars(select(ResearchQuestion).where(ResearchQuestion.study_id == row.id, ResearchQuestion.active.is_(True)).order_by(ResearchQuestion.order_index)).all()
    return {
        "id": row.id,
        "title": row.title,
        "study_mode": row.study_mode,
        "status": row.status,
        "research_question": row.research_question,
        "contribution_statement": row.contribution_statement,
        "consent_version": row.consent_version,
        "random_assignment_enabled": row.random_assignment_enabled,
        "protocol": research_protocol(),
        "questions": [research_question_public(item) for item in questions],
        "demo_marker": row.demo_marker,
        "created_at": row.created_at.isoformat(),
    }


def research_question_public(row: ResearchQuestion) -> dict[str, Any]:
    return {
        "id": row.id,
        "construct": row.construct,
        "prompt": row.prompt,
        "scale_min": row.scale_min,
        "scale_max": row.scale_max,
        "scale_label": row.scale_label,
        "instrument_type": row.instrument_type,
        "question_version": row.question_version,
    }


def list_research_studies(db: Session) -> list[dict[str, Any]]:
    ensure_research_study(db, demo=True)
    rows = db.scalars(select(ResearchStudy).order_by(ResearchStudy.created_at.desc())).all()
    return [research_study_public(db, row) for row in rows]


def consent_to_research(db: Session, study: ResearchStudy, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("consent_given"):
        raise ValueError("Research consent must be explicit before data collection.")
    if study.demo_marker != _demo_marker(profile) and _demo_marker(profile):
        raise ValueError("Demo data must not be mixed into non-demo research studies.")
    participant = db.scalar(select(ResearchParticipant).where(ResearchParticipant.study_id == study.id, ResearchParticipant.profile_id == profile.id).order_by(ResearchParticipant.created_at.desc()))
    if not participant:
        pseudo = hashlib.sha256(f"{study.id}:{profile.id}:{profile.user_id}".encode("utf-8")).hexdigest()[:18]
        participant = ResearchParticipant(study_id=study.id, profile_id=profile.id, user_id=profile.user_id, pseudonymous_id=f"p-{pseudo}", demo_marker=_demo_marker(profile))
        db.add(participant)
        db.flush()
    consent = ResearchConsent(
        study_id=study.id,
        participant_id=participant.id,
        profile_id=profile.id,
        consent_version=payload.get("consent_version") or study.consent_version,
        consent_given=True,
        consent_text_snapshot_json=research_consent_template(),
    )
    db.add(consent)
    db.commit()
    consent_payload = consent_public(consent)
    return {"participant": participant_public(participant), "consent": consent_payload, **consent_payload}


def withdraw_research_consent(db: Session, study: ResearchStudy, profile: Profile) -> dict[str, Any]:
    participant = db.scalar(select(ResearchParticipant).where(ResearchParticipant.study_id == study.id, ResearchParticipant.profile_id == profile.id).order_by(ResearchParticipant.created_at.desc()))
    if not participant:
        raise LookupError("Research participant not found")
    consents = db.scalars(select(ResearchConsent).where(ResearchConsent.participant_id == participant.id, ResearchConsent.withdrawn_at.is_(None))).all()
    for consent in consents:
        consent.withdrawn_at = _now()
    participant.status = "withdrawn"
    db.commit()
    return {"participant": participant_public(participant), "withdrawn": True}


def research_consent_template() -> dict[str, Any]:
    return {
        "study_purpose": "Evaluate the OrganicAI career guidance workflow for a master's thesis.",
        "researcher_identity": "Researcher placeholder to be completed before live study.",
        "data_collected": ["survey ratings", "workflow completion metrics", "evidence-count changes", "application outcome categories"],
        "data_not_collected": ["national identity numbers", "medical information", "exact home addresses", "bank information", "benefit case numbers", "raw legal documents"],
        "storage_duration": "Duration placeholder to be completed before live study.",
        "withdrawal_process": "Participant may withdraw consent and be excluded from export.",
        "anonymisation": "Exports use pseudonymous participant IDs and exclude names, email, raw CV text, and personal URLs by default.",
        "contact": "Contact placeholder.",
        "consent_version": RESEARCH_CONSENT_VERSION,
    }


def participant_public(row: ResearchParticipant) -> dict[str, Any]:
    return {"id": row.id, "study_id": row.study_id, "profile_id": row.profile_id, "pseudonymous_id": row.pseudonymous_id, "status": row.status, "demo_marker": row.demo_marker}


def consent_public(row: ResearchConsent) -> dict[str, Any]:
    return {"id": row.id, "consent_version": row.consent_version, "consent_given": row.consent_given, "withdrawn_at": row.withdrawn_at.isoformat() if row.withdrawn_at else None, "created_at": row.created_at.isoformat()}


def _active_consent(db: Session, study_id: str, profile_id: str) -> tuple[ResearchParticipant, ResearchConsent]:
    participant = db.scalar(select(ResearchParticipant).where(ResearchParticipant.study_id == study_id, ResearchParticipant.profile_id == profile_id, ResearchParticipant.status == "active").order_by(ResearchParticipant.created_at.desc()))
    if not participant:
        raise ValueError("Research consent is required before creating a research session.")
    consent = db.scalar(select(ResearchConsent).where(ResearchConsent.participant_id == participant.id, ResearchConsent.consent_given.is_(True), ResearchConsent.withdrawn_at.is_(None)).order_by(ResearchConsent.created_at.desc()))
    if not consent:
        raise ValueError("Active research consent is required before data collection.")
    return participant, consent


def create_research_session(db: Session, study: ResearchStudy, profile: Profile, payload: dict[str, Any]) -> dict[str, Any]:
    participant, _ = _active_consent(db, study.id, profile.id)
    workflow_stage = payload.get("workflow_stage") or "pre_test"
    session = ResearchSession(study_id=study.id, participant_id=participant.id, profile_id=profile.id, workflow_stage=workflow_stage, demo_marker=_demo_marker(profile))
    db.add(session)
    db.add(ResearchAssignment(study_id=study.id, participant_id=participant.id, assignment_type="manual", workflow=payload.get("workflow") or study.study_mode))
    db.commit()
    return research_session_public(db, session)


def record_research_responses(db: Session, session: ResearchSession, payload: dict[str, Any]) -> dict[str, Any]:
    participant = db.get(ResearchParticipant, session.participant_id)
    if not participant or participant.status != "active":
        raise ValueError("Active participant consent is required before recording responses.")
    _active_consent(db, session.study_id, session.profile_id)
    for item in payload.get("responses", []):
        question = db.get(ResearchQuestion, item.get("question_id"))
        if not question or question.study_id != session.study_id:
            raise LookupError("Research question not found for this study")
        db.add(
            ResearchResponse(
                session_id=session.id,
                study_id=session.study_id,
                participant_id=session.participant_id,
                profile_id=session.profile_id,
                question_id=question.id,
                workflow_stage=payload.get("workflow_stage") or session.workflow_stage,
                numeric_response=item.get("numeric_response"),
                text_response_redacted=_clean_text(item.get("text_response") or "", 500),
                response_metadata_json={"raw_text_stored": False},
                question_version=question.question_version,
            )
        )
    if payload.get("complete_session"):
        session.status = "completed"
        session.completed_at = _now()
    db.commit()
    return research_session_public(db, session)


def record_research_metrics(db: Session, session: ResearchSession, payload: dict[str, Any]) -> dict[str, Any]:
    _active_consent(db, session.study_id, session.profile_id)
    metrics = []
    for item in payload.get("metrics", []):
        metric = ResearchInteractionMetric(
            session_id=session.id,
            study_id=session.study_id,
            participant_id=session.participant_id,
            profile_id=session.profile_id,
            metric_name=item.get("metric_name") or "workflow_completion",
            metric_value=float(item.get("metric_value", 1)),
            workflow_stage=item.get("workflow_stage") or session.workflow_stage,
            metadata_json={key: value for key, value in (item.get("metadata") or {}).items() if "text" not in key.lower()},
            raw_text_excluded=True,
        )
        db.add(metric)
        metrics.append(metric)
    db.commit()
    return {"session_id": session.id, "metrics": [metric_public(item) for item in metrics]}


def research_session_public(db: Session, row: ResearchSession) -> dict[str, Any]:
    responses = db.scalars(select(ResearchResponse).where(ResearchResponse.session_id == row.id).order_by(ResearchResponse.created_at)).all()
    metrics = db.scalars(select(ResearchInteractionMetric).where(ResearchInteractionMetric.session_id == row.id).order_by(ResearchInteractionMetric.created_at)).all()
    return {
        "id": row.id,
        "study_id": row.study_id,
        "participant_id": row.participant_id,
        "profile_id": row.profile_id,
        "workflow_stage": row.workflow_stage,
        "status": row.status,
        "responses": [response_public(item) for item in responses],
        "metrics": [metric_public(item) for item in metrics],
        "started_at": row.started_at.isoformat(),
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
    }


def response_public(row: ResearchResponse) -> dict[str, Any]:
    return {
        "id": row.id,
        "question_id": row.question_id,
        "workflow_stage": row.workflow_stage,
        "numeric_response": row.numeric_response,
        "text_response_redacted": row.text_response_redacted,
        "question_version": row.question_version,
        "created_at": row.created_at.isoformat(),
    }


def metric_public(row: ResearchInteractionMetric) -> dict[str, Any]:
    return {
        "id": row.id,
        "metric_name": row.metric_name,
        "metric_value": row.metric_value,
        "workflow_stage": row.workflow_stage,
        "metadata": row.metadata_json or {},
        "raw_text_excluded": row.raw_text_excluded,
    }


def require_research_session(db: Session, session_id: str, profile: Profile | None = None) -> ResearchSession:
    session = db.get(ResearchSession, session_id)
    if not session:
        raise LookupError("Research session not found")
    if profile and session.profile_id != profile.id:
        raise PermissionError("Research session does not belong to this profile")
    return session


def study_summary(db: Session, study: ResearchStudy) -> dict[str, Any]:
    participants = db.scalars(select(ResearchParticipant).where(ResearchParticipant.study_id == study.id, ResearchParticipant.status == "active")).all()
    sessions = db.scalars(select(ResearchSession).where(ResearchSession.study_id == study.id)).all()
    responses = db.scalars(select(ResearchResponse).where(ResearchResponse.study_id == study.id)).all()
    metrics = db.scalars(select(ResearchInteractionMetric).where(ResearchInteractionMetric.study_id == study.id)).all()
    return {
        "study": research_study_public(db, study),
        "participant_count": len(participants),
        "session_count": len(sessions),
        "response_count": len(responses),
        "metric_count": len(metrics),
        "no_empirical_claim": "This prototype stores evaluation data but does not claim the research question has been answered.",
    }


def create_research_export(db: Session, study: ResearchStudy, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    include_demo = bool(payload.get("include_demo", False))
    participants = db.scalars(select(ResearchParticipant).where(ResearchParticipant.study_id == study.id)).all()
    allowed_participants = [item for item in participants if item.status == "active" and (include_demo or not item.demo_marker)]
    participant_ids = [item.id for item in allowed_participants]
    responses = db.scalars(select(ResearchResponse).where(ResearchResponse.participant_id.in_(participant_ids))).all() if participant_ids else []
    metrics = db.scalars(select(ResearchInteractionMetric).where(ResearchInteractionMetric.participant_id.in_(participant_ids))).all() if participant_ids else []
    applications = db.scalars(select(JobApplication).where(JobApplication.profile_id.in_([item.profile_id for item in allowed_participants]))).all() if allowed_participants else []
    payload_json = {
        "schema_version": RESEARCH_EXPORT_VERSION,
        "study_version": "research-study-v1",
        "export_timestamp": _now().isoformat(),
        "participant_summary": [
            {"pseudonymous_id": item.pseudonymous_id, "status": item.status, "demo_marker": item.demo_marker}
            for item in allowed_participants
        ],
        "survey_responses": [
            {"pseudonymous_id": next((p.pseudonymous_id for p in allowed_participants if p.id == item.participant_id), ""), "question_id": item.question_id, "workflow_stage": item.workflow_stage, "numeric_response": item.numeric_response, "question_version": item.question_version}
            for item in responses
        ],
        "workflow_metrics": [
            {"pseudonymous_id": next((p.pseudonymous_id for p in allowed_participants if p.id == item.participant_id), ""), "metric_name": item.metric_name, "metric_value": item.metric_value, "workflow_stage": item.workflow_stage}
            for item in metrics
        ],
        "application_outcomes": [
            {"profile_pseudonymous_ref": hashlib.sha256(item.profile_id.encode("utf-8")).hexdigest()[:12], "status": item.status, "source": item.source, "raw_notes_excluded": True}
            for item in applications
        ],
        "data_dictionary": research_data_dictionary(),
        "excluded_fields": ["names", "email_addresses", "raw_cv_text", "raw_cover_letter_text", "personal_urls", "national_identity_numbers"],
    }
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["pseudonymous_id", "question_id", "workflow_stage", "numeric_response", "question_version"])
    writer.writeheader()
    writer.writerows(payload_json["survey_responses"])
    run = ResearchExportRun(
        study_id=study.id,
        status="preview",
        export_format=payload.get("export_format") or "json_csv",
        schema_version=RESEARCH_EXPORT_VERSION,
        study_version="research-study-v1",
        preview_json={**payload_json, "csv_preview": csv_buffer.getvalue()},
        exclusions_json=payload_json["excluded_fields"],
        demo_records_excluded=not include_demo,
    )
    db.add(run)
    db.commit()
    return research_export_public(run)


def research_data_dictionary() -> list[dict[str, str]]:
    return [
        {"field": "pseudonymous_id", "description": "Participant identifier that does not contain name or email."},
        {"field": "question_id", "description": "Versioned survey question identifier."},
        {"field": "workflow_stage", "description": "pre_test, post_test, sus, or module stage."},
        {"field": "numeric_response", "description": "Likert response value."},
        {"field": "metric_name", "description": "Consented behavioural metric name without raw typed text."},
        {"field": "application_outcomes.status", "description": "Recorded tracker status, not a causal interpretation."},
    ]


def research_export_public(row: ResearchExportRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "study_id": row.study_id,
        "status": row.status,
        "export_format": row.export_format,
        "schema_version": row.schema_version,
        "study_version": row.study_version,
        "preview": row.preview_json or {},
        "exclusions": row.exclusions_json or [],
        "demo_records_excluded": row.demo_records_excluded,
        "generated_at": row.generated_at.isoformat(),
    }


def get_research_export(db: Session, export_id: str) -> dict[str, Any]:
    row = db.get(ResearchExportRun, export_id)
    if not row:
        raise LookupError("Research export not found")
    return research_export_public(row)


def require_study(db: Session, study_id: str) -> ResearchStudy:
    row = db.get(ResearchStudy, study_id)
    if not row:
        raise LookupError("Research study not found")
    return row


def seed_demo_market_application(db: Session, profile: Profile) -> None:
    sync_demo_labour_market(db)
    jobs = db.scalars(select(JobPosting).where(JobPosting.provider == "demo", JobPosting.is_active.is_(True)).order_by(JobPosting.publication_time.desc())).all()
    saved = [save_job_for_profile(db, profile, job) for job in jobs[:3]]
    if jobs:
        analysis = create_job_analysis(db, profile, {"job_id": jobs[0].id})
        analysis_row = db.get(JobAnalysis, analysis["id"])
        for requirement in db.scalars(select(JobRequirement).where(JobRequirement.analysis_id == analysis_row.id)).all():
            update_requirement(db, requirement, {"action": "accept"}, profile.user_id)
        confirm_job_analysis(db, analysis_row, profile.user_id)
        match_analysis_evidence(db, analysis_row)
        calculate_job_readiness(db, analysis_row)
        cv = create_application_document(db, profile, {"job_analysis_id": analysis_row.id, "document_type": "cv", "language": "en"})
        cover = create_application_document(db, profile, {"job_analysis_id": analysis_row.id, "document_type": "cover_letter", "language": "en"})
        app = create_application(db, profile, {"job_id": jobs[0].id, "job_analysis_id": analysis_row.id, "cv_document_id": cv["id"], "cover_letter_document_id": cover["id"], "status": "Preparing"})
        app_row = db.get(JobApplication, app["id"])
        add_application_stage(db, app_row, {"stage_type": "recruiter", "result": "advanced_to_screening", "feedback": "Fictional demo outcome only."})
        record_application_outcome(db, app_row, {"outcome": "Recruiter screening", "outcome_date": "2026-07-21", "feedback_confirmed": False, "user_interpretation": "Demo: response reached recruiter screening."})
        recalibrate_from_application(db, app_row)
    for job in jobs[1:3]:
        app = create_application(db, profile, {"job_id": job.id, "status": "Saved"})
        app_row = db.get(JobApplication, app["id"])
        if job == jobs[1]:
            record_application_outcome(db, app_row, {"outcome": "Rejected", "outcome_date": "2026-07-20", "feedback_confirmed": False, "user_interpretation": "No confirmed reason was provided."})
    study = ensure_research_study(db, demo=True)
    study_row = db.get(ResearchStudy, study["id"])
    consent_to_research(db, study_row, profile, {"consent_given": True})
    session = create_research_session(db, study_row, profile, {"workflow_stage": "post_test", "workflow": "experimental"})
    session_row = db.get(ResearchSession, session["id"])
    questions = db.scalars(select(ResearchQuestion).where(ResearchQuestion.study_id == study_row.id).order_by(ResearchQuestion.order_index)).all()
    record_research_responses(db, session_row, {"responses": [{"question_id": item.id, "numeric_response": 4 if item.instrument_type != "sus" else 3} for item in questions[:8]], "complete_session": True})
    record_research_metrics(db, session_row, {"metrics": [{"metric_name": "job_analysed", "metric_value": 1}, {"metric_name": "cv_draft_created", "metric_value": 1}, {"metric_name": "unsupported_claims_corrected", "metric_value": 1}]})


def delete_market_application_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids = [profile_id for profile_id in profile_ids if profile_id]
    if not ids:
        return
    document_ids = db.scalars(select(ApplicationDocument.id).where(ApplicationDocument.profile_id.in_(ids))).all()
    claim_ids = db.scalars(select(DocumentClaim.id).where(DocumentClaim.profile_id.in_(ids))).all()
    application_ids = db.scalars(select(JobApplication.id).where(JobApplication.profile_id.in_(ids))).all()
    analysis_ids = db.scalars(select(JobAnalysis.id).where(JobAnalysis.profile_id.in_(ids))).all()
    master_ids = db.scalars(select(MasterCareerProfile.id).where(MasterCareerProfile.profile_id.in_(ids))).all()
    participant_ids = db.scalars(select(ResearchParticipant.id).where(ResearchParticipant.profile_id.in_(ids))).all()
    session_ids = db.scalars(select(ResearchSession.id).where(ResearchSession.profile_id.in_(ids))).all()
    if claim_ids:
        db.execute(delete(DocumentClaimEvidenceLink).where(DocumentClaimEvidenceLink.claim_id.in_(claim_ids)))
        db.execute(delete(DocumentReviewEvent).where(DocumentReviewEvent.claim_id.in_(claim_ids)))
    if document_ids:
        db.execute(delete(ApplicationDocumentVersion).where(ApplicationDocumentVersion.document_id.in_(document_ids)))
        db.execute(delete(DocumentClaimEvidenceLink).where(DocumentClaimEvidenceLink.document_id.in_(document_ids)))
        db.execute(delete(DocumentReviewEvent).where(DocumentReviewEvent.document_id.in_(document_ids)))
        db.execute(delete(DocumentClaim).where(DocumentClaim.document_id.in_(document_ids)))
        db.execute(delete(DocumentSection).where(DocumentSection.document_id.in_(document_ids)))
    if application_ids:
        for model in [ApplicationOutcome, ApplicationFeedback, ApplicationStageRecord, ApplicationContact, JobApplicationEvent, ApplicationRecalibrationRun]:
            db.execute(delete(model).where(model.application_id.in_(application_ids)))
    db.execute(delete(ApplicationRecalibrationRun).where(ApplicationRecalibrationRun.profile_id.in_(ids)))
    if analysis_ids:
        db.execute(delete(JobRequirementEvidenceMatch).where(JobRequirementEvidenceMatch.analysis_id.in_(analysis_ids)))
        db.execute(delete(JobAnalysisCorrection).where(JobAnalysisCorrection.analysis_id.in_(analysis_ids)))
        db.execute(delete(JobAnalysisVersion).where(JobAnalysisVersion.analysis_id.in_(analysis_ids)))
        db.execute(delete(JobReadinessResult).where(JobReadinessResult.analysis_id.in_(analysis_ids)))
        db.execute(delete(JobRequirement).where(JobRequirement.analysis_id.in_(analysis_ids)))
    if master_ids:
        db.execute(delete(CareerProfileEntry).where(CareerProfileEntry.master_profile_id.in_(master_ids)))
    if session_ids:
        db.execute(delete(ResearchResponse).where(ResearchResponse.session_id.in_(session_ids)))
        db.execute(delete(ResearchInteractionMetric).where(ResearchInteractionMetric.session_id.in_(session_ids)))
    if participant_ids:
        db.execute(delete(ResearchConsent).where(ResearchConsent.participant_id.in_(participant_ids)))
        db.execute(delete(ResearchAssignment).where(ResearchAssignment.participant_id.in_(participant_ids)))
    for model in [JobApplication, ApplicationDocument, JobAnalysis, MasterCareerProfile, MarketRadarPreference, ResearchSession, ResearchParticipant]:
        db.execute(delete(model).where(model.profile_id.in_(ids)))
    db.commit()

