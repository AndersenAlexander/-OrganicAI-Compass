# Recommendation Provenance

Status: implemented.

Week 6 outputs expose provenance through shared decision-support snapshots and `/api/v1/recommendation-provenance/{target_type}/{target_id}`.

Supported targets:

- adaptive experiment recommendations;
- transition simulations;
- robustness runs.

Each trace includes:

- target ID and type;
- profile ID where applicable;
- input snapshot;
- decision-support snapshot;
- algorithm version;
- rule-set version;
- source versions;
- weights or objective configuration where applicable;
- limitations;
- change explanation.

Historical results are not silently recalculated. Recalculation creates a new run or simulation so previous assumptions remain auditable.
