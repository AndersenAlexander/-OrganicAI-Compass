from __future__ import annotations

import zipfile
from pathlib import Path

from app.scripts.create_source_archive import ROOT, build_archive, excluded


def test_source_archive_excludes_secrets_databases_reports_and_logs(tmp_path):
    output = tmp_path / "OrganicAI-Compass-source.zip"
    report = build_archive(output)
    assert report["created"] is True
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
    assert "SOURCE_ARCHIVE_MANIFEST.json" in names
    assert not any((name.endswith(".env") or "/.env" in name) and not name.endswith(".example") for name in names)
    assert not any(name.endswith(".db") or name.endswith(".dump") or name.endswith(".log") for name in names)
    assert not any(name.startswith("reports/") for name in names)
    assert not any("/node_modules/" in name for name in names)
    assert not any(name.startswith("browser-extension/dist/") for name in names)
    assert "backend/app/scripts/create_source_archive.py" in names


def test_source_archive_excludes_nested_dependency_and_build_dirs():
    nested_dependency = ROOT / "browser-extension" / "node_modules" / "typescript" / "package.json"
    nested_build = ROOT / "browser-extension" / "dist" / "popup.js"

    assert excluded(nested_dependency) == (True, "local data, dependency, report, or generated directory")
    assert excluded(nested_build) == (True, "local data, dependency, report, or generated directory")


def test_source_archive_includes_safe_environment_templates_only():
    assert excluded(ROOT / ".env.production.example") == (False, None)
    assert excluded(ROOT / "backend" / ".env.production.example") == (False, None)
    assert excluded(ROOT / ".env.production") == (True, "environment secret file")
