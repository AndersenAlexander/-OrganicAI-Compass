from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.time import utc_now
from app.db.engine import engine


class DatabaseConnectionStatus(BaseModel):
    dialect: str
    reachable: bool
    error_code: str | None = None
    checked_at: datetime = Field(default_factory=utc_now)


def check_database_connection() -> DatabaseConnectionStatus:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return DatabaseConnectionStatus(dialect=engine.dialect.name, reachable=True)
    except SQLAlchemyError as exc:
        return DatabaseConnectionStatus(
            dialect=engine.dialect.name,
            reachable=False,
            error_code=exc.__class__.__name__,
        )
