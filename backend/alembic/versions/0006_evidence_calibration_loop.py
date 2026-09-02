"""persist evidence gaps, proposals, and hypothesis provenance

Revision ID: 0006_evidence_calibration_loop
Revises: 0005_human_diagnostic_v2
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_evidence_calibration_loop"
down_revision = "0005_human_diagnostic_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "career_evidence_gaps",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("hypothesis_id", sa.String(), nullable=True),
        sa.Column("career_match_id", sa.String(), nullable=True),
        sa.Column("skill_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("capability_label", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("gap_kind", sa.String(length=40), nullable=False, server_default="evidence_gap"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("current_evidence_status", sa.String(length=40), nullable=False, server_default="MISSING"),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recency_issue", sa.Text(), nullable=False, server_default=""),
        sa.Column("suggested_action", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="MISSING"),
        sa.Column("source_metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("version", sa.String(length=60), nullable=False, server_default="career-evidence-gap-v1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["career_match_id"], ["career_matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in {
        "ix_career_evidence_gaps_profile_id": ["profile_id"],
        "ix_career_evidence_gaps_user_id": ["user_id"],
        "ix_career_evidence_gaps_hypothesis_id": ["hypothesis_id"],
        "ix_career_evidence_gaps_career_match_id": ["career_match_id"],
        "ix_career_evidence_gaps_skill_id": ["skill_id"],
        "ix_career_evidence_gaps_gap_kind": ["gap_kind"],
        "ix_career_evidence_gaps_current_evidence_status": ["current_evidence_status"],
        "ix_career_evidence_gaps_status": ["status"],
    }.items():
        op.create_index(name, "career_evidence_gaps", columns)

    op.create_table(
        "career_evidence_proposals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("hypothesis_id", sa.String(), nullable=True),
        sa.Column("evidence_gap_id", sa.String(), nullable=True),
        sa.Column("experiment_session_id", sa.String(), nullable=True),
        sa.Column("experiment_result_id", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(length=60), nullable=False, server_default="EXPERIMENT"),
        sa.Column("category", sa.String(length=80), nullable=False, server_default="project_evidence"),
        sa.Column("capability_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("capability_label", sa.String(length=180), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("artifact_reference", sa.Text(), nullable=False, server_default=""),
        sa.Column("expected_evidence_gain", sa.String(length=80), nullable=False, server_default="Moderate"),
        sa.Column("actual_evidence_gain", sa.String(length=80), nullable=False, server_default="Unknown"),
        sa.Column("verification_state", sa.String(length=60), nullable=False, server_default="PROVISIONAL"),
        sa.Column("relevance", sa.String(length=80), nullable=False, server_default="Pending user review"),
        sa.Column("recency", sa.String(length=80), nullable=False, server_default="Dated at acceptance"),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("user_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("user_edit_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["experiment_session_id"], ["career_experiment_sessions.id"]),
        sa.ForeignKeyConstraint(["experiment_result_id"], ["career_experiment_results.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in {
        "ix_career_evidence_proposals_profile_id": ["profile_id"],
        "ix_career_evidence_proposals_user_id": ["user_id"],
        "ix_career_evidence_proposals_hypothesis_id": ["hypothesis_id"],
        "ix_career_evidence_proposals_evidence_gap_id": ["evidence_gap_id"],
        "ix_career_evidence_proposals_experiment_session_id": ["experiment_session_id"],
        "ix_career_evidence_proposals_experiment_result_id": ["experiment_result_id"],
        "ix_career_evidence_proposals_source_type": ["source_type"],
        "ix_career_evidence_proposals_capability_id": ["capability_id"],
        "ix_career_evidence_proposals_verification_state": ["verification_state"],
        "ix_career_evidence_proposals_status": ["status"],
    }.items():
        op.create_index(name, "career_evidence_proposals", columns)

    with op.batch_alter_table("career_hypotheses") as batch_op:
        batch_op.add_column(sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("fit_band", sa.String(length=80), nullable=False, server_default="Insufficient evidence"))
        batch_op.add_column(sa.Column("based_on_diagnostic_version", sa.String(length=80), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("based_on_profile_version", sa.String(length=80), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("supporting_signals_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("caution_signals_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("missing_evidence_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("conflicting_evidence_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("source_breakdown_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("market_limitations_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("support_limitations_json", sa.JSON(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("user_decision_state", sa.String(length=40), nullable=False, server_default="UNREVIEWED"))
        batch_op.create_index("ix_career_hypotheses_user_decision_state", ["user_decision_state"])

    with op.batch_alter_table("career_experiment_sessions") as batch_op:
        batch_op.add_column(sa.Column("evidence_gap_id", sa.String(), nullable=True))
        batch_op.create_index("ix_career_experiment_sessions_evidence_gap_id", ["evidence_gap_id"])

    with op.batch_alter_table("career_experiment_results") as batch_op:
        batch_op.add_column(sa.Column("actual_evidence_gain_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.add_column(sa.Column("evidence_proposal_id", sa.String(), nullable=True))
        batch_op.create_index("ix_career_experiment_results_evidence_proposal_id", ["evidence_proposal_id"])

    with op.batch_alter_table("career_recalibration_runs") as batch_op:
        batch_op.add_column(sa.Column("hypothesis_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("evidence_proposal_id", sa.String(), nullable=True))
        batch_op.create_index("ix_career_recalibration_runs_hypothesis_id", ["hypothesis_id"])
        batch_op.create_index("ix_career_recalibration_runs_evidence_proposal_id", ["evidence_proposal_id"])


def downgrade() -> None:
    with op.batch_alter_table("career_recalibration_runs") as batch_op:
        batch_op.drop_index("ix_career_recalibration_runs_evidence_proposal_id")
        batch_op.drop_index("ix_career_recalibration_runs_hypothesis_id")
        batch_op.drop_column("evidence_proposal_id")
        batch_op.drop_column("hypothesis_id")
    with op.batch_alter_table("career_experiment_results") as batch_op:
        batch_op.drop_index("ix_career_experiment_results_evidence_proposal_id")
        batch_op.drop_column("evidence_proposal_id")
        batch_op.drop_column("actual_evidence_gain_json")
    with op.batch_alter_table("career_experiment_sessions") as batch_op:
        batch_op.drop_index("ix_career_experiment_sessions_evidence_gap_id")
        batch_op.drop_column("evidence_gap_id")
    with op.batch_alter_table("career_hypotheses") as batch_op:
        batch_op.drop_index("ix_career_hypotheses_user_decision_state")
        for column in [
            "user_decision_state", "explanation_json", "support_limitations_json", "market_limitations_json",
            "source_breakdown_json", "conflicting_evidence_json", "missing_evidence_json", "caution_signals_json",
            "supporting_signals_json", "based_on_profile_version", "based_on_diagnostic_version", "fit_band",
            "current_version_number",
        ]:
            batch_op.drop_column(column)
    for name in [
        "ix_career_evidence_proposals_status", "ix_career_evidence_proposals_verification_state",
        "ix_career_evidence_proposals_capability_id", "ix_career_evidence_proposals_source_type",
        "ix_career_evidence_proposals_experiment_result_id", "ix_career_evidence_proposals_experiment_session_id",
        "ix_career_evidence_proposals_evidence_gap_id", "ix_career_evidence_proposals_hypothesis_id",
        "ix_career_evidence_proposals_user_id", "ix_career_evidence_proposals_profile_id",
    ]:
        op.drop_index(name, table_name="career_evidence_proposals")
    op.drop_table("career_evidence_proposals")
    for name in [
        "ix_career_evidence_gaps_status", "ix_career_evidence_gaps_current_evidence_status",
        "ix_career_evidence_gaps_gap_kind", "ix_career_evidence_gaps_skill_id",
        "ix_career_evidence_gaps_career_match_id", "ix_career_evidence_gaps_hypothesis_id",
        "ix_career_evidence_gaps_user_id", "ix_career_evidence_gaps_profile_id",
    ]:
        op.drop_index(name, table_name="career_evidence_gaps")
    op.drop_table("career_evidence_gaps")
