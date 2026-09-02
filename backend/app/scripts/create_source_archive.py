from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SECRET_PATTERN = re.compile(
    r"("
    r"sk-[A-Za-z0-9_-]{30,}|"
    r"sk-proj-[A-Za-z0-9_-]{30,}|"
    r"(?:ELEVENLABS_API_KEY|OPENAI_API_KEY|SECRET_KEY|JWT_SECRET|ELEVENLABS_CUSTOM_LLM_SECRET)=\\S{12,}|"
    r"postgres(?:ql)?(?:\\+\\w+)?://[^\\s:@]+:[^\\s:@]+@"
    r")",
    re.IGNORECASE,
)

EXCLUDED_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "playwright-report",
    "privacy-exports",
    "private",
    "reports",
    "test-results",
    "uploads",
    "venv",
}
EXCLUDED_DIRS = {
    "backend/.tmp",
    "backend/.venv",
    "frontend/dist",
    "backend/data",
    "backend/backups",
    "backend/tmp",
    "backend/tmp/privacy-exports",
    "backend/tmp/email-outbox",
    "backend/tmp/privacy-worker",
    "backend/tmp/provider-deletion",
    "backend/.pytest_cache",
    "reports",
    "privacy-exports",
    "playwright-report",
    "test-results",
    "frontend/playwright-report",
    "frontend/test-results",
    "frontend/qa",
}
EXCLUDED_SUFFIXES = {".db", ".dump", ".log", ".pyc", ".zip"}
EXCLUDED_NAMES = {".env", ".env.postgres-test", "backend/.env", "backend/.env.pre-task11-4", "backend/.env.postgres-test"}
EXCLUDED_SECRET_BEARING_FILES = {
    "evidence/task13b02/postgres-prepare-output.txt",
    "evidence/task13b02/postgres-test-migration-validation.md",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_environment_template(path: Path) -> bool:
    return path.name.startswith(".env") and path.name.endswith(".example")


def excluded(path: Path) -> tuple[bool, str | None]:
    relative = rel(path)
    parts = relative.split("/")
    if any(part in EXCLUDED_DIR_NAMES for part in parts[:-1]):
        return True, "local data, dependency, report, or generated directory"
    for index in range(1, len(parts) + 1):
        if "/".join(parts[:index]) in EXCLUDED_DIRS:
            return True, "local data, dependency, report, or generated directory"
    if relative in EXCLUDED_SECRET_BEARING_FILES:
        return True, "secret-bearing historical evidence"
    if relative in EXCLUDED_NAMES or (path.name.startswith(".env.") and not safe_environment_template(path)):
        return True, "environment secret file"
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True, "local database, dump, log, or bytecode artifact"
    if path.name.endswith(".png") and path.parent == ROOT:
        return True, "local screenshot or image artifact"
    return False, None


def scan_source(files: list[Path]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in files:
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".json", ".md", ".txt", ".yml", ".yaml", ".example"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SECRET_PATTERN.search(text):
            findings.append({"file": rel(path), "category": "potential_secret_pattern"})
    return findings


def build_archive(output: Path) -> dict:
    included: list[Path] = []
    excluded_counts: dict[str, int] = {}
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        is_excluded, reason = excluded(path)
        if is_excluded:
            excluded_counts[reason or "excluded"] = excluded_counts.get(reason or "excluded", 0) + 1
        else:
            included.append(path)
    findings = scan_source(included)
    if findings:
        return {"created": False, "blockingFindings": findings, "secretValuesIncluded": False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in included:
            archive.write(path, rel(path))
        manifest = {
            "archive": output.name,
            "includedFileCount": len(included),
            "excludedCategories": excluded_counts,
            "secretValuesIncluded": False,
            "localDatabasesIncluded": False,
            "environmentFilesIncluded": False,
        }
        archive.writestr("SOURCE_ARCHIVE_MANIFEST.json", json.dumps(manifest, indent=2))
    return {"created": True, **manifest}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a sanitized OrganicAI Compass source archive.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    report = build_archive(output)
    print(json.dumps(report, indent=2))
    return 0 if report.get("created") else 1


if __name__ == "__main__":
    raise SystemExit(main())
