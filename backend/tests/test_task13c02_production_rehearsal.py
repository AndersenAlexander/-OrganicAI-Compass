from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import Settings
from app.services.production_readiness import production_go_no_go_report
from app.services.production_rehearsal import (
    ACTIVE_DATABASE_NAME,
    PROJECT_NAME,
    RESTORE_DATABASE_NAME,
    VOLUME_NAME,
    assert_restore_target_allowed,
    rehearsal_summary_passed,
    resource_inventory,
    sanitize_manifest,
    validate_rehearsal_database_name,
)
from app.services.runtime_configuration import check_runtime_configuration


ROOT = Path(__file__).resolve().parents[2]


def production_rehearsal_settings(**overrides) -> Settings:
    values = {
        "app_env": "production",
        "production_rehearsal_mode": True,
        "secret_key": "s" * 64,
        "database_url": "postgresql+psycopg2://organicai_prod_rehearsal:synthetic-password@postgres:5432/organicai_prod_rehearsal",
        "production_postgres_ssl_required": False,
        "data_export_encryption_key": "e" * 64,
        "deletion_ledger_hmac_key": "d" * 64,
        "public_backend_url": "https://api.rehearsal.example.test",
        "frontend_public_url": "https://app.rehearsal.example.test",
        "frontend_url": "https://app.rehearsal.example.test",
        "email_public_base_url": "https://app.rehearsal.example.test",
        "allowed_origins": "https://app.rehearsal.example.test",
        "allowed_hosts": "api.rehearsal.local,app.rehearsal.local,backend",
        "auth_cookie_secure": True,
        "auth_cookie_httponly": True,
        "auth_cookie_samesite": "lax",
        "email_delivery_driver": "disabled",
        "demo_account_enabled": False,
        "hsts_enabled": True,
        "csp_report_only": False,
        "integration_diagnostics_enabled": False,
        "openai_api_key": "disabled",
        "elevenlabs_api_key": "disabled",
        "elevenlabs_agent_id": "disabled",
        "elevenlabs_live_voice_enabled": False,
        "elevenlabs_custom_llm_enabled": False,
        "real_provider_tests_enabled": False,
        "real_privacy_provider_tests_enabled": False,
        "live_provider_validation_enabled": False,
        "live_provider_write_validation_enabled": False,
        "openai_live_canary_enabled": False,
        "secret_rotation_openai_confirmed": True,
        "secret_rotation_elevenlabs_confirmed": True,
        "secret_rotation_postgres_confirmed": True,
        "secret_rotation_application_confirmed": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def write_release_candidate_evidence(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "final-test-summary.json").write_text(
        json.dumps(
            {
                "backend": {"fullNonPostgres": {"status": "passed"}},
                "postgresql": {"markerSuite": {"failed": 0}},
                "frontend": {"build": {"status": "passed"}},
                "e2e": {"fullPlaywright": {"failed": 0}},
            }
        ),
        encoding="utf-8",
    )
    (path / "staging-service-summary.json").write_text(
        json.dumps({"runtimeSmoke": {"status": "passed"}, "observability": {"status": "passed"}}),
        encoding="utf-8",
    )
    (path / "source-archive-audit-final.json").write_text(
        json.dumps({"status": "passed", "blockedEntryCount": 0}),
        encoding="utf-8",
    )


def write_rehearsal_evidence(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    checks = {
        "freshPostgresMigration": {"status": "PASSED"},
        "schemaDrift": {"status": "PASSED"},
        "runtimeReadiness": {"status": "PASSED"},
        "reverseProxySmoke": {"status": "PASSED"},
        "syntheticAcceptance": {"status": "PASSED"},
        "backup": {"status": "PASSED"},
        "restore": {"status": "PASSED"},
        "applicationRollback": {"status": "PASSED"},
        "failureRecovery": {"status": "PASSED"},
        "security": {"status": "PASSED"},
        "observability": {"status": "PASSED"},
        "safeTeardown": {"status": "PASSED"},
    }
    (path / "final-summary.json").write_text(
        json.dumps(
            {
                "status": "PASSED",
                "classifications": {"local_production_rehearsal_validated": "PASSED"},
                "checks": checks,
                "guards": {
                    "realProvidersCalled": False,
                    "realEmailSent": False,
                    "destructiveOperationCount": 0,
                    "secretDisclosureCount": 0,
                },
            }
        ),
        encoding="utf-8",
    )


def test_production_rehearsal_resource_names_and_ports_are_isolated():
    inventory = resource_inventory()
    compose = (ROOT / "docker-compose.production-rehearsal.yml").read_text(encoding="utf-8")

    assert inventory["projectName"] == PROJECT_NAME
    assert inventory["activeDatabase"] == ACTIVE_DATABASE_NAME
    assert inventory["restoreDatabase"] == RESTORE_DATABASE_NAME
    assert inventory["volume"] == VOLUME_NAME
    assert "organicai-prod-rehearsal-postgres" in compose
    assert "organicai_prod_rehearsal_network" in compose
    assert "127.0.0.1:28080:8080" in compose
    assert "127.0.0.1:55532:5432" in compose
    assert "127.0.0.1:18080:8080" not in compose
    assert "organicai_staging_postgres_data" not in compose


def test_rehearsal_runtime_allows_disabled_email_only_in_rehearsal_mode():
    settings = production_rehearsal_settings()
    report = check_runtime_configuration(settings)

    assert report.ready is True
    assert any(
        check.key == "EMAIL_DELIVERY_DRIVER"
        and check.status == "ok"
        and "rehearsal" in check.message.lower()
        for check in report.checks
    )

    real_production = production_rehearsal_settings(production_rehearsal_mode=False)
    real_report = check_runtime_configuration(real_production)
    assert any(check.key == "EMAIL_DELIVERY_DRIVER" and check.status == "error" for check in real_report.checks)


def test_rehearsal_env_example_disables_real_providers_and_contains_no_real_secret_shape():
    env_example = (ROOT / ".env.production-rehearsal.example").read_text(encoding="utf-8")

    assert "APP_ENV=production" in env_example
    assert "PRODUCTION_REHEARSAL_MODE=true" in env_example
    assert "EMAIL_DELIVERY_DRIVER=disabled" in env_example
    assert "OPENAI_API_KEY=disabled" in env_example
    assert "ELEVENLABS_API_KEY=disabled" in env_example
    assert "LIVE_PROVIDER_VALIDATION_ENABLED=false" in env_example
    assert "REAL_PROVIDER_TESTS_ENABLED=false" in env_example
    assert "sk-" not in env_example
    assert "smtp_password" not in env_example.lower()


def test_restore_target_guard_blocks_staging_active_and_out_of_namespace_targets():
    validate_rehearsal_database_name(RESTORE_DATABASE_NAME)
    assert_restore_target_allowed(
        "postgresql+psycopg2://u:p@127.0.0.1:55532/organicai_prod_rehearsal_restore",
        "postgresql+psycopg2://u:p@127.0.0.1:55532/organicai_prod_rehearsal",
    )

    with pytest.raises(ValueError):
        validate_rehearsal_database_name("organicai_staging")
    with pytest.raises(ValueError):
        assert_restore_target_allowed(
            "postgresql+psycopg2://u:p@127.0.0.1:55532/organicai_prod_rehearsal",
            "postgresql+psycopg2://u:p@127.0.0.1:55532/organicai_prod_rehearsal",
        )
    with pytest.raises(ValueError):
        validate_rehearsal_database_name("organicai_test")


def test_backup_manifest_sanitization_removes_secret_material():
    manifest = {
        "fileName": "organicai-prod-rehearsal.dump",
        "sha256": "a" * 64,
        "databaseUrl": "postgresql://user:password@localhost/db",
        "nested": {"apiKey": "sk-secret", "token": "token-value"},
        "sourceSanitized": {"dialect": "postgresql", "hostConfigured": True},
    }

    sanitized = sanitize_manifest(manifest)
    rendered = json.dumps(sanitized)

    assert sanitized["fileName"] == "organicai-prod-rehearsal.dump"
    assert sanitized["secretValuesIncluded"] is False
    assert "password" not in rendered
    assert "sk-secret" not in rendered
    assert "token-value" not in rendered


def test_safe_stop_script_preserves_volumes_and_omits_destructive_docker_operations():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "scripts" / "production-rehearsal-stop.ps1",
            ROOT / "scripts" / "production-rehearsal-common.ps1",
        ]
    ).lower()

    assert "volumes, backups and logs retained" in combined
    assert "down -v" not in combined
    assert "docker system prune" not in combined
    assert "docker volume prune" not in combined
    assert "wsl --unregister" not in combined


def test_go_no_go_includes_local_production_rehearsal_but_keeps_external_blockers(tmp_path):
    release_evidence = tmp_path / "task13b05"
    rehearsal_evidence = tmp_path / "task13c02"
    write_release_candidate_evidence(release_evidence)
    write_rehearsal_evidence(rehearsal_evidence)

    report = production_go_no_go_report(release_evidence, production_rehearsal_settings())
    checks = {check["id"]: check for check in report["checks"]}

    assert report["classifications"]["local_release_candidate_ready"] is True
    assert report["classifications"]["local_staging_validated"] is True
    assert report["classifications"]["local_production_rehearsal_validated"] is True
    assert checks["LOCAL-PROD-REHEARSAL"]["status"] == "PASSED"
    assert report["classifications"]["production_deployment_ready"] is False
    assert report["classifications"]["production_operationally_ready"] is False
    assert any(check["status"] == "EXTERNAL MANUAL ACTION REQUIRED" for check in report["checks"])
    assert "synthetic-password" not in json.dumps(report)


def test_rehearsal_summary_requires_all_guards_and_checks():
    assert rehearsal_summary_passed(
        {
            "status": "PASSED",
            "classifications": {"local_production_rehearsal_validated": "PASSED"},
            "checks": {
                name: {"status": "PASSED"}
                for name in [
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
                ]
            },
            "guards": {
                "realProvidersCalled": False,
                "realEmailSent": False,
                "destructiveOperationCount": 0,
                "secretDisclosureCount": 0,
            },
        }
    )
    assert not rehearsal_summary_passed(
        {
            "status": "PASSED",
            "classifications": {"local_production_rehearsal_validated": "PASSED"},
            "checks": {"freshPostgresMigration": {"status": "PASSED"}},
            "guards": {
                "realProvidersCalled": True,
                "realEmailSent": False,
                "destructiveOperationCount": 0,
                "secretDisclosureCount": 0,
            },
        }
    )
