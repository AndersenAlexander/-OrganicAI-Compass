"""make deterministic career experiment evaluations idempotent

Revision ID: 0013_deterministic_experiment_evidence
Revises: 0012_career_experiment_roadmap_links
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_deterministic_experiment_evidence"
down_revision = "0012_career_experiment_roadmap_links"
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
    columns = _columns(bind, "career_experiment_results")
    indexes = _indexes(bind, "career_experiment_results")
    constraints = _constraints(bind, "career_experiment_results")
    with op.batch_alter_table("career_experiment_results") as batch_op:
        # Existing rows intentionally remain NULL: that preserves all history
        # and avoids inferring an idempotency identity for pre-0013 records.
        if "idempotency_key" not in columns:
            batch_op.add_column(sa.Column("idempotency_key", sa.String(length=255), nullable=True))
        if "ix_career_experiment_results_idempotency_key" not in indexes:
            batch_op.create_index("ix_career_experiment_results_idempotency_key", ["idempotency_key"])
        if "uq_career_experiment_results_idempotency_key" not in constraints:
            batch_op.create_unique_constraint("uq_career_experiment_results_idempotency_key", ["idempotency_key"])


def downgrade() -> None:
    bind = op.get_bind()
    indexes = _indexes(bind, "career_experiment_results")
    constraints = _constraints(bind, "career_experiment_results")
    with op.batch_alter_table("career_experiment_results") as batch_op:
        if "uq_career_experiment_results_idempotency_key" in constraints:
            batch_op.drop_constraint("uq_career_experiment_results_idempotency_key", type_="unique")
        if "ix_career_experiment_results_idempotency_key" in indexes:
            batch_op.drop_index("ix_career_experiment_results_idempotency_key")
        if "idempotency_key" in _columns(bind, "career_experiment_results"):
            batch_op.drop_column("idempotency_key")
