from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from app.config import Settings, get_settings
from app.services.email.validation import email_configuration_status
from app.services.production_rehearsal import rehearsal_evidence_check
from app.services.runtime_configuration import check_runtime_configuration, sanitized_report_dict
from app.services.secret_readiness import audit_secret_readiness


Status = Literal["PASSED", "PARTIAL", "BLOCKED", "NOT EXECUTED", "EXTERNAL MANUAL ACTION REQUIRED"]

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ReadinessCheck:
    id: str
    description: str
    status: Status
    required_for_deployment: bool
    required_for_operations: bool
    evidence: str
    rollback: str
    acceptance: str


def _read_json(path: Path) -> dict[str, Any] | None:
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
    return None


def _evidence_dir(path: str | Path | None) -> Path:
    return Path(path).resolve() if path else ROOT / "evidence" / "task13b05"


def _local_release_candidate_check(evidence_dir: Path) -> ReadinessCheck:
    summary = _read_json(evidence_dir / "final-test-summary.json")
    passed = bool(
        summary
        and summary.get("backend", {}).get("fullNonPostgres", {}).get("status") == "passed"
        and summary.get("postgresql", {}).get("markerSuite", {}).get("failed") == 0
        and summary.get("frontend", {}).get("build", {}).get("status") == "passed"
        and summary.get("e2e", {}).get("fullPlaywright", {}).get("failed") == 0
    )
    return ReadinessCheck(
        id="LOCAL-RC",
        description="Local release-candidate regression evidence",
        status="PASSED" if passed else "BLOCKED",
        required_for_deployment=True,
        required_for_operations=True,
        evidence=str(evidence_dir / "final-test-summary.json"),
        rollback="Revert the candidate build and rerun the local release gate.",
        acceptance="Backend, PostgreSQL, frontend, build and mock E2E evidence all pass with zero failed tests.",
    )


def _local_staging_check(evidence_dir: Path) -> ReadinessCheck:
    summary = _read_json(evidence_dir / "staging-service-summary.json")
    passed = bool(
        summary
        and summary.get("runtimeSmoke", {}).get("status") == "passed"
        and summary.get("observability", {}).get("status") == "passed"
    )
    return ReadinessCheck(
        id="LOCAL-STAGING",
        description="Local Docker staging health, readiness and observability",
        status="PASSED" if passed else "BLOCKED",
        required_for_deployment=True,
        required_for_operations=True,
        evidence=str(evidence_dir / "staging-service-summary.json"),
        rollback="Stop only the affected local staging service and restart from the last known working image.",
        acceptance="Health and readiness pass, PostgreSQL is reachable, migrations are current, and observability targets are up.",
    )


def _production_rehearsal_evidence_dir(evidence_dir: Path) -> Path:
    if evidence_dir.name == "task13c02":
        return evidence_dir
    sibling = evidence_dir.parent / "task13c02"
    if sibling.exists():
        return sibling
    return ROOT / "evidence" / "task13c02"


def _local_production_rehearsal_check(evidence_dir: Path) -> ReadinessCheck:
    rehearsal_dir = _production_rehearsal_evidence_dir(evidence_dir)
    check = rehearsal_evidence_check(rehearsal_dir / "final-summary.json")
    return ReadinessCheck(
        id="LOCAL-PROD-REHEARSAL",
        description="Local production deployment rehearsal, backup/restore and rollback evidence",
        status="PASSED" if check["status"] == "PASSED" else "BLOCKED",
        required_for_deployment=True,
        required_for_operations=True,
        evidence=str(rehearsal_dir / "final-summary.json"),
        rollback="Stop only organicai-prod-rehearsal services; preserve rehearsal volumes, backups and logs unless explicit cleanup is approved.",
        acceptance="Fresh PostgreSQL migration, readiness, reverse proxy smoke, synthetic acceptance, backup, disposable restore, rollback and recovery drills all pass without real providers or secret disclosure.",
    )


def _source_archive_check(evidence_dir: Path) -> ReadinessCheck:
    archive = _read_json(evidence_dir / "source-archive-audit-final.json")
    passed = bool(archive and archive.get("status") == "passed" and archive.get("blockedEntryCount") == 0)
    return ReadinessCheck(
        id="ARCHIVE",
        description="Sanitized source archive safety",
        status="PASSED" if passed else "BLOCKED",
        required_for_deployment=True,
        required_for_operations=False,
        evidence=str(evidence_dir / "source-archive-audit-final.json"),
        rollback="Discard the archive and regenerate it after exclusions are corrected.",
        acceptance="Archive audit reports blockedEntryCount=0 and includes only safe source, docs and review evidence.",
    )


def _external_check(
    check_id: str,
    description: str,
    passed: bool,
    *,
    required_for_operations: bool = False,
    evidence: str,
    rollback: str,
    acceptance: str,
) -> ReadinessCheck:
    return ReadinessCheck(
        id=check_id,
        description=description,
        status="PASSED" if passed else "EXTERNAL MANUAL ACTION REQUIRED",
        required_for_deployment=True,
        required_for_operations=required_for_operations,
        evidence=evidence,
        rollback=rollback,
        acceptance=acceptance,
    )


def _sanitized_secret_report(secret_report: dict[str, Any]) -> dict[str, Any]:
    """Keep go/no-go output limited to operational status, never fingerprints."""
    sanitized = dict(secret_report)
    items = []
    for item in secret_report.get("items", []):
        items.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "configured": item.get("configured"),
                "rotation_attested": item.get("rotation_attested"),
                "production_critical": item.get("production_critical"),
                "blocking": item.get("blocking"),
            }
        )
    sanitized["items"] = items
    sanitized["secretValuesIncluded"] = False
    sanitized["fingerprintsIncluded"] = False
    return sanitized


def production_go_no_go_report(evidence_dir: str | Path | None = None, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    evidence = _evidence_dir(evidence_dir)
    runtime_report = check_runtime_configuration(settings)
    secret_report = audit_secret_readiness(settings)
    email_status = email_configuration_status(settings)
    runtime_errors = [check for check in runtime_report.checks if check.status == "error"]
    production_environment_ready = settings.app_env == "production" and not runtime_errors
    secret_blocking = secret_report["blockingFindingCount"] > 0 or secret_report["rotationRequiredCount"] > 0 or secret_report["defaultSecretsRejected"]

    checks: list[ReadinessCheck] = [
        _local_release_candidate_check(evidence),
        _local_staging_check(evidence),
        _local_production_rehearsal_check(evidence),
        _source_archive_check(evidence),
        ReadinessCheck(
            id="ENV-CONTRACT",
            description="Production environment contract validation",
            status="PASSED" if production_environment_ready else "BLOCKED",
            required_for_deployment=True,
            required_for_operations=True,
            evidence="backend/app.scripts.validate_production_environment",
            rollback="Remove the candidate environment and restore the previous secret set/configuration.",
            acceptance="Runtime configuration has no production error checks.",
        ),
        ReadinessCheck(
            id="SECRET-ROTATION",
            description="Secret rotation and placeholder status",
            status="PASSED" if not secret_blocking else "EXTERNAL MANUAL ACTION REQUIRED",
            required_for_deployment=True,
            required_for_operations=True,
            evidence="backend/app.scripts.secret_rotation_status",
            rollback="Restore previous active secret version while revoking only the failed candidate version.",
            acceptance="No placeholders, no rotation-required items, and rotation evidence recorded without secret values.",
        ),
        ReadinessCheck(
            id="EMAIL",
            description="Production transactional email acceptance",
            status="PASSED" if settings.email_acceptance_test_passed and email_status.get("productionReady") else "EXTERNAL MANUAL ACTION REQUIRED",
            required_for_deployment=True,
            required_for_operations=True,
            evidence="reports/provider-validation/email-delivery-status.json",
            rollback="Disable production email driver or restore previous provider credentials.",
            acceptance="Controlled verification/reset/password notification email accepted by provider and inbox delivery verified.",
        ),
        _external_check(
            "REMOTE-CI",
            "Remote CI execution",
            settings.remote_ci_validated,
            evidence="Remote workflow URL and sanitized artifact summary",
            rollback="Revert the failing branch or disable deployment promotion for that commit.",
            acceptance="Backend, PostgreSQL, frontend, build, mock E2E, archive and secret scans pass remotely.",
        ),
        _external_check(
            "DNS",
            "Public DNS records",
            settings.production_dns_validated,
            evidence="DNS query evidence for app/API/callback hostnames",
            rollback="Lower TTL before cutover and restore previous DNS records.",
            acceptance="Approved hostnames resolve to the selected deployment endpoints.",
        ),
        _external_check(
            "TLS",
            "Trusted TLS certificates and HTTPS routing",
            settings.production_tls_validated,
            evidence="Certificate issuer, expiry and HTTPS health-check evidence",
            rollback="Restore previous certificate or route traffic back to last known working endpoint.",
            acceptance="HTTPS health/readiness pass, redirect works, and HSTS is enabled only after rollback window approval.",
        ),
        _external_check(
            "OPENAI",
            "OpenAI real-provider acceptance",
            settings.openai_acceptance_test_passed,
            evidence="reports/provider-validation/openai-provider-status.json",
            rollback="Disable OpenAI live provider flags and return to deterministic fallback paths.",
            acceptance="Opt-in synthetic canary passes within cost/timeout limits with sanitized evidence.",
        ),
        _external_check(
            "ELEVENLABS",
            "ElevenLabs live voice acceptance",
            settings.elevenlabs_acceptance_test_passed,
            evidence="Playwright live-provider report or provider-validation evidence",
            rollback="Disable live voice and custom LLM flags; keep mock/provider-error fallback active.",
            acceptance="Opt-in synthetic live voice session passes without user data and cleanup evidence is recorded.",
        ),
        _external_check(
            "BACKUP-RESTORE",
            "Production backup and restore confirmation",
            settings.production_backup_restore_validated,
            required_for_operations=True,
            evidence="Sanitized backup manifest and disposable restore verification",
            rollback="Pause migration/deployment and restore from the last verified backup into a disposable target first.",
            acceptance="Backup is encrypted/stored as expected and restores into a disposable database with schema current.",
        ),
        _external_check(
            "MONITORING",
            "Production monitoring and incident ownership",
            settings.production_monitoring_validated and bool(settings.production_incident_response_owner.strip()),
            required_for_operations=True,
            evidence="Alert routing screenshot/export and named owner attestation",
            rollback="Disable promotion or route traffic back until paging and dashboards are verified.",
            acceptance="Availability, readiness, latency, errors, provider, worker, database, backup and certificate alerts route to an owner.",
        ),
        _external_check(
            "LEGAL-PRIVACY",
            "Legal/privacy review",
            settings.production_legal_privacy_review_approved,
            required_for_operations=True,
            evidence="Reviewed privacy/legal pack approval record",
            rollback="Remove public access and pause data collection until review is complete.",
            acceptance="Professional review approves notices, subprocessors, transfers, retention, deletion/export and AI/voice disclosures.",
        ),
    ]
    deployment_blocking = [check for check in checks if check.required_for_deployment and check.status != "PASSED"]
    operational_blocking = [check for check in checks if check.required_for_operations and check.status != "PASSED"]
    classifications = {
        "local_release_candidate_ready": next(check.status for check in checks if check.id == "LOCAL-RC") == "PASSED",
        "local_staging_validated": next(check.status for check in checks if check.id == "LOCAL-STAGING") == "PASSED",
        "local_production_rehearsal_validated": next(check.status for check in checks if check.id == "LOCAL-PROD-REHEARSAL") == "PASSED",
        "production_deployment_ready": not deployment_blocking,
        "production_operationally_ready": not deployment_blocking and not operational_blocking,
    }
    return {
        "formatVersion": 1,
        "environment": settings.app_env,
        "status": "PASSED" if classifications["production_operationally_ready"] else "BLOCKED",
        "blockingFindingCount": len(deployment_blocking) + len([check for check in operational_blocking if check not in deployment_blocking]),
        "classifications": classifications,
        "checks": [asdict(check) for check in checks],
        "runtimeConfiguration": sanitized_report_dict(runtime_report),
        "secretReadiness": _sanitized_secret_report(secret_report),
        "email": email_status,
        "secretValuesIncluded": False,
    }


def readable_summary(report: dict[str, Any]) -> str:
    lines = [
        f"Production go/no-go: {report['status']}",
        f"Environment: {report['environment']}",
        f"Blocking findings: {report['blockingFindingCount']}",
    ]
    lines.extend(f"{name}: {'PASSED' if passed else 'BLOCKED'}" for name, passed in report["classifications"].items())
    lines.append("Checks:")
    lines.extend(f"- {check['id']}: {check['status']} - {check['description']}" for check in report["checks"])
    return "\n".join(lines)
