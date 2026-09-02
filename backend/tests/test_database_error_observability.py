from __future__ import annotations

import asyncio
import json
import logging
import sqlite3

from fastapi import Request
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.main import database_exception_handler


def test_database_exception_handler_logs_safe_structured_diagnostics(caplog):
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/auth/demo-login",
            "raw_path": b"/api/auth/demo-login",
            "query_string": b"",
            "headers": [],
            "scheme": "http",
            "server": ("127.0.0.1", 8022),
            "client": ("127.0.0.1", 50000),
            "root_path": "",
        }
    )
    request.state.request_id = "database-observability-test"
    original = sqlite3.OperationalError(
        "database is locked password=never-log-this demo@example.test"
    )

    try:
        raise OperationalError(
            "INSERT INTO auth_sessions (token) VALUES (?)",
            {"token": "never-log-this-token"},
            original,
        )
    except SQLAlchemyError as error:
        with caplog.at_level(logging.ERROR, logger="organicai.database"):
            response = asyncio.run(database_exception_handler(request, error))

    assert response.status_code == 503
    response_body = json.loads(response.body)
    assert response_body["error"] == {
        "code": "DATABASE_UNAVAILABLE",
        "message": "The database is temporarily unavailable.",
        "requestId": "database-observability-test",
        "details": None,
    }

    log_record = json.loads(caplog.records[-1].message)
    assert log_record["event_type"] == "database_exception"
    assert log_record["request_id"] == "database-observability-test"
    assert log_record["route"] == "/api/auth/demo-login"
    assert log_record["method"] == "POST"
    assert log_record["exception_type"].endswith(".OperationalError")
    assert log_record["sqlalchemy_exception_subclass"] == "OperationalError"
    assert log_record["database_operation"] == "INSERT"
    assert log_record["dbapi_exception_type"] == "sqlite3.OperationalError"
    assert log_record["dbapi_error_code"] is None
    assert log_record["duration_ms_at_exception"] is None
    assert log_record["safe_message"] == "database is locked password=[REDACTED] [REDACTED_EMAIL]"
    assert "test_database_exception_handler_logs_safe_structured_diagnostics" in log_record["stack_trace"]

    serialized = caplog.records[-1].message
    assert "never-log-this" not in serialized
    assert "INSERT INTO" not in serialized
    assert "auth_sessions" not in serialized
