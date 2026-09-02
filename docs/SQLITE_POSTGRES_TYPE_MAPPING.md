# SQLite to PostgreSQL Type Mapping

The migration service uses SQLAlchemy metadata and Core inserts. It does not call business services.

Policy:

- Booleans: `0/1` and `true/false` are converted to Python `bool`. Invalid values fail strict mode.
- Datetime: ISO-like strings are parsed. Ambiguous values fail strict mode.
- JSON: JSON strings are decoded for JSON columns. Invalid JSON fails strict mode.
- Empty strings and nulls: values are preserved; empty strings are not converted to null.
- IDs: string IDs are copied exactly.
- UUIDs: no PostgreSQL UUID conversion is applied in Task 11.
- Enums: string values are preserved unless a future explicit enum migration is added.

Strict mode is controlled by:

```env
DB_MIGRATION_STRICT=true
DB_MIGRATION_ALLOW_PARTIAL=false
```
