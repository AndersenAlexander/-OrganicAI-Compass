from __future__ import annotations

from app.database import Base, import_models
from app.privacy.categories import PersonalDataCategory


def _tables() -> set[str]:
    import_models()
    return set(Base.metadata.tables)


def classify_table(table_name: str) -> str:
    if table_name in {"users", "diagnostics", "profiles", "conversations", "messages", "fear_transforms", "roadmaps"}:
        return "personal-user-data"
    if table_name.startswith(("auth_", "account_tokens")):
        return "security-data"
    if table_name.startswith(("privacy_", "data_", "deletion_suppression", "retention_")):
        return "security-data"
    if table_name.startswith("external_provider"):
        return "provider-linkage"
    if table_name.startswith("research_") or "research" in table_name:
        return "research-data"
    if table_name.startswith(("learning_provider", "learning_resource", "external_provider_cache", "labour_market_provider", "job_posting", "job_location", "job_classification", "job_skill", "job_language", "esco_")):
        return "shared-system-data"
    if table_name.startswith(("rag_", "market_signal", "skill_normalisation", "fairness_audit", "recommendation_system_card")):
        return "operational-data"
    if table_name in {"assessment_definitions", "assessment_modules", "assessment_items", "assessment_options", "career_role_templates", "career_experiment_templates", "career_experiment_rubrics", "career_experiment_criteria", "support_programmes", "support_programme_versions", "support_rules", "support_opportunity_links"}:
        return "shared-system-data"
    return "personal-user-data"


TABLE_REGISTRY: dict[str, str] = {}


def table_registry() -> dict[str, str]:
    tables = _tables()
    registry = {table: classify_table(table) for table in sorted(tables)}
    TABLE_REGISTRY.clear()
    TABLE_REGISTRY.update(registry)
    return registry


def personal_data_categories() -> list[PersonalDataCategory]:
    registry = table_registry()

    def matching(*prefixes: str, exact: set[str] | None = None) -> list[str]:
        exact = exact or set()
        return sorted(table for table in registry if table in exact or table.startswith(prefixes))

    return [
        PersonalDataCategory(
            key="account-profile",
            title="Account profile",
            description="Account identity, demo flags, email verification state, and account lifecycle state.",
            tables=["users"],
            ownership_paths=["users.id"],
            purposes=["account authentication", "service delivery", "account security"],
            processing_classification="essential-service",
            data_origin="provided-by-user",
            sensitivity="confidential",
            retention_policy_key="account-lifecycle",
            export_behavior="include sanitized account fields; exclude password hashes and auth secrets",
            deletion_behavior="tombstone or delete through controlled account deletion",
            research_behavior="excluded unless explicitly pseudonymized through research consent",
            provider_behavior="local only",
        ),
        PersonalDataCategory(
            key="auth-security",
            title="Authentication and security records",
            description="Sessions, account tokens, auth events, privacy ledgers, provider hashes, and suppression records.",
            tables=matching("auth_", "account_tokens", "privacy_", "data_", "deletion_suppression", "retention_", "external_provider"),
            ownership_paths=["user_id where present", "hashed/pseudonymous subject where account deletion completed"],
            purposes=["session security", "fraud prevention", "legal-or-security retention"],
            processing_classification="account-security",
            data_origin="security-generated",
            sensitivity="security-secret",
            retention_policy_key="security-ledger",
            export_behavior="include event summaries only; never export token hashes, password hashes, IP hashes, or provider object hashes",
            deletion_behavior="retain minimal append-only security proof; revoke active sessions and expire tokens",
            research_behavior="excluded",
            provider_behavior="provider object hashes only, no secrets",
        ),
        PersonalDataCategory(
            key="diagnostic-profile",
            title="Diagnostics and profiles",
            description="Questionnaire answers, generated profile, feedback, talent-map data, and inferred collaboration style.",
            tables=matching("diagnostic", "profile", "fear_", exact={"profiles", "diagnostics", "fear_transforms"}),
            ownership_paths=["diagnostics.user_id", "profiles.user_id", "profile_id to profiles.id"],
            purposes=["requested diagnostic", "profile generation", "personal roadmap"],
            processing_classification="user-requested-feature",
            data_origin="provided-by-user",
            sensitivity="special-category-possible",
            retention_policy_key="account-content",
            export_behavior="include owned records; exclude security fields and hashes",
            deletion_behavior="delete category after dependency preview",
            research_behavior="only with active research opt-in and pseudonymization",
            provider_behavior="may be sent to configured AI providers when a feature is used",
        ),
        PersonalDataCategory(
            key="conversation-history",
            title="Conversation history",
            description="Persisted account-history conversations and messages, including text/voice message transcript rows.",
            tables=["conversations", "messages"],
            ownership_paths=["conversations.user_id", "messages.conversation_id to conversations.id"],
            purposes=["AI coach conversation", "history reload", "continuity"],
            processing_classification="optional-personalization",
            data_origin="provided-by-user",
            sensitivity="special-category-possible",
            retention_policy_key="conversation-history",
            export_behavior="include account-history conversations only",
            deletion_behavior="delete owned conversations/messages; ephemeral turns are never inserted",
            research_behavior="excluded unless research opt-in; ephemeral excluded always",
            provider_behavior="OpenAI/ElevenLabs processing may occur when features are used",
        ),
        PersonalDataCategory(
            key="roadmaps-recommendations-learning",
            title="Roadmaps, recommendations and learning plans",
            description="Generated plans, recommendations, learning preferences, progress, and adaptation events.",
            tables=matching("roadmap", "recommendation", "learning_", exact={"roadmaps"}),
            ownership_paths=["user_id where present", "profile_id to profiles.id", "roadmap_id to roadmaps.id"],
            purposes=["requested recommendations", "learning planning", "roadmap adaptation"],
            processing_classification="user-requested-feature",
            data_origin="generated-by-system",
            sensitivity="potentially-sensitive",
            retention_policy_key="account-content",
            export_behavior="include owned records",
            deletion_behavior="delete category after dependency preview",
            research_behavior="only with active research opt-in and pseudonymization",
            provider_behavior="may include provider-returned metadata without secrets",
        ),
        PersonalDataCategory(
            key="career-application-research",
            title="Career, application and research modules",
            description="Assessment, career resilience, interview, market application, innovation, originality and research records.",
            tables=matching("assessment", "career_", "job_", "application_", "document_", "interview", "mock_", "offer_", "star_", "browser_", "advisor_", "innovation_", "adaptive_", "originality_", "research_", "market_", "master_", "skill_", "support_"),
            ownership_paths=["user_id where present", "profile_id to profiles.id", "participant pseudonym where research data"],
            purposes=["requested career/application features", "optional research"],
            processing_classification="user-requested-feature",
            data_origin="provided-by-user",
            sensitivity="special-category-possible",
            retention_policy_key="account-content",
            export_behavior="include owned product records with security fields and hashes excluded; research export uses separate pseudonymous rules",
            deletion_behavior="delete owned product records; research withdrawal handles research linkage",
            research_behavior="requires active opt-in and pseudonymous subject IDs",
            provider_behavior="provider processing tracked when persistent provider objects exist",
        ),
        PersonalDataCategory(
            key="provider-operational",
            title="Provider and operational metadata",
            description="RAG runs, external provider cache, market provider data, sync cursors and operational metadata.",
            tables=matching("rag_", "external_provider_cache", "labour_market_", "market_signal", "esco_"),
            ownership_paths=["user_id/profile_id where present; otherwise shared operational record"],
            purposes=["service operation", "retrieval quality", "provider synchronization"],
            processing_classification="essential-service",
            data_origin="observed",
            sensitivity="standard",
            retention_policy_key="operational-logs",
            export_behavior="include only user-linked summaries; exclude embeddings, hashes, and shared provider cache",
            deletion_behavior="delete or unlink user-linked operational rows where safe",
            research_behavior="aggregated only after review",
            provider_behavior="no API keys or provider secrets",
        ),
    ]


def table_category_map() -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {table: [] for table in table_registry()}
    for category in personal_data_categories():
        for table in category.tables:
            if table in mapping:
                mapping[table].append(category.key)
    return mapping


def user_inventory_response() -> dict:
    categories = [category.to_dict() for category in personal_data_categories()]
    return {
        "principles": [
            "purpose limitation",
            "data minimization",
            "storage limitation",
            "accuracy",
            "integrity and confidentiality",
            "accountability",
            "privacy by default",
            "privacy by design",
        ],
        "categories": categories,
        "technicalDetails": {
            "tableCount": len(table_registry()),
            "classifiedTables": len(table_registry()),
            "legacyOrphanArchive": "excluded from active user exports and deletion",
        },
        "legalReviewRequired": True,
    }
