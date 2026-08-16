from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    "playwright-report",
    "test-results",
    "__pycache__",
    "backups",
}
IGNORED_FILES = {".env.example"}
TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".env",
    ".yml",
    ".yaml",
    ".toml",
}
SENSITIVE_PATTERNS = [
    ("OPENAI_KEY", re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("DATABASE_CREDENTIALS", re.compile(r"(?i)(postgres|mysql)://[^:\s]+:[^@\s]+@")),
    ("JWT_TOKEN", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}")),
]


def iter_files():
    for path in ROOT.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.is_dir():
            continue
        if path.name in IGNORED_FILES:
            continue
        yield path


def scan_file(path: Path) -> list[str]:
    relative = path.relative_to(ROOT).as_posix()
    findings: list[str] = []
    if path.name == ".env":
        findings.append(f"{relative}: LOCAL_ENV_FILE")
        return findings
    if path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        findings.append(f"{relative}: LOCAL_DATABASE_ARTIFACT")
        return findings
    if path.suffix.lower() in {".mp3", ".wav", ".webm", ".m4a"}:
        findings.append(f"{relative}: AUDIO_ARTIFACT")
        return findings
    if path.suffix.lower() not in TEXT_EXTENSIONS or path.stat().st_size > 1_000_000:
        return findings
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return findings
    for name, pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            findings.append(f"{relative}: {name}")
    return findings


def main() -> int:
    blocking: list[str] = []
    warnings: list[str] = []
    for path in iter_files():
        for finding in scan_file(path):
            if finding.endswith(("LOCAL_ENV_FILE", "LOCAL_DATABASE_ARTIFACT", "AUDIO_ARTIFACT")):
                warnings.append(finding)
            else:
                blocking.append(finding)
    for finding in warnings:
        print(f"warning: {finding}")
    for finding in blocking:
        print(f"error: {finding}")
    if blocking:
        return 1
    print("Security scan completed without blocking findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
