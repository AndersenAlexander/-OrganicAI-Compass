"""harden market-to-application provenance and evidence safety

Revision ID: 0007_market_application_provenance
Revises: 0006_evidence_calibration_loop
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_market_application_provenance"
down_revision = "0006_evidence_calibration_loop"
branch_labels = None
depends_on = None


def _add_columns(table: str, columns: dict[str, sa.Column]) -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns(table)}
    missing = [column for name, column in columns.items() if name not in existing]
    if missing:
        with op.batch_alter_table(table) as batch_op:
            for column in missing:
                batch_op.add_column(column)


def _indexes(table: str, names: dict[str, list[str]]) -> None:
    bind = op.get_bind()
    existing = {index["name"] for index in sa.inspect(bind).get_indexes(table)}
    for name, columns in names.items():
        if name not in existing:
            op.create_index(name, table, columns)


def upgrade() -> None:
    _add_columns(
        "labour_market_providers",
        {
            "last_successful_fetch": sa.Column("last_successful_fetch", sa.DateTime(), nullable=True),
            "freshness_timestamp": sa.Column("freshness_timestamp", sa.DateTime(), nullable=True),
            "error_state": sa.Column("error_state", sa.Text(), nullable=False, server_default=""),
            "fallback_state": sa.Column("fallback_state", sa.String(length=60), nullable=False, server_default="none"),
            "coverage_notes": sa.Column("coverage_notes", sa.Text(), nullable=False, server_default=""),
        },
    )
    _indexes("labour_market_providers", {
        "ix_labour_market_providers_last_successful_fetch": ["last_successful_fetch"],
        "ix_labour_market_providers_freshness_timestamp": ["freshness_timestamp"],
    })

    _add_columns(
        "job_postings",
        {
            "canonical_job_key": sa.Column("canonical_job_key", sa.String(length=255), nullable=False, server_default=""),
            "source_provenance_json": sa.Column("source_provenance_json", sa.JSON(), nullable=False, server_default="[]"),
        },
    )
    _indexes("job_postings", {"ix_job_postings_canonical_job_key": ["canonical_job_key"]})

    _add_columns("market_radar_preferences", {"role_title": sa.Column("role_title", sa.String(length=255), nullable=False, server_default="")})

    _add_columns(
        "market_signal_runs",
        {
            "source_window_start": sa.Column("source_window_start", sa.DateTime(), nullable=True),
            "source_window_end": sa.Column("source_window_end", sa.DateTime(), nullable=True),
            "sample_count": sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
            "coverage_sufficient": sa.Column("coverage_sufficient", sa.Boolean(), nullable=False, server_default=sa.false()),
        },
    )
    _add_columns(
        "market_signal_results",
        {
            "coverage_label": sa.Column("coverage_label", sa.String(length=160), nullable=False, server_default="Insufficient coverage"),
            "source_window_json": sa.Column("source_window_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )

    _add_columns(
        "job_analyses",
        {
            "source_type": sa.Column("source_type", sa.String(length=80), nullable=False, server_default="pasted_job_ad"),
            "source_metadata_json": sa.Column("source_metadata_json", sa.JSON(), nullable=False, server_default="{}"),
            "user_confirmed": sa.Column("user_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
            "user_confirmed_at": sa.Column("user_confirmed_at", sa.DateTime(), nullable=True),
        },
    )
    _indexes("job_analyses", {"ix_job_analyses_source_type": ["source_type"], "ix_job_analyses_user_confirmed": ["user_confirmed"]})

    _add_columns(
        "job_analysis_versions",
        {
            "version_kind": sa.Column("version_kind", sa.String(length=60), nullable=False, server_default="extraction"),
            "edited_by_user": sa.Column("edited_by_user", sa.Boolean(), nullable=False, server_default=sa.false()),
        },
    )

    _add_columns(
        "job_requirements",
        {
            "extracted_requirement_type": sa.Column("extracted_requirement_type", sa.String(length=60), nullable=False, server_default="unclear"),
            "extracted_requirement_category": sa.Column("extracted_requirement_category", sa.String(length=80), nullable=False, server_default="skills"),
            "user_edited": sa.Column("user_edited", sa.Boolean(), nullable=False, server_default=sa.false()),
            "confirmed_at": sa.Column("confirmed_at", sa.DateTime(), nullable=True),
            "confirmed_by": sa.Column("confirmed_by", sa.String(), nullable=True),
            "confirmation_action": sa.Column("confirmation_action", sa.String(length=60), nullable=False, server_default="pending_review"),
            "extraction_timestamp": sa.Column("extraction_timestamp", sa.DateTime(), nullable=True),
            "job_analysis_version": sa.Column("job_analysis_version", sa.String(length=80), nullable=False, server_default="job-analysis-v1"),
        },
    )
    _indexes("job_requirements", {"ix_job_requirements_user_edited": ["user_edited"], "ix_job_requirements_confirmed_by": ["confirmed_by"]})

    _add_columns(
        "job_readiness_results",
        {
            "supported_count": sa.Column("supported_count", sa.Integer(), nullable=False, server_default="0"),
            "partial_count": sa.Column("partial_count", sa.Integer(), nullable=False, server_default="0"),
            "missing_count": sa.Column("missing_count", sa.Integer(), nullable=False, server_default="0"),
            "outdated_count": sa.Column("outdated_count", sa.Integer(), nullable=False, server_default="0"),
            "unknown_count": sa.Column("unknown_count", sa.Integer(), nullable=False, server_default="0"),
            "unsupported_claims_risk_json": sa.Column("unsupported_claims_risk_json", sa.JSON(), nullable=False, server_default="[]"),
            "source_limitations_json": sa.Column("source_limitations_json", sa.JSON(), nullable=False, server_default="[]"),
            "formula_version": sa.Column("formula_version", sa.String(length=80), nullable=False, server_default="job-readiness-v2"),
        },
    )

    _add_columns("job_requirement_evidence_matches", {"evidence_status": sa.Column("evidence_status", sa.String(length=40), nullable=False, server_default="NOT ASSESSED")})
    _indexes("job_requirement_evidence_matches", {"ix_job_requirement_evidence_matches_evidence_status": ["evidence_status"]})

    _add_columns(
        "application_documents",
        {
            "source_profile_version": sa.Column("source_profile_version", sa.String(length=100), nullable=False, server_default="profile-current"),
            "source_job_analysis_version": sa.Column("source_job_analysis_version", sa.String(length=100), nullable=False, server_default=""),
            "source_evidence_version": sa.Column("source_evidence_version", sa.String(length=100), nullable=False, server_default="evidence-passport-v1"),
            "user_edited_at": sa.Column("user_edited_at", sa.DateTime(), nullable=True),
        },
    )
    _add_columns(
        "application_document_versions",
        {
            "version_kind": sa.Column("version_kind", sa.String(length=60), nullable=False, server_default="generated"),
            "source_profile_version": sa.Column("source_profile_version", sa.String(length=100), nullable=False, server_default="profile-current"),
            "source_job_analysis_version": sa.Column("source_job_analysis_version", sa.String(length=100), nullable=False, server_default=""),
            "source_evidence_version": sa.Column("source_evidence_version", sa.String(length=100), nullable=False, server_default="evidence-passport-v1"),
            "evidence_lock_state": sa.Column("evidence_lock_state", sa.String(length=80), nullable=False, server_default="needs_review"),
            "edited_by_user": sa.Column("edited_by_user", sa.Boolean(), nullable=False, server_default=sa.false()),
        },
    )
    _add_columns(
        "document_claims",
        {
            "support_state": sa.Column("support_state", sa.String(length=40), nullable=False, server_default="NEEDS_REVIEW"),
            "generated_by": sa.Column("generated_by", sa.String(length=80), nullable=False, server_default="deterministic_template"),
            "edited_by_user": sa.Column("edited_by_user", sa.Boolean(), nullable=False, server_default=sa.false()),
            "claim_version": sa.Column("claim_version", sa.Integer(), nullable=False, server_default="1"),
        },
    )
    _indexes("document_claims", {"ix_document_claims_support_state": ["support_state"]})

    _add_columns(
        "job_applications",
        {
            "confirmed_job_analysis_version": sa.Column("confirmed_job_analysis_version", sa.String(length=100), nullable=False, server_default=""),
            "readiness_snapshot_json": sa.Column("readiness_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
            "evidence_snapshot_json": sa.Column("evidence_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )


def downgrade() -> None:
    # This migration is intentionally additive. Dropping these columns would
    # destroy provenance for existing applications, so rollback is a no-op.
    pass
