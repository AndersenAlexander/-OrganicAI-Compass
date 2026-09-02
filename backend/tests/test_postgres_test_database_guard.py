from __future__ import annotations

import pytest

from app.scripts.prepare_postgres_test_database import (
    PostgresTestDatabaseError,
    is_disposable_database_name,
    target_from_url,
)


def test_postgres_test_database_guard_rejects_protected_database():
    with pytest.raises(PostgresTestDatabaseError):
        target_from_url("postgresql+psycopg2://user:secret@127.0.0.1:5432/organicai_app")


def test_postgres_test_database_guard_allows_disposable_database():
    target = target_from_url("postgresql+psycopg2://user:secret@127.0.0.1:5432/organicai_task13b03_test")
    assert target.database_name == "organicai_task13b03_test"
    assert is_disposable_database_name(target.database_name) is True
    assert "secret" not in target.redacted_url


def test_postgres_test_database_guard_rejects_malformed_url():
    with pytest.raises(PostgresTestDatabaseError):
        target_from_url("not a url")


def test_postgres_test_database_guard_rejects_non_postgresql_url():
    with pytest.raises(PostgresTestDatabaseError):
        target_from_url("sqlite:///organicai_task13b03_test.db")


def test_postgres_test_database_guard_rejects_missing_database_name():
    with pytest.raises(PostgresTestDatabaseError):
        target_from_url("postgresql+psycopg2://user:secret@127.0.0.1:5432")
