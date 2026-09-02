from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings
from app.db.engine import engine


@dataclass(frozen=True)
class DatabaseMigrationStatus:
    dialect: str
    reachable: bool
    current_revision: str | None
    head_revision: str | None
    migration_state: str
    multiple_heads: bool = False
    error_code: str | None = None

    @property
    def current(self) -> bool:
        return self.migration_state == "current"


def alembic_config(settings: Settings | None = None) -> Config:
    settings = settings or get_settings()
    backend_dir = Path(__file__).resolve().parents[2]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def get_alembic_head(settings: Settings | None = None) -> tuple[str | None, bool]:
    script = ScriptDirectory.from_config(alembic_config(settings))
    heads = script.get_heads()
    return (heads[0] if len(heads) == 1 else None, len(heads) > 1)


def get_database_migration_status(
    settings: Settings | None = None,
    *,
    database_url: str | None = None,
    bind: Engine | None = None,
) -> DatabaseMigrationStatus:
    settings = settings or get_settings()
    head, multiple_heads = get_alembic_head(settings)
    owns_engine = False
    if bind is not None:
        target_engine = bind
    elif database_url is not None:
        target_engine = create_engine(database_url)
        owns_engine = True
    else:
        target_engine = engine
    try:
        with target_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current = context.get_current_revision()
    except SQLAlchemyError as exc:
        return DatabaseMigrationStatus(
            dialect=target_engine.dialect.name,
            reachable=False,
            current_revision=None,
            head_revision=head,
            migration_state="unreachable",
            multiple_heads=multiple_heads,
            error_code=exc.__class__.__name__,
        )
    finally:
        if owns_engine:
            target_engine.dispose()

    if multiple_heads:
        state = "multiple_heads"
    elif current is None:
        state = "missing"
    elif head is None:
        state = "unknown"
    elif current == head:
        state = "current"
    else:
        state = "behind"
    return DatabaseMigrationStatus(
        dialect=target_engine.dialect.name,
        reachable=True,
        current_revision=current,
        head_revision=head,
        migration_state=state,
        multiple_heads=multiple_heads,
    )
