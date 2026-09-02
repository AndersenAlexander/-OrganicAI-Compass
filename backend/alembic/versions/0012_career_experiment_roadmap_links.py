"""persist explicit career experiment roadmap action links

Revision ID: 0012_career_experiment_roadmap_links
Revises: 0011_schema_convergence
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_career_experiment_roadmap_links"
down_revision = "0011_schema_convergence"
branch_labels = None
depends_on = None


def _columns(bind: sa.Connection, table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns(table)}


def _indexes(bind: sa.Connection, table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(bind).get_indexes(table)}


def _constraints(bind: sa.Connection, table: str) -> set[str]:
    return {
        constraint["name"]
        for constraint in sa.inspect(bind).get_unique_constraints(table)
        if constraint.get("name")
    }


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "roadmap_actions")
    with op.batch_alter_table("roadmap_actions") as batch_op:
        if "career_experiment_session_id" not in columns:
            batch_op.add_column(sa.Column("career_experiment_session_id", sa.String(), nullable=True))
        if "career_hypothesis_id" not in columns:
            batch_op.add_column(sa.Column("career_hypothesis_id", sa.String(), nullable=True))
        if "evidence_gap_id" not in columns:
            batch_op.add_column(sa.Column("evidence_gap_id", sa.String(), nullable=True))

    # Safely recover links created before dedicated source-id fields existed.
    # Existing duplicate legacy rows are intentionally left unlinked rather than
    # deleted; the service repairs one confirmed action without losing user data.
    bind.execute(
        sa.text(
            """
            UPDATE roadmap_actions
            SET career_experiment_session_id = recommendation_id,
                career_hypothesis_id = (
                    SELECT hypothesis_id
                    FROM career_experiment_sessions
                    WHERE career_experiment_sessions.id = roadmap_actions.recommendation_id
                ),
                evidence_gap_id = (
                    SELECT evidence_gap_id
                    FROM career_experiment_sessions
                    WHERE career_experiment_sessions.id = roadmap_actions.recommendation_id
                )
            WHERE source_type = 'career_experiment'
              AND recommendation_id IS NOT NULL
              AND career_experiment_session_id IS NULL
              AND EXISTS (
                    SELECT 1
                    FROM career_experiment_sessions
                    WHERE career_experiment_sessions.id = roadmap_actions.recommendation_id
              )
              AND 1 = (
                    SELECT COUNT(*)
                    FROM roadmap_actions AS duplicate_actions
                    WHERE duplicate_actions.source_type = 'career_experiment'
                      AND duplicate_actions.recommendation_id = roadmap_actions.recommendation_id
              )
            """
        )
    )

    indexes = _indexes(bind, "roadmap_actions")
    constraints = _constraints(bind, "roadmap_actions")
    with op.batch_alter_table("roadmap_actions") as batch_op:
        if "ix_roadmap_actions_career_hypothesis_id" not in indexes:
            batch_op.create_index("ix_roadmap_actions_career_hypothesis_id", ["career_hypothesis_id"])
        if "ix_roadmap_actions_evidence_gap_id" not in indexes:
            batch_op.create_index("ix_roadmap_actions_evidence_gap_id", ["evidence_gap_id"])
        if "uq_roadmap_actions_career_experiment_session_id" not in constraints:
            batch_op.create_unique_constraint(
                "uq_roadmap_actions_career_experiment_session_id",
                ["career_experiment_session_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    indexes = _indexes(bind, "roadmap_actions")
    constraints = _constraints(bind, "roadmap_actions")
    with op.batch_alter_table("roadmap_actions") as batch_op:
        if "uq_roadmap_actions_career_experiment_session_id" in constraints:
            batch_op.drop_constraint("uq_roadmap_actions_career_experiment_session_id", type_="unique")
        if "ix_roadmap_actions_evidence_gap_id" in indexes:
            batch_op.drop_index("ix_roadmap_actions_evidence_gap_id")
        if "ix_roadmap_actions_career_hypothesis_id" in indexes:
            batch_op.drop_index("ix_roadmap_actions_career_hypothesis_id")
        batch_op.drop_column("evidence_gap_id")
        batch_op.drop_column("career_hypothesis_id")
        batch_op.drop_column("career_experiment_session_id")
