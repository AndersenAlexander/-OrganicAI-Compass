from __future__ import annotations

import faulthandler
import json
import os
import sys
import time
from hashlib import sha256
from typing import Iterator

import pytest

from app.scripts.prepare_postgres_test_database import (
    PostgresTestDatabaseError,
    assert_no_connection_or_worker_leak,
    collect_connection_lifecycle,
    create_postgres_test_engine,
    prepare_postgres_test_database,
    render_connection_url,
    target_from_url,
)


def _is_postgres_test(request: pytest.FixtureRequest) -> bool:
    return "postgres" in request.node.keywords


def _node_application_name(nodeid: str) -> str:
    digest = sha256(nodeid.encode("utf-8")).hexdigest()[:12]
    return f"organicai-pgtest-{digest}"


@pytest.fixture(autouse=True)
def postgres_timeout_and_diagnostics(request: pytest.FixtureRequest) -> Iterator[None]:
    if not _is_postgres_test(request):
        yield
        return

    timeout_seconds = int(os.environ.get("PYTEST_POSTGRES_TIMEOUT_SECONDS", "60"))
    sys.stderr.write(f"\nPOSTGRES_TEST_START nodeid={request.node.nodeid} timeoutSeconds={timeout_seconds}\n")
    faulthandler.dump_traceback_later(timeout_seconds, exit=True, file=sys.stderr)
    started = time.monotonic()
    before = None
    after = None
    database_url = os.environ.get("TEST_POSTGRES_DATABASE_URL", "")
    try:
        if database_url:
            target_from_url(database_url)
            before = collect_connection_lifecycle(database_url)
        yield
    finally:
        faulthandler.cancel_dump_traceback_later()
        duration = round(time.monotonic() - started, 3)
        if database_url:
            try:
                after = collect_connection_lifecycle(database_url)
            except Exception as exc:  # diagnostics must not hide the primary test result
                after = {"error": exc.__class__.__name__}
        sys.stderr.write(
            "POSTGRES_TEST_END "
            + json.dumps(
                {
                    "nodeid": request.node.nodeid,
                    "durationSeconds": duration,
                    "before": before,
                    "after": after,
                },
                sort_keys=True,
            )
            + "\n"
        )


@pytest.fixture
def postgres_database_url() -> str:
    database_url = os.environ.get("TEST_POSTGRES_DATABASE_URL", "")
    if not database_url:
        pytest.skip("TEST_POSTGRES_DATABASE_URL is not configured.")
    try:
        target = target_from_url(database_url)
    except PostgresTestDatabaseError as exc:
        pytest.fail(str(exc))
    return render_connection_url(target.url)


@pytest.fixture
def prepared_postgres_database_url(postgres_database_url: str) -> str:
    prepare_postgres_test_database(
        postgres_database_url,
        database_name=None,
        drop_recreate=True,
        migrate=True,
        validate_schema=False,
        downgrade_reupgrade=False,
    )
    return postgres_database_url


@pytest.fixture
def postgres_test_engine(request: pytest.FixtureRequest, prepared_postgres_database_url: str):
    engine = create_postgres_test_engine(
        prepared_postgres_database_url,
        application_name=_node_application_name(request.node.nodeid),
    )
    try:
        yield engine
    finally:
        engine.dispose()
        assert_no_connection_or_worker_leak(prepared_postgres_database_url)
