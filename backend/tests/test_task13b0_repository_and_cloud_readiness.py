from __future__ import annotations

import json
from pathlib import Path

from app.scripts.audit_cloud_staging_readiness import audit_cloud_staging_readiness
from app.scripts.audit_repository_safety import scan_repository


REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".env.*",
    "!.env.example",
    "!.env.staging.example",
    "*.db",
    "*.dump",
    "*.zip",
    "*.oci",
    "privacy-exports/",
    "grafana-data/",
    "prometheus-data/",
    "otel-data/",
]


def test_gitignore_contains_required_repository_safety_patterns():
    root = Path(__file__).resolve().parents[2]
    content = (root / ".gitignore").read_text(encoding="utf-8")
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        assert pattern in content


def test_repository_safety_scanner_redacts_secret_values(tmp_path: Path):
    (tmp_path / ".gitignore").write_text(".env\n*.db\n", encoding="utf-8")
    fake_secret = "sk-" + "proj-do-not-print-this-value"
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY={fake_secret}\n", encoding="utf-8")
    (tmp_path / "safe.py").write_text("print('ok')\n", encoding="utf-8")
    report = scan_repository(tmp_path)
    text = json.dumps(report)
    assert report["secretValuesIncluded"] is False
    assert fake_secret not in text
    assert report["blockingFindingCount"] == 0


def test_repository_safety_blocks_unignored_secret_candidate(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    (tmp_path / "settings.env").write_text("SECRET_KEY=realistic-secret-value-that-is-not-safe\n", encoding="utf-8")
    report = scan_repository(tmp_path)
    assert report["blockingFindingCount"] >= 1
    assert any(item["category"] == "secret_key" for item in report["findings"])


def test_cloud_readiness_blocks_missing_provider_region_remote_ci_and_rotation(tmp_path: Path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    for name in [
        "CLOUD_POSTGRESQL_MIGRATION_PLAN.md",
        "CLOUD_SECRET_MANAGEMENT_PLAN.md",
        "CLOUD_OBSERVABILITY_PLAN.md",
        "CLOUD_BACKUP_AND_RECOVERY_PLAN.md",
    ]:
        (tmp_path / "docs" / name).write_text("# plan\n", encoding="utf-8")
    report = audit_cloud_staging_readiness(tmp_path)
    blocked = {check["category"] for check in report["checks"] if check["status"] == "blocked"}
    assert {"remote repository", "remote CI evidence", "secret rotation", "provider selection", "region"} <= blocked
    assert report["task13b1ApprovedToStart"] is False


def test_cloud_environment_template_contains_placeholders_only():
    root = Path(__file__).resolve().parents[2]
    template = (root / ".env.cloud-staging.example").read_text(encoding="utf-8")
    assert "PUBLIC_BASE_URL=https://staging.example.invalid" in template
    assert "OPENAI_ENABLED=false" in template
    assert "ELEVENLABS_ENABLED=false" in template
    assert "EMAIL_DRIVER=disabled" in template
    assert "sk-" not in template
    assert "xi-api-key" not in template
