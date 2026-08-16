from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(frozen=True)
class SanitizedDatabaseUrl:
    dialect: str
    driver: str | None
    host_configured: bool
    database_configured: bool
    username_configured: bool


def parse_database_url(database_url: str) -> SanitizedDatabaseUrl:
    try:
        url = make_url(database_url)
    except ArgumentError:
        return SanitizedDatabaseUrl(
            dialect="invalid",
            driver=None,
            host_configured=False,
            database_configured=False,
            username_configured=False,
        )
    return SanitizedDatabaseUrl(
        dialect=url.get_backend_name(),
        driver=url.get_driver_name() if url.get_driver_name() != url.get_backend_name() else None,
        host_configured=bool(url.host),
        database_configured=bool(url.database),
        username_configured=bool(url.username),
    )


def redact_database_url(database_url: str) -> str:
    try:
        return str(make_url(database_url).render_as_string(hide_password=True))
    except ArgumentError:
        return "<invalid database url>"


def is_sqlite_url(database_url: str) -> bool:
    return parse_database_url(database_url).dialect == "sqlite"


def is_postgres_url(database_url: str) -> bool:
    return parse_database_url(database_url).dialect in {"postgresql", "postgres"}
