from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

from app.services.database_admin import sanitized_database_identity, sha256_file
from app.services.postgres_backup import (
    _docker_compose_container_path,
    _docker_compose_cp_prefix,
    _docker_compose_exec_prefix,
    _validate_pg_identifier,
    docker_compose_config,
    pg_tools_mode,
    run_pg_tool,
    verify_pg_dump_archive,
)


def load_backup_manifest(backup_path: Path) -> dict[str, Any]:
    manifest_path = backup_path.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError("Backup manifest was not found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("sha256") != sha256_file(backup_path):
        raise ValueError("Backup checksum does not match manifest.")
    return manifest


def target_database_empty(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        return not inspect(engine).get_table_names(schema="public")
    finally:
        engine.dispose()


def restore_postgres_backup(
    backup_path: Path,
    target_database_url: str,
    *,
    active_database_url: str,
    apply: bool = False,
    allow_active_target: bool = False,
    allow_non_empty: bool = False,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    manifest = load_backup_manifest(backup_path)
    verify_pg_dump_archive(backup_path)
    target = make_url(target_database_url)
    active = make_url(active_database_url)
    if target.get_backend_name() not in {"postgresql", "postgres"}:
        raise ValueError("Restore target must be PostgreSQL.")
    if str(target) == str(active) and not allow_active_target:
        raise ValueError("Restore target matches the active database and is blocked.")
    if not target_database_empty(target_database_url) and not allow_non_empty:
        raise ValueError("Restore target is not empty.")
    if not apply:
        return {
            "status": "dry_run",
            "target": sanitized_database_identity(target_database_url),
            "manifest": {"fileName": manifest.get("fileName"), "databaseType": manifest.get("databaseType")},
        }

    if pg_tools_mode() == "docker-compose":
        database = _validate_pg_identifier(target.database, "database name")
        username = _validate_pg_identifier(target.username, "username")
        _compose_file, service = docker_compose_config()
        container_path = _docker_compose_container_path(backup_path)
        copied = False
        try:
            copy_in = [*_docker_compose_cp_prefix(), str(backup_path), f"{service}:{container_path}"]
            result = run_pg_tool(copy_in, timeout_seconds=timeout_seconds)
            if result.returncode != 0:
                raise RuntimeError("Docker Compose restore copy-in failed.")
            copied = True
            command = [
                *_docker_compose_exec_prefix(),
                "pg_restore",
                "--dbname",
                database,
                "--username",
                username,
                container_path,
            ]
            result = run_pg_tool(command, timeout_seconds=timeout_seconds)
            if result.returncode != 0:
                raise RuntimeError("pg_restore failed.")
        finally:
            if copied:
                run_pg_tool([*_docker_compose_exec_prefix(), "rm", "-f", container_path], timeout_seconds=timeout_seconds)
        return {"status": "success", "target": sanitized_database_identity(target_database_url)}

    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        raise FileNotFoundError("pg_restore was not found on PATH.")
    env = os.environ.copy()
    if target.password:
        env["PGPASSWORD"] = target.password
    command = [pg_restore, "--dbname", target.database or ""]
    if target.host:
        command.extend(["--host", target.host])
    if target.port:
        command.extend(["--port", str(target.port)])
    if target.username:
        command.extend(["--username", target.username])
    command.append(str(backup_path))
    result = run_pg_tool(command, env=env, timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError("pg_restore failed.")
    return {"status": "success", "target": sanitized_database_identity(target_database_url)}
