from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.services.database_admin import require_path_within, resolve_backend_path, sanitized_database_identity, sha256_file, utc_iso, utc_timestamp, write_json_atomic

SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
SAFE_SERVICE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SAFE_BACKUP_FILE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def postgres_table_counts(database_url: str) -> dict[str, int]:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    counts: dict[str, int] = {}
    with engine.connect() as connection:
        for table in sorted(inspector.get_table_names(schema="public")):
            quoted = '"' + table.replace('"', '""') + '"'
            counts[table] = int(connection.execute(text(f"select count(*) from public.{quoted}")).scalar_one())
    engine.dispose()
    return counts


def pg_tools_mode() -> str:
    mode = (os.environ.get("PG_TOOLS_MODE") or "local").strip().lower()
    if mode not in {"local", "docker-compose"}:
        raise ValueError("PG_TOOLS_MODE must be local or docker-compose.")
    return mode


def _validate_pg_identifier(value: str | None, label: str) -> str:
    if not value or not SAFE_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"Invalid PostgreSQL {label}.")
    return value


def _validate_compose_service(value: str | None) -> str:
    if not value or not SAFE_SERVICE_RE.fullmatch(value):
        raise ValueError("Invalid Docker Compose service name.")
    return value


def _validate_backup_filename(name: str) -> str:
    if not SAFE_BACKUP_FILE_RE.fullmatch(name):
        raise ValueError("Invalid backup filename.")
    return name


def docker_compose_config() -> tuple[Path, str]:
    compose_file = resolve_backend_path(os.environ.get("PG_DOCKER_COMPOSE_FILE") or "../docker-compose.persistence.yml")
    if not compose_file.exists() or not compose_file.is_file():
        raise FileNotFoundError("Docker Compose persistence file was not found.")
    service = _validate_compose_service(os.environ.get("PG_DOCKER_SERVICE") or "organicai-postgres")
    return compose_file, service


def docker_compose_env_file() -> Path | None:
    configured = os.environ.get("PG_DOCKER_ENV_FILE")
    if not configured:
        return None
    env_file = resolve_backend_path(configured)
    if not env_file.exists() or not env_file.is_file():
        raise FileNotFoundError("Docker Compose env file was not found.")
    return env_file


def docker_compose_base_command() -> list[str]:
    compose_file, _service = docker_compose_config()
    docker = _docker_path()
    command = [docker, "compose"]
    env_file = docker_compose_env_file()
    if env_file is not None:
        command.extend(["--env-file", str(env_file)])
    command.extend(["-f", str(compose_file)])
    return command


def _docker_path() -> str:
    docker = shutil.which("docker")
    if not docker:
        raise FileNotFoundError("docker was not found on PATH.")
    return docker


def run_pg_tool(command: list[str], *, env: dict[str, str] | None = None, timeout_seconds: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, env=env, shell=False)


def build_pg_dump_command(database_url: str, output_path: Path) -> tuple[list[str], dict[str, str]]:
    url = make_url(database_url)
    if url.get_backend_name() not in {"postgresql", "postgres"}:
        raise ValueError("PostgreSQL backup requires a PostgreSQL DATABASE_URL.")
    if pg_tools_mode() != "local":
        raise ValueError("build_pg_dump_command is only available in local PG tools mode.")
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise FileNotFoundError("pg_dump was not found on PATH.")
    command = [pg_dump, "--format=custom", "--file", str(output_path)]
    if url.host:
        command.extend(["--host", url.host])
    if url.port:
        command.extend(["--port", str(url.port)])
    if url.username:
        command.extend(["--username", url.username])
    if url.database:
        command.extend(["--dbname", url.database])
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    return command, env


def _docker_compose_container_path(path: Path) -> str:
    return f"/tmp/{_validate_backup_filename(path.name)}"


def _docker_compose_exec_prefix() -> list[str]:
    _compose_file, service = docker_compose_config()
    return [*docker_compose_base_command(), "exec", "-T", service]


def _docker_compose_cp_prefix() -> list[str]:
    return [*docker_compose_base_command(), "cp"]


def verify_pg_dump_archive(path: Path, timeout_seconds: int = 60) -> None:
    if pg_tools_mode() == "docker-compose":
        _verify_pg_dump_archive_docker(path, timeout_seconds=timeout_seconds)
        return
    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        raise FileNotFoundError("pg_restore was not found on PATH.")
    result = run_pg_tool([pg_restore, "--list", str(path)], timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError("pg_restore archive verification failed.")


def _verify_pg_dump_archive_in_container(container_path: str, timeout_seconds: int = 60) -> None:
    result = run_pg_tool([*_docker_compose_exec_prefix(), "pg_restore", "--list", container_path], timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError("pg_restore archive verification failed.")


def _verify_pg_dump_archive_docker(path: Path, timeout_seconds: int = 60) -> None:
    compose_file, service = docker_compose_config()
    container_path = _docker_compose_container_path(path)
    copied = False
    try:
        copy_in = [*_docker_compose_cp_prefix(), str(path), f"{service}:{container_path}"]
        result = run_pg_tool(copy_in, timeout_seconds=timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError("Docker Compose backup copy-in failed.")
        copied = True
        _verify_pg_dump_archive_in_container(container_path, timeout_seconds=timeout_seconds)
    finally:
        if copied:
            run_pg_tool([*_docker_compose_exec_prefix(), "rm", "-f", container_path], timeout_seconds=timeout_seconds)


def _read_postgres_schema_version(database_url: str) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            if "alembic_version" not in inspect(engine).get_table_names(schema="public"):
                return None
            return connection.execute(text("select version_num from public.alembic_version limit 1")).scalar_one_or_none()
    finally:
        engine.dispose()


def _read_postgres_server_version(database_url: str) -> str | None:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            value = connection.execute(text("show server_version")).scalar_one_or_none()
            return str(value) if value is not None else None
    finally:
        engine.dispose()


def _backup_postgres_database_local(database_url: str, tmp_dump: Path, timeout_seconds: int) -> None:
    command, env = build_pg_dump_command(database_url, tmp_dump)
    result = run_pg_tool(command, env=env, timeout_seconds=timeout_seconds)
    if result.returncode != 0:
        tmp_dump.unlink(missing_ok=True)
        raise RuntimeError("pg_dump failed.")
    verify_pg_dump_archive(tmp_dump)


def _backup_postgres_database_docker(database_url: str, tmp_dump: Path, timeout_seconds: int) -> None:
    url = make_url(database_url)
    if url.get_backend_name() not in {"postgresql", "postgres"}:
        raise ValueError("PostgreSQL backup requires a PostgreSQL DATABASE_URL.")
    database = _validate_pg_identifier(url.database, "database name")
    username = _validate_pg_identifier(url.username, "username")
    _compose_file, service = docker_compose_config()
    container_path = _docker_compose_container_path(tmp_dump)
    dump_command = [
        *docker_compose_base_command(),
        "exec",
        "-T",
        service,
        "pg_dump",
        "--format=custom",
        "--file",
        container_path,
        "--username",
        username,
        "--dbname",
        database,
    ]
    try:
        result = run_pg_tool(dump_command, timeout_seconds=timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError("pg_dump failed.")
        _verify_pg_dump_archive_in_container(container_path, timeout_seconds=timeout_seconds)
        copy_out = [*_docker_compose_cp_prefix(), f"{service}:{container_path}", str(tmp_dump)]
        result = run_pg_tool(copy_out, timeout_seconds=timeout_seconds)
        if result.returncode != 0:
            raise RuntimeError("Docker Compose backup copy-out failed.")
    finally:
        run_pg_tool([*_docker_compose_exec_prefix(), "rm", "-f", container_path], timeout_seconds=timeout_seconds)


def backup_postgres_database(
    database_url: str,
    backup_directory: str | Path,
    application_version: str = "",
    timeout_seconds: int = 300,
    *,
    prefix: str = "organicai-postgres",
) -> dict[str, Any]:
    backup_dir = resolve_backend_path(backup_directory)
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_timestamp()
    _validate_backup_filename(prefix)
    base_name = f"{prefix}-{timestamp}"
    final_dump = require_path_within(backup_dir, backup_dir / f"{base_name}.dump")
    tmp_dump = require_path_within(backup_dir, backup_dir / f"{base_name}.dump.tmp")
    manifest_path = require_path_within(backup_dir, backup_dir / f"{base_name}.manifest.json")
    if tmp_dump.exists():
        tmp_dump.unlink()

    mode = pg_tools_mode()
    if mode == "docker-compose":
        _backup_postgres_database_docker(database_url, tmp_dump, timeout_seconds)
    else:
        _backup_postgres_database_local(database_url, tmp_dump, timeout_seconds)
    tmp_dump.replace(final_dump)
    counts = postgres_table_counts(database_url)
    manifest = {
        "formatVersion": 1,
        "databaseType": "postgresql",
        "backupFormat": "custom",
        "createdAt": utc_iso(),
        "applicationVersion": application_version,
        "schemaVersion": _read_postgres_schema_version(database_url),
        "postgresqlVersion": _read_postgres_server_version(database_url),
        "toolsMode": mode,
        "fileName": final_dump.name,
        "sha256": sha256_file(final_dump),
        "sizeBytes": final_dump.stat().st_size,
        "tableCounts": counts,
        "sourceSanitized": sanitized_database_identity(database_url),
    }
    write_json_atomic(manifest_path, manifest)
    return {"backupPath": str(final_dump), "manifestPath": str(manifest_path), "manifest": manifest}
