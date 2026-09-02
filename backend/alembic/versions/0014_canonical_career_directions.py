"""make current career directions canonical and unique per profile

Revision ID: 0014_canonical_career_directions
Revises: 0013_deterministic_experiment_evidence
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_canonical_career_directions"
down_revision = "0013_deterministic_experiment_evidence"
branch_labels = None
depends_on = None


def _columns(bind: sa.Connection, table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(bind).get_columns(table)}


def _indexes(bind: sa.Connection, table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(bind).get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if "canonical_direction_id" not in _columns(bind, "career_hypotheses"):
        with op.batch_alter_table("career_hypotheses") as batch_op:
            batch_op.add_column(sa.Column("canonical_direction_id", sa.String(length=255), nullable=True))

    # Do not infer an identity from a human-readable title.  Catalogue-backed
    # rows share the role-template id; legacy unclassified rows remain unique
    # by their match/hypothesis id so none of their history is discarded.
    bind.execute(
        sa.text(
            """
            UPDATE career_hypotheses
            SET canonical_direction_id = CASE
                WHEN role_template_id IS NOT NULL AND TRIM(role_template_id) <> ''
                    THEN 'role-template:' || role_template_id
                WHEN career_match_id IS NOT NULL
                    THEN 'career-match:' || career_match_id
                ELSE 'career-hypothesis:' || id
            END
            WHERE canonical_direction_id IS NULL OR TRIM(canonical_direction_id) = ''
            """
        )
    )

    # Preserve duplicate snapshots as historical/superseded hypotheses.  The
    # completed deep-dive snapshot ranks above a Human Diagnostic snapshot for
    # the same canonical direction, then the most recent source wins.
    bind.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    hypothesis.id,
                    ROW_NUMBER() OVER (
                        PARTITION BY hypothesis.profile_id, hypothesis.canonical_direction_id
                        ORDER BY
                            CASE WHEN career_match.session_id IS NOT NULL THEN 1 ELSE 0 END DESC,
                            CASE WHEN assessment_session.status = 'completed' THEN 1 ELSE 0 END DESC,
                            COALESCE(
                                assessment_session.completed_at,
                                assessment_session.updated_at,
                                career_match.created_at,
                                hypothesis.updated_at,
                                hypothesis.created_at
                            ) DESC,
                            hypothesis.id DESC
                    ) AS position
                FROM career_hypotheses AS hypothesis
                LEFT JOIN career_matches AS career_match ON career_match.id = hypothesis.career_match_id
                LEFT JOIN assessment_sessions AS assessment_session ON assessment_session.id = career_match.session_id
                WHERE hypothesis.status = 'active'
            )
            UPDATE career_hypotheses
            SET status = 'superseded'
            WHERE id IN (SELECT id FROM ranked WHERE position > 1)
            """
        )
    )

    indexes = _indexes(bind, "career_hypotheses")
    with op.batch_alter_table("career_hypotheses") as batch_op:
        if "ix_career_hypotheses_canonical_direction_id" not in indexes:
            batch_op.create_index("ix_career_hypotheses_canonical_direction_id", ["canonical_direction_id"])
    if "uq_career_hypotheses_active_canonical_direction" not in indexes:
        op.create_index(
            "uq_career_hypotheses_active_canonical_direction",
            "career_hypotheses",
            ["profile_id", "canonical_direction_id"],
            unique=True,
            postgresql_where=sa.text("status = 'active'"),
            sqlite_where=sa.text("status = 'active'"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    indexes = _indexes(bind, "career_hypotheses")
    if "uq_career_hypotheses_active_canonical_direction" in indexes:
        op.drop_index("uq_career_hypotheses_active_canonical_direction", table_name="career_hypotheses")
    with op.batch_alter_table("career_hypotheses") as batch_op:
        if "ix_career_hypotheses_canonical_direction_id" in indexes:
            batch_op.drop_index("ix_career_hypotheses_canonical_direction_id")
        if "canonical_direction_id" in _columns(bind, "career_hypotheses"):
            batch_op.drop_column("canonical_direction_id")
