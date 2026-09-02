# Legacy Orphan Archive

Task 11.3 creates a local-only SQLite archive for legacy `messages` rows whose `conversation_id` no longer has a matching `conversations.id`.

## Archive Policy

- The original database remains read-only during archive creation.
- The archive database stores complete original `messages` rows, including message content, because the active database cleanup must be lossless.
- Normal reports, manifests, UI text, and API responses must not include message content, raw message IDs, raw conversation IDs, tokens, passwords, or database URLs.
- The archive is not exposed through a frontend view, backend endpoint, download endpoint, RAG index, analytics pipeline, model-training flow, or release bundle.
- Archive access is manual administrative access only.
- Retention and privacy decisions remain pending Task 12 privacy work.

## Task 11.3 Artifact

Generated archive pattern:

```text
backend/backups/legacy-orphans/organicai-orphan-messages-<timestamp>.db
backend/backups/legacy-orphans/organicai-orphan-messages-<timestamp>.manifest.json
```

Generated verification report:

```text
reports/database-integrity/legacy-orphan-archive-verification.json
```

Task 11.3 verification result:

- Archived rows: 156
- Source orphan ID match: passed
- SQLite integrity: ok
- Duplicate archived rows: 0
- Unexpected non-orphan rows: 0
- Manifest contains message content: no

## Administrative Inspection

Summary-only inspection:

```powershell
python -m app.scripts.inspect_legacy_orphan_archive --summary
```

Single-message local inspection requires an explicit hash and `--show-content`:

```powershell
python -m app.scripts.inspect_legacy_orphan_archive --message-id-hash <hash> --show-content
```

The content inspection mode is local-terminal only and must not be copied into logs or reports.
