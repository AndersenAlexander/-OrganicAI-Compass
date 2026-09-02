from __future__ import annotations

from dataclasses import asdict, dataclass


PROCESSING_CLASSES = {
    "essential-service",
    "account-security",
    "user-requested-feature",
    "optional-personalization",
    "optional-research",
    "optional-analytics",
    "legal-or-security-retention",
    "unknown-requires-review",
}

TABLE_CLASSES = {
    "personal-user-data",
    "shared-system-data",
    "demo-data",
    "research-data",
    "security-data",
    "operational-data",
    "provider-linkage",
    "anonymous-aggregate",
    "legacy-evidence",
}

ORIGINS = {
    "provided-by-user",
    "observed",
    "generated-by-system",
    "inferred",
    "derived",
    "provider-returned",
    "security-generated",
}

SENSITIVITIES = {
    "standard",
    "confidential",
    "potentially-sensitive",
    "special-category-possible",
    "security-secret",
}


@dataclass(frozen=True)
class PersonalDataCategory:
    key: str
    title: str
    description: str
    tables: list[str]
    ownership_paths: list[str]
    purposes: list[str]
    processing_classification: str
    data_origin: str
    sensitivity: str
    retention_policy_key: str
    export_behavior: str
    deletion_behavior: str
    research_behavior: str
    provider_behavior: str

    def to_dict(self) -> dict:
        return asdict(self)


SECURITY_SECRET_FIELDS = {
    "hashed_password",
    "refresh_token_hash",
    "token_hash",
    "request_context_hash",
    "ip_hash",
    "user_agent_hash",
    "external_object_id_hash",
    "encryption_key_hash",
    "entry_hash",
    "previous_entry_hash",
}
