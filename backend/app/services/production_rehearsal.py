from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[3]
PROJECT_NAME = "organicai-prod-rehearsal"
COMPOSE_FILE = "docker-compose.production-rehearsal.yml"
ENV_EXAMPLE_FILE = ".env.production-rehearsal.example"
ENV_RUNTIME_FILE = ".tmp/production-rehearsal.env"
EVIDENCE_DIR = ROOT / "evidence" / "task13c02"

ACTIVE_DATABASE_NAME = "organicai_prod_rehearsal"
RESTORE_DATABASE_NAME = "organicai_prod_rehearsal_restore"
NETWORK_NAME = "organicai_prod_rehearsal_network"
VOLUME_NAME = "organicai_prod_rehearsal_postgres_data"

PORTS = {
    "proxy": 28080,
    "postgres": 55532,
    "otel_http": 14318,
    "prometheus": 29090,
    "grafana": 23000,
}

CONTAINER_NAMES = {
    "postgres": "organicai-prod-rehearsal-postgres",
    "migrator": "organicai-prod-rehearsal-migrator",
    "backend": "organicai-prod-rehearsal-backend",
    "worker": "organicai-prod-rehearsal-worker",
    "frontend": "organicai-prod-rehearsal-frontend",
    "proxy": "organicai-prod-rehearsal-proxy",
    "otel": "organicai-prod-rehearsal-otel",
    "prometheus": "organicai-prod-rehearsal-prometheus",
    "grafana": "organicai-prod-rehearsal-grafana",
}

PROTECTED_DATABASE_NAMES = {
    "organicai",
    "organicai_dev",
    "organicai_development",
    "organicai_test",
    "organicai_staging",
    "organicai_production",
    "postgres",
    "template0",
    "template1",
}

REQUIRED_EVIDENCE_CHECKS = (
    "freshPostgresMigration",
    "schemaDrift",
    "runtimeReadiness",
    "reverseProxySmoke",
    "syntheticAcceptance",
    "backup",
    "restore",
    "applicationRollback",
    "failureRecovery",
    "security",
    "observability",
    "safeTeardown",
)

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
SECRETISH_KEYS = ("url", "password", "secret", "token", "key", "credential")


def resource_inventory() -> dict[str, Any]:
    return {
        "projectName": PROJECT_NAME,
        "composeFile": COMPOSE_FILE,
        "envExampleFile": ENV_EXAMPLE_FILE,
        "envRuntimeFile": ENV_RUNTIME_FILE,
        "network": NETWORK_NAME,
        "volume": VOLUME_NAME,
        "containers": CONTAINER_NAMES,
        "ports": PORTS,
        "activeDatabase": ACTIVE_DATABASE_NAME,
        "restoreDatabase": RESTORE_DATABASE_NAME,
    }


def validate_database_identifier(value: str | None) -> str:
    clean = str(value or "").strip()
    if not SAFE_IDENTIFIER_RE.fullmatch(clean):
        raise ValueError("Invalid rehearsal database identifier.")
    return clean


def validate_rehearsal_database_name(value: str | None) -> str:
    clean = validate_database_identifier(value)
    if clean in PROTECTED_DATABASE_NAMES:
        raise ValueError("Protected database name is blocked.")
    if clean not in {ACTIVE_DATABASE_NAME, RESTORE_DATABASE_NAME} and not clean.startswith(f"{RESTORE_DATABASE_NAME}_"):
        raise ValueError("Database name is outside the production rehearsal namespace.")
    return clean


def assert_restore_target_allowed(target_database_url: str, active_database_url: str) -> str:
    target = make_url(target_database_url)
    active = make_url(active_database_url)
    target_database = validate_rehearsal_database_name(target.database)
    if target_database == active.database:
        raise ValueError("Restore target matches the active rehearsal database.")
    if target_database == ACTIVE_DATABASE_NAME:
        raise ValueError("Active rehearsal database cannot be a restore target.")
    return target_database


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_manifest(value)
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def sanitize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in manifest.items():
        lower_key = str(key).lower()
        if any(marker in lower_key for marker in SECRETISH_KEYS):
            if lower_key in {"filename", "sha256", "sizebytes", "schemaversion", "postgresqlversion"}:
                sanitized[key] = value
            elif lower_key == "sourcesanitized":
                sanitized[key] = _redact(value)
            else:
                sanitized[key] = "<redacted>"
            continue
        sanitized[key] = _redact(value)
    sanitized["secretValuesIncluded"] = False
    return sanitized


def read_rehearsal_summary(path: str | Path | None = None) -> dict[str, Any] | None:
    summary_path = Path(path).resolve() if path else EVIDENCE_DIR / "final-summary.json"
    for encoding in ("utf-8", "utf-8-sig", "utf-16"):
        try:
            return json.loads(summary_path.read_text(encoding=encoding))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
    return None


def rehearsal_summary_passed(summary: dict[str, Any] | None) -> bool:
    if not summary or summary.get("status") != "PASSED":
        return False
    classifications = summary.get("classifications", {})
    if classifications.get("local_production_rehearsal_validated") != "PASSED":
        return False
    checks = summary.get("checks", {})
    if not all(checks.get(name, {}).get("status") == "PASSED" for name in REQUIRED_EVIDENCE_CHECKS):
        return False
    guards = summary.get("guards", {})
    return (
        guards.get("realProvidersCalled") is False
        and guards.get("realEmailSent") is False
        and int(guards.get("destructiveOperationCount", 0)) == 0
        and int(guards.get("secretDisclosureCount", 0)) == 0
    )


def rehearsal_evidence_check(path: str | Path | None = None) -> dict[str, Any]:
    summary = read_rehearsal_summary(path)
    passed = rehearsal_summary_passed(summary)
    return {
        "status": "PASSED" if passed else "BLOCKED",
        "summaryAvailable": summary is not None,
        "evidencePath": str(Path(path).resolve() if path else EVIDENCE_DIR / "final-summary.json"),
        "requiredChecks": list(REQUIRED_EVIDENCE_CHECKS),
    }
