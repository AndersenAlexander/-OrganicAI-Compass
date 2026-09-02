from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SECRET_PATTERNS = {
    "openai_api_key": re.compile(r"(?m)^OPENAI_API_KEY\s*=\s*(?!\s*(?:$|<|REDACTED|your-|placeholder)).+"),
    "elevenlabs_api_key": re.compile(r"(?m)^ELEVENLABS_API_KEY\s*=\s*(?!\s*(?:$|<|REDACTED|your-|placeholder)).+"),
    "database_url": re.compile(r"(?m)^DATABASE_URL\s*=\s*(?!\s*(?:$|<|REDACTED|postgresql-connection-string)).+"),
    "postgres_password": re.compile(r"(?m)^POSTGRES_PASSWORD\s*=\s*(?!\s*(?:$|<|REDACTED)).+"),
    "secret_key": re.compile(r"(?m)^SECRET_KEY\s*=\s*(?!\s*(?:$|<|REDACTED|change-this)).+"),
    "webhook_secret": re.compile(r"(?m)^WEBHOOK_SECRET\s*=\s*(?!\s*(?:$|<|REDACTED)).+"),
    "smtp_password": re.compile(r"(?m)^SMTP_PASSWORD\s*=\s*(?!\s*(?:$|<|REDACTED)).+"),
    "export_key": re.compile(r"(?m)^DATA_EXPORT_ENCRYPTION_KEY\s*=\s*(?!\s*(?:$|<|REDACTED)).+"),
    "deletion_hmac": re.compile(r"(?m)^DELETION_LEDGER_HMAC_KEY\s*=\s*(?!\s*(?:$|<|REDACTED)).+"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I),
    "openai_token": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{12,}"),
    "elevenlabs_header": re.compile(r"\bxi-api-key\b", re.I),
    "private_key": re.compile(r"BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY", re.I),
    "password_reset_token": re.compile(r"(?m)^PASSWORD_RESET_TOKEN\s*=\s*(?!\s*$).+"),
    "refresh_token": re.compile(r"(?m)^REFRESH_TOKEN\s*=\s*(?!\s*$).+"),
    "session_cookie": re.compile(r"(?m)^SESSION_COOKIE\s*=\s*(?!\s*$).+"),
}

ARTIFACT_PATTERNS = {
    "environment_file": [".env", ".env.*"],
    "database_file": ["*.db", "*.sqlite", "*.sqlite3"],
    "dump_or_backup": ["*.dump", "*.backup", "*.bak", "backups/*", "backend/backups/*"],
    "privacy_export": ["privacy-exports/*", "*/privacy-exports/*"],
    "development_outbox": ["development-outbox/*", "*/development-outbox/*"],
    "source_archive": ["*.zip", "*.tar", "*.tar.gz"],
    "oci_export": ["*.oci", "*.oci.tar"],
    "runtime_log": ["*.log", "logs/*"],
}

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".tmp",
    "tmp",
    "temp",
    "dist",
}

SAFE_TEMPLATE_FILES = {
    ".env.staging.example",
    ".env.cloud-staging.example",
    ".env.postgres-test.example",
    ".env.production.example",
    ".env.production-rehearsal.example",
    ".env.example",
    "backend/.env.example",
    "backend/.env.production.example",
    "frontend/.env.example",
}

DEFAULT_IGNORE_PATTERNS = [
    ".env",
    ".env.*",
    "!.env.example",
    "!.env.staging.example",
    "!.env.cloud-staging.example",
    "!.env.postgres-test.example",
    "!.env.production.example",
    "!.env.production-rehearsal.example",
    "!backend/.env.example",
    "!backend/.env.production.example",
    "!frontend/.env.example",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "secrets/*",
    "credentials/*",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.dump",
    "*.backup",
    "*.bak",
    "backend/data/*",
    "backend/backups/*",
    "backups/*",
    "logs/*",
    "*.log",
    "tmp/*",
    "temp/*",
    "development-outbox/*",
    "privacy-exports/*",
    "deletion-ledger/*",
    "orphan-archive/*",
    "playwright-report/*",
    "test-results/*",
    "blob-report/*",
    "screenshots/private/*",
    "traces/*",
    "dist/*",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.oci",
    "*.oci.tar",
    "grafana-data/*",
    "prometheus-data/*",
    "otel-data/*",
    ".DS_Store",
    "Thumbs.db",
    ".vscode/*",
    ".idea/*",
]


@dataclass(frozen=True)
class Finding:
    path: str
    category: str
    severity: str
    trackedStatus: str
    remediationStatus: str


def _normalized(path: Path) -> str:
    return path.as_posix()


def load_ignore_patterns(root: Path) -> list[str]:
    patterns = list(DEFAULT_IGNORE_PATTERNS)
    ignore_file = root / ".gitignore"
    if ignore_file.exists():
        for raw in ignore_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_ignored(rel: str, patterns: Iterable[str]) -> bool:
    ignored = False
    for pattern in patterns:
        negated = pattern.startswith("!")
        clean = pattern[1:] if negated else pattern
        clean = clean.rstrip("/")
        checks = {clean, clean.replace("\\", "/")}
        if "/" not in clean:
            checks.add(f"*/{clean}")
        matched = any(fnmatch.fnmatch(rel, item) or fnmatch.fnmatch(Path(rel).name, item) for item in checks)
        if matched:
            ignored = not negated
    return ignored


def git_tracked_files(root: Path) -> set[str] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


def iter_candidate_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in DEFAULT_EXCLUDED_DIRS for part in rel_parts):
            continue
        yield path


def _artifact_category(rel: str, size: int) -> str | None:
    if rel in SAFE_TEMPLATE_FILES:
        return None
    for category, patterns in ARTIFACT_PATTERNS.items():
        if any(fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern) for pattern in patterns):
            return category
    if size > 10 * 1024 * 1024:
        return "large_binary"
    return None


def _status(rel: str, ignored: bool, tracked: set[str] | None) -> str:
    if tracked is not None and rel in tracked:
        return "tracked"
    if ignored:
        return "excluded-by-policy"
    return "candidate"


def _finding(path: str, category: str, tracked_status: str) -> Finding:
    review_only_categories = {"large_binary", "elevenlabs_header", "bearer_token"}
    review_only_suffixes = {".md", ".rst", ".txt"}
    candidate = (
        tracked_status in {"tracked", "candidate"}
        and category not in review_only_categories
        and Path(path).suffix.lower() not in review_only_suffixes
    )
    return Finding(
        path=path,
        category=category,
        severity="blocking" if candidate else "warning",
        trackedStatus=tracked_status,
        remediationStatus="manual-review-required" if candidate else "excluded-by-policy",
    )


def scan_repository(root: Path) -> dict:
    root = root.resolve()
    ignore_patterns = load_ignore_patterns(root)
    tracked = git_tracked_files(root)
    findings: list[Finding] = []

    for path in iter_candidate_files(root):
        rel = _normalized(path.relative_to(root))
        ignored = is_ignored(rel, ignore_patterns)
        tracked_status = _status(rel, ignored, tracked)

        artifact_category = _artifact_category(rel, path.stat().st_size)
        if artifact_category:
            findings.append(_finding(rel, artifact_category, tracked_status))

        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        if rel in SAFE_TEMPLATE_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for category, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(_finding(rel, category, tracked_status))

    unique = []
    seen = set()
    for item in findings:
        key = (item.path, item.category, item.trackedStatus)
        if key not in seen:
            unique.append(item)
            seen.add(key)

    blocking = [item for item in unique if item.severity == "blocking"]
    return {
        "formatVersion": 1,
        "repositoryRoot": str(root),
        "gitStatusAvailable": tracked is not None,
        "blockingFindingCount": len(blocking),
        "findingCount": len(unique),
        "secretValuesIncluded": False,
        "findings": [item.__dict__ for item in sorted(unique, key=lambda f: (f.severity, f.path, f.category))],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    args = parser.parse_args()
    report = scan_repository(Path(args.root))
    print(json.dumps(report, indent=2))
    return 1 if report["blockingFindingCount"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
