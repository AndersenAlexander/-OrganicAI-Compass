"""widen PostgreSQL Alembic version metadata for long revision identifiers

Revision ID: 0010_alembic_version_capacity
Revises: 0009_collaboration_traceability_extensions
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_alembic_version_capacity"
down_revision = "0009_collaboration_traceability_extensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    version_column = next(
        column for column in sa.inspect(bind).get_columns("alembic_version") if column["name"] == "version_num"
    )
    if getattr(version_column["type"], "length", None) and version_column["type"].length < 128:
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=version_column["type"],
            type_=sa.String(length=128),
            existing_nullable=False,
        )


def downgrade() -> None:
    # Later historical revision identifiers exceed 32 characters, so shrinking
    # this metadata column would make the migration history unrecordable.
    pass
