from __future__ import annotations

from app.config import get_settings
from app.database import check_database_connection, get_database_migration_status
from app.services.database_integrity import verify_database_integrity


def main() -> int:
    settings = get_settings()
    connection = check_database_connection()
    if not settings.database_url:
        print("Database configuration error: DATABASE_URL is missing.")
        return 1
    print(f"Database dialect: {connection.dialect}")
    print(f"Connection: {'reachable' if connection.reachable else 'unreachable'}")
    if not connection.reachable:
        return 2
    migration = get_database_migration_status(settings)
    print(f"Migration revision: {migration.current_revision or 'missing'}")
    print(f"Migration head: {migration.head_revision or 'unknown'}")
    print(f"Migration state: {migration.migration_state}")
    print(f"Pool: {'enabled' if connection.dialect != 'sqlite' else 'disabled for sqlite'}")
    integrity = verify_database_integrity()
    print(f"Integrity: {'passed' if integrity['status'] == 'passed' else 'failed'}")
    print(f"Environment: {settings.app_env}")
    if migration.migration_state != "current" and settings.db_require_migration_head:
        return 3
    if integrity["status"] != "passed":
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
