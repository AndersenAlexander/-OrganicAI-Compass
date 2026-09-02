from __future__ import annotations

import time
from collections import OrderedDict
from datetime import datetime
from app.core.time import utc_now_naive
from typing import Any

TTL_SECONDS = 30 * 60
MAX_ENTRIES = 256

_latest_turns: OrderedDict[tuple[str, str], tuple[float, dict[str, Any]]] = OrderedDict()


def _purge_expired(now: float | None = None) -> None:
    current_time = now if now is not None else time.monotonic()
    expired = [key for key, (created, _) in _latest_turns.items() if current_time - created > TTL_SECONDS]
    for key in expired:
        _latest_turns.pop(key, None)
    while len(_latest_turns) > MAX_ENTRIES:
        _latest_turns.popitem(last=False)


def save_latest_voice_turn(*, user_id: str, elevenlabs_conversation_id: str, payload: dict[str, Any]) -> None:
    _purge_expired()
    key = (user_id, elevenlabs_conversation_id)
    _latest_turns[key] = (
        time.monotonic(),
        {
            **payload,
            "createdAt": payload.get("createdAt") or utc_now_naive().isoformat(),
        },
    )
    _latest_turns.move_to_end(key)
    _purge_expired()


def get_latest_voice_turn(*, user_id: str, elevenlabs_conversation_id: str) -> dict[str, Any] | None:
    _purge_expired()
    key = (user_id, elevenlabs_conversation_id)
    item = _latest_turns.get(key)
    if item is None:
        return None
    _latest_turns.move_to_end(key)
    return dict(item[1])


def clear_latest_voice_turns() -> None:
    _latest_turns.clear()

