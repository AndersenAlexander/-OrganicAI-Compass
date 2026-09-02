"""converge historical extension schema with current model metadata

Revision ID: 0011_schema_convergence
Revises: 0010_alembic_version_capacity
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_schema_convergence"
down_revision = "0010_alembic_version_capacity"
branch_labels = None
depends_on = None


def _drop_indexes(table: str, names: set[str]) -> None:
    bind = op.get_bind()
    existing = {index["name"] for index in sa.inspect(bind).get_indexes(table)}
    for name in sorted(names & existing):
        op.drop_index(name, table_name=table)


def _indexes(table: str, names: dict[str, list[str]]) -> None:
    bind = op.get_bind()
    existing = {index["name"] for index in sa.inspect(bind).get_indexes(table)}
    for name, columns in names.items():
        if name not in existing:
            op.create_index(name, table, columns)


def _orphan_count(table: str, local_column: str, referred_table: str, referred_column: str) -> int:
    bind = op.get_bind()
    metadata = sa.MetaData()
    child = sa.Table(table, metadata, autoload_with=bind)
    parent = sa.Table(referred_table, metadata, autoload_with=bind)
    statement = (
        sa.select(sa.func.count())
        .select_from(child.outerjoin(parent, child.c[local_column] == parent.c[referred_column]))
        .where(child.c[local_column].is_not(None), parent.c[referred_column].is_(None))
    )
    return int(bind.execute(statement).scalar_one())


def _foreign_keys(table: str, constraints: dict[str, tuple[str, str, str]]) -> None:
    bind = op.get_bind()
    existing = {
        (tuple(foreign_key["constrained_columns"]), foreign_key["referred_table"], tuple(foreign_key["referred_columns"]))
        for foreign_key in sa.inspect(bind).get_foreign_keys(table)
    }
    missing = [
        (name, local_column, referred_table, referred_column)
        for name, (local_column, referred_table, referred_column) in constraints.items()
        if ((local_column,), referred_table, (referred_column,)) not in existing
    ]
    for _name, local_column, referred_table, referred_column in missing:
        orphan_count = _orphan_count(table, local_column, referred_table, referred_column)
        if orphan_count:
            raise RuntimeError(
                f"Cannot add {table}.{local_column} foreign key: "
                f"{orphan_count} non-null value(s) do not reference {referred_table}.{referred_column}."
            )
    if missing:
        with op.batch_alter_table(table) as batch_op:
            for name, local_column, referred_table, referred_column in missing:
                batch_op.create_foreign_key(name, referred_table, [local_column], [referred_column])


def _make_extraction_timestamp_required() -> None:
    bind = op.get_bind()
    columns = {column["name"]: column for column in sa.inspect(bind).get_columns("job_requirements")}
    required_columns = {"created_at", "extraction_timestamp"}
    missing_columns = required_columns - columns.keys()
    if missing_columns:
        raise RuntimeError(
            "Cannot converge job_requirements timestamps; missing prerequisite column(s): "
            + ", ".join(sorted(missing_columns))
        )
    column = columns["extraction_timestamp"]
    if not column["nullable"]:
        return
    bind.execute(
        sa.text(
            "UPDATE job_requirements "
            "SET extraction_timestamp = COALESCE(created_at, CURRENT_TIMESTAMP) "
            "WHERE extraction_timestamp IS NULL"
        )
    )
    with op.batch_alter_table("job_requirements") as batch_op:
        batch_op.alter_column(
            "extraction_timestamp",
            existing_type=column["type"],
            existing_nullable=True,
            nullable=False,
        )


def upgrade() -> None:
    _drop_indexes("browser_job_captures", {"ix_browser_job_captures_analysis_version"})
    _drop_indexes("advisor_shares", {"ix_advisor_shares_version_number"})
    _drop_indexes("advisor_comments", {"ix_advisor_comments_version_number"})
    _drop_indexes("interviews", {"ix_interviews_requirement_set_version"})
    _indexes("star_stories", {"ix_star_stories_canonical_story_id": ["canonical_story_id"]})
    _foreign_keys(
        "application_recalibration_runs",
        {
            "fk_application_recalibration_runs_interview_id_interviews": (
                "interview_id",
                "interviews",
                "id",
            )
        },
    )
    _foreign_keys(
        "career_decision_journal_entries",
        {
            "fk_career_journal_experiment_id_career_experiment_sessions": (
                "linked_experiment_id",
                "career_experiment_sessions",
                "id",
            ),
            "fk_career_journal_interview_id_interviews": (
                "interview_id",
                "interviews",
                "id",
            ),
        },
    )
    _foreign_keys(
        "job_requirements",
        {
            "fk_job_requirements_confirmed_by_users": (
                "confirmed_by",
                "users",
                "id",
            )
        },
    )
    _make_extraction_timestamp_required()


def downgrade() -> None:
    # Forward-only convergence: reversing these constraints would recreate the
    # historical drift and weaken referential integrity.
    pass
