"""harden collaboration, journal provenance and browser capture review

Revision ID: 0009_collaboration_traceability_extensions
Revises: 0008_interview_outcome_safety
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_collaboration_traceability_extensions"
down_revision = "0008_interview_outcome_safety"
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
        "browser_job_captures",
        {
            "source_type": sa.Column("source_type", sa.String(length=80), nullable=False, server_default="BROWSER_CAPTURE"),
            "confirmed_text": sa.Column("confirmed_text", sa.Text(), nullable=False, server_default=""),
            "user_edited_text": sa.Column("user_edited_text", sa.Boolean(), nullable=False, server_default=sa.false()),
            "confirmed_at": sa.Column("confirmed_at", sa.DateTime(), nullable=True),
            "analysis_version": sa.Column("analysis_version", sa.String(length=80), nullable=False, server_default="not_analysed"),
        },
    )
    _add_columns(
        "advisor_shares",
        {
            "permission_code": sa.Column("permission_code", sa.String(length=40), nullable=False, server_default="READ_ONLY"),
            "excluded_sections_json": sa.Column("excluded_sections_json", sa.JSON(), nullable=False, server_default="[]"),
            "scope_snapshot_json": sa.Column("scope_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
            "version_number": sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        },
    )
    _add_columns(
        "advisor_comments",
        {
            "target_version": sa.Column("target_version", sa.String(length=120), nullable=False, server_default=""),
            "proposal_type": sa.Column("proposal_type", sa.String(length=80), nullable=False, server_default="COMMENT"),
            "proposal_payload_json": sa.Column("proposal_payload_json", sa.JSON(), nullable=False, server_default="{}"),
            "version_number": sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
            "resolved_at": sa.Column("resolved_at", sa.DateTime(), nullable=True),
        },
    )
    _add_columns(
        "career_decision_journal_entries",
        {
            "uncertainty_json": sa.Column("uncertainty_json", sa.JSON(), nullable=False, server_default="{}"),
            "confidence": sa.Column("confidence", sa.String(length=80), nullable=False, server_default=""),
            "reversibility": sa.Column("reversibility", sa.String(length=80), nullable=False, server_default=""),
            "source_attributions_json": sa.Column("source_attributions_json", sa.JSON(), nullable=False, server_default="[]"),
            "system_suggestions_json": sa.Column("system_suggestions_json", sa.JSON(), nullable=False, server_default="[]"),
            "ai_explanations_json": sa.Column("ai_explanations_json", sa.JSON(), nullable=False, server_default="[]"),
            "evidence_observations_json": sa.Column("evidence_observations_json", sa.JSON(), nullable=False, server_default="[]"),
            "adviser_inputs_json": sa.Column("adviser_inputs_json", sa.JSON(), nullable=False, server_default="[]"),
            "user_reasoning": sa.Column("user_reasoning", sa.Text(), nullable=False, server_default=""),
            "linked_experiment_id": sa.Column("linked_experiment_id", sa.String(), nullable=True),
            "interview_id": sa.Column("interview_id", sa.String(), nullable=True),
            "later_outcome": sa.Column("later_outcome", sa.Text(), nullable=False, server_default=""),
            "lessons_learned": sa.Column("lessons_learned", sa.Text(), nullable=False, server_default=""),
        },
    )
    _indexes(
        "browser_job_captures",
        {"ix_browser_job_captures_source_type": ["source_type"], "ix_browser_job_captures_analysis_version": ["analysis_version"]},
    )
    _indexes(
        "advisor_shares",
        {"ix_advisor_shares_permission_code": ["permission_code"], "ix_advisor_shares_version_number": ["version_number"]},
    )
    _indexes(
        "advisor_comments",
        {"ix_advisor_comments_proposal_type": ["proposal_type"], "ix_advisor_comments_version_number": ["version_number"]},
    )
    _indexes(
        "career_decision_journal_entries",
        {"ix_career_decision_journal_entries_linked_experiment_id": ["linked_experiment_id"], "ix_career_decision_journal_entries_interview_id": ["interview_id"]},
    )


def downgrade() -> None:
    # Additive migration: preserve collaboration and provenance data on rollback.
    pass
