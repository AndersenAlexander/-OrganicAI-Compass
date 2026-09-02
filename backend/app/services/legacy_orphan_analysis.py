from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.core.time import utc_from_timestamp
from app.services.database_admin import resolve_backend_path, sha256_file, utc_iso, write_json_atomic

ALLOWED_REMEDIATION_ACTIONS = {
    "retain-and-relink",
    "delete-child-after-review",
    "restore-parent-from-backup",
    "set-null-if-semantically-valid",
    "archive-outside-active-schema",
    "ignore-with-explicit-waiver",
    "manual-review",
}

CREATED_AT_COLUMNS = ("created_at", "createdAt", "created", "timestamp")
DEMO_FLAG_COLUMNS = ("is_demo", "demo", "demo_mode")
TEXT_DEMO_COLUMNS = ("source", "origin", "category", "type")
SENSITIVE_PATTERNS = (
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE),
    re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"),
    re.compile(r"\b(?:ssn|social security|passport|iban|bank account|credit card|diagnosis|medical|salary)\b", re.IGNORECASE),
)
DEMO_CONTENT_MARKERS = ("demo", "test", "sample", "mock", "example", "placeholder", "synthetic")
SYSTEM_ROLES = {"assistant", "system", "tool"}
CONSERVATIVE_ARCHIVE_ACTION = "archive-and-remove-from-active-data"


def _connect_readonly(database_path: Path) -> sqlite3.Connection:
    uri = database_path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _table_info(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(f"PRAGMA table_info({_quote_identifier(table)})")]


def _foreign_key_list(conn: sqlite3.Connection, table: str) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in conn.execute(f"PRAGMA foreign_key_list({_quote_identifier(table)})"):
        grouped[int(row["id"])].append(dict(row))
    return grouped


def _row_counts(conn: sqlite3.Connection, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in tables:
        counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table)}").fetchone()[0])
    return counts


def _hash_identifier(salt: bytes, table: str, rowid: Any) -> str:
    digest = hashlib.sha256(salt + f"{table}:{rowid}".encode("utf-8")).hexdigest()
    return digest[:16]


def _hash_value(salt: bytes, namespace: str, value: Any) -> str:
    digest = hashlib.sha256(salt + f"{namespace}:{value}".encode("utf-8", errors="replace")).hexdigest()
    return digest[:16]


def _classify_category(child_table: str, parent_table: str, nullable: bool) -> str:
    joined = f"{child_table} {parent_table}".lower()
    if nullable:
        return "optional nullable-reference anomalies"
    if any(token in joined for token in ("user", "owner", "profile", "diagnostic", "assessment")):
        return "critical ownership orphans"
    if any(token in joined for token in ("conversation", "message", "chat", "history", "voice", "transcript")):
        return "conversation/history orphans"
    if "recommendation" in joined:
        return "recommendation orphans"
    if "roadmap" in joined:
        return "roadmap orphans"
    if any(token in joined for token in ("rag", "research", "demo", "learning", "market", "innovation", "originality")):
        return "research/demo orphans"
    return "critical ownership orphans"


def _risk_for_category(category: str, nullable: bool) -> str:
    if nullable:
        return "medium"
    if category == "critical ownership orphans":
        return "critical"
    if category in {"conversation/history orphans", "recommendation orphans", "roadmap orphans"}:
        return "high"
    return "medium"


def _recommended_action(category: str, nullable: bool) -> str:
    if nullable:
        return "set-null-if-semantically-valid"
    if category == "research/demo orphans":
        return "manual-review"
    return "manual-review"


def _created_at_bounds(conn: sqlite3.Connection, table: str, rowids: list[Any]) -> tuple[str | None, str | None]:
    if not rowids:
        return None, None
    columns = {column["name"] for column in _table_info(conn, table)}
    created_column = next((column for column in CREATED_AT_COLUMNS if column in columns), None)
    if not created_column:
        return None, None
    placeholders = ",".join("?" for _ in rowids)
    query = (
        f"SELECT MIN({_quote_identifier(created_column)}), MAX({_quote_identifier(created_column)}) "
        f"FROM {_quote_identifier(table)} WHERE rowid IN ({placeholders})"
    )
    row = conn.execute(query, rowids).fetchone()
    return (row[0], row[1]) if row else (None, None)


def _likely_demo_data(conn: sqlite3.Connection, table: str, rowids: list[Any]) -> bool:
    if not rowids:
        return False
    columns = {column["name"] for column in _table_info(conn, table)}
    predicates: list[str] = []
    if any(column in columns for column in DEMO_FLAG_COLUMNS):
        predicates.extend(f"COALESCE({_quote_identifier(column)}, 0) = 1" for column in DEMO_FLAG_COLUMNS if column in columns)
    if any(column in columns for column in TEXT_DEMO_COLUMNS):
        predicates.extend(
            f"LOWER(COALESCE({_quote_identifier(column)}, '')) LIKE '%demo%'"
            for column in TEXT_DEMO_COLUMNS
            if column in columns
        )
    if not predicates:
        return False
    placeholders = ",".join("?" for _ in rowids)
    query = f"SELECT COUNT(*) FROM {_quote_identifier(table)} WHERE rowid IN ({placeholders}) AND ({' OR '.join(predicates)})"
    return int(conn.execute(query, rowids).fetchone()[0]) > 0


def _root_cause(category: str, likely_demo: bool, nullable: bool, alembic_present: bool) -> dict[str, Any]:
    signals: list[str] = []
    status = "unknown"
    if not alembic_present:
        status = "probable"
        signals.append("legacy database has no Alembic revision")
    if likely_demo:
        status = "probable"
        signals.append("affected rows match demo/test markers")
    if nullable:
        status = "probable"
        signals.append("nullable reference contains a value without a matching parent")
    if category == "research/demo orphans":
        status = "probable"
        signals.append("relation belongs to experimental or demo-oriented tables")
    if not signals:
        signals.append("requires review against historical backups and application logs")
    return {"status": status, "signals": signals}


def analyze_legacy_orphans(database_path: str | Path) -> dict[str, Any]:
    database = resolve_backend_path(database_path)
    before_sha = sha256_file(database)
    stat = database.stat()
    salt = os.urandom(32)
    conn = _connect_readonly(database)
    try:
        integrity_check = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk_rows = [dict(row) for row in conn.execute("PRAGMA foreign_key_check")]
        tables = _table_names(conn)
        row_counts = _row_counts(conn, tables)
        alembic_revision_present = False
        if "alembic_version" in tables:
            alembic_revision_present = int(conn.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0]) > 0
        table_columns = {table: _table_info(conn, table) for table in tables}
        fk_by_table = {table: _foreign_key_list(conn, table) for table in tables}

        grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
        for row in fk_rows:
            grouped[(row["table"], int(row["fkid"]), row["parent"])].append(row)

        relations: list[dict[str, Any]] = []
        category_counts: Counter[str] = Counter()
        table_counts: Counter[str] = Counter()
        distinct_rows = {(row["table"], row["rowid"]) for row in fk_rows}
        for (child_table, fkid, parent_table), violations in sorted(grouped.items()):
            fk_entries = sorted(fk_by_table.get(child_table, {}).get(fkid, []), key=lambda item: item["seq"])
            child_columns = [entry["from"] for entry in fk_entries]
            parent_columns = [entry["to"] for entry in fk_entries]
            column_info = {column["name"]: column for column in table_columns.get(child_table, [])}
            nullable = any(not bool(column_info.get(column, {}).get("notnull")) for column in child_columns)
            delete_cascade = any(str(entry.get("on_delete", "")).upper() == "CASCADE" for entry in fk_entries)
            affected_rowids = sorted({item["rowid"] for item in violations}, key=lambda value: str(value))
            oldest, newest = _created_at_bounds(conn, child_table, affected_rowids)
            likely_demo = _likely_demo_data(conn, child_table, affected_rowids)
            category = _classify_category(child_table, parent_table, nullable)
            risk = _risk_for_category(category, nullable)
            action = _recommended_action(category, nullable)
            category_counts[category] += len(violations)
            table_counts[child_table] += len(violations)
            relations.append(
                {
                    "childTable": child_table,
                    "childColumn": child_columns[0] if len(child_columns) == 1 else child_columns,
                    "childColumns": child_columns,
                    "parentTable": parent_table,
                    "parentColumn": parent_columns[0] if len(parent_columns) == 1 else parent_columns,
                    "parentColumns": parent_columns,
                    "orphanCount": len(violations),
                    "distinctAffectedRows": len(affected_rowids),
                    "nullableRelationship": nullable,
                    "deleteCascadeConfigured": delete_cascade,
                    "affectedIdentifierHashes": [_hash_identifier(salt, child_table, rowid) for rowid in affected_rowids[:25]],
                    "affectedIdentifierHashLimit": 25,
                    "oldestCreatedAt": oldest,
                    "newestCreatedAt": newest,
                    "likelyDemoData": likely_demo,
                    "category": category,
                    "risk": risk,
                    "recommendedAction": action,
                    "rootCause": _root_cause(category, likely_demo, nullable, alembic_revision_present),
                }
            )
    finally:
        conn.close()

    after_sha = sha256_file(database)
    distinct_affected = len(distinct_rows)
    expected_count = 156
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "database": "backend/organicai.db" if database.name == "organicai.db" else database.name,
        "openedReadOnly": True,
        "sourceProof": {
            "fileSizeBytes": stat.st_size,
            "modifiedTimeUtc": utc_from_timestamp(stat.st_mtime).isoformat(),
            "sha256Before": before_sha,
            "sha256After": after_sha,
            "sha256Matches": before_sha == after_sha,
            "tableCount": len(tables),
            "rowCounts": row_counts,
        },
        "summary": {
            "sqliteIntegrityCheck": integrity_check,
            "expectedLegacyOrphanCount": expected_count,
            "orphanViolations": len(fk_rows),
            "totalOrphanRowsDetected": len(fk_rows),
            "distinctAffectedRows": distinct_affected,
            "countExplanation": (
                "The historical count is the SQLite PRAGMA foreign_key_check violation count; "
                "distinct affected rows are reported separately because one row can violate multiple relationships."
            ),
            "categoryCounts": dict(category_counts),
            "highestRiskRelations": [
                {
                    "childTable": item["childTable"],
                    "parentTable": item["parentTable"],
                    "orphanCount": item["orphanCount"],
                    "risk": item["risk"],
                }
                for item in sorted(relations, key=lambda value: (value["risk"] != "critical", -value["orphanCount"]))[:10]
            ],
            "tablesWithMostIssues": [{"table": table, "orphanCount": count} for table, count in table_counts.most_common(10)],
        },
        "privacy": {
            "rawIdentifiersIncluded": False,
            "rowContentIncluded": False,
            "hashing": "sha256 truncated to 16 hex characters with process-local salt",
        },
        "relations": relations,
    }


def write_legacy_orphan_report(database_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    output = resolve_backend_path(output_path)
    report = analyze_legacy_orphans(database_path)
    write_json_atomic(output, report)
    report["reportPath"] = str(output)
    return report


def _content_bucket(value: str | None) -> str:
    length = len(value or "")
    if length == 0:
        return "0"
    if length <= 80:
        return "1-80"
    if length <= 400:
        return "81-400"
    if length <= 1200:
        return "401-1200"
    return "1201+"


def _classify_message_content(row: sqlite3.Row) -> str:
    content = str(row["content"] or "") if "content" in row.keys() else ""
    role = str(row["role"] or "").strip().lower() if "role" in row.keys() else ""
    input_mode = str(row["input_mode"] or "").strip().lower() if "input_mode" in row.keys() else ""
    combined = f"{role} {input_mode} {content}".lower()
    if not content.strip():
        return "empty"
    if any(marker in combined for marker in DEMO_CONTENT_MARKERS):
        return "demo/test"
    if role in SYSTEM_ROLES:
        return "system-generated"
    if any(pattern.search(content) for pattern in SENSITIVE_PATTERNS):
        return "potentially sensitive personal content"
    if role == "user":
        return "ordinary user content"
    return "unknown"


def _classification_key(classification: str) -> str:
    return {
        "empty": "empty",
        "system-generated": "systemGenerated",
        "demo/test": "demoOrTest",
        "ordinary user content": "ordinaryUserContent",
        "potentially sensitive personal content": "potentiallySensitive",
        "unknown": "unknown",
    }[classification]


def _message_orphan_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    tables = set(_table_names(conn))
    if not {"messages", "conversations"}.issubset(tables):
        return []
    return list(
        conn.execute(
            """
            SELECT m.rowid AS _rowid, m.*
            FROM messages m
            LEFT JOIN conversations c ON m.conversation_id = c.id
            WHERE m.conversation_id IS NOT NULL AND c.id IS NULL
            ORDER BY m.created_at, m.rowid
            """
        )
    )


def get_legacy_orphan_message_rows(database_path: str | Path) -> list[dict[str, Any]]:
    database = resolve_backend_path(database_path)
    conn = _connect_readonly(database)
    try:
        return [dict(row) for row in _message_orphan_rows(conn)]
    finally:
        conn.close()


def _candidate_reference_columns(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []
    for table in _table_names(conn):
        if table in {"messages", "conversations", "alembic_version"}:
            continue
        for column in _table_info(conn, table):
            name = str(column["name"])
            lower = name.lower()
            if "conversation" in lower:
                candidates.append((table, name, "missing-conversation-id"))
            elif lower in {"message_id", "target_id", "source_id"} or "message" in lower:
                candidates.append((table, name, "message-id"))
            elif any(token in lower for token in ("session", "trace", "request")):
                candidates.append((table, name, "session-or-trace"))
    return candidates


def _related_surviving_records(
    conn: sqlite3.Connection,
    *,
    salt: bytes,
    message_id: str,
    missing_conversation_id: str,
    candidates: list[tuple[str, str, str]],
) -> tuple[list[dict[str, Any]], str, str | None, str | None]:
    related: list[dict[str, Any]] = []
    user_values: set[str] = set()
    profile_values: set[str] = set()
    for table, column, match_type in candidates:
        value = missing_conversation_id if match_type == "missing-conversation-id" else message_id
        table_info = _table_info(conn, table)
        table_columns = {item["name"] for item in table_info}
        quoted_table = _quote_identifier(table)
        quoted_column = _quote_identifier(column)
        count = int(conn.execute(f"SELECT COUNT(*) FROM {quoted_table} WHERE {quoted_column} = ?", (value,)).fetchone()[0])
        if count <= 0:
            continue
        owner_status = "not_available"
        owner_hash = None
        profile_hash = None
        if "user_id" in table_columns:
            users = [
                row[0]
                for row in conn.execute(
                    f"SELECT DISTINCT user_id FROM {quoted_table} WHERE {quoted_column} = ? AND user_id IS NOT NULL",
                    (value,),
                )
            ]
            user_values.update(str(item) for item in users)
            if len(users) == 1:
                owner_status = "resolved"
                owner_hash = _hash_value(salt, "users.id", users[0])
            elif len(users) > 1:
                owner_status = "ambiguous"
        if "profile_id" in table_columns:
            profiles = [
                row[0]
                for row in conn.execute(
                    f"SELECT DISTINCT profile_id FROM {quoted_table} WHERE {quoted_column} = ? AND profile_id IS NOT NULL",
                    (value,),
                )
            ]
            profile_values.update(str(item) for item in profiles)
            if len(profiles) == 1:
                profile_hash = _hash_value(salt, "profiles.id", profiles[0])
        related.append(
            {
                "tableHash": _hash_value(salt, "table", table),
                "column": column,
                "matchType": match_type,
                "recordCount": count,
                "ownerStatus": owner_status,
                "ownerHash": owner_hash,
                "profileHash": profile_hash,
            }
        )
    owner_status = "unknown"
    owner_hash = None
    profile_hash = None
    if len(user_values) == 1:
        owner_status = "resolved"
        owner_hash = _hash_value(salt, "users.id", next(iter(user_values)))
    elif len(user_values) > 1:
        owner_status = "ambiguous"
    if len(profile_values) == 1:
        profile_hash = _hash_value(salt, "profiles.id", next(iter(profile_values)))
    return related, owner_status, owner_hash, profile_hash


def _metadata_keys(row: sqlite3.Row) -> list[str]:
    keys: set[str] = set()
    for column in row.keys():
        lower = column.lower()
        if lower in {"content", "id", "conversation_id"}:
            continue
        if "metadata" not in lower and not lower.endswith("_json"):
            continue
        value = row[column]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                keys.update(str(key) for key in parsed.keys())
        elif isinstance(value, dict):
            keys.update(str(key) for key in value.keys())
    return sorted(keys)


def analyze_legacy_orphan_messages(database_path: str | Path) -> dict[str, Any]:
    database = resolve_backend_path(database_path)
    source_sha = sha256_file(database)
    salt = os.urandom(32)
    conn = _connect_readonly(database)
    try:
        rows = _message_orphan_rows(conn)
        candidates = _candidate_reference_columns(conn)
        message_columns = [column["name"] for column in _table_info(conn, "messages")] if "messages" in _table_names(conn) else []
        fk_rows = [dict(row) for row in conn.execute("PRAGMA foreign_key_check")]
        groups: dict[str, dict[str, Any]] = {}
        items: list[dict[str, Any]] = []
        content_counts: Counter[str] = Counter(
            {
                "empty": 0,
                "systemGenerated": 0,
                "demoOrTest": 0,
                "ordinaryUserContent": 0,
                "potentiallySensitive": 0,
                "unknown": 0,
            }
        )
        role_counts: Counter[str] = Counter()
        input_mode_counts: Counter[str] = Counter()
        confidence_counts: Counter[str] = Counter()
        action_counts: Counter[str] = Counter()
        owner_resolved_rows = 0

        for row in rows:
            message_id = str(row["id"])
            missing_conversation_id = str(row["conversation_id"])
            message_hash = _hash_value(salt, "messages.id", message_id)
            missing_hash = _hash_value(salt, "conversations.id", missing_conversation_id)
            parent_exists = (
                int(conn.execute("SELECT COUNT(*) FROM conversations WHERE id = ?", (missing_conversation_id,)).fetchone()[0]) > 0
            )
            related, owner_status, owner_hash, profile_hash = _related_surviving_records(
                conn,
                salt=salt,
                message_id=message_id,
                missing_conversation_id=missing_conversation_id,
                candidates=candidates,
            )
            if owner_status == "resolved":
                owner_resolved_rows += 1
            classification = _classify_message_content(row)
            content_counts[_classification_key(classification)] += 1
            role = str(row["role"] or "unknown") if "role" in row.keys() else "unknown"
            input_mode = str(row["input_mode"] or "unknown") if "input_mode" in row.keys() else "unknown"
            role_counts[role] += 1
            input_mode_counts[input_mode] += 1
            confidence = "exact" if parent_exists else "none"
            proposed_action = "relink-existing-parent" if parent_exists else CONSERVATIVE_ARCHIVE_ACTION
            reason_codes = ["parent-conversation-missing"]
            if not parent_exists:
                reason_codes.extend(["no-proven-parent", "lossless-archive-required", "active-fk-cleanup-needed"])
            confidence_counts[confidence] += 1
            action_counts[proposed_action] += 1
            created_at = row["created_at"] if "created_at" in row.keys() else None
            metadata_keys = _metadata_keys(row)
            item = {
                "messageIdHash": message_hash,
                "missingConversationIdHash": missing_hash,
                "role": role,
                "inputMode": input_mode,
                "createdAt": created_at,
                "updatedAt": row["updated_at"] if "updated_at" in row.keys() else None,
                "ownerStatus": owner_status,
                "ownerHash": owner_hash,
                "profileHash": profile_hash,
                "contentPresent": bool(str(row["content"] or "").strip()) if "content" in row.keys() else False,
                "contentLengthBucket": _content_bucket(str(row["content"] or "") if "content" in row.keys() else ""),
                "contentClassification": classification,
                "metadataKeys": metadata_keys,
                "relatedSurvivingRecordCount": sum(record["recordCount"] for record in related),
                "relatedSurvivingRecords": related[:10],
                "relatedSurvivingRecordLimit": 10,
                "relinkConfidence": confidence,
                "proposedAction": proposed_action,
                "approvedForSimulation": proposed_action == CONSERVATIVE_ARCHIVE_ACTION,
                "approvedForOriginal": False,
                "reasonCodes": reason_codes,
            }
            items.append(item)
            group = groups.setdefault(
                missing_hash,
                {
                    "missingConversationIdHash": missing_hash,
                    "messageCount": 0,
                    "ownerStatusCounts": Counter(),
                    "roleCounts": Counter(),
                    "inputModeCounts": Counter(),
                    "contentClassificationCounts": Counter(),
                    "oldestCreatedAt": created_at,
                    "newestCreatedAt": created_at,
                    "relinkConfidence": confidence,
                    "proposedAction": proposed_action,
                },
            )
            group["messageCount"] += 1
            group["ownerStatusCounts"][owner_status] += 1
            group["roleCounts"][role] += 1
            group["inputModeCounts"][input_mode] += 1
            group["contentClassificationCounts"][_classification_key(classification)] += 1
            if created_at and (group["oldestCreatedAt"] is None or str(created_at) < str(group["oldestCreatedAt"])):
                group["oldestCreatedAt"] = created_at
            if created_at and (group["newestCreatedAt"] is None or str(created_at) > str(group["newestCreatedAt"])):
                group["newestCreatedAt"] = created_at
            if confidence != group["relinkConfidence"]:
                group["relinkConfidence"] = "mixed"
            if proposed_action != group["proposedAction"]:
                group["proposedAction"] = "mixed"
    finally:
        conn.close()

    group_payload = []
    for group in groups.values():
        group_payload.append(
            {
                **{key: value for key, value in group.items() if not isinstance(value, Counter)},
                "ownerStatusCounts": dict(group["ownerStatusCounts"]),
                "roleCounts": dict(group["roleCounts"]),
                "inputModeCounts": dict(group["inputModeCounts"]),
                "contentClassificationCounts": dict(group["contentClassificationCounts"]),
            }
        )
    group_payload.sort(key=lambda item: (-item["messageCount"], str(item["oldestCreatedAt"] or "")))

    orphan_violations = len(fk_rows)
    distinct_rows = len({(row["table"], row["rowid"]) for row in fk_rows})
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "database": "backend/organicai.db" if database.name == "organicai.db" else database.name,
        "sourceHash": source_sha,
        "openedReadOnly": True,
        "summary": {
            "orphanViolations": orphan_violations,
            "distinctAffectedRows": distinct_rows,
            "messageOrphanRows": len(rows),
            "missingConversationGroups": len(groups),
            "ownerResolvedRows": owner_resolved_rows,
            "ownerUnknownRows": len(rows) - owner_resolved_rows,
            "likelyDemoRows": content_counts["demoOrTest"],
            "likelyRealRows": content_counts["ordinaryUserContent"] + content_counts["potentiallySensitive"],
            "relinkCandidateRows": confidence_counts["exact"],
            "provenParentReconstructionCandidateRows": 0,
            "archiveOnlyCandidateRows": action_counts[CONSERVATIVE_ARCHIVE_ACTION],
            "manualReviewCandidateRows": 0,
        },
        "contentClassification": dict(content_counts),
        "roleCounts": dict(role_counts),
        "inputModeCounts": dict(input_mode_counts),
        "confidenceCounts": dict(confidence_counts),
        "actionCounts": dict(action_counts),
        "schema": {
            "messageColumns": message_columns,
            "messageContentColumnPresent": "content" in message_columns,
        },
        "privacy": {
            "rawIdentifiersIncluded": False,
            "messageContentIncluded": False,
            "hashing": "sha256 truncated to 16 hex characters with process-local salt",
            "hashSaltStored": False,
        },
        "groups": group_payload,
        "items": items,
    }


def write_legacy_orphan_forensic_report(database_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    output = resolve_backend_path(output_path)
    report = analyze_legacy_orphan_messages(database_path)
    write_json_atomic(output, report)
    report["reportPath"] = str(output)
    return report


def build_message_remediation_manifest(analysis: dict[str, Any], archive_file: str, source_hash: str | None = None) -> dict[str, Any]:
    actions = []
    for item in analysis.get("items", []):
        proposed_action = item.get("proposedAction") or CONSERVATIVE_ARCHIVE_ACTION
        confidence = item.get("relinkConfidence") or "none"
        approved_for_simulation = proposed_action == CONSERVATIVE_ARCHIVE_ACTION or (
            confidence == "exact" and proposed_action in {"relink-existing-parent", "reconstruct-proven-parent"}
        )
        actions.append(
            {
                "messageIdHash": item["messageIdHash"],
                "missingConversationIdHash": item["missingConversationIdHash"],
                "confidence": confidence,
                "proposedAction": proposed_action,
                "approvedForSimulation": approved_for_simulation,
                "approvedForOriginal": False,
                "reasonCodes": item.get("reasonCodes", []),
            }
        )
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "sourceDatabase": analysis.get("database", "backend/organicai.db"),
        "sourceHash": source_hash or analysis.get("sourceHash"),
        "archiveFile": archive_file,
        "actions": actions,
        "policy": {
            "approvedForOriginalAlwaysFalse": all(action["approvedForOriginal"] is False for action in actions),
            "deletionWithoutArchiveForbidden": True,
            "relinkRequiresExactConfidence": True,
            "manualApprovalRequiredForOriginal": True,
        },
        "privacy": {
            "rawIdentifiersIncluded": False,
            "messageContentIncluded": False,
        },
    }


def build_remediation_plan(analysis: dict[str, Any]) -> dict[str, Any]:
    items = []
    for relation in analysis.get("relations", []):
        action = relation.get("recommendedAction", "manual-review")
        if action not in ALLOWED_REMEDIATION_ACTIONS:
            action = "manual-review"
        items.append(
            {
                "childTable": relation["childTable"],
                "childColumns": relation.get("childColumns") or [relation.get("childColumn")],
                "parentTable": relation["parentTable"],
                "parentColumns": relation.get("parentColumns") or [relation.get("parentColumn")],
                "orphanCount": relation["orphanCount"],
                "distinctAffectedRows": relation.get("distinctAffectedRows", relation["orphanCount"]),
                "risk": relation["risk"],
                "rootCause": relation["rootCause"],
                "recommendedAction": action,
                "allowedActions": sorted(ALLOWED_REMEDIATION_ACTIONS),
                "approvedForSimulation": False,
                "requiresHumanReview": True,
                "notes": "No legacy data changes are authorized by Task 11.1.",
            }
        )
    return {
        "formatVersion": 1,
        "generatedAt": utc_iso(),
        "sourceReport": analysis.get("reportPath") or "reports/database-integrity/legacy-orphans.json",
        "orphanViolations": analysis.get("summary", {}).get("orphanViolations"),
        "distinctAffectedRows": analysis.get("summary", {}).get("distinctAffectedRows"),
        "policy": {
            "createPlaceholderParentsAutomatically": False,
            "legacyDatabaseModificationAuthorized": False,
            "manualApprovalRequired": True,
        },
        "items": items,
    }


def write_remediation_plan(analysis: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    output = resolve_backend_path(output_path)
    plan = build_remediation_plan(analysis)
    write_json_atomic(output, plan)
    plan["reportPath"] = str(output)
    return plan


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(resolve_backend_path(path).read_text(encoding="utf-8"))
