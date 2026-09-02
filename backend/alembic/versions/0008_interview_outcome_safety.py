"""harden interview lifecycle, evidence provenance and outcome safety

Revision ID: 0008_interview_outcome_safety
Revises: 0007_market_application_provenance
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_interview_outcome_safety"
down_revision = "0007_market_application_provenance"
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
        "interviews",
        {
            "status": sa.Column("status", sa.String(length=40), nullable=False, server_default="PLANNED"),
            "requirement_set_version": sa.Column("requirement_set_version", sa.String(length=120), nullable=False, server_default="unlinked"),
            "version_number": sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
            "version_metadata_json": sa.Column("version_metadata_json", sa.JSON(), nullable=False, server_default="{}"),
            "outcome_source": sa.Column("outcome_source", sa.String(length=120), nullable=False, server_default=""),
            "outcome_reason": sa.Column("outcome_reason", sa.Text(), nullable=False, server_default=""),
        },
    )
    _add_columns(
        "interview_preparation_briefs",
        {
            "requirement_set_version": sa.Column("requirement_set_version", sa.String(length=120), nullable=False, server_default="unlinked"),
            "version_number": sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
            "source_snapshot_json": sa.Column("source_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )
    _add_columns(
        "interview_questions",
        {
            "question_type": sa.Column("question_type", sa.String(length=80), nullable=False, server_default="experience"),
            "question_status": sa.Column("question_status", sa.String(length=40), nullable=False, server_default="active"),
            "user_edited": sa.Column("user_edited", sa.Boolean(), nullable=False, server_default=sa.false()),
            "custom": sa.Column("custom", sa.Boolean(), nullable=False, server_default=sa.false()),
            "related_evidence_gap_json": sa.Column("related_evidence_gap_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )
    _add_columns(
        "star_stories",
        {
            "support_state": sa.Column("support_state", sa.String(length=40), nullable=False, server_default="NEEDS_REVIEW"),
            "linked_capability": sa.Column("linked_capability", sa.String(length=160), nullable=False, server_default=""),
            "canonical_story_id": sa.Column("canonical_story_id", sa.String(), nullable=True),
            "adaptation_context_json": sa.Column("adaptation_context_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )
    _add_columns(
        "mock_interview_sessions",
        {
            "panel_personas_json": sa.Column("panel_personas_json", sa.JSON(), nullable=False, server_default="[]"),
            "persona_feedback_json": sa.Column("persona_feedback_json", sa.JSON(), nullable=False, server_default="{}"),
            "text_fallback_available": sa.Column("text_fallback_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        },
    )
    _add_columns(
        "mock_interview_turns",
        {
            "transcript_source": sa.Column("transcript_source", sa.String(length=40), nullable=False, server_default="text"),
            "transcript_storage_status": sa.Column("transcript_storage_status", sa.String(length=40), nullable=False, server_default="not_stored"),
            "user_edited_transcript": sa.Column("user_edited_transcript", sa.Boolean(), nullable=False, server_default=sa.false()),
        },
    )
    _add_columns(
        "voice_provider_sessions",
        {
            "transcript_text": sa.Column("transcript_text", sa.Text(), nullable=False, server_default=""),
            "user_edited_transcript": sa.Column("user_edited_transcript", sa.Text(), nullable=False, server_default=""),
            "transcript_storage_status": sa.Column("transcript_storage_status", sa.String(length=40), nullable=False, server_default="not_stored"),
        },
    )
    _add_columns(
        "interview_reflections",
        {
            "user_observation": sa.Column("user_observation", sa.Text(), nullable=False, server_default=""),
            "system_suggestion_json": sa.Column("system_suggestion_json", sa.JSON(), nullable=False, server_default="[]"),
            "outcome_source": sa.Column("outcome_source", sa.String(length=120), nullable=False, server_default=""),
            "outcome_reason": sa.Column("outcome_reason", sa.Text(), nullable=False, server_default=""),
            "outcome_confirmed": sa.Column("outcome_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        },
    )
    _add_columns(
        "offer_reviews",
        {
            "version_number": sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
            "comparison_snapshot_json": sa.Column("comparison_snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
        },
    )
    _add_columns(
        "application_recalibration_runs",
        {
            "interview_id": sa.Column("interview_id", sa.String(), nullable=True),
            "user_decision": sa.Column("user_decision", sa.String(length=40), nullable=False, server_default="PENDING"),
            "before_state_json": sa.Column("before_state_json", sa.JSON(), nullable=False, server_default="{}"),
            "after_state_json": sa.Column("after_state_json", sa.JSON(), nullable=False, server_default="{}"),
            "source_label": sa.Column("source_label", sa.String(length=120), nullable=False, server_default="Interview reflection"),
            "limitation": sa.Column("limitation", sa.Text(), nullable=False, server_default="One interview outcome is limited evidence and does not determine career fit."),
        },
    )
    _indexes(
        "interviews",
        {"ix_interviews_status": ["status"], "ix_interviews_requirement_set_version": ["requirement_set_version"]},
    )
    _indexes(
        "interview_questions",
        {"ix_interview_questions_question_status": ["question_status"], "ix_interview_questions_question_type": ["question_type"]},
    )
    _indexes("star_stories", {"ix_star_stories_support_state": ["support_state"]})
    _indexes("application_recalibration_runs", {"ix_application_recalibration_runs_interview_id": ["interview_id"], "ix_application_recalibration_runs_user_decision": ["user_decision"]})


def downgrade() -> None:
    # This migration is intentionally additive. Existing installations retain data if rolled back.
    pass
