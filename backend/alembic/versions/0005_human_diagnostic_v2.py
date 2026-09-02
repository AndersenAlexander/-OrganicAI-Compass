"""human diagnostic v2 provenance and progressive save

Revision ID: 0005_human_diagnostic_v2
Revises: 0004_provider_operations
Create Date: 2026-08-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_human_diagnostic_v2"
down_revision = "0004_provider_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    diagnostic_columns = {column["name"] for column in inspector.get_columns("diagnostics")}
    required_columns = {
        "status": sa.Column("status", sa.String(length=30), nullable=False, server_default="in_progress"),
        "current_step": sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        "diagnostic_version": sa.Column("diagnostic_version", sa.String(length=50), nullable=False, server_default="human-diagnostic-v2"),
        "updated_at": sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        "completed_at": sa.Column("completed_at", sa.DateTime(), nullable=True),
    }
    missing_columns = [column for name, column in required_columns.items() if name not in diagnostic_columns]
    if missing_columns:
        with op.batch_alter_table("diagnostics") as batch_op:
            for column in missing_columns:
                batch_op.add_column(column)
    diagnostic_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("diagnostics")}
    if "ix_diagnostics_status" not in diagnostic_indexes:
        op.create_index("ix_diagnostics_status", "diagnostics", ["status"])

    if "diagnostic_responses" not in inspector.get_table_names():
        op.create_table(
            "diagnostic_responses",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("diagnostic_id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("question_id", sa.String(length=120), nullable=False),
            sa.Column("assessment_domain", sa.String(length=80), nullable=False),
            sa.Column("question_type", sa.String(length=40), nullable=False),
            sa.Column("response_json", sa.JSON(), nullable=True),
            sa.Column("normalized_value", sa.Float(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("source", sa.String(length=40), nullable=False, server_default="self_report"),
            sa.Column("version", sa.String(length=50), nullable=False, server_default="human-diagnostic-v2"),
            sa.Column("interpretation", sa.Text(), nullable=True),
            sa.Column("completeness", sa.Float(), nullable=False, server_default="1"),
            sa.Column("scoring_metadata", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["diagnostic_id"], ["diagnostics.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    response_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("diagnostic_responses")}
    for name, columns in {
        "ix_diagnostic_responses_diagnostic_id": ["diagnostic_id"],
        "ix_diagnostic_responses_user_id": ["user_id"],
        "ix_diagnostic_responses_question_id": ["question_id"],
        "ix_diagnostic_responses_assessment_domain": ["assessment_domain"],
    }.items():
        if name not in response_indexes:
            op.create_index(name, "diagnostic_responses", columns)


def downgrade() -> None:
    op.drop_index("ix_diagnostic_responses_assessment_domain", table_name="diagnostic_responses")
    op.drop_index("ix_diagnostic_responses_question_id", table_name="diagnostic_responses")
    op.drop_index("ix_diagnostic_responses_user_id", table_name="diagnostic_responses")
    op.drop_index("ix_diagnostic_responses_diagnostic_id", table_name="diagnostic_responses")
    op.drop_table("diagnostic_responses")
    with op.batch_alter_table("diagnostics") as batch_op:
        batch_op.drop_index("ix_diagnostics_status")
        batch_op.drop_column("completed_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("diagnostic_version")
        batch_op.drop_column("current_step")
        batch_op.drop_column("status")
