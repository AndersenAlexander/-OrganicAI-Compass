from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from app.services.database_admin import resolve_backend_path
from app.services.legacy_orphan_archive import summarize_legacy_orphan_archive


def _latest_archive(directory: str | Path) -> Path:
    archive_dir = resolve_backend_path(directory)
    archives = sorted(archive_dir.glob("organicai-orphan-messages-*.db"), key=lambda item: item.stat().st_mtime)
    if not archives:
        raise FileNotFoundError("No legacy orphan archive found.")
    return archives[-1]


def _show_single_message(archive: Path, message_id_hash: str) -> dict[str, str | None]:
    connection = sqlite3.connect(archive.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        evidence = connection.execute(
            "SELECT message_id FROM orphan_message_index WHERE message_id_hash = ?",
            (message_id_hash,),
        ).fetchone()
        if evidence is None:
            raise LookupError("No archived message matches the supplied hash.")
        row = connection.execute(
            """
            SELECT m.role, m.content, m.created_at
            FROM orphan_messages m
            WHERE m.id = ?
            LIMIT 1
            """,
            (evidence["message_id"],),
        ).fetchone()
        if row is None:
            raise LookupError("Archived message row is unavailable.")
        return {"role": row["role"], "content": row["content"], "createdAt": row["created_at"]}
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a local legacy orphan archive without exposing bulk content.")
    parser.add_argument("--archive")
    parser.add_argument("--archive-dir", default="./backups/legacy-orphans")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--message-id-hash")
    parser.add_argument("--show-content", action="store_true")
    args = parser.parse_args()
    try:
        archive = resolve_backend_path(args.archive) if args.archive else _latest_archive(args.archive_dir)
        if args.message_id_hash:
            if not args.show_content:
                raise ValueError("--show-content is required for single-message content inspection.")
            message = _show_single_message(archive, args.message_id_hash)
            print("WARNING: displaying one archived local message in this terminal only. Do not paste this output into logs.")
            print(json.dumps(message, indent=2, sort_keys=True))
            return 0
        summary = summarize_legacy_orphan_archive(archive)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "success", **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
