from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.engine import make_url

from app.core.time import utc_now


BACKEND_DIR = Path(__file__).resolve().parents[2]


def utc_timestamp() -> str:
    return utc_now().strftime("%Y%m%d-%H%M%S")


def utc_iso() -> str:
    return utc_now().isoformat()


def resolve_backend_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path.resolve()


def require_path_within(parent: Path, target: Path) -> Path:
    parent_resolved = parent.resolve()
    target_resolved = target.resolve()
    if parent_resolved != target_resolved and parent_resolved not in target_resolved.parents:
        raise ValueError("Path is outside the configured directory.")
    return target_resolved


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def sqlite_path_from_url(database_url: str) -> Path:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        raise ValueError("Database URL is not SQLite.")
    if not url.database:
        raise ValueError("In-memory SQLite databases cannot be backed up as files.")
    return resolve_backend_path(url.database)


def sanitized_database_identity(database_url: str) -> dict[str, Any]:
    url = make_url(database_url)
    return {
        "dialect": url.get_backend_name(),
        "driver": url.get_driver_name() if url.get_driver_name() != url.get_backend_name() else None,
        "hostConfigured": bool(url.host),
        "databaseConfigured": bool(url.database),
        "usernameConfigured": bool(url.username),
    }
