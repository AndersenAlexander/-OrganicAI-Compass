# Deletion Suppression Ledger

Technical draft - requires legal review before public deployment.

`deletion_suppression_ledger` records irreversible deletion/tombstone instructions without storing raw subject identifiers. Entries contain:

- Subject type
- Hashed subject identifier
- Action
- Request ID
- Previous entry hash
- Entry hash
- Metadata
- Timestamp

The ledger is append-only in application behavior. Restored databases must apply the ledger before restored user-facing services are resumed.
