from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from typing import Iterator

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransaction


logger = logging.getLogger("organicai.database")
_CONTEXT_KEY = "organicai_transaction_observability_context"
_ACTIVE_KEY = "organicai_transaction_observability_active"
_REQUEST_CONTEXT: ContextVar[dict[str, object] | None] = ContextVar(
    "organicai_database_request_context",
    default=None,
)


def _emit(event_type: str, active: dict[str, object], **extra: object) -> None:
    logger.info(json.dumps({"event_type": event_type, **active, **extra}, separators=(",", ":")))


def _connection_identifier(connection: Connection) -> str:
    pooled = connection.connection
    driver_connection = getattr(pooled, "driver_connection", pooled)
    return hex(id(driver_connection))


def _begin_observation(session: Session, connection: Connection | None = None) -> dict[str, object] | None:
    context = session.info.get(_CONTEXT_KEY) or _REQUEST_CONTEXT.get()
    if not isinstance(context, dict):
        return None
    active = session.info.get(_ACTIVE_KEY)
    if isinstance(active, dict):
        if connection is not None and active.get("connection_identifier") is None:
            active["connection_identifier"] = _connection_identifier(connection)
        return active
    active = {
        **context,
        "session_identifier": hex(id(session)),
        "connection_identifier": _connection_identifier(connection) if connection is not None else None,
        "write_transaction": False,
        "database_operation": "READ",
        "started_perf_counter": perf_counter(),
    }
    session.info[_ACTIVE_KEY] = active
    _emit("DB_TX_BEGIN", {key: value for key, value in active.items() if key != "started_perf_counter"})
    return active


def _finish_observation(session: Session, event_type: str) -> None:
    active = session.info.pop(_ACTIVE_KEY, None)
    if not isinstance(active, dict):
        return
    started = float(active.pop("started_perf_counter", perf_counter()))
    duration_ms = max(0, int((perf_counter() - started) * 1000))
    _emit(event_type, active, duration_ms=duration_ms)
    _emit("DB_TX_DURATION_MS", active, duration_ms=duration_ms, outcome=event_type)


@event.listens_for(Session, "after_begin")
def _after_begin(session: Session, transaction: SessionTransaction, connection: Connection) -> None:
    if transaction.parent is None:
        _begin_observation(session, connection)


@event.listens_for(Session, "before_commit")
def _before_commit(session: Session) -> None:
    active = _begin_observation(session)
    if active is not None:
        safe_active = {key: value for key, value in active.items() if key != "started_perf_counter"}
        _emit("DB_TX_COMMIT_START", safe_active)


@event.listens_for(Session, "before_flush")
def _before_flush(session: Session, _flush_context: object, _instances: object) -> None:
    active = _begin_observation(session)
    if active is not None:
        active["write_transaction"] = True
        active["database_operation"] = "ORM_FLUSH"


@event.listens_for(Session, "after_commit")
def _after_commit(session: Session) -> None:
    _finish_observation(session, "DB_TX_COMMIT_OK")


@event.listens_for(Session, "after_rollback")
def _after_rollback(session: Session) -> None:
    _finish_observation(session, "DB_TX_ROLLBACK")


@contextmanager
def observe_session_transactions(session: Session, *, request_id: str, operation_name: str) -> Iterator[None]:
    previous = session.info.get(_CONTEXT_KEY)
    session.info[_CONTEXT_KEY] = {
        "request_id": request_id,
        "operation_name": operation_name,
    }
    try:
        yield
    finally:
        if previous is None:
            session.info.pop(_CONTEXT_KEY, None)
        else:
            session.info[_CONTEXT_KEY] = previous


@contextmanager
def observe_request_transactions(*, request_id: str, route: str, method: str) -> Iterator[None]:
    token = _REQUEST_CONTEXT.set(
        {
            "request_id": request_id,
            "operation_name": f"{method} {route}",
        }
    )
    try:
        yield
    finally:
        _REQUEST_CONTEXT.reset(token)
