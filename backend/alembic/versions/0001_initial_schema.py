"""Initial schema for OrganicAI Compass.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-27 12:11:38.936715
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Reviewed initial schema generated from SQLAlchemy metadata for Task 11.
    op.create_table('assessment_definitions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('methodology_note', sa.Text(), nullable=False),
    sa.Column('disclaimer', sa.Text(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_definitions'))
    )
    with op.batch_alter_table('assessment_definitions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_definitions_version'), ['version'], unique=False)

    op.create_table('assessment_items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('module_id', sa.String(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('item_type', sa.String(length=40), nullable=False),
    sa.Column('dimension', sa.String(length=80), nullable=True),
    sa.Column('reverse_scored', sa.Boolean(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('required', sa.Boolean(), nullable=False),
    sa.Column('quick_mode', sa.Boolean(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_items'))
    )
    with op.batch_alter_table('assessment_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_items_dimension'), ['dimension'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_items_module_id'), ['module_id'], unique=False)

    op.create_table('assessment_modules',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('assessment_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('optional', sa.Boolean(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_modules'))
    )
    with op.batch_alter_table('assessment_modules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_modules_assessment_id'), ['assessment_id'], unique=False)

    op.create_table('assessment_options',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('item_id', sa.String(), nullable=False),
    sa.Column('value', sa.String(length=120), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('score_value', sa.Float(), nullable=True),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_options'))
    )
    with op.batch_alter_table('assessment_options', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_options_item_id'), ['item_id'], unique=False)

    op.create_table('career_experiment_templates',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('target_role_family', sa.String(length=160), nullable=False),
    sa.Column('purpose', sa.Text(), nullable=False),
    sa.Column('real_world_scenario', sa.Text(), nullable=False),
    sa.Column('user_instructions_json', sa.JSON(), nullable=False),
    sa.Column('expected_deliverables_json', sa.JSON(), nullable=False),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
    sa.Column('difficulty', sa.String(length=40), nullable=False),
    sa.Column('required_skills_json', sa.JSON(), nullable=False),
    sa.Column('evaluated_skills_json', sa.JSON(), nullable=False),
    sa.Column('optional_prerequisites_json', sa.JSON(), nullable=False),
    sa.Column('allowed_tools_json', sa.JSON(), nullable=False),
    sa.Column('ai_assistance_policy', sa.Text(), nullable=False),
    sa.Column('reflection_questions_json', sa.JSON(), nullable=False),
    sa.Column('completion_criteria_json', sa.JSON(), nullable=False),
    sa.Column('evidence_generated_json', sa.JSON(), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_templates'))
    )
    with op.batch_alter_table('career_experiment_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_templates_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_templates_difficulty'), ['difficulty'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_templates_target_role_family'), ['target_role_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_templates_title'), ['title'], unique=False)

    op.create_table('career_role_profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('slug', sa.String(length=180), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('career_family', sa.String(length=160), nullable=False),
    sa.Column('aliases_json', sa.JSON(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('profile_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('last_reviewed_date', sa.String(length=40), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_role_profiles'))
    )
    with op.batch_alter_table('career_role_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_role_profiles_career_family'), ['career_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_role_profiles_slug'), ['slug'], unique=True)
        batch_op.create_index(batch_op.f('ix_career_role_profiles_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_role_profiles_title'), ['title'], unique=False)

    op.create_table('career_role_templates',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('role_family', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('required_skills_json', sa.JSON(), nullable=False),
    sa.Column('useful_transferable_skills_json', sa.JSON(), nullable=False),
    sa.Column('interest_profile_json', sa.JSON(), nullable=False),
    sa.Column('work_style_tendencies_json', sa.JSON(), nullable=False),
    sa.Column('compatible_work_values_json', sa.JSON(), nullable=False),
    sa.Column('ai_augmentation_opportunities_json', sa.JSON(), nullable=False),
    sa.Column('entry_requirements_json', sa.JSON(), nullable=False),
    sa.Column('skill_gap_categories_json', sa.JSON(), nullable=False),
    sa.Column('typical_transition_path_json', sa.JSON(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('version', sa.String(length=50), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_role_templates'))
    )
    with op.batch_alter_table('career_role_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_role_templates_role_family'), ['role_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_role_templates_title'), ['title'], unique=False)

    op.create_table('esco_concepts',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('esco_uri', sa.Text(), nullable=False),
    sa.Column('preferred_label', sa.String(length=255), nullable=False),
    sa.Column('concept_type', sa.String(length=80), nullable=False),
    sa.Column('taxonomy_version', sa.String(length=80), nullable=False),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_esco_concepts'))
    )
    with op.batch_alter_table('esco_concepts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_esco_concepts_concept_type'), ['concept_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_concepts_esco_uri'), ['esco_uri'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_concepts_preferred_label'), ['preferred_label'], unique=False)

    op.create_table('external_provider_cache',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_name', sa.String(length=80), nullable=False),
    sa.Column('cache_key', sa.String(length=255), nullable=False),
    sa.Column('response_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_external_provider_cache'))
    )
    with op.batch_alter_table('external_provider_cache', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_external_provider_cache_cache_key'), ['cache_key'], unique=False)
        batch_op.create_index(batch_op.f('ix_external_provider_cache_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_external_provider_cache_provider_name'), ['provider_name'], unique=False)

    op.create_table('fairness_audit_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('audit_type', sa.String(length=120), nullable=False),
    sa.Column('synthetic_only', sa.Boolean(), nullable=False),
    sa.Column('fixtures_json', sa.JSON(), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('summary_json', sa.JSON(), nullable=False),
    sa.Column('system_card_version', sa.String(length=80), nullable=False),
    sa.Column('reproducibility_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fairness_audit_runs'))
    )
    with op.batch_alter_table('fairness_audit_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fairness_audit_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_fairness_audit_runs_status'), ['status'], unique=False)

    op.create_table('fear_transforms',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('input_fear', sa.String(), nullable=False),
    sa.Column('output', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fear_transforms'))
    )
    with op.batch_alter_table('fear_transforms', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_fear_transforms_profile_id'), ['profile_id'], unique=False)

    op.create_table('innovation_audit_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('actor_type', sa.String(length=80), nullable=False),
    sa.Column('actor_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(length=120), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('event_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_innovation_audit_events'))
    )
    with op.batch_alter_table('innovation_audit_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_actor_id'), ['actor_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_actor_type'), ['actor_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_target_id'), ['target_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_innovation_audit_events_target_type'), ['target_type'], unique=False)

    op.create_table('job_postings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('external_job_id', sa.String(length=255), nullable=False),
    sa.Column('source_url', sa.Text(), nullable=False),
    sa.Column('provider_event_id', sa.String(length=255), nullable=True),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('employer', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('publication_time', sa.DateTime(), nullable=True),
    sa.Column('expiry_time', sa.DateTime(), nullable=True),
    sa.Column('last_provider_update', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('inactive_reason', sa.String(length=120), nullable=False),
    sa.Column('employment_type', sa.String(length=120), nullable=False),
    sa.Column('full_time_part_time', sa.String(length=80), nullable=False),
    sa.Column('work_mode', sa.String(length=80), nullable=False),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('county', sa.String(length=120), nullable=False),
    sa.Column('municipality', sa.String(length=120), nullable=False),
    sa.Column('city', sa.String(length=120), nullable=False),
    sa.Column('coordinates_json', sa.JSON(), nullable=False),
    sa.Column('language_requirements_json', sa.JSON(), nullable=False),
    sa.Column('experience_requirements_json', sa.JSON(), nullable=False),
    sa.Column('education_requirements_json', sa.JSON(), nullable=False),
    sa.Column('occupation_classifications_json', sa.JSON(), nullable=False),
    sa.Column('esco_classifications_json', sa.JSON(), nullable=False),
    sa.Column('styrk_classifications_json', sa.JSON(), nullable=False),
    sa.Column('extracted_skills_json', sa.JSON(), nullable=False),
    sa.Column('career_families_json', sa.JSON(), nullable=False),
    sa.Column('original_provider_metadata_json', sa.JSON(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(), nullable=False),
    sa.Column('source_version', sa.String(length=80), nullable=False),
    sa.Column('content_hash', sa.String(length=128), nullable=False),
    sa.Column('historical_retention_allowed', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_postings')),
    sa.UniqueConstraint('provider', 'external_job_id', name='uq_job_provider_external')
    )
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_postings_city'), ['city'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_content_hash'), ['content_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_county'), ['county'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_employer'), ['employer'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_expiry_time'), ['expiry_time'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_external_job_id'), ['external_job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_ingested_at'), ['ingested_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_is_active'), ['is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_last_provider_update'), ['last_provider_update'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_municipality'), ['municipality'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_provider'), ['provider'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_provider_event_id'), ['provider_event_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_publication_time'), ['publication_time'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_postings_work_mode'), ['work_mode'], unique=False)

    op.create_table('labour_market_providers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_name', sa.String(length=80), nullable=False),
    sa.Column('display_name', sa.String(length=160), nullable=False),
    sa.Column('provider_type', sa.String(length=60), nullable=False),
    sa.Column('base_url', sa.Text(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('configured', sa.Boolean(), nullable=False),
    sa.Column('reachable', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('degraded_reason', sa.Text(), nullable=False),
    sa.Column('documentation_url', sa.Text(), nullable=False),
    sa.Column('documentation_checked_date', sa.String(length=40), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_labour_market_providers'))
    )
    with op.batch_alter_table('labour_market_providers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_labour_market_providers_enabled'), ['enabled'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_providers_provider_name'), ['provider_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_providers_status'), ['status'], unique=False)

    op.create_table('learning_providers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_name', sa.String(length=80), nullable=False),
    sa.Column('display_name', sa.String(length=160), nullable=False),
    sa.Column('provider_type', sa.String(length=60), nullable=False),
    sa.Column('base_url', sa.Text(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('supports_external_search', sa.Boolean(), nullable=False),
    sa.Column('api_enabled', sa.Boolean(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_providers'))
    )
    with op.batch_alter_table('learning_providers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_providers_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_providers_provider_name'), ['provider_name'], unique=False)

    op.create_table('market_signal_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('observation_window_days', sa.Integer(), nullable=False),
    sa.Column('comparison_window_days', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('coverage_label', sa.String(length=120), nullable=False),
    sa.Column('provider_status_json', sa.JSON(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_market_signal_runs'))
    )
    with op.batch_alter_table('market_signal_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_market_signal_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_signal_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_signal_runs_status'), ['status'], unique=False)

    op.create_table('market_snapshots',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('region', sa.String(length=120), nullable=False),
    sa.Column('source_type', sa.String(length=60), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('snapshot_date', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('last_checked_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_market_snapshots'))
    )
    with op.batch_alter_table('market_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_market_snapshots_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_snapshots_region'), ['region'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_snapshots_status'), ['status'], unique=False)

    op.create_table('originality_audit_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('actor_type', sa.String(length=80), nullable=False),
    sa.Column('actor_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(length=120), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('event_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_originality_audit_events'))
    )
    with op.batch_alter_table('originality_audit_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_originality_audit_events_actor_id'), ['actor_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_originality_audit_events_actor_type'), ['actor_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_originality_audit_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_originality_audit_events_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_originality_audit_events_target_id'), ['target_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_originality_audit_events_target_type'), ['target_type'], unique=False)

    op.create_table('rag_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('conversation_id', sa.String(), nullable=True),
    sa.Column('message_id', sa.String(), nullable=True),
    sa.Column('query', sa.Text(), nullable=False),
    sa.Column('query_normalized', sa.Text(), nullable=True),
    sa.Column('mode', sa.String(length=32), nullable=False),
    sa.Column('run_origin', sa.String(length=20), nullable=False),
    sa.Column('retrieval_top_k', sa.Integer(), nullable=False),
    sa.Column('relevance_threshold', sa.Float(), nullable=False),
    sa.Column('retrieved_count', sa.Integer(), nullable=False),
    sa.Column('used_source_count', sa.Integer(), nullable=False),
    sa.Column('highest_similarity_score', sa.Float(), nullable=True),
    sa.Column('average_similarity_score', sa.Float(), nullable=True),
    sa.Column('retrieval_duration_ms', sa.Integer(), nullable=True),
    sa.Column('generation_duration_ms', sa.Integer(), nullable=True),
    sa.Column('total_duration_ms', sa.Integer(), nullable=True),
    sa.Column('embedding_model', sa.String(length=120), nullable=True),
    sa.Column('generation_model', sa.String(length=120), nullable=True),
    sa.Column('provider', sa.String(length=40), nullable=True),
    sa.Column('answer', sa.Text(), nullable=True),
    sa.Column('confidence_note', sa.Text(), nullable=True),
    sa.Column('ethical_note', sa.Text(), nullable=True),
    sa.Column('context_quality', sa.String(length=20), nullable=False),
    sa.Column('fallback_reason', sa.String(length=80), nullable=True),
    sa.Column('insufficient_context', sa.Boolean(), nullable=False),
    sa.Column('prompt_injection_flag', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False),
    sa.Column('error_code', sa.String(length=80), nullable=True),
    sa.Column('error_message_safe', sa.String(length=300), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rag_runs'))
    )
    with op.batch_alter_table('rag_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rag_runs_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_rag_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_rag_runs_run_origin'), ['run_origin'], unique=False)
        batch_op.create_index(batch_op.f('ix_rag_runs_user_id'), ['user_id'], unique=False)

    op.create_table('recommendation_system_card_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('card_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendation_system_card_versions'))
    )
    with op.batch_alter_table('recommendation_system_card_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recommendation_system_card_versions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendation_system_card_versions_version'), ['version'], unique=False)

    op.create_table('research_studies',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('study_mode', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('research_question', sa.Text(), nullable=False),
    sa.Column('contribution_statement', sa.Text(), nullable=False),
    sa.Column('consent_version', sa.String(length=80), nullable=False),
    sa.Column('random_assignment_enabled', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_studies'))
    )
    with op.batch_alter_table('research_studies', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_studies_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_studies_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_studies_study_mode'), ['study_mode'], unique=False)

    op.create_table('skill_normalisation_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('input_count', sa.Integer(), nullable=False),
    sa.Column('mapped_count', sa.Integer(), nullable=False),
    sa.Column('ambiguous_count', sa.Integer(), nullable=False),
    sa.Column('fallback_count', sa.Integer(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_normalisation_runs'))
    )
    with op.batch_alter_table('skill_normalisation_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_normalisation_runs_status'), ['status'], unique=False)

    op.create_table('skill_recency',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('first_demonstrated_at', sa.DateTime(), nullable=True),
    sa.Column('most_recent_evidence_at', sa.DateTime(), nullable=True),
    sa.Column('last_professional_use_at', sa.DateTime(), nullable=True),
    sa.Column('evidence_age_days', sa.Integer(), nullable=True),
    sa.Column('refresh_recommendation', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_recency'))
    )
    with op.batch_alter_table('skill_recency', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_recency_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_recency_skill_id'), ['skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_recency_status'), ['status'], unique=False)

    op.create_table('support_opportunity_links',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('source_type', sa.String(length=80), nullable=False),
    sa.Column('source_id', sa.String(), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('relationship', sa.String(length=160), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_opportunity_links'))
    )
    with op.batch_alter_table('support_opportunity_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_opportunity_links_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_opportunity_links_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_opportunity_links_source_type'), ['source_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_opportunity_links_target_id'), ['target_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_opportunity_links_target_type'), ['target_type'], unique=False)

    op.create_table('support_programmes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('authority', sa.String(length=120), nullable=False),
    sa.Column('jurisdiction', sa.String(length=80), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('current_rule_version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_programmes'))
    )
    with op.batch_alter_table('support_programmes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_programmes_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_programmes_authority'), ['authority'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_programmes_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_programmes_jurisdiction'), ['jurisdiction'], unique=False)

    op.create_table('users',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('is_demo', sa.Boolean(), nullable=False),
    sa.Column('demo_dataset_version', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('adaptive_experiment_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('input_snapshot_json', sa.JSON(), nullable=False),
    sa.Column('scoring_version', sa.String(length=80), nullable=False),
    sa.Column('weight_version', sa.String(length=80), nullable=False),
    sa.Column('weights_json', sa.JSON(), nullable=False),
    sa.Column('source_versions_json', sa.JSON(), nullable=False),
    sa.Column('data_coverage_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_adaptive_experiment_runs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_adaptive_experiment_runs'))
    )
    with op.batch_alter_table('adaptive_experiment_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_runs_user_id'), ['user_id'], unique=False)

    op.create_table('advisor_shares',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('adviser_display_name', sa.String(length=160), nullable=False),
    sa.Column('adviser_role', sa.String(length=80), nullable=False),
    sa.Column('purpose', sa.Text(), nullable=False),
    sa.Column('permission_level', sa.String(length=80), nullable=False),
    sa.Column('allowed_sections_json', sa.JSON(), nullable=False),
    sa.Column('allowed_actions_json', sa.JSON(), nullable=False),
    sa.Column('export_allowed', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('max_access_attempts', sa.Integer(), nullable=False),
    sa.Column('access_attempts', sa.Integer(), nullable=False),
    sa.Column('optional_pin_hash', sa.String(length=128), nullable=True),
    sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_advisor_shares_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_advisor_shares'))
    )
    with op.batch_alter_table('advisor_shares', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_advisor_shares_adviser_role'), ['adviser_role'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_permission_level'), ['permission_level'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_token_hash'), ['token_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_shares_user_id'), ['user_id'], unique=False)

    op.create_table('assessment_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('mode', sa.String(length=30), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('consent_accepted', sa.Boolean(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('completion_time_seconds', sa.Integer(), nullable=True),
    sa.Column('last_confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('source_type', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_assessment_sessions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_sessions'))
    )
    with op.batch_alter_table('assessment_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_sessions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_sessions_mode'), ['mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_sessions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_sessions_user_id'), ['user_id'], unique=False)

    op.create_table('browser_extension_connections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('display_name', sa.String(length=160), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('permissions_json', sa.JSON(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_browser_extension_connections_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_browser_extension_connections'))
    )
    with op.batch_alter_table('browser_extension_connections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_token_hash'), ['token_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_extension_connections_user_id'), ['user_id'], unique=False)

    op.create_table('career_comparisons',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('match_ids_json', sa.JSON(), nullable=False),
    sa.Column('criteria_weights_json', sa.JSON(), nullable=False),
    sa.Column('decision_priorities_json', sa.JSON(), nullable=False),
    sa.Column('matrix_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_comparisons_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_comparisons'))
    )
    with op.batch_alter_table('career_comparisons', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_comparisons_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_comparisons_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_comparisons_user_id'), ['user_id'], unique=False)

    op.create_table('career_experiment_rubrics',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('experiment_template_id', sa.String(), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('rating_scale_json', sa.JSON(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_template_id'], ['career_experiment_templates.id'], name=op.f('fk_career_experiment_rubrics_experiment_template_id_career_experiment_templates')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_rubrics'))
    )
    with op.batch_alter_table('career_experiment_rubrics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_rubrics_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_rubrics_experiment_template_id'), ['experiment_template_id'], unique=False)

    op.create_table('career_role_profile_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('role_profile_id', sa.String(), nullable=False),
    sa.Column('slug', sa.String(length=180), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['role_profile_id'], ['career_role_profiles.id'], name=op.f('fk_career_role_profile_versions_role_profile_id_career_role_profiles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_role_profile_versions'))
    )
    with op.batch_alter_table('career_role_profile_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_role_profile_versions_role_profile_id'), ['role_profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_role_profile_versions_slug'), ['slug'], unique=False)

    op.create_table('career_transition_simulations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('scenario_name', sa.String(length=180), nullable=False),
    sa.Column('preset', sa.String(length=120), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('controls_json', sa.JSON(), nullable=False),
    sa.Column('objective_config_json', sa.JSON(), nullable=False),
    sa.Column('input_snapshot_json', sa.JSON(), nullable=False),
    sa.Column('pareto_front_json', sa.JSON(), nullable=False),
    sa.Column('scenario_comparisons_json', sa.JSON(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('objective_version', sa.String(length=80), nullable=False),
    sa.Column('source_versions_json', sa.JSON(), nullable=False),
    sa.Column('data_coverage_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('saved', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_transition_simulations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_transition_simulations'))
    )
    with op.batch_alter_table('career_transition_simulations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_preset'), ['preset'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_saved'), ['saved'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_scenario_name'), ['scenario_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_simulations_user_id'), ['user_id'], unique=False)

    op.create_table('conversations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_conversations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_conversations'))
    )
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_conversations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_conversations_user_id'), ['user_id'], unique=False)

    op.create_table('diagnostics',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_diagnostics_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_diagnostics'))
    )
    with op.batch_alter_table('diagnostics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_diagnostics_user_id'), ['user_id'], unique=False)

    op.create_table('esco_labels',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('concept_id', sa.String(), nullable=False),
    sa.Column('language', sa.String(length=20), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('label_type', sa.String(length=60), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['esco_concepts.id'], name=op.f('fk_esco_labels_concept_id_esco_concepts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_esco_labels'))
    )
    with op.batch_alter_table('esco_labels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_esco_labels_concept_id'), ['concept_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_labels_label'), ['label'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_labels_language'), ['language'], unique=False)

    op.create_table('esco_mappings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('original_phrase', sa.String(length=255), nullable=False),
    sa.Column('normalised_phrase', sa.String(length=255), nullable=False),
    sa.Column('concept_id', sa.String(), nullable=True),
    sa.Column('esco_uri', sa.Text(), nullable=True),
    sa.Column('preferred_label', sa.String(length=255), nullable=False),
    sa.Column('alternative_labels_json', sa.JSON(), nullable=False),
    sa.Column('concept_type', sa.String(length=80), nullable=False),
    sa.Column('taxonomy_version', sa.String(length=80), nullable=False),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('confidence', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['esco_concepts.id'], name=op.f('fk_esco_mappings_concept_id_esco_concepts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_esco_mappings'))
    )
    with op.batch_alter_table('esco_mappings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_esco_mappings_concept_id'), ['concept_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_mappings_normalised_phrase'), ['normalised_phrase'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_mappings_original_phrase'), ['original_phrase'], unique=False)
        batch_op.create_index(batch_op.f('ix_esco_mappings_status'), ['status'], unique=False)

    op.create_table('job_analyses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_id', sa.String(), nullable=True),
    sa.Column('input_type', sa.String(length=60), nullable=False),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('organisation', sa.String(length=255), nullable=False),
    sa.Column('location', sa.String(length=255), nullable=False),
    sa.Column('deadline', sa.String(length=80), nullable=True),
    sa.Column('raw_text_excerpt', sa.Text(), nullable=False),
    sa.Column('structured_output_json', sa.JSON(), nullable=False),
    sa.Column('uncertainties_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('extraction_version', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_analyses_job_id_job_postings')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_job_analyses_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_analyses'))
    )
    with op.batch_alter_table('job_analyses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_analyses_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_input_type'), ['input_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analyses_user_id'), ['user_id'], unique=False)

    op.create_table('job_classifications',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_id', sa.String(), nullable=False),
    sa.Column('classification_type', sa.String(length=80), nullable=False),
    sa.Column('code', sa.String(length=120), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_classifications_job_id_job_postings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_classifications'))
    )
    with op.batch_alter_table('job_classifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_classifications_classification_type'), ['classification_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_classifications_code'), ['code'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_classifications_job_id'), ['job_id'], unique=False)

    op.create_table('job_language_requirements',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_id', sa.String(), nullable=False),
    sa.Column('language', sa.String(length=80), nullable=False),
    sa.Column('level', sa.String(length=80), nullable=False),
    sa.Column('requirement_type', sa.String(length=60), nullable=False),
    sa.Column('source_excerpt', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_language_requirements_job_id_job_postings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_language_requirements'))
    )
    with op.batch_alter_table('job_language_requirements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_language_requirements_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_language_requirements_language'), ['language'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_language_requirements_requirement_type'), ['requirement_type'], unique=False)

    op.create_table('job_locations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_id', sa.String(), nullable=False),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('county', sa.String(length=120), nullable=False),
    sa.Column('municipality', sa.String(length=120), nullable=False),
    sa.Column('city', sa.String(length=120), nullable=False),
    sa.Column('postal_code_area', sa.String(length=40), nullable=False),
    sa.Column('coordinates_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_locations_job_id_job_postings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_locations'))
    )
    with op.batch_alter_table('job_locations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_locations_city'), ['city'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_locations_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_locations_county'), ['county'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_locations_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_locations_municipality'), ['municipality'], unique=False)

    op.create_table('job_loss_profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('consent_accepted', sa.Boolean(), nullable=False),
    sa.Column('country_of_residence', sa.String(length=80), nullable=False),
    sa.Column('country_of_employment', sa.String(length=80), nullable=False),
    sa.Column('municipality_or_region', sa.String(length=160), nullable=False),
    sa.Column('last_working_date', sa.String(length=40), nullable=True),
    sa.Column('contract_termination_type', sa.String(length=80), nullable=False),
    sa.Column('employment_status', sa.String(length=80), nullable=False),
    sa.Column('reduction_in_working_hours', sa.Integer(), nullable=True),
    sa.Column('jobseeker_registration_status', sa.String(length=80), nullable=False),
    sa.Column('current_benefits_json', sa.JSON(), nullable=False),
    sa.Column('work_permit_or_residency_status', sa.String(length=120), nullable=False),
    sa.Column('education', sa.Text(), nullable=False),
    sa.Column('training_interest', sa.String(length=120), nullable=False),
    sa.Column('availability_for_work', sa.String(length=120), nullable=False),
    sa.Column('relocation_preferences', sa.Text(), nullable=False),
    sa.Column('sensitive_explanations_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_job_loss_profiles_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_loss_profiles'))
    )
    with op.batch_alter_table('job_loss_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_loss_profiles_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_loss_profiles_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_loss_profiles_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_loss_profiles_user_id'), ['user_id'], unique=False)

    op.create_table('job_posting_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_id', sa.String(), nullable=False),
    sa.Column('provider_event_id', sa.String(length=255), nullable=True),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('content_hash', sa.String(length=128), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_posting_versions_job_id_job_postings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_posting_versions'))
    )
    with op.batch_alter_table('job_posting_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_posting_versions_content_hash'), ['content_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_posting_versions_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_posting_versions_provider_event_id'), ['provider_event_id'], unique=False)

    op.create_table('job_skill_mentions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('job_id', sa.String(), nullable=False),
    sa.Column('original_phrase', sa.String(length=255), nullable=False),
    sa.Column('normalised_skill_id', sa.String(length=160), nullable=True),
    sa.Column('normalised_label', sa.String(length=255), nullable=False),
    sa.Column('esco_uri', sa.Text(), nullable=True),
    sa.Column('requirement_type', sa.String(length=60), nullable=False),
    sa.Column('confidence', sa.String(length=60), nullable=False),
    sa.Column('extraction_method', sa.String(length=80), nullable=False),
    sa.Column('source_excerpt', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_skill_mentions_job_id_job_postings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_skill_mentions'))
    )
    with op.batch_alter_table('job_skill_mentions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_skill_mentions_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_skill_mentions_normalised_skill_id'), ['normalised_skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_skill_mentions_original_phrase'), ['original_phrase'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_skill_mentions_requirement_type'), ['requirement_type'], unique=False)

    op.create_table('labour_market_sync_cursors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_id', sa.String(), nullable=False),
    sa.Column('cursor_key', sa.String(length=120), nullable=False),
    sa.Column('next_url', sa.Text(), nullable=True),
    sa.Column('next_id', sa.String(length=255), nullable=True),
    sa.Column('etag', sa.String(length=255), nullable=True),
    sa.Column('last_modified', sa.String(length=255), nullable=True),
    sa.Column('latest_event_timestamp', sa.DateTime(), nullable=True),
    sa.Column('cursor_status', sa.String(length=60), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['labour_market_providers.id'], name=op.f('fk_labour_market_sync_cursors_provider_id_labour_market_providers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_labour_market_sync_cursors'))
    )
    with op.batch_alter_table('labour_market_sync_cursors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_labour_market_sync_cursors_cursor_key'), ['cursor_key'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_sync_cursors_cursor_status'), ['cursor_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_sync_cursors_provider_id'), ['provider_id'], unique=False)

    op.create_table('labour_market_sync_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_id', sa.String(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('fetched_count', sa.Integer(), nullable=False),
    sa.Column('created_count', sa.Integer(), nullable=False),
    sa.Column('updated_count', sa.Integer(), nullable=False),
    sa.Column('inactive_count', sa.Integer(), nullable=False),
    sa.Column('error_count', sa.Integer(), nullable=False),
    sa.Column('error_json', sa.JSON(), nullable=False),
    sa.Column('cursor_before_json', sa.JSON(), nullable=False),
    sa.Column('cursor_after_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['labour_market_providers.id'], name=op.f('fk_labour_market_sync_runs_provider_id_labour_market_providers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_labour_market_sync_runs'))
    )
    with op.batch_alter_table('labour_market_sync_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_labour_market_sync_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_sync_runs_provider_id'), ['provider_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_labour_market_sync_runs_status'), ['status'], unique=False)

    op.create_table('learning_preferences',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('preferred_language', sa.String(length=20), nullable=False),
    sa.Column('acceptable_secondary_languages_json', sa.JSON(), nullable=False),
    sa.Column('free_only', sa.Boolean(), nullable=False),
    sa.Column('max_budget_per_course', sa.Float(), nullable=True),
    sa.Column('monthly_learning_budget', sa.Float(), nullable=True),
    sa.Column('available_hours_per_week', sa.Float(), nullable=False),
    sa.Column('preferred_content_formats_json', sa.JSON(), nullable=False),
    sa.Column('preferred_session_length_minutes', sa.Integer(), nullable=True),
    sa.Column('theory_practice_preference', sa.String(length=40), nullable=False),
    sa.Column('certificate_importance', sa.String(length=40), nullable=False),
    sa.Column('preferred_difficulty', sa.String(length=40), nullable=False),
    sa.Column('target_completion_date', sa.String(length=40), nullable=True),
    sa.Column('accessibility_preferences_json', sa.JSON(), nullable=False),
    sa.Column('subtitles_required', sa.Boolean(), nullable=False),
    sa.Column('mobile_friendly', sa.Boolean(), nullable=False),
    sa.Column('offline_availability', sa.Boolean(), nullable=False),
    sa.Column('provider_exclusions_json', sa.JSON(), nullable=False),
    sa.Column('strict_duration_limit_minutes', sa.Integer(), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_preferences_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_preferences'))
    )
    with op.batch_alter_table('learning_preferences', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_preferences_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_preferences_user_id'), ['user_id'], unique=False)

    op.create_table('learning_resource_comparisons',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('recommendation_ids_json', sa.JSON(), nullable=False),
    sa.Column('resource_ids_json', sa.JSON(), nullable=False),
    sa.Column('criteria_weights_json', sa.JSON(), nullable=False),
    sa.Column('matrix_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_resource_comparisons_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_comparisons'))
    )
    with op.batch_alter_table('learning_resource_comparisons', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_comparisons_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_comparisons_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_comparisons_user_id'), ['user_id'], unique=False)

    op.create_table('learning_resources',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('provider_id', sa.String(), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('canonical_url', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('resource_type', sa.String(length=80), nullable=False),
    sa.Column('level', sa.String(length=40), nullable=False),
    sa.Column('language', sa.String(length=20), nullable=False),
    sa.Column('subtitles_json', sa.JSON(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('cost_type', sa.String(length=40), nullable=False),
    sa.Column('displayed_price', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('instructor_organization', sa.String(length=255), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('review_count', sa.Integer(), nullable=True),
    sa.Column('publication_date', sa.String(length=40), nullable=True),
    sa.Column('last_updated_date', sa.String(length=40), nullable=True),
    sa.Column('last_verified_at', sa.DateTime(), nullable=True),
    sa.Column('prerequisites_json', sa.JSON(), nullable=False),
    sa.Column('certificate_available', sa.Boolean(), nullable=True),
    sa.Column('practical_exercises', sa.Boolean(), nullable=False),
    sa.Column('project_included', sa.Boolean(), nullable=False),
    sa.Column('quality_status', sa.String(length=60), nullable=False),
    sa.Column('source_provenance', sa.Text(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('affiliate', sa.Boolean(), nullable=False),
    sa.Column('affiliate_disclosure', sa.Text(), nullable=False),
    sa.Column('notes_limitations', sa.Text(), nullable=False),
    sa.Column('metadata_version', sa.String(length=60), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['learning_providers.id'], name=op.f('fk_learning_resources_provider_id_learning_providers')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resources'))
    )
    with op.batch_alter_table('learning_resources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resources_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_cost_type'), ['cost_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_external_id'), ['external_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_language'), ['language'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_last_verified_at'), ['last_verified_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_level'), ['level'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_provider_id'), ['provider_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_quality_status'), ['quality_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_resource_type'), ['resource_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resources_title'), ['title'], unique=False)

    op.create_table('market_radar_preferences',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('county', sa.String(length=120), nullable=False),
    sa.Column('municipality', sa.String(length=120), nullable=False),
    sa.Column('commuting_area', sa.String(length=160), nullable=False),
    sa.Column('radius_km', sa.Integer(), nullable=True),
    sa.Column('work_modes_json', sa.JSON(), nullable=False),
    sa.Column('preferred_languages_json', sa.JSON(), nullable=False),
    sa.Column('employment_types_json', sa.JSON(), nullable=False),
    sa.Column('full_time_part_time_json', sa.JSON(), nullable=False),
    sa.Column('career_families_json', sa.JSON(), nullable=False),
    sa.Column('selected_hypothesis_id', sa.String(), nullable=True),
    sa.Column('minimum_publication_date', sa.String(length=40), nullable=True),
    sa.Column('experience_level', sa.String(length=80), nullable=False),
    sa.Column('excluded_employers_json', sa.JSON(), nullable=False),
    sa.Column('excluded_keywords_json', sa.JSON(), nullable=False),
    sa.Column('relocation_preference', sa.String(length=120), nullable=False),
    sa.Column('user_confirmed_storage', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_market_radar_preferences_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_market_radar_preferences'))
    )
    with op.batch_alter_table('market_radar_preferences', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_market_radar_preferences_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_radar_preferences_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_radar_preferences_selected_hypothesis_id'), ['selected_hypothesis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_radar_preferences_user_id'), ['user_id'], unique=False)

    op.create_table('market_role_signals',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('snapshot_id', sa.String(), nullable=False),
    sa.Column('role_family', sa.String(length=160), nullable=False),
    sa.Column('opportunity_count', sa.Integer(), nullable=False),
    sa.Column('geography_json', sa.JSON(), nullable=False),
    sa.Column('work_modes_json', sa.JSON(), nullable=False),
    sa.Column('language_requirements_json', sa.JSON(), nullable=False),
    sa.Column('recurring_skills_json', sa.JSON(), nullable=False),
    sa.Column('experience_level', sa.String(length=80), nullable=False),
    sa.Column('emerging_requirements_json', sa.JSON(), nullable=False),
    sa.Column('posting_recency_label', sa.String(length=80), nullable=False),
    sa.Column('demand_direction', sa.String(length=80), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['snapshot_id'], ['market_snapshots.id'], name=op.f('fk_market_role_signals_snapshot_id_market_snapshots')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_market_role_signals'))
    )
    with op.batch_alter_table('market_role_signals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_market_role_signals_role_family'), ['role_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_role_signals_snapshot_id'), ['snapshot_id'], unique=False)

    op.create_table('market_signal_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=False),
    sa.Column('signal_type', sa.String(length=80), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=False),
    sa.Column('trend_label', sa.String(length=120), nullable=False),
    sa.Column('observation_count', sa.Integer(), nullable=False),
    sa.Column('comparison_count', sa.Integer(), nullable=False),
    sa.Column('confidence_label', sa.String(length=120), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('factor_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['market_signal_runs.id'], name=op.f('fk_market_signal_results_run_id_market_signal_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_market_signal_results'))
    )
    with op.batch_alter_table('market_signal_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_market_signal_results_label'), ['label'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_signal_results_run_id'), ['run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_signal_results_signal_type'), ['signal_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_market_signal_results_trend_label'), ['trend_label'], unique=False)

    op.create_table('master_career_profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('professional_summary', sa.Text(), nullable=False),
    sa.Column('language_profile_json', sa.JSON(), nullable=False),
    sa.Column('portfolio_links_json', sa.JSON(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_master_career_profiles_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_master_career_profiles'))
    )
    with op.batch_alter_table('master_career_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_master_career_profiles_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_master_career_profiles_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_master_career_profiles_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_master_career_profiles_user_id'), ['user_id'], unique=False)

    op.create_table('profiles',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('diagnostic_id', sa.String(), nullable=True),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_profiles_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_profiles'))
    )
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_profiles_user_id'), ['user_id'], unique=False)

    op.create_table('rag_feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('rag_run_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('feedback_type', sa.String(length=40), nullable=False),
    sa.Column('rating', sa.String(length=32), nullable=False),
    sa.Column('reason_code', sa.String(length=40), nullable=True),
    sa.Column('comment', sa.String(length=1000), nullable=True),
    sa.Column('source_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['rag_run_id'], ['rag_runs.id'], name=op.f('fk_rag_feedback_rag_run_id_rag_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rag_feedback')),
    sa.UniqueConstraint('rag_run_id', 'user_id', 'feedback_type', 'source_id', name='uq_rag_feedback_target')
    )
    with op.batch_alter_table('rag_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rag_feedback_rag_run_id'), ['rag_run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_rag_feedback_user_id'), ['user_id'], unique=False)

    op.create_table('rag_run_sources',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('rag_run_id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=True),
    sa.Column('document_name', sa.String(length=255), nullable=False),
    sa.Column('chunk_id', sa.String(length=255), nullable=False),
    sa.Column('section_title', sa.String(length=255), nullable=True),
    sa.Column('chunk_position', sa.Integer(), nullable=True),
    sa.Column('similarity_score', sa.Float(), nullable=False),
    sa.Column('rank', sa.Integer(), nullable=False),
    sa.Column('was_used_in_context', sa.Boolean(), nullable=False),
    sa.Column('source_excerpt', sa.Text(), nullable=False),
    sa.Column('injection_risk', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['rag_run_id'], ['rag_runs.id'], name=op.f('fk_rag_run_sources_rag_run_id_rag_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_rag_run_sources'))
    )
    with op.batch_alter_table('rag_run_sources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_rag_run_sources_rag_run_id'), ['rag_run_id'], unique=False)

    op.create_table('recommendation_robustness_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('input_snapshot_json', sa.JSON(), nullable=False),
    sa.Column('baseline_json', sa.JSON(), nullable=False),
    sa.Column('variations_json', sa.JSON(), nullable=False),
    sa.Column('stability_results_json', sa.JSON(), nullable=False),
    sa.Column('sensitivity_matrix_json', sa.JSON(), nullable=False),
    sa.Column('dependency_flags_json', sa.JSON(), nullable=False),
    sa.Column('metrics_json', sa.JSON(), nullable=False),
    sa.Column('data_coverage_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('scoring_version', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_recommendation_robustness_runs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendation_robustness_runs'))
    )
    with op.batch_alter_table('recommendation_robustness_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recommendation_robustness_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendation_robustness_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendation_robustness_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendation_robustness_runs_user_id'), ['user_id'], unique=False)

    op.create_table('recommendations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('profile_signals_json', sa.JSON(), nullable=False),
    sa.Column('rag_sources_json', sa.JSON(), nullable=False),
    sa.Column('score_components_json', sa.JSON(), nullable=False),
    sa.Column('retrieval_metadata_json', sa.JSON(), nullable=False),
    sa.Column('relevance_score', sa.Float(), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('effort', sa.String(length=20), nullable=False),
    sa.Column('impact', sa.String(length=20), nullable=False),
    sa.Column('time_horizon', sa.String(length=30), nullable=False),
    sa.Column('estimated_duration', sa.String(length=80), nullable=False),
    sa.Column('prerequisites_json', sa.JSON(), nullable=False),
    sa.Column('first_action', sa.Text(), nullable=False),
    sa.Column('success_indicator', sa.Text(), nullable=False),
    sa.Column('ethical_cautions_json', sa.JSON(), nullable=False),
    sa.Column('what_to_verify_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('user_rating', sa.Integer(), nullable=True),
    sa.Column('user_feedback', sa.Text(), nullable=True),
    sa.Column('generation_version', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_recommendations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendations'))
    )
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recommendations_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendations_user_id'), ['user_id'], unique=False)

    op.create_table('research_export_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('export_format', sa.String(length=40), nullable=False),
    sa.Column('schema_version', sa.String(length=80), nullable=False),
    sa.Column('study_version', sa.String(length=80), nullable=False),
    sa.Column('preview_json', sa.JSON(), nullable=False),
    sa.Column('exclusions_json', sa.JSON(), nullable=False),
    sa.Column('demo_records_excluded', sa.Boolean(), nullable=False),
    sa.Column('generated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_export_runs_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_export_runs'))
    )
    with op.batch_alter_table('research_export_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_export_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_export_runs_study_id'), ['study_id'], unique=False)

    op.create_table('research_originality_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('pseudonymous_id', sa.String(length=120), nullable=False),
    sa.Column('consent_confirmed', sa.Boolean(), nullable=False),
    sa.Column('assigned_condition', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('baseline_json', sa.JSON(), nullable=False),
    sa.Column('experimental_json', sa.JSON(), nullable=False),
    sa.Column('feedback_json', sa.JSON(), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('export_filter_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_research_originality_sessions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_originality_sessions'))
    )
    with op.batch_alter_table('research_originality_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_assigned_condition'), ['assigned_condition'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_pseudonymous_id'), ['pseudonymous_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_originality_sessions_user_id'), ['user_id'], unique=False)

    op.create_table('research_participants',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('pseudonymous_id', sa.String(length=160), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_participants_study_id_research_studies')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_research_participants_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_participants'))
    )
    with op.batch_alter_table('research_participants', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_participants_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_participants_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_participants_pseudonymous_id'), ['pseudonymous_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_participants_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_participants_study_id'), ['study_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_participants_user_id'), ['user_id'], unique=False)

    op.create_table('research_questions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('construct', sa.String(length=120), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('scale_min', sa.Integer(), nullable=False),
    sa.Column('scale_max', sa.Integer(), nullable=False),
    sa.Column('scale_label', sa.String(length=120), nullable=False),
    sa.Column('instrument_type', sa.String(length=80), nullable=False),
    sa.Column('question_version', sa.String(length=80), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_questions_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_questions'))
    )
    with op.batch_alter_table('research_questions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_questions_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_questions_construct'), ['construct'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_questions_instrument_type'), ['instrument_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_questions_study_id'), ['study_id'], unique=False)

    op.create_table('research_study_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('protocol_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_study_versions_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_study_versions'))
    )
    with op.batch_alter_table('research_study_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_study_versions_study_id'), ['study_id'], unique=False)

    op.create_table('roadmaps',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_roadmaps_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmaps'))
    )
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmaps_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmaps_user_id'), ['user_id'], unique=False)

    op.create_table('star_stories',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('situation', sa.Text(), nullable=False),
    sa.Column('task', sa.Text(), nullable=False),
    sa.Column('action', sa.Text(), nullable=False),
    sa.Column('result', sa.Text(), nullable=False),
    sa.Column('reflection', sa.Text(), nullable=False),
    sa.Column('skills_demonstrated_json', sa.JSON(), nullable=False),
    sa.Column('related_job_requirements_json', sa.JSON(), nullable=False),
    sa.Column('evidence_links_json', sa.JSON(), nullable=False),
    sa.Column('dates_json', sa.JSON(), nullable=False),
    sa.Column('organisation_or_context', sa.String(length=255), nullable=False),
    sa.Column('confidentiality_status', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('claim_statuses_json', sa.JSON(), nullable=False),
    sa.Column('suitable_stages_json', sa.JSON(), nullable=False),
    sa.Column('tags_json', sa.JSON(), nullable=False),
    sa.Column('quality_status', sa.String(length=120), nullable=False),
    sa.Column('quality_json', sa.JSON(), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_star_stories_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_star_stories'))
    )
    with op.batch_alter_table('star_stories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_star_stories_confidentiality_status'), ['confidentiality_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_stories_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_stories_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_stories_quality_status'), ['quality_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_stories_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_stories_user_id'), ['user_id'], unique=False)

    op.create_table('support_programme_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('programme_id', sa.String(), nullable=False),
    sa.Column('norwegian_name', sa.String(length=255), nullable=False),
    sa.Column('english_name', sa.String(length=255), nullable=False),
    sa.Column('authority', sa.String(length=120), nullable=False),
    sa.Column('jurisdiction', sa.String(length=80), nullable=False),
    sa.Column('official_url', sa.Text(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('target_group', sa.Text(), nullable=False),
    sa.Column('known_conditions_json', sa.JSON(), nullable=False),
    sa.Column('required_information_json', sa.JSON(), nullable=False),
    sa.Column('application_or_contact_route', sa.Text(), nullable=False),
    sa.Column('documents_json', sa.JSON(), nullable=False),
    sa.Column('deadlines_json', sa.JSON(), nullable=False),
    sa.Column('incompatibilities_json', sa.JSON(), nullable=False),
    sa.Column('source_publication_date', sa.String(length=40), nullable=False),
    sa.Column('last_checked_date', sa.String(length=40), nullable=False),
    sa.Column('rule_version', sa.String(length=80), nullable=False),
    sa.Column('verification_status', sa.String(length=80), nullable=False),
    sa.Column('human_assessment_required', sa.Boolean(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('categories_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['programme_id'], ['support_programmes.id'], name=op.f('fk_support_programme_versions_programme_id_support_programmes')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_programme_versions'))
    )
    with op.batch_alter_table('support_programme_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_programme_versions_programme_id'), ['programme_id'], unique=False)

    op.create_table('advisor_comments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('share_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('adviser_display_name', sa.String(length=160), nullable=False),
    sa.Column('adviser_role', sa.String(length=80), nullable=False),
    sa.Column('target_type', sa.String(length=80), nullable=False),
    sa.Column('target_id', sa.String(), nullable=False),
    sa.Column('suggestion_type', sa.String(length=120), nullable=False),
    sa.Column('comment_text', sa.Text(), nullable=False),
    sa.Column('evidence_validation', sa.String(length=120), nullable=False),
    sa.Column('supporting_reference', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('user_response', sa.Text(), nullable=False),
    sa.Column('provenance', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['share_id'], ['advisor_shares.id'], name=op.f('fk_advisor_comments_share_id_advisor_shares')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_advisor_comments'))
    )
    with op.batch_alter_table('advisor_comments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_advisor_comments_adviser_role'), ['adviser_role'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_evidence_validation'), ['evidence_validation'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_share_id'), ['share_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_suggestion_type'), ['suggestion_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_target_id'), ['target_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_advisor_comments_target_type'), ['target_type'], unique=False)

    op.create_table('ai_readiness_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('literacy_level', sa.String(length=40), nullable=False),
    sa.Column('readiness_level', sa.String(length=40), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_ai_readiness_results_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_readiness_results_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_readiness_results'))
    )
    with op.batch_alter_table('ai_readiness_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_readiness_results_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_readiness_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_readiness_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_ai_readiness_results_user_id'), ['user_id'], unique=False)

    op.create_table('application_documents',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('job_application_id', sa.String(), nullable=True),
    sa.Column('document_type', sa.String(length=60), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('language', sa.String(length=40), nullable=False),
    sa.Column('variant', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('evidence_lock_status', sa.String(length=80), nullable=False),
    sa.Column('readiness_status', sa.String(length=80), nullable=False),
    sa.Column('export_warning_acknowledged', sa.Boolean(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_application_documents_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_application_documents_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_documents'))
    )
    with op.batch_alter_table('application_documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_documents_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_document_type'), ['document_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_evidence_lock_status'), ['evidence_lock_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_job_application_id'), ['job_application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_readiness_status'), ['readiness_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_documents_user_id'), ['user_id'], unique=False)

    op.create_table('assessment_interpretations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('source_type', sa.String(length=40), nullable=False),
    sa.Column('confirmation_status', sa.String(length=40), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('corrections_json', sa.JSON(), nullable=False),
    sa.Column('reflection_answers_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_assessment_interpretations_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_assessment_interpretations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_interpretations'))
    )
    with op.batch_alter_table('assessment_interpretations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_interpretations_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_interpretations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_interpretations_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_interpretations_user_id'), ['user_id'], unique=False)

    op.create_table('assessment_responses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('module_id', sa.String(length=80), nullable=False),
    sa.Column('item_id', sa.String(length=120), nullable=False),
    sa.Column('response_type', sa.String(length=40), nullable=False),
    sa.Column('numeric_value', sa.Float(), nullable=True),
    sa.Column('text_value', sa.Text(), nullable=True),
    sa.Column('option_value', sa.String(length=255), nullable=True),
    sa.Column('payload_json', sa.JSON(), nullable=False),
    sa.Column('excluded_from_recommendations', sa.Boolean(), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('source_type', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_assessment_responses_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_assessment_responses_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_responses'))
    )
    with op.batch_alter_table('assessment_responses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_responses_item_id'), ['item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_responses_module_id'), ['module_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_responses_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_responses_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_responses_user_id'), ['user_id'], unique=False)

    op.create_table('assessment_scores',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('score_type', sa.String(length=50), nullable=False),
    sa.Column('dimension', sa.String(length=100), nullable=False),
    sa.Column('raw_score', sa.Float(), nullable=False),
    sa.Column('normalized_score', sa.Float(), nullable=False),
    sa.Column('label', sa.String(length=120), nullable=False),
    sa.Column('interpretation', sa.Text(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('source_type', sa.String(length=30), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('score_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_assessment_scores_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_assessment_scores_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assessment_scores'))
    )
    with op.batch_alter_table('assessment_scores', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assessment_scores_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_scores_dimension'), ['dimension'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_scores_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_scores_score_type'), ['score_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_scores_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assessment_scores_user_id'), ['user_id'], unique=False)

    op.create_table('browser_job_captures',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('extension_connection_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('source_url', sa.Text(), nullable=False),
    sa.Column('page_title', sa.String(length=255), nullable=False),
    sa.Column('detected_title', sa.String(length=255), nullable=False),
    sa.Column('detected_employer', sa.String(length=255), nullable=False),
    sa.Column('source_domain', sa.String(length=255), nullable=False),
    sa.Column('captured_text_raw', sa.Text(), nullable=False),
    sa.Column('sanitised_text', sa.Text(), nullable=False),
    sa.Column('selected_text', sa.Text(), nullable=False),
    sa.Column('confirmed_fields_json', sa.JSON(), nullable=False),
    sa.Column('capture_method', sa.String(length=120), nullable=False),
    sa.Column('requested_action', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('content_hash', sa.String(length=128), nullable=False),
    sa.Column('quality_warnings_json', sa.JSON(), nullable=False),
    sa.Column('extension_version', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('captured_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['extension_connection_id'], ['browser_extension_connections.id'], name=op.f('fk_browser_job_captures_extension_connection_id_browser_extension_connections')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_browser_job_captures_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_browser_job_captures_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_browser_job_captures')),
    sa.UniqueConstraint('profile_id', 'source_url', 'content_hash', name='uq_browser_capture_profile_url_hash')
    )
    with op.batch_alter_table('browser_job_captures', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_browser_job_captures_capture_method'), ['capture_method'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_captured_at'), ['captured_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_content_hash'), ['content_hash'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_extension_connection_id'), ['extension_connection_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_requested_action'), ['requested_action'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_source_domain'), ['source_domain'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_browser_job_captures_user_id'), ['user_id'], unique=False)

    op.create_table('career_experiment_criteria',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('rubric_id', sa.String(), nullable=False),
    sa.Column('criterion_id', sa.String(length=120), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('rating_scale_json', sa.JSON(), nullable=False),
    sa.Column('evidence_requirement', sa.Text(), nullable=False),
    sa.Column('interpretation_json', sa.JSON(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['rubric_id'], ['career_experiment_rubrics.id'], name=op.f('fk_career_experiment_criteria_rubric_id_career_experiment_rubrics')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_criteria'))
    )
    with op.batch_alter_table('career_experiment_criteria', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_criteria_criterion_id'), ['criterion_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_criteria_rubric_id'), ['rubric_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_criteria_skill_id'), ['skill_id'], unique=False)

    op.create_table('career_interest_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('combined_profile', sa.String(length=160), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_career_interest_results_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_interest_results_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_interest_results'))
    )
    with op.batch_alter_table('career_interest_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_interest_results_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_interest_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_interest_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_interest_results_user_id'), ['user_id'], unique=False)

    op.create_table('career_matches',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('role_template_id', sa.String(), nullable=True),
    sa.Column('category', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('role_family', sa.String(length=120), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('alignment_score', sa.Float(), nullable=False),
    sa.Column('alignment_label', sa.String(length=80), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('supporting_factors_json', sa.JSON(), nullable=False),
    sa.Column('conflicting_factors_json', sa.JSON(), nullable=False),
    sa.Column('missing_skills_json', sa.JSON(), nullable=False),
    sa.Column('transferable_skills_json', sa.JSON(), nullable=False),
    sa.Column('ai_opportunities_json', sa.JSON(), nullable=False),
    sa.Column('next_step', sa.Text(), nullable=False),
    sa.Column('transition_difficulty', sa.String(length=80), nullable=False),
    sa.Column('time_horizon', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('user_feedback', sa.Text(), nullable=True),
    sa.Column('user_priority', sa.Integer(), nullable=True),
    sa.Column('assumptions_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_career_matches_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_matches_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_matches'))
    )
    with op.batch_alter_table('career_matches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_matches_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_role_template_id'), ['role_template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_matches_user_id'), ['user_id'], unique=False)

    op.create_table('career_profile_entries',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('master_profile_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('entry_type', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('start_date', sa.String(length=40), nullable=True),
    sa.Column('end_date', sa.String(length=40), nullable=True),
    sa.Column('origin', sa.String(length=80), nullable=False),
    sa.Column('source_id', sa.String(), nullable=True),
    sa.Column('user_confirmation_state', sa.String(length=60), nullable=False),
    sa.Column('last_update', sa.DateTime(), nullable=False),
    sa.Column('evidence_relationship_json', sa.JSON(), nullable=False),
    sa.Column('inclusion_permission', sa.String(length=80), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['master_profile_id'], ['master_career_profiles.id'], name=op.f('fk_career_profile_entries_master_profile_id_master_career_profiles')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_profile_entries'))
    )
    with op.batch_alter_table('career_profile_entries', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_profile_entries_entry_type'), ['entry_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_profile_entries_master_profile_id'), ['master_profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_profile_entries_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_profile_entries_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_profile_entries_user_confirmation_state'), ['user_confirmation_state'], unique=False)

    op.create_table('career_transition_paths',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('simulation_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('role_slug', sa.String(length=180), nullable=False),
    sa.Column('path_type', sa.String(length=120), nullable=False),
    sa.Column('objectives_json', sa.JSON(), nullable=False),
    sa.Column('normalised_objectives_json', sa.JSON(), nullable=False),
    sa.Column('objective_directions_json', sa.JSON(), nullable=False),
    sa.Column('is_pareto_optimal', sa.Boolean(), nullable=False),
    sa.Column('dominated_by_json', sa.JSON(), nullable=False),
    sa.Column('dominated_explanation', sa.Text(), nullable=False),
    sa.Column('existing_assets_json', sa.JSON(), nullable=False),
    sa.Column('missing_assets_json', sa.JSON(), nullable=False),
    sa.Column('required_experiments_json', sa.JSON(), nullable=False),
    sa.Column('required_learning_json', sa.JSON(), nullable=False),
    sa.Column('transition_stages_json', sa.JSON(), nullable=False),
    sa.Column('relevant_jobs_json', sa.JSON(), nullable=False),
    sa.Column('support_opportunities_json', sa.JSON(), nullable=False),
    sa.Column('assumptions_json', sa.JSON(), nullable=False),
    sa.Column('uncertainties_json', sa.JSON(), nullable=False),
    sa.Column('reversibility', sa.String(length=80), nullable=False),
    sa.Column('next_action', sa.Text(), nullable=False),
    sa.Column('user_selection_status', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['simulation_id'], ['career_transition_simulations.id'], name=op.f('fk_career_transition_paths_simulation_id_career_transition_simulations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_transition_paths'))
    )
    with op.batch_alter_table('career_transition_paths', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_transition_paths_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_paths_is_pareto_optimal'), ['is_pareto_optimal'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_paths_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_paths_role_slug'), ['role_slug'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_paths_simulation_id'), ['simulation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_transition_paths_title'), ['title'], unique=False)

    op.create_table('change_readiness_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('feasibility_label', sa.String(length=120), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('constraints_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_change_readiness_results_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_change_readiness_results_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_change_readiness_results'))
    )
    with op.batch_alter_table('change_readiness_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_change_readiness_results_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_change_readiness_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_change_readiness_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_change_readiness_results_user_id'), ['user_id'], unique=False)

    op.create_table('immediate_action_plans',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_loss_profile_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_loss_profile_id'], ['job_loss_profiles.id'], name=op.f('fk_immediate_action_plans_job_loss_profile_id_job_loss_profiles')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_immediate_action_plans_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_immediate_action_plans'))
    )
    with op.batch_alter_table('immediate_action_plans', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_immediate_action_plans_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_plans_job_loss_profile_id'), ['job_loss_profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_plans_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_plans_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_plans_user_id'), ['user_id'], unique=False)

    op.create_table('job_analysis_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['job_analyses.id'], name=op.f('fk_job_analysis_versions_analysis_id_job_analyses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_analysis_versions'))
    )
    with op.batch_alter_table('job_analysis_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_analysis_versions_analysis_id'), ['analysis_id'], unique=False)

    op.create_table('job_readiness_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('readiness_label', sa.String(length=80), nullable=False),
    sa.Column('reasons_json', sa.JSON(), nullable=False),
    sa.Column('blockers_json', sa.JSON(), nullable=False),
    sa.Column('recommended_actions_json', sa.JSON(), nullable=False),
    sa.Column('deterministic_version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['job_analyses.id'], name=op.f('fk_job_readiness_results_analysis_id_job_analyses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_readiness_results'))
    )
    with op.batch_alter_table('job_readiness_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_readiness_results_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_readiness_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_readiness_results_readiness_label'), ['readiness_label'], unique=False)

    op.create_table('job_requirements',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('requirement_text', sa.Text(), nullable=False),
    sa.Column('requirement_category', sa.String(length=80), nullable=False),
    sa.Column('requirement_type', sa.String(length=60), nullable=False),
    sa.Column('source_excerpt', sa.Text(), nullable=False),
    sa.Column('source_location', sa.String(length=160), nullable=False),
    sa.Column('extraction_method', sa.String(length=80), nullable=False),
    sa.Column('confidence', sa.String(length=60), nullable=False),
    sa.Column('user_confirmation_state', sa.String(length=60), nullable=False),
    sa.Column('normalised_skill_id', sa.String(length=160), nullable=True),
    sa.Column('esco_uri', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['job_analyses.id'], name=op.f('fk_job_requirements_analysis_id_job_analyses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_requirements'))
    )
    with op.batch_alter_table('job_requirements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_requirements_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_normalised_skill_id'), ['normalised_skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_requirement_category'), ['requirement_category'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_requirement_type'), ['requirement_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirements_user_confirmation_state'), ['user_confirmation_state'], unique=False)

    op.create_table('learning_resource_objectives',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('resource_id', sa.String(), nullable=False),
    sa.Column('objective_key', sa.String(length=160), nullable=False),
    sa.Column('coverage_level', sa.String(length=40), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], name=op.f('fk_learning_resource_objectives_resource_id_learning_resources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_objectives'))
    )
    with op.batch_alter_table('learning_resource_objectives', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_objectives_objective_key'), ['objective_key'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_objectives_resource_id'), ['resource_id'], unique=False)

    op.create_table('learning_resource_skills',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('resource_id', sa.String(), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('coverage_level', sa.String(length=40), nullable=False),
    sa.Column('target_level', sa.String(length=40), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], name=op.f('fk_learning_resource_skills_resource_id_learning_resources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_skills'))
    )
    with op.batch_alter_table('learning_resource_skills', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_skills_resource_id'), ['resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_skills_skill_id'), ['skill_id'], unique=False)

    op.create_table('learning_resource_verifications',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('resource_id', sa.String(), nullable=False),
    sa.Column('verification_status', sa.String(length=60), nullable=False),
    sa.Column('verified_at', sa.DateTime(), nullable=True),
    sa.Column('verified_by', sa.String(length=120), nullable=True),
    sa.Column('verification_method', sa.String(length=120), nullable=False),
    sa.Column('last_availability_check', sa.DateTime(), nullable=True),
    sa.Column('external_metadata_timestamp', sa.DateTime(), nullable=True),
    sa.Column('verification_notes', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], name=op.f('fk_learning_resource_verifications_resource_id_learning_resources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_verifications'))
    )
    with op.batch_alter_table('learning_resource_verifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_verifications_resource_id'), ['resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_verifications_verification_status'), ['verification_status'], unique=False)

    op.create_table('learning_resource_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('resource_id', sa.String(), nullable=False),
    sa.Column('metadata_version', sa.String(length=60), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['resource_id'], ['learning_resources.id'], name=op.f('fk_learning_resource_versions_resource_id_learning_resources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_versions'))
    )
    with op.batch_alter_table('learning_resource_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_versions_resource_id'), ['resource_id'], unique=False)

    op.create_table('messages',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('conversation_id', sa.String(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('input_mode', sa.String(length=20), nullable=True),
    sa.Column('audio_url', sa.String(length=512), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name=op.f('fk_messages_conversation_id_conversations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_messages'))
    )
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_messages_conversation_id'), ['conversation_id'], unique=False)

    op.create_table('personality_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_personality_results_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_personality_results_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_personality_results'))
    )
    with op.batch_alter_table('personality_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_personality_results_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_personality_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_personality_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_personality_results_user_id'), ['user_id'], unique=False)

    op.create_table('recommendation_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], name=op.f('fk_recommendation_events_recommendation_id_recommendations')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_recommendation_events_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendation_events'))
    )
    with op.batch_alter_table('recommendation_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recommendation_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_recommendation_events_recommendation_id'), ['recommendation_id'], unique=False)

    op.create_table('recommendation_feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('relevant', sa.Boolean(), nullable=True),
    sa.Column('feedback_text', sa.Text(), nullable=True),
    sa.Column('reason_code', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], name=op.f('fk_recommendation_feedback_recommendation_id_recommendations')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_recommendation_feedback_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendation_feedback'))
    )
    with op.batch_alter_table('recommendation_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_recommendation_feedback_recommendation_id'), ['recommendation_id'], unique=False)

    op.create_table('research_assignments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('participant_id', sa.String(), nullable=False),
    sa.Column('assignment_type', sa.String(length=80), nullable=False),
    sa.Column('workflow', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['research_participants.id'], name=op.f('fk_research_assignments_participant_id_research_participants')),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_assignments_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_assignments'))
    )
    with op.batch_alter_table('research_assignments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_assignments_participant_id'), ['participant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_assignments_study_id'), ['study_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_assignments_workflow'), ['workflow'], unique=False)

    op.create_table('research_consents',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('participant_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('consent_version', sa.String(length=80), nullable=False),
    sa.Column('consent_given', sa.Boolean(), nullable=False),
    sa.Column('withdrawn_at', sa.DateTime(), nullable=True),
    sa.Column('consent_text_snapshot_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['research_participants.id'], name=op.f('fk_research_consents_participant_id_research_participants')),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_consents_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_consents'))
    )
    with op.batch_alter_table('research_consents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_consents_consent_given'), ['consent_given'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_consents_participant_id'), ['participant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_consents_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_consents_study_id'), ['study_id'], unique=False)

    op.create_table('research_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('participant_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('workflow_stage', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['research_participants.id'], name=op.f('fk_research_sessions_participant_id_research_participants')),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_sessions_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_sessions'))
    )
    with op.batch_alter_table('research_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_sessions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_sessions_participant_id'), ['participant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_sessions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_sessions_study_id'), ['study_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_sessions_workflow_stage'), ['workflow_stage'], unique=False)

    op.create_table('roadmap_actions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('recommendation_id', sa.String(), nullable=True),
    sa.Column('horizon', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('first_step', sa.Text(), nullable=False),
    sa.Column('success_criteria', sa.Text(), nullable=False),
    sa.Column('estimated_minutes', sa.Integer(), nullable=True),
    sa.Column('effort', sa.String(), nullable=False),
    sa.Column('impact', sa.String(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('progress_percentage', sa.Integer(), nullable=False),
    sa.Column('due_date', sa.String(), nullable=True),
    sa.Column('scheduled_date', sa.String(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('skipped_at', sa.DateTime(), nullable=True),
    sa.Column('skip_reason', sa.Text(), nullable=True),
    sa.Column('user_notes', sa.Text(), nullable=False),
    sa.Column('source_type', sa.String(), nullable=False),
    sa.Column('profile_signals_json', sa.JSON(), nullable=False),
    sa.Column('rag_sources_json', sa.JSON(), nullable=False),
    sa.Column('ethical_cautions_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], name=op.f('fk_roadmap_actions_roadmap_id_roadmaps')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_roadmap_actions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_actions'))
    )
    with op.batch_alter_table('roadmap_actions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_actions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_actions_recommendation_id'), ['recommendation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_actions_roadmap_id'), ['roadmap_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_actions_user_id'), ['user_id'], unique=False)

    op.create_table('roadmap_checkins',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('check_in_type', sa.String(), nullable=False),
    sa.Column('energy_level', sa.Integer(), nullable=True),
    sa.Column('confidence_level', sa.Integer(), nullable=True),
    sa.Column('perceived_progress', sa.Integer(), nullable=True),
    sa.Column('main_blocker', sa.Text(), nullable=False),
    sa.Column('what_worked', sa.Text(), nullable=False),
    sa.Column('what_changed', sa.Text(), nullable=False),
    sa.Column('user_note', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], name=op.f('fk_roadmap_checkins_roadmap_id_roadmaps')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_roadmap_checkins_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_checkins'))
    )
    with op.batch_alter_table('roadmap_checkins', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_checkins_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_checkins_roadmap_id'), ['roadmap_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_checkins_user_id'), ['user_id'], unique=False)

    op.create_table('roadmap_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_id', sa.String(), nullable=False),
    sa.Column('action_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], name=op.f('fk_roadmap_events_roadmap_id_roadmaps')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_roadmap_events_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_events'))
    )
    with op.batch_alter_table('roadmap_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_events_action_id'), ['action_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_events_roadmap_id'), ['roadmap_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_events_user_id'), ['user_id'], unique=False)

    op.create_table('roadmap_milestones',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('target_date', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('success_criteria', sa.Text(), nullable=False),
    sa.Column('evidence_note', sa.Text(), nullable=False),
    sa.Column('linked_action_ids', sa.JSON(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], name=op.f('fk_roadmap_milestones_roadmap_id_roadmaps')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_milestones'))
    )
    with op.batch_alter_table('roadmap_milestones', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_milestones_roadmap_id'), ['roadmap_id'], unique=False)

    op.create_table('roadmap_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['roadmap_id'], ['roadmaps.id'], name=op.f('fk_roadmap_versions_roadmap_id_roadmaps')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_versions'))
    )
    with op.batch_alter_table('roadmap_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_versions_roadmap_id'), ['roadmap_id'], unique=False)

    op.create_table('skills_inventory',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('category', sa.String(length=80), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('skill_label', sa.String(length=160), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('evidence_status', sa.String(length=50), nullable=False),
    sa.Column('evidence_note', sa.Text(), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_skills_inventory_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_skills_inventory_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skills_inventory'))
    )
    with op.batch_alter_table('skills_inventory', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skills_inventory_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_skills_inventory_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_skills_inventory_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skills_inventory_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skills_inventory_skill_id'), ['skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skills_inventory_user_id'), ['user_id'], unique=False)

    op.create_table('star_story_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('story_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['story_id'], ['star_stories.id'], name=op.f('fk_star_story_versions_story_id_star_stories')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_star_story_versions'))
    )
    with op.batch_alter_table('star_story_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_star_story_versions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_star_story_versions_story_id'), ['story_id'], unique=False)

    op.create_table('support_rules',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('programme_id', sa.String(), nullable=False),
    sa.Column('programme_version_id', sa.String(), nullable=False),
    sa.Column('rule_version', sa.String(length=80), nullable=False),
    sa.Column('conditions_json', sa.JSON(), nullable=False),
    sa.Column('missing_information_fields_json', sa.JSON(), nullable=False),
    sa.Column('relevance_logic_json', sa.JSON(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['programme_id'], ['support_programmes.id'], name=op.f('fk_support_rules_programme_id_support_programmes')),
    sa.ForeignKeyConstraint(['programme_version_id'], ['support_programme_versions.id'], name=op.f('fk_support_rules_programme_version_id_support_programme_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_rules'))
    )
    with op.batch_alter_table('support_rules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_rules_active'), ['active'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_rules_programme_id'), ['programme_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_rules_programme_version_id'), ['programme_version_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_rules_rule_version'), ['rule_version'], unique=False)

    op.create_table('support_screenings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_loss_profile_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('country', sa.String(length=80), nullable=False),
    sa.Column('input_values_json', sa.JSON(), nullable=False),
    sa.Column('unknown_fields_json', sa.JSON(), nullable=False),
    sa.Column('preliminary_result_json', sa.JSON(), nullable=False),
    sa.Column('source_references_json', sa.JSON(), nullable=False),
    sa.Column('rule_version', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_loss_profile_id'], ['job_loss_profiles.id'], name=op.f('fk_support_screenings_job_loss_profile_id_job_loss_profiles')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_support_screenings_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_screenings'))
    )
    with op.batch_alter_table('support_screenings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_screenings_country'), ['country'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screenings_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screenings_job_loss_profile_id'), ['job_loss_profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screenings_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screenings_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screenings_user_id'), ['user_id'], unique=False)

    op.create_table('work_value_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('top_values_json', sa.JSON(), nullable=False),
    sa.Column('conflicts_json', sa.JSON(), nullable=False),
    sa.Column('results_json', sa.JSON(), nullable=False),
    sa.Column('assessment_version', sa.String(length=50), nullable=False),
    sa.Column('scoring_version', sa.String(length=50), nullable=False),
    sa.Column('confirmation_status', sa.String(length=30), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['assessment_sessions.id'], name=op.f('fk_work_value_results_session_id_assessment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_work_value_results_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_work_value_results'))
    )
    with op.batch_alter_table('work_value_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_work_value_results_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_work_value_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_work_value_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_work_value_results_user_id'), ['user_id'], unique=False)

    op.create_table('application_document_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('warnings_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['application_documents.id'], name=op.f('fk_application_document_versions_document_id_application_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_document_versions'))
    )
    with op.batch_alter_table('application_document_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_document_versions_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_document_versions_profile_id'), ['profile_id'], unique=False)

    op.create_table('career_decisions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('decision_type', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_career_decisions_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_decisions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_decisions'))
    )
    with op.batch_alter_table('career_decisions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_decisions_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decisions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decisions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decisions_user_id'), ['user_id'], unique=False)

    op.create_table('career_experiment_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('experiment_template_id', sa.String(), nullable=False),
    sa.Column('hypothesis_id', sa.String(), nullable=True),
    sa.Column('roadmap_action_id', sa.String(), nullable=True),
    sa.Column('mode', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('confidence_label', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.Column('evaluated_at', sa.DateTime(), nullable=True),
    sa.Column('archived_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_career_experiment_sessions_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['experiment_template_id'], ['career_experiment_templates.id'], name=op.f('fk_career_experiment_sessions_experiment_template_id_career_experiment_templates')),
    sa.ForeignKeyConstraint(['roadmap_action_id'], ['roadmap_actions.id'], name=op.f('fk_career_experiment_sessions_roadmap_action_id_roadmap_actions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_experiment_sessions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_sessions'))
    )
    with op.batch_alter_table('career_experiment_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_experiment_template_id'), ['experiment_template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_hypothesis_id'), ['hypothesis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_mode'), ['mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_roadmap_action_id'), ['roadmap_action_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_sessions_user_id'), ['user_id'], unique=False)

    op.create_table('career_hypotheses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('role_template_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('role_family', sa.String(length=160), nullable=False),
    sa.Column('statement', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('uncertainty_label', sa.String(length=80), nullable=False),
    sa.Column('current_alignment_score', sa.Float(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_career_hypotheses_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_hypotheses_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_hypotheses'))
    )
    with op.batch_alter_table('career_hypotheses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_hypotheses_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_role_family'), ['role_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_role_template_id'), ['role_template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypotheses_user_id'), ['user_id'], unique=False)

    op.create_table('career_match_factors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('match_id', sa.String(), nullable=False),
    sa.Column('factor_type', sa.String(length=80), nullable=False),
    sa.Column('label', sa.String(length=160), nullable=False),
    sa.Column('raw_value', sa.Float(), nullable=False),
    sa.Column('normalized_value', sa.Float(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('polarity', sa.String(length=20), nullable=False),
    sa.Column('evidence_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['match_id'], ['career_matches.id'], name=op.f('fk_career_match_factors_match_id_career_matches')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_match_factors'))
    )
    with op.batch_alter_table('career_match_factors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_match_factors_factor_type'), ['factor_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_match_factors_match_id'), ['match_id'], unique=False)

    op.create_table('document_sections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('section_type', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('include_in_export', sa.Boolean(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['application_documents.id'], name=op.f('fk_document_sections_document_id_application_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_sections'))
    )
    with op.batch_alter_table('document_sections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_sections_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_sections_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_sections_section_type'), ['section_type'], unique=False)

    op.create_table('immediate_action_items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('plan_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('urgency', sa.String(length=80), nullable=False),
    sa.Column('official_source_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('due_date', sa.String(length=40), nullable=True),
    sa.Column('user_confirmation', sa.Boolean(), nullable=False),
    sa.Column('order_index', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['immediate_action_plans.id'], name=op.f('fk_immediate_action_items_plan_id_immediate_action_plans')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_immediate_action_items'))
    )
    with op.batch_alter_table('immediate_action_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_immediate_action_items_plan_id'), ['plan_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_items_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_items_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_immediate_action_items_urgency'), ['urgency'], unique=False)

    op.create_table('job_analysis_corrections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('requirement_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('correction_type', sa.String(length=80), nullable=False),
    sa.Column('before_json', sa.JSON(), nullable=False),
    sa.Column('after_json', sa.JSON(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['job_analyses.id'], name=op.f('fk_job_analysis_corrections_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['requirement_id'], ['job_requirements.id'], name=op.f('fk_job_analysis_corrections_requirement_id_job_requirements')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_job_analysis_corrections_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_analysis_corrections'))
    )
    with op.batch_alter_table('job_analysis_corrections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_analysis_corrections_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analysis_corrections_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analysis_corrections_requirement_id'), ['requirement_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_analysis_corrections_user_id'), ['user_id'], unique=False)

    op.create_table('job_applications',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('cv_document_id', sa.String(), nullable=True),
    sa.Column('cover_letter_document_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('organisation', sa.String(length=255), nullable=False),
    sa.Column('source', sa.String(length=120), nullable=False),
    sa.Column('application_date', sa.String(length=40), nullable=True),
    sa.Column('deadline', sa.String(length=80), nullable=True),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('contacts_json', sa.JSON(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('next_action', sa.Text(), nullable=False),
    sa.Column('roadmap_action_id', sa.String(), nullable=True),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_job_applications_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['cover_letter_document_id'], ['application_documents.id'], name=op.f('fk_job_applications_cover_letter_document_id_application_documents')),
    sa.ForeignKeyConstraint(['cv_document_id'], ['application_documents.id'], name=op.f('fk_job_applications_cv_document_id_application_documents')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_job_applications_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['job_id'], ['job_postings.id'], name=op.f('fk_job_applications_job_id_job_postings')),
    sa.ForeignKeyConstraint(['roadmap_action_id'], ['roadmap_actions.id'], name=op.f('fk_job_applications_roadmap_action_id_roadmap_actions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_job_applications_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_applications'))
    )
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_applications_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_cover_letter_document_id'), ['cover_letter_document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_cv_document_id'), ['cv_document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_roadmap_action_id'), ['roadmap_action_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_applications_user_id'), ['user_id'], unique=False)

    op.create_table('research_interaction_metrics',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('participant_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('metric_name', sa.String(length=120), nullable=False),
    sa.Column('metric_value', sa.Float(), nullable=False),
    sa.Column('workflow_stage', sa.String(length=80), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('raw_text_excluded', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['research_participants.id'], name=op.f('fk_research_interaction_metrics_participant_id_research_participants')),
    sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name=op.f('fk_research_interaction_metrics_session_id_research_sessions')),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_interaction_metrics_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_interaction_metrics'))
    )
    with op.batch_alter_table('research_interaction_metrics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_interaction_metrics_metric_name'), ['metric_name'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_interaction_metrics_participant_id'), ['participant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_interaction_metrics_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_interaction_metrics_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_interaction_metrics_study_id'), ['study_id'], unique=False)

    op.create_table('research_responses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('study_id', sa.String(), nullable=False),
    sa.Column('participant_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('question_id', sa.String(), nullable=False),
    sa.Column('workflow_stage', sa.String(length=80), nullable=False),
    sa.Column('numeric_response', sa.Float(), nullable=True),
    sa.Column('text_response_redacted', sa.Text(), nullable=False),
    sa.Column('response_metadata_json', sa.JSON(), nullable=False),
    sa.Column('question_version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['research_participants.id'], name=op.f('fk_research_responses_participant_id_research_participants')),
    sa.ForeignKeyConstraint(['question_id'], ['research_questions.id'], name=op.f('fk_research_responses_question_id_research_questions')),
    sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], name=op.f('fk_research_responses_session_id_research_sessions')),
    sa.ForeignKeyConstraint(['study_id'], ['research_studies.id'], name=op.f('fk_research_responses_study_id_research_studies')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_research_responses'))
    )
    with op.batch_alter_table('research_responses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_research_responses_participant_id'), ['participant_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_responses_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_responses_question_id'), ['question_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_responses_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_responses_study_id'), ['study_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_research_responses_workflow_stage'), ['workflow_stage'], unique=False)

    op.create_table('skill_evidence',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('skill_inventory_id', sa.String(), nullable=False),
    sa.Column('evidence_type', sa.String(length=60), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('verification_status', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['skill_inventory_id'], ['skills_inventory.id'], name=op.f('fk_skill_evidence_skill_inventory_id_skills_inventory')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_evidence'))
    )
    with op.batch_alter_table('skill_evidence', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_evidence_skill_inventory_id'), ['skill_inventory_id'], unique=False)

    op.create_table('skill_gap_analyses',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('role_template_id', sa.String(), nullable=True),
    sa.Column('analysis_version', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('hard_filters_json', sa.JSON(), nullable=False),
    sa.Column('context_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_skill_gap_analyses_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_skill_gap_analyses_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_gap_analyses'))
    )
    with op.batch_alter_table('skill_gap_analyses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_role_template_id'), ['role_template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_analyses_user_id'), ['user_id'], unique=False)

    op.create_table('support_screening_factors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('screening_id', sa.String(), nullable=False),
    sa.Column('programme_id', sa.String(), nullable=False),
    sa.Column('input_values_json', sa.JSON(), nullable=False),
    sa.Column('unknown_fields_json', sa.JSON(), nullable=False),
    sa.Column('preliminary_label', sa.String(length=80), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('source_references_json', sa.JSON(), nullable=False),
    sa.Column('last_checked_date', sa.String(length=40), nullable=False),
    sa.Column('rule_version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['programme_id'], ['support_programmes.id'], name=op.f('fk_support_screening_factors_programme_id_support_programmes')),
    sa.ForeignKeyConstraint(['screening_id'], ['support_screenings.id'], name=op.f('fk_support_screening_factors_screening_id_support_screenings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_screening_factors'))
    )
    with op.batch_alter_table('support_screening_factors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_screening_factors_preliminary_label'), ['preliminary_label'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screening_factors_programme_id'), ['programme_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_screening_factors_screening_id'), ['screening_id'], unique=False)

    op.create_table('supported_path_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('market_snapshot_id', sa.String(), nullable=True),
    sa.Column('support_screening_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['market_snapshot_id'], ['market_snapshots.id'], name=op.f('fk_supported_path_runs_market_snapshot_id_market_snapshots')),
    sa.ForeignKeyConstraint(['support_screening_id'], ['support_screenings.id'], name=op.f('fk_supported_path_runs_support_screening_id_support_screenings')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_supported_path_runs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_supported_path_runs'))
    )
    with op.batch_alter_table('supported_path_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supported_path_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_runs_market_snapshot_id'), ['market_snapshot_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_runs_support_screening_id'), ['support_screening_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_runs_user_id'), ['user_id'], unique=False)

    op.create_table('adaptive_experiment_recommendations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('experiment_template_id', sa.String(), nullable=True),
    sa.Column('career_experiment_session_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('experiment_type', sa.String(length=120), nullable=False),
    sa.Column('priority_band', sa.String(length=80), nullable=False),
    sa.Column('score_internal', sa.Float(), nullable=False),
    sa.Column('rank_position', sa.Integer(), nullable=False),
    sa.Column('related_hypotheses_json', sa.JSON(), nullable=False),
    sa.Column('uncertainty_json', sa.JSON(), nullable=False),
    sa.Column('skills_tested_json', sa.JSON(), nullable=False),
    sa.Column('evidence_expected_json', sa.JSON(), nullable=False),
    sa.Column('expected_evidence_gain_json', sa.JSON(), nullable=False),
    sa.Column('actual_evidence_gain_json', sa.JSON(), nullable=False),
    sa.Column('estimated_duration', sa.String(length=80), nullable=False),
    sa.Column('estimated_effort', sa.String(length=80), nullable=False),
    sa.Column('estimated_cost', sa.String(length=80), nullable=False),
    sa.Column('market_relevance', sa.String(length=80), nullable=False),
    sa.Column('cross_path_usefulness', sa.String(length=80), nullable=False),
    sa.Column('accessibility_considerations_json', sa.JSON(), nullable=False),
    sa.Column('support_options_json', sa.JSON(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('score_components_json', sa.JSON(), nullable=False),
    sa.Column('alternatives_json', sa.JSON(), nullable=False),
    sa.Column('data_quality_warnings_json', sa.JSON(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('user_confirmation_status', sa.String(length=80), nullable=False),
    sa.Column('rejection_reason', sa.String(length=120), nullable=False),
    sa.Column('rejection_feedback_json', sa.JSON(), nullable=False),
    sa.Column('roadmap_confirmation_status', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_experiment_session_id'], ['career_experiment_sessions.id'], name=op.f('fk_adaptive_experiment_recommendations_career_experiment_session_id_career_experiment_sessions')),
    sa.ForeignKeyConstraint(['experiment_template_id'], ['career_experiment_templates.id'], name=op.f('fk_adaptive_experiment_recommendations_experiment_template_id_career_experiment_templates')),
    sa.ForeignKeyConstraint(['run_id'], ['adaptive_experiment_runs.id'], name=op.f('fk_adaptive_experiment_recommendations_run_id_adaptive_experiment_runs')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_adaptive_experiment_recommendations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_adaptive_experiment_recommendations'))
    )
    with op.batch_alter_table('adaptive_experiment_recommendations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_career_experiment_session_id'), ['career_experiment_session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_experiment_template_id'), ['experiment_template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_priority_band'), ['priority_band'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_run_id'), ['run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_user_confirmation_status'), ['user_confirmation_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_adaptive_experiment_recommendations_user_id'), ['user_id'], unique=False)

    op.create_table('application_contacts',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=255), nullable=False),
    sa.Column('contact_method', sa.String(length=120), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_application_contacts_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_contacts'))
    )
    with op.batch_alter_table('application_contacts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_contacts_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_contacts_profile_id'), ['profile_id'], unique=False)

    op.create_table('application_feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('feedback_type', sa.String(length=80), nullable=False),
    sa.Column('feedback_text', sa.Text(), nullable=False),
    sa.Column('confirmed_source', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_application_feedback_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_feedback'))
    )
    with op.batch_alter_table('application_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_feedback_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_feedback_feedback_type'), ['feedback_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_feedback_profile_id'), ['profile_id'], unique=False)

    op.create_table('application_outcomes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('outcome', sa.String(length=80), nullable=False),
    sa.Column('outcome_date', sa.String(length=40), nullable=True),
    sa.Column('employer_feedback', sa.Text(), nullable=False),
    sa.Column('feedback_confirmed', sa.Boolean(), nullable=False),
    sa.Column('user_interpretation', sa.Text(), nullable=False),
    sa.Column('ai_interpretation', sa.Text(), nullable=False),
    sa.Column('observed_data_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_application_outcomes_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_outcomes'))
    )
    with op.batch_alter_table('application_outcomes', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_outcomes_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_outcomes_outcome'), ['outcome'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_outcomes_profile_id'), ['profile_id'], unique=False)

    op.create_table('application_recalibration_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('observed_data_json', sa.JSON(), nullable=False),
    sa.Column('user_interpretation_json', sa.JSON(), nullable=False),
    sa.Column('ai_interpretation_json', sa.JSON(), nullable=False),
    sa.Column('suggestions_json', sa.JSON(), nullable=False),
    sa.Column('roadmap_changes_require_confirmation', sa.Boolean(), nullable=False),
    sa.Column('accepted_by_user', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_application_recalibration_runs_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_recalibration_runs'))
    )
    with op.batch_alter_table('application_recalibration_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_recalibration_runs_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_recalibration_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_recalibration_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_recalibration_runs_status'), ['status'], unique=False)

    op.create_table('application_stage_records',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('stage_type', sa.String(length=80), nullable=False),
    sa.Column('scheduled_date', sa.String(length=80), nullable=True),
    sa.Column('preparation_notes', sa.Text(), nullable=False),
    sa.Column('probable_questions_json', sa.JSON(), nullable=False),
    sa.Column('selected_evidence_json', sa.JSON(), nullable=False),
    sa.Column('user_reflection', sa.Text(), nullable=False),
    sa.Column('result', sa.String(length=80), nullable=False),
    sa.Column('feedback', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_application_stage_records_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_application_stage_records'))
    )
    with op.batch_alter_table('application_stage_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_application_stage_records_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_stage_records_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_stage_records_result'), ['result'], unique=False)
        batch_op.create_index(batch_op.f('ix_application_stage_records_stage_type'), ['stage_type'], unique=False)

    op.create_table('career_decision_journal_entries',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('decision_type', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('decision_summary', sa.Text(), nullable=False),
    sa.Column('context', sa.Text(), nullable=False),
    sa.Column('selected_option', sa.String(length=255), nullable=False),
    sa.Column('options_json', sa.JSON(), nullable=False),
    sa.Column('assumptions_json', sa.JSON(), nullable=False),
    sa.Column('evidence_links_json', sa.JSON(), nullable=False),
    sa.Column('adviser_comment_ids_json', sa.JSON(), nullable=False),
    sa.Column('career_slug', sa.String(length=180), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('privacy_scope', sa.String(length=80), nullable=False),
    sa.Column('review_date', sa.String(length=40), nullable=True),
    sa.Column('outcome_status', sa.String(length=80), nullable=False),
    sa.Column('outcome_json', sa.JSON(), nullable=False),
    sa.Column('reconsideration_reason', sa.Text(), nullable=False),
    sa.Column('roadmap_mutation_allowed', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_career_decision_journal_entries_application_id_job_applications')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_career_decision_journal_entries_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_decision_journal_entries_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_decision_journal_entries'))
    )
    with op.batch_alter_table('career_decision_journal_entries', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_career_slug'), ['career_slug'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_decision_type'), ['decision_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_outcome_status'), ['outcome_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_privacy_scope'), ['privacy_scope'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_review_date'), ['review_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_title'), ['title'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_entries_user_id'), ['user_id'], unique=False)

    op.create_table('career_experiment_submissions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('text_response', sa.Text(), nullable=False),
    sa.Column('project_url', sa.Text(), nullable=True),
    sa.Column('repository_url', sa.Text(), nullable=True),
    sa.Column('portfolio_url', sa.Text(), nullable=True),
    sa.Column('document_metadata_json', sa.JSON(), nullable=False),
    sa.Column('file_references_json', sa.JSON(), nullable=False),
    sa.Column('completion_notes', sa.Text(), nullable=False),
    sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
    sa.Column('ai_tools_used_json', sa.JSON(), nullable=False),
    sa.Column('assistance_level', sa.String(length=60), nullable=False),
    sa.Column('self_rated_difficulty', sa.Integer(), nullable=True),
    sa.Column('self_rated_enjoyment', sa.Integer(), nullable=True),
    sa.Column('confidence_before', sa.Integer(), nullable=True),
    sa.Column('confidence_after', sa.Integer(), nullable=True),
    sa.Column('reflection_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['career_experiment_sessions.id'], name=op.f('fk_career_experiment_submissions_session_id_career_experiment_sessions')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_experiment_submissions_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_submissions'))
    )
    with op.batch_alter_table('career_experiment_submissions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_submissions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_submissions_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_submissions_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_submissions_user_id'), ['user_id'], unique=False)

    op.create_table('career_hypothesis_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('hypothesis_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['hypothesis_id'], ['career_hypotheses.id'], name=op.f('fk_career_hypothesis_versions_hypothesis_id_career_hypotheses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_hypothesis_versions'))
    )
    with op.batch_alter_table('career_hypothesis_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_hypothesis_versions_hypothesis_id'), ['hypothesis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_hypothesis_versions_profile_id'), ['profile_id'], unique=False)

    op.create_table('document_claims',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=False),
    sa.Column('section_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('claim_text', sa.Text(), nullable=False),
    sa.Column('claim_type', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('safer_alternative', sa.Text(), nullable=False),
    sa.Column('deterministic_reason', sa.Text(), nullable=False),
    sa.Column('user_confirmation_state', sa.String(length=60), nullable=False),
    sa.Column('blocked_for_export', sa.Boolean(), nullable=False),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['application_documents.id'], name=op.f('fk_document_claims_document_id_application_documents')),
    sa.ForeignKeyConstraint(['section_id'], ['document_sections.id'], name=op.f('fk_document_claims_section_id_document_sections')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_claims'))
    )
    with op.batch_alter_table('document_claims', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_claims_blocked_for_export'), ['blocked_for_export'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_claim_type'), ['claim_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_section_id'), ['section_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claims_user_confirmation_state'), ['user_confirmation_state'], unique=False)

    op.create_table('interviews',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('cv_document_id', sa.String(), nullable=True),
    sa.Column('cover_letter_document_id', sa.String(), nullable=True),
    sa.Column('organisation', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=255), nullable=False),
    sa.Column('stage_type', sa.String(length=80), nullable=False),
    sa.Column('stage_order', sa.Integer(), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(), nullable=True),
    sa.Column('timezone', sa.String(length=80), nullable=False),
    sa.Column('location_or_platform', sa.String(length=255), nullable=False),
    sa.Column('interview_format', sa.String(length=80), nullable=False),
    sa.Column('expected_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('participants_json', sa.JSON(), nullable=False),
    sa.Column('preparation_status', sa.String(length=80), nullable=False),
    sa.Column('mock_session_status', sa.String(length=80), nullable=False),
    sa.Column('confidence_before', sa.Integer(), nullable=True),
    sa.Column('confidence_after', sa.Integer(), nullable=True),
    sa.Column('interview_result', sa.String(length=80), nullable=False),
    sa.Column('follow_up_status', sa.String(length=80), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('version', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_interviews_application_id_job_applications')),
    sa.ForeignKeyConstraint(['cover_letter_document_id'], ['application_documents.id'], name=op.f('fk_interviews_cover_letter_document_id_application_documents')),
    sa.ForeignKeyConstraint(['cv_document_id'], ['application_documents.id'], name=op.f('fk_interviews_cv_document_id_application_documents')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_interviews_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_interviews_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interviews'))
    )
    with op.batch_alter_table('interviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interviews_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_cover_letter_document_id'), ['cover_letter_document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_cv_document_id'), ['cv_document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_follow_up_status'), ['follow_up_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_interview_result'), ['interview_result'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_mock_session_status'), ['mock_session_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_preparation_status'), ['preparation_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_source'), ['source'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_stage_type'), ['stage_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_interviews_user_id'), ['user_id'], unique=False)

    op.create_table('job_application_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('from_status', sa.String(length=80), nullable=False),
    sa.Column('to_status', sa.String(length=80), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('event_metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_job_application_events_application_id_job_applications')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_application_events'))
    )
    with op.batch_alter_table('job_application_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_application_events_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_application_events_created_by'), ['created_by'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_application_events_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_application_events_profile_id'), ['profile_id'], unique=False)

    op.create_table('job_requirement_evidence_matches',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('requirement_id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('evidence_id', sa.String(), nullable=True),
    sa.Column('evidence_type', sa.String(length=80), nullable=False),
    sa.Column('evidence_strength', sa.String(length=80), nullable=False),
    sa.Column('match_category', sa.String(length=80), nullable=False),
    sa.Column('recency_label', sa.String(length=80), nullable=False),
    sa.Column('gap', sa.Text(), nullable=False),
    sa.Column('transferable_evidence_json', sa.JSON(), nullable=False),
    sa.Column('recommended_action', sa.Text(), nullable=False),
    sa.Column('deterministic_reason', sa.Text(), nullable=False),
    sa.Column('user_confirmation_state', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['job_analyses.id'], name=op.f('fk_job_requirement_evidence_matches_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['evidence_id'], ['skill_evidence.id'], name=op.f('fk_job_requirement_evidence_matches_evidence_id_skill_evidence')),
    sa.ForeignKeyConstraint(['requirement_id'], ['job_requirements.id'], name=op.f('fk_job_requirement_evidence_matches_requirement_id_job_requirements')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_requirement_evidence_matches'))
    )
    with op.batch_alter_table('job_requirement_evidence_matches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_evidence_id'), ['evidence_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_evidence_strength'), ['evidence_strength'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_match_category'), ['match_category'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_job_requirement_evidence_matches_requirement_id'), ['requirement_id'], unique=False)

    op.create_table('learning_recommendation_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('skill_gap_analysis_id', sa.String(), nullable=True),
    sa.Column('preferences_id', sa.String(), nullable=True),
    sa.Column('recommendation_version', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('provider_status_json', sa.JSON(), nullable=False),
    sa.Column('filters_json', sa.JSON(), nullable=False),
    sa.Column('ranking_weights_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_learning_recommendation_runs_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['preferences_id'], ['learning_preferences.id'], name=op.f('fk_learning_recommendation_runs_preferences_id_learning_preferences')),
    sa.ForeignKeyConstraint(['skill_gap_analysis_id'], ['skill_gap_analyses.id'], name=op.f('fk_learning_recommendation_runs_skill_gap_analysis_id_skill_gap_analyses')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_recommendation_runs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_recommendation_runs'))
    )
    with op.batch_alter_table('learning_recommendation_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_preferences_id'), ['preferences_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_skill_gap_analysis_id'), ['skill_gap_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_runs_user_id'), ['user_id'], unique=False)

    op.create_table('skill_evidence_confidence',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('skill_evidence_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('confidence_label', sa.String(length=80), nullable=False),
    sa.Column('strength_label', sa.String(length=80), nullable=False),
    sa.Column('score_internal', sa.Float(), nullable=False),
    sa.Column('factors_json', sa.JSON(), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['skill_evidence_id'], ['skill_evidence.id'], name=op.f('fk_skill_evidence_confidence_skill_evidence_id_skill_evidence')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_evidence_confidence'))
    )
    with op.batch_alter_table('skill_evidence_confidence', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_evidence_confidence_confidence_label'), ['confidence_label'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_confidence_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_confidence_skill_evidence_id'), ['skill_evidence_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_confidence_skill_id'), ['skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_confidence_strength_label'), ['strength_label'], unique=False)

    op.create_table('skill_evidence_sources',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('skill_evidence_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('source_type', sa.String(length=80), nullable=False),
    sa.Column('source_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('url', sa.Text(), nullable=True),
    sa.Column('source_metadata_json', sa.JSON(), nullable=False),
    sa.Column('verified_by', sa.String(length=120), nullable=True),
    sa.Column('independent_confirmation', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['skill_evidence_id'], ['skill_evidence.id'], name=op.f('fk_skill_evidence_sources_skill_evidence_id_skill_evidence')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_evidence_sources'))
    )
    with op.batch_alter_table('skill_evidence_sources', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_evidence_sources_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_sources_skill_evidence_id'), ['skill_evidence_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_sources_source_id'), ['source_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_evidence_sources_source_type'), ['source_type'], unique=False)

    op.create_table('skill_gap_items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('skill_label', sa.String(length=160), nullable=False),
    sa.Column('current_level', sa.Integer(), nullable=False),
    sa.Column('target_level', sa.Integer(), nullable=False),
    sa.Column('gap_size', sa.Integer(), nullable=False),
    sa.Column('importance', sa.Float(), nullable=False),
    sa.Column('evidence_level', sa.String(length=60), nullable=False),
    sa.Column('required', sa.Boolean(), nullable=False),
    sa.Column('ai_augmentable', sa.Boolean(), nullable=False),
    sa.Column('prerequisite_skill_ids_json', sa.JSON(), nullable=False),
    sa.Column('missing_prerequisites_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=60), nullable=False),
    sa.Column('priority_label', sa.String(length=40), nullable=False),
    sa.Column('priority_score_internal', sa.Float(), nullable=False),
    sa.Column('user_priority', sa.Integer(), nullable=True),
    sa.Column('dependency_order', sa.Integer(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['skill_gap_analyses.id'], name=op.f('fk_skill_gap_items_analysis_id_skill_gap_analyses')),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_skill_gap_items_career_match_id_career_matches')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_gap_items'))
    )
    with op.batch_alter_table('skill_gap_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_gap_items_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_items_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_items_priority_label'), ['priority_label'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_items_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_items_skill_id'), ['skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_skill_gap_items_status'), ['status'], unique=False)

    op.create_table('support_application_briefs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('job_loss_profile_id', sa.String(), nullable=True),
    sa.Column('support_screening_id', sa.String(), nullable=True),
    sa.Column('supported_path_run_id', sa.String(), nullable=True),
    sa.Column('content_json', sa.JSON(), nullable=False),
    sa.Column('disclaimer', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('official_source_references_json', sa.JSON(), nullable=False),
    sa.Column('unresolved_questions_json', sa.JSON(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['job_loss_profile_id'], ['job_loss_profiles.id'], name=op.f('fk_support_application_briefs_job_loss_profile_id_job_loss_profiles')),
    sa.ForeignKeyConstraint(['support_screening_id'], ['support_screenings.id'], name=op.f('fk_support_application_briefs_support_screening_id_support_screenings')),
    sa.ForeignKeyConstraint(['supported_path_run_id'], ['supported_path_runs.id'], name=op.f('fk_support_application_briefs_supported_path_run_id_supported_path_runs')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_support_application_briefs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_application_briefs'))
    )
    with op.batch_alter_table('support_application_briefs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_application_briefs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_job_loss_profile_id'), ['job_loss_profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_support_screening_id'), ['support_screening_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_supported_path_run_id'), ['supported_path_run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_application_briefs_user_id'), ['user_id'], unique=False)

    op.create_table('supported_path_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('role_family', sa.String(length=160), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('personal_fit_label', sa.String(length=80), nullable=False),
    sa.Column('capability_fit_label', sa.String(length=80), nullable=False),
    sa.Column('market_fit_label', sa.String(length=80), nullable=False),
    sa.Column('support_fit_label', sa.String(length=80), nullable=False),
    sa.Column('transition_difficulty', sa.String(length=80), nullable=False),
    sa.Column('estimated_preparation_range', sa.String(length=80), nullable=False),
    sa.Column('main_strengths_json', sa.JSON(), nullable=False),
    sa.Column('main_gaps_json', sa.JSON(), nullable=False),
    sa.Column('main_uncertainties_json', sa.JSON(), nullable=False),
    sa.Column('required_experiment_id', sa.String(), nullable=True),
    sa.Column('required_experiment_title', sa.String(length=255), nullable=False),
    sa.Column('possible_public_support_json', sa.JSON(), nullable=False),
    sa.Column('next_best_action', sa.Text(), nullable=False),
    sa.Column('official_assessment_required', sa.Boolean(), nullable=False),
    sa.Column('factor_scores_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_supported_path_results_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['run_id'], ['supported_path_runs.id'], name=op.f('fk_supported_path_results_run_id_supported_path_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_supported_path_results'))
    )
    with op.batch_alter_table('supported_path_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_supported_path_results_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_results_required_experiment_id'), ['required_experiment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_results_role_family'), ['role_family'], unique=False)
        batch_op.create_index(batch_op.f('ix_supported_path_results_run_id'), ['run_id'], unique=False)

    op.create_table('career_decision_journal_versions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('entry_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('snapshot_json', sa.JSON(), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['entry_id'], ['career_decision_journal_entries.id'], name=op.f('fk_career_decision_journal_versions_entry_id_career_decision_journal_entries')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_decision_journal_versions'))
    )
    with op.batch_alter_table('career_decision_journal_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_decision_journal_versions_entry_id'), ['entry_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_decision_journal_versions_profile_id'), ['profile_id'], unique=False)

    op.create_table('career_experiment_results',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('submission_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('overall_score', sa.Float(), nullable=False),
    sa.Column('overall_label', sa.String(length=80), nullable=False),
    sa.Column('criteria_scores_json', sa.JSON(), nullable=False),
    sa.Column('skills_evaluated_json', sa.JSON(), nullable=False),
    sa.Column('strengths_json', sa.JSON(), nullable=False),
    sa.Column('improvement_areas_json', sa.JSON(), nullable=False),
    sa.Column('deterministic_version', sa.String(length=60), nullable=False),
    sa.Column('evidence_created_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['career_experiment_sessions.id'], name=op.f('fk_career_experiment_results_session_id_career_experiment_sessions')),
    sa.ForeignKeyConstraint(['submission_id'], ['career_experiment_submissions.id'], name=op.f('fk_career_experiment_results_submission_id_career_experiment_submissions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_results'))
    )
    with op.batch_alter_table('career_experiment_results', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_results_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_results_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_results_submission_id'), ['submission_id'], unique=False)

    op.create_table('career_experiment_reviews',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('submission_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('source_type', sa.String(length=60), nullable=False),
    sa.Column('reviewer_id', sa.String(), nullable=True),
    sa.Column('scores_json', sa.JSON(), nullable=False),
    sa.Column('narrative', sa.Text(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['career_experiment_sessions.id'], name=op.f('fk_career_experiment_reviews_session_id_career_experiment_sessions')),
    sa.ForeignKeyConstraint(['submission_id'], ['career_experiment_submissions.id'], name=op.f('fk_career_experiment_reviews_submission_id_career_experiment_submissions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_experiment_reviews'))
    )
    with op.batch_alter_table('career_experiment_reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_experiment_reviews_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_reviews_reviewer_id'), ['reviewer_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_reviews_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_reviews_source_type'), ['source_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_experiment_reviews_submission_id'), ['submission_id'], unique=False)

    op.create_table('document_claim_evidence_links',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('claim_id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('evidence_type', sa.String(length=80), nullable=False),
    sa.Column('evidence_id', sa.String(), nullable=True),
    sa.Column('source_id', sa.String(), nullable=True),
    sa.Column('relationship', sa.String(length=120), nullable=False),
    sa.Column('confidence', sa.String(length=80), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['claim_id'], ['document_claims.id'], name=op.f('fk_document_claim_evidence_links_claim_id_document_claims')),
    sa.ForeignKeyConstraint(['document_id'], ['application_documents.id'], name=op.f('fk_document_claim_evidence_links_document_id_application_documents')),
    sa.ForeignKeyConstraint(['evidence_id'], ['skill_evidence.id'], name=op.f('fk_document_claim_evidence_links_evidence_id_skill_evidence')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_claim_evidence_links'))
    )
    with op.batch_alter_table('document_claim_evidence_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_claim_id'), ['claim_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_evidence_id'), ['evidence_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_evidence_type'), ['evidence_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_claim_evidence_links_source_id'), ['source_id'], unique=False)

    op.create_table('document_review_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('document_id', sa.String(), nullable=False),
    sa.Column('claim_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(length=80), nullable=False),
    sa.Column('event_json', sa.JSON(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['claim_id'], ['document_claims.id'], name=op.f('fk_document_review_events_claim_id_document_claims')),
    sa.ForeignKeyConstraint(['document_id'], ['application_documents.id'], name=op.f('fk_document_review_events_document_id_application_documents')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_document_review_events_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_review_events'))
    )
    with op.batch_alter_table('document_review_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_review_events_claim_id'), ['claim_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_review_events_document_id'), ['document_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_review_events_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_review_events_user_id'), ['user_id'], unique=False)

    op.create_table('interview_follow_up_drafts',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('draft_type', sa.String(length=80), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('source_facts_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_interview_follow_up_drafts_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_interview_follow_up_drafts_interview_id_interviews')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_follow_up_drafts'))
    )
    with op.batch_alter_table('interview_follow_up_drafts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_follow_up_drafts_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_follow_up_drafts_draft_type'), ['draft_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_follow_up_drafts_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_follow_up_drafts_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_follow_up_drafts_status'), ['status'], unique=False)

    op.create_table('interview_preparation_briefs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('sections_json', sa.JSON(), nullable=False),
    sa.Column('readiness_checklist_json', sa.JSON(), nullable=False),
    sa.Column('source_notes_json', sa.JSON(), nullable=False),
    sa.Column('language', sa.String(length=40), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('deterministic_origin', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_interview_preparation_briefs_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_interview_preparation_briefs_interview_id_interviews')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_interview_preparation_briefs_job_analysis_id_job_analyses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_preparation_briefs'))
    )
    with op.batch_alter_table('interview_preparation_briefs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_preparation_briefs_status'), ['status'], unique=False)

    op.create_table('interview_questions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('job_analysis_id', sa.String(), nullable=True),
    sa.Column('category', sa.String(length=80), nullable=False),
    sa.Column('stage', sa.String(length=80), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('why_it_may_be_asked', sa.Text(), nullable=False),
    sa.Column('related_job_requirement_id', sa.String(), nullable=True),
    sa.Column('related_job_requirement', sa.Text(), nullable=False),
    sa.Column('related_evidence_json', sa.JSON(), nullable=False),
    sa.Column('answer_objective', sa.Text(), nullable=False),
    sa.Column('risk_level', sa.String(length=40), nullable=False),
    sa.Column('difficulty', sa.String(length=40), nullable=False),
    sa.Column('source_type', sa.String(length=80), nullable=False),
    sa.Column('origin', sa.String(length=80), nullable=False),
    sa.Column('saved_by_user', sa.Boolean(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_interview_questions_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_interview_questions_interview_id_interviews')),
    sa.ForeignKeyConstraint(['job_analysis_id'], ['job_analyses.id'], name=op.f('fk_interview_questions_job_analysis_id_job_analyses')),
    sa.ForeignKeyConstraint(['related_job_requirement_id'], ['job_requirements.id'], name=op.f('fk_interview_questions_related_job_requirement_id_job_requirements')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_questions'))
    )
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_questions_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_difficulty'), ['difficulty'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_job_analysis_id'), ['job_analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_related_job_requirement_id'), ['related_job_requirement_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_risk_level'), ['risk_level'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_saved_by_user'), ['saved_by_user'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_questions_stage'), ['stage'], unique=False)

    op.create_table('interview_reflections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('stage_completed', sa.String(length=80), nullable=False),
    sa.Column('completed_date', sa.String(length=40), nullable=True),
    sa.Column('participants_json', sa.JSON(), nullable=False),
    sa.Column('questions_remembered_json', sa.JSON(), nullable=False),
    sa.Column('strong_answers_json', sa.JSON(), nullable=False),
    sa.Column('weak_answers_json', sa.JSON(), nullable=False),
    sa.Column('unexpected_topics_json', sa.JSON(), nullable=False),
    sa.Column('confirmed_interviewer_feedback', sa.Text(), nullable=False),
    sa.Column('user_interpretation', sa.Text(), nullable=False),
    sa.Column('ai_interpretation_json', sa.JSON(), nullable=False),
    sa.Column('next_step', sa.String(length=160), nullable=False),
    sa.Column('follow_up_deadline', sa.String(length=40), nullable=True),
    sa.Column('confidence_before', sa.Integer(), nullable=True),
    sa.Column('confidence_after', sa.Integer(), nullable=True),
    sa.Column('additional_evidence_needed_json', sa.JSON(), nullable=False),
    sa.Column('outcome_status', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_interview_reflections_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_interview_reflections_interview_id_interviews')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_reflections'))
    )
    with op.batch_alter_table('interview_reflections', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_reflections_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_reflections_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_reflections_outcome_status'), ['outcome_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_reflections_profile_id'), ['profile_id'], unique=False)

    op.create_table('learning_objectives',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('analysis_id', sa.String(), nullable=False),
    sa.Column('gap_item_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('objective_key', sa.String(length=160), nullable=False),
    sa.Column('skill_id', sa.String(length=120), nullable=False),
    sa.Column('target_level', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('prerequisite_ids_json', sa.JSON(), nullable=False),
    sa.Column('estimated_effort_minutes', sa.Integer(), nullable=False),
    sa.Column('evidence_expected', sa.Text(), nullable=False),
    sa.Column('role_relevance', sa.Text(), nullable=False),
    sa.Column('priority', sa.String(length=40), nullable=False),
    sa.Column('objective_version', sa.String(length=60), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['skill_gap_analyses.id'], name=op.f('fk_learning_objectives_analysis_id_skill_gap_analyses')),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_learning_objectives_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['gap_item_id'], ['skill_gap_items.id'], name=op.f('fk_learning_objectives_gap_item_id_skill_gap_items')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_objectives'))
    )
    with op.batch_alter_table('learning_objectives', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_objectives_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_gap_item_id'), ['gap_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_objective_key'), ['objective_key'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_skill_id'), ['skill_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_objectives_status'), ['status'], unique=False)

    op.create_table('learning_paths',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('recommendation_run_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('weekly_effort_hours', sa.Float(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_learning_paths_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['recommendation_run_id'], ['learning_recommendation_runs.id'], name=op.f('fk_learning_paths_recommendation_run_id_learning_recommendation_runs')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_paths_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_paths'))
    )
    with op.batch_alter_table('learning_paths', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_paths_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_paths_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_paths_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_paths_recommendation_run_id'), ['recommendation_run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_paths_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_paths_user_id'), ['user_id'], unique=False)

    op.create_table('mock_interview_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('mode', sa.String(length=80), nullable=False),
    sa.Column('delivery_mode', sa.String(length=40), nullable=False),
    sa.Column('persona', sa.String(length=80), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('question_sequence_json', sa.JSON(), nullable=False),
    sa.Column('transcript_confirmed', sa.Boolean(), nullable=False),
    sa.Column('transcript_retained', sa.Boolean(), nullable=False),
    sa.Column('timing_enabled', sa.Boolean(), nullable=False),
    sa.Column('feedback_json', sa.JSON(), nullable=False),
    sa.Column('rubric_results_json', sa.JSON(), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_mock_interview_sessions_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_mock_interview_sessions_interview_id_interviews')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mock_interview_sessions'))
    )
    with op.batch_alter_table('mock_interview_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_delivery_mode'), ['delivery_mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_mode'), ['mode'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_persona'), ['persona'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_sessions_status'), ['status'], unique=False)

    op.create_table('offer_reviews',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('application_id', sa.String(), nullable=True),
    sa.Column('interview_id', sa.String(), nullable=True),
    sa.Column('organisation', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=255), nullable=False),
    sa.Column('offer_items_json', sa.JSON(), nullable=False),
    sa.Column('user_priorities_json', sa.JSON(), nullable=False),
    sa.Column('review_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('source', sa.String(length=80), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['job_applications.id'], name=op.f('fk_offer_reviews_application_id_job_applications')),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_offer_reviews_interview_id_interviews')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_offer_reviews_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_offer_reviews'))
    )
    with op.batch_alter_table('offer_reviews', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_offer_reviews_application_id'), ['application_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_reviews_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_reviews_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_reviews_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_reviews_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_offer_reviews_user_id'), ['user_id'], unique=False)

    op.create_table('practical_projects',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('skill_gap_item_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('skills_demonstrated_json', sa.JSON(), nullable=False),
    sa.Column('estimated_effort_minutes', sa.Integer(), nullable=False),
    sa.Column('suggested_deliverables_json', sa.JSON(), nullable=False),
    sa.Column('completion_criteria_json', sa.JSON(), nullable=False),
    sa.Column('portfolio_value', sa.Text(), nullable=False),
    sa.Column('prerequisites_json', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_practical_projects_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['skill_gap_item_id'], ['skill_gap_items.id'], name=op.f('fk_practical_projects_skill_gap_item_id_skill_gap_items')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_practical_projects_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_practical_projects'))
    )
    with op.batch_alter_table('practical_projects', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_practical_projects_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_practical_projects_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_practical_projects_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_practical_projects_skill_gap_item_id'), ['skill_gap_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_practical_projects_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_practical_projects_user_id'), ['user_id'], unique=False)

    op.create_table('career_recalibration_runs',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('experiment_result_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('before_json', sa.JSON(), nullable=False),
    sa.Column('after_json', sa.JSON(), nullable=False),
    sa.Column('changed_recommendations_json', sa.JSON(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('uncertainty_label', sa.String(length=80), nullable=False),
    sa.Column('version', sa.String(length=60), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_career_recalibration_runs_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['experiment_result_id'], ['career_experiment_results.id'], name=op.f('fk_career_recalibration_runs_experiment_result_id_career_experiment_results')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_career_recalibration_runs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_recalibration_runs'))
    )
    with op.batch_alter_table('career_recalibration_runs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_experiment_result_id'), ['experiment_result_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_runs_user_id'), ['user_id'], unique=False)

    op.create_table('interview_answers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('question_id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('answer_objective', sa.Text(), nullable=False),
    sa.Column('key_points_json', sa.JSON(), nullable=False),
    sa.Column('selected_evidence_json', sa.JSON(), nullable=False),
    sa.Column('selected_star_story_id', sa.String(), nullable=True),
    sa.Column('suggested_structure_json', sa.JSON(), nullable=False),
    sa.Column('possible_opening', sa.Text(), nullable=False),
    sa.Column('possible_closing', sa.Text(), nullable=False),
    sa.Column('risk_areas_json', sa.JSON(), nullable=False),
    sa.Column('unsupported_claims_json', sa.JSON(), nullable=False),
    sa.Column('claim_statuses_json', sa.JSON(), nullable=False),
    sa.Column('user_draft', sa.Text(), nullable=False),
    sa.Column('revised_draft', sa.Text(), nullable=False),
    sa.Column('final_approved_answer', sa.Text(), nullable=False),
    sa.Column('user_confirmed', sa.Boolean(), nullable=False),
    sa.Column('origin', sa.String(length=80), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_interview_answers_interview_id_interviews')),
    sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], name=op.f('fk_interview_answers_question_id_interview_questions')),
    sa.ForeignKeyConstraint(['selected_star_story_id'], ['star_stories.id'], name=op.f('fk_interview_answers_selected_star_story_id_star_stories')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interview_answers'))
    )
    with op.batch_alter_table('interview_answers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_interview_answers_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_answers_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_answers_question_id'), ['question_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_interview_answers_selected_star_story_id'), ['selected_star_story_id'], unique=False)

    op.create_table('learning_path_phases',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('learning_path_id', sa.String(), nullable=False),
    sa.Column('phase_index', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('objectives_json', sa.JSON(), nullable=False),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
    sa.Column('weekly_effort_hours', sa.Float(), nullable=False),
    sa.Column('completion_evidence', sa.Text(), nullable=False),
    sa.Column('dependencies_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], name=op.f('fk_learning_path_phases_learning_path_id_learning_paths')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_path_phases'))
    )
    with op.batch_alter_table('learning_path_phases', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_path_phases_learning_path_id'), ['learning_path_id'], unique=False)

    op.create_table('learning_recommendations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('career_match_id', sa.String(), nullable=True),
    sa.Column('skill_gap_item_id', sa.String(), nullable=True),
    sa.Column('learning_objective_id', sa.String(), nullable=True),
    sa.Column('learning_resource_id', sa.String(), nullable=False),
    sa.Column('alignment_label', sa.String(length=80), nullable=False),
    sa.Column('ranking_score_internal', sa.Float(), nullable=False),
    sa.Column('rank_position', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('limitations_json', sa.JSON(), nullable=False),
    sa.Column('recommendation_version', sa.String(length=60), nullable=False),
    sa.Column('demo_marker', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['career_match_id'], ['career_matches.id'], name=op.f('fk_learning_recommendations_career_match_id_career_matches')),
    sa.ForeignKeyConstraint(['learning_objective_id'], ['learning_objectives.id'], name=op.f('fk_learning_recommendations_learning_objective_id_learning_objectives')),
    sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], name=op.f('fk_learning_recommendations_learning_resource_id_learning_resources')),
    sa.ForeignKeyConstraint(['run_id'], ['learning_recommendation_runs.id'], name=op.f('fk_learning_recommendations_run_id_learning_recommendation_runs')),
    sa.ForeignKeyConstraint(['skill_gap_item_id'], ['skill_gap_items.id'], name=op.f('fk_learning_recommendations_skill_gap_item_id_skill_gap_items')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_recommendations_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_recommendations'))
    )
    with op.batch_alter_table('learning_recommendations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_recommendations_career_match_id'), ['career_match_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_demo_marker'), ['demo_marker'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_learning_objective_id'), ['learning_objective_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_learning_resource_id'), ['learning_resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_run_id'), ['run_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_skill_gap_item_id'), ['skill_gap_item_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendations_user_id'), ['user_id'], unique=False)

    op.create_table('mock_interview_turns',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('session_id', sa.String(), nullable=False),
    sa.Column('interview_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('question_id', sa.String(), nullable=True),
    sa.Column('turn_index', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('answer_text', sa.Text(), nullable=False),
    sa.Column('corrected_transcript', sa.Text(), nullable=False),
    sa.Column('response_duration_seconds', sa.Integer(), nullable=True),
    sa.Column('estimated_word_count', sa.Integer(), nullable=False),
    sa.Column('attempt_number', sa.Integer(), nullable=False),
    sa.Column('completion_status', sa.String(length=80), nullable=False),
    sa.Column('follow_up_questions_json', sa.JSON(), nullable=False),
    sa.Column('rubric_json', sa.JSON(), nullable=False),
    sa.Column('feedback_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_mock_interview_turns_interview_id_interviews')),
    sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], name=op.f('fk_mock_interview_turns_question_id_interview_questions')),
    sa.ForeignKeyConstraint(['session_id'], ['mock_interview_sessions.id'], name=op.f('fk_mock_interview_turns_session_id_mock_interview_sessions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mock_interview_turns'))
    )
    with op.batch_alter_table('mock_interview_turns', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_mock_interview_turns_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_turns_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_turns_question_id'), ['question_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_mock_interview_turns_session_id'), ['session_id'], unique=False)

    op.create_table('voice_provider_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('mock_session_id', sa.String(), nullable=True),
    sa.Column('interview_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('provider', sa.String(length=80), nullable=False),
    sa.Column('provider_session_id', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=80), nullable=False),
    sa.Column('language', sa.String(length=40), nullable=False),
    sa.Column('consent_confirmed', sa.Boolean(), nullable=False),
    sa.Column('audio_retained', sa.Boolean(), nullable=False),
    sa.Column('transcript_retained', sa.Boolean(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], name=op.f('fk_voice_provider_sessions_interview_id_interviews')),
    sa.ForeignKeyConstraint(['mock_session_id'], ['mock_interview_sessions.id'], name=op.f('fk_voice_provider_sessions_mock_session_id_mock_interview_sessions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_voice_provider_sessions'))
    )
    with op.batch_alter_table('voice_provider_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_voice_provider_sessions_interview_id'), ['interview_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_voice_provider_sessions_mock_session_id'), ['mock_session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_voice_provider_sessions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_voice_provider_sessions_status'), ['status'], unique=False)

    op.create_table('career_recalibration_factors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('run_id', sa.String(), nullable=False),
    sa.Column('factor_type', sa.String(length=80), nullable=False),
    sa.Column('label', sa.String(length=160), nullable=False),
    sa.Column('before_value', sa.Float(), nullable=True),
    sa.Column('after_value', sa.Float(), nullable=True),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['career_recalibration_runs.id'], name=op.f('fk_career_recalibration_factors_run_id_career_recalibration_runs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_recalibration_factors'))
    )
    with op.batch_alter_table('career_recalibration_factors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_recalibration_factors_factor_type'), ['factor_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_career_recalibration_factors_run_id'), ['run_id'], unique=False)

    op.create_table('learning_path_items',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('learning_path_id', sa.String(), nullable=False),
    sa.Column('phase_id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=True),
    sa.Column('learning_resource_id', sa.String(), nullable=True),
    sa.Column('learning_objective_id', sa.String(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('progress_percentage', sa.Integer(), nullable=False),
    sa.Column('user_reported_progress', sa.Text(), nullable=False),
    sa.Column('completion_date', sa.String(length=40), nullable=True),
    sa.Column('evidence_url', sa.Text(), nullable=True),
    sa.Column('reflection', sa.Text(), nullable=False),
    sa.Column('difficulty_feedback', sa.String(length=60), nullable=True),
    sa.Column('relevance_feedback', sa.String(length=60), nullable=True),
    sa.Column('expected_evidence', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['learning_objective_id'], ['learning_objectives.id'], name=op.f('fk_learning_path_items_learning_objective_id_learning_objectives')),
    sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], name=op.f('fk_learning_path_items_learning_path_id_learning_paths')),
    sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], name=op.f('fk_learning_path_items_learning_resource_id_learning_resources')),
    sa.ForeignKeyConstraint(['phase_id'], ['learning_path_phases.id'], name=op.f('fk_learning_path_items_phase_id_learning_path_phases')),
    sa.ForeignKeyConstraint(['recommendation_id'], ['learning_recommendations.id'], name=op.f('fk_learning_path_items_recommendation_id_learning_recommendations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_path_items'))
    )
    with op.batch_alter_table('learning_path_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_path_items_learning_objective_id'), ['learning_objective_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_path_items_learning_path_id'), ['learning_path_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_path_items_learning_resource_id'), ['learning_resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_path_items_phase_id'), ['phase_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_path_items_recommendation_id'), ['recommendation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_path_items_status'), ['status'], unique=False)

    op.create_table('learning_recommendation_factors',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=False),
    sa.Column('factor_type', sa.String(length=80), nullable=False),
    sa.Column('factor_value', sa.Float(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['recommendation_id'], ['learning_recommendations.id'], name=op.f('fk_learning_recommendation_factors_recommendation_id_learning_recommendations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_recommendation_factors'))
    )
    with op.batch_alter_table('learning_recommendation_factors', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_recommendation_factors_factor_type'), ['factor_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_recommendation_factors_recommendation_id'), ['recommendation_id'], unique=False)

    op.create_table('learning_resource_feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=True),
    sa.Column('learning_resource_id', sa.String(), nullable=True),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('reason_code', sa.String(length=60), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('relevant', sa.Boolean(), nullable=True),
    sa.Column('feedback_text', sa.Text(), nullable=True),
    sa.Column('effect_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], name=op.f('fk_learning_resource_feedback_learning_resource_id_learning_resources')),
    sa.ForeignKeyConstraint(['recommendation_id'], ['learning_recommendations.id'], name=op.f('fk_learning_resource_feedback_recommendation_id_learning_recommendations')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_resource_feedback_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resource_feedback'))
    )
    with op.batch_alter_table('learning_resource_feedback', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_resource_feedback_learning_resource_id'), ['learning_resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_feedback_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_feedback_reason_code'), ['reason_code'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_feedback_recommendation_id'), ['recommendation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_learning_resource_feedback_user_id'), ['user_id'], unique=False)

    op.create_table('roadmap_learning_actions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('roadmap_action_id', sa.String(), nullable=False),
    sa.Column('profile_id', sa.String(), nullable=False),
    sa.Column('recommendation_id', sa.String(), nullable=True),
    sa.Column('learning_resource_id', sa.String(), nullable=True),
    sa.Column('learning_objective_id', sa.String(), nullable=True),
    sa.Column('expected_evidence', sa.Text(), nullable=False),
    sa.Column('evidence_url', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['learning_objective_id'], ['learning_objectives.id'], name=op.f('fk_roadmap_learning_actions_learning_objective_id_learning_objectives')),
    sa.ForeignKeyConstraint(['learning_resource_id'], ['learning_resources.id'], name=op.f('fk_roadmap_learning_actions_learning_resource_id_learning_resources')),
    sa.ForeignKeyConstraint(['recommendation_id'], ['learning_recommendations.id'], name=op.f('fk_roadmap_learning_actions_recommendation_id_learning_recommendations')),
    sa.ForeignKeyConstraint(['roadmap_action_id'], ['roadmap_actions.id'], name=op.f('fk_roadmap_learning_actions_roadmap_action_id_roadmap_actions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_learning_actions'))
    )
    with op.batch_alter_table('roadmap_learning_actions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_learning_objective_id'), ['learning_objective_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_learning_resource_id'), ['learning_resource_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_profile_id'), ['profile_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_recommendation_id'), ['recommendation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_roadmap_action_id'), ['roadmap_action_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_roadmap_learning_actions_status'), ['status'], unique=False)

    # End reviewed initial schema.


def downgrade() -> None:
    # Drop the initial schema in reverse dependency order.
    with op.batch_alter_table('roadmap_learning_actions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_status'))
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_roadmap_action_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_learning_resource_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_learning_actions_learning_objective_id'))

    op.drop_table('roadmap_learning_actions')
    with op.batch_alter_table('learning_resource_feedback', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_feedback_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_feedback_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_feedback_reason_code'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_feedback_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_feedback_learning_resource_id'))

    op.drop_table('learning_resource_feedback')
    with op.batch_alter_table('learning_recommendation_factors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_factors_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_factors_factor_type'))

    op.drop_table('learning_recommendation_factors')
    with op.batch_alter_table('learning_path_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_path_items_status'))
        batch_op.drop_index(batch_op.f('ix_learning_path_items_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_learning_path_items_phase_id'))
        batch_op.drop_index(batch_op.f('ix_learning_path_items_learning_resource_id'))
        batch_op.drop_index(batch_op.f('ix_learning_path_items_learning_path_id'))
        batch_op.drop_index(batch_op.f('ix_learning_path_items_learning_objective_id'))

    op.drop_table('learning_path_items')
    with op.batch_alter_table('career_recalibration_factors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_recalibration_factors_run_id'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_factors_factor_type'))

    op.drop_table('career_recalibration_factors')
    with op.batch_alter_table('voice_provider_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_voice_provider_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_voice_provider_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_voice_provider_sessions_mock_session_id'))
        batch_op.drop_index(batch_op.f('ix_voice_provider_sessions_interview_id'))

    op.drop_table('voice_provider_sessions')
    with op.batch_alter_table('mock_interview_turns', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mock_interview_turns_session_id'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_turns_question_id'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_turns_profile_id'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_turns_interview_id'))

    op.drop_table('mock_interview_turns')
    with op.batch_alter_table('learning_recommendations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_status'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_skill_gap_item_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_run_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_learning_resource_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_learning_objective_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendations_career_match_id'))

    op.drop_table('learning_recommendations')
    with op.batch_alter_table('learning_path_phases', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_path_phases_learning_path_id'))

    op.drop_table('learning_path_phases')
    with op.batch_alter_table('interview_answers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_answers_selected_star_story_id'))
        batch_op.drop_index(batch_op.f('ix_interview_answers_question_id'))
        batch_op.drop_index(batch_op.f('ix_interview_answers_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interview_answers_interview_id'))

    op.drop_table('interview_answers')
    with op.batch_alter_table('career_recalibration_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_status'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_experiment_result_id'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_recalibration_runs_career_match_id'))

    op.drop_table('career_recalibration_runs')
    with op.batch_alter_table('practical_projects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_practical_projects_user_id'))
        batch_op.drop_index(batch_op.f('ix_practical_projects_status'))
        batch_op.drop_index(batch_op.f('ix_practical_projects_skill_gap_item_id'))
        batch_op.drop_index(batch_op.f('ix_practical_projects_profile_id'))
        batch_op.drop_index(batch_op.f('ix_practical_projects_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_practical_projects_career_match_id'))

    op.drop_table('practical_projects')
    with op.batch_alter_table('offer_reviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_offer_reviews_user_id'))
        batch_op.drop_index(batch_op.f('ix_offer_reviews_status'))
        batch_op.drop_index(batch_op.f('ix_offer_reviews_profile_id'))
        batch_op.drop_index(batch_op.f('ix_offer_reviews_interview_id'))
        batch_op.drop_index(batch_op.f('ix_offer_reviews_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_offer_reviews_application_id'))

    op.drop_table('offer_reviews')
    with op.batch_alter_table('mock_interview_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_persona'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_mode'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_interview_id'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_delivery_mode'))
        batch_op.drop_index(batch_op.f('ix_mock_interview_sessions_application_id'))

    op.drop_table('mock_interview_sessions')
    with op.batch_alter_table('learning_paths', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_paths_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_paths_status'))
        batch_op.drop_index(batch_op.f('ix_learning_paths_recommendation_run_id'))
        batch_op.drop_index(batch_op.f('ix_learning_paths_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_paths_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_learning_paths_career_match_id'))

    op.drop_table('learning_paths')
    with op.batch_alter_table('learning_objectives', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_objectives_status'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_skill_id'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_objective_key'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_gap_item_id'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_career_match_id'))
        batch_op.drop_index(batch_op.f('ix_learning_objectives_analysis_id'))

    op.drop_table('learning_objectives')
    with op.batch_alter_table('interview_reflections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_reflections_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interview_reflections_outcome_status'))
        batch_op.drop_index(batch_op.f('ix_interview_reflections_interview_id'))
        batch_op.drop_index(batch_op.f('ix_interview_reflections_application_id'))

    op.drop_table('interview_reflections')
    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_questions_stage'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_saved_by_user'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_risk_level'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_related_job_requirement_id'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_interview_id'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_difficulty'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_category'))
        batch_op.drop_index(batch_op.f('ix_interview_questions_application_id'))

    op.drop_table('interview_questions')
    with op.batch_alter_table('interview_preparation_briefs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_status'))
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_interview_id'))
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_interview_preparation_briefs_application_id'))

    op.drop_table('interview_preparation_briefs')
    with op.batch_alter_table('interview_follow_up_drafts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interview_follow_up_drafts_status'))
        batch_op.drop_index(batch_op.f('ix_interview_follow_up_drafts_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interview_follow_up_drafts_interview_id'))
        batch_op.drop_index(batch_op.f('ix_interview_follow_up_drafts_draft_type'))
        batch_op.drop_index(batch_op.f('ix_interview_follow_up_drafts_application_id'))

    op.drop_table('interview_follow_up_drafts')
    with op.batch_alter_table('document_review_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_review_events_user_id'))
        batch_op.drop_index(batch_op.f('ix_document_review_events_profile_id'))
        batch_op.drop_index(batch_op.f('ix_document_review_events_document_id'))
        batch_op.drop_index(batch_op.f('ix_document_review_events_claim_id'))

    op.drop_table('document_review_events')
    with op.batch_alter_table('document_claim_evidence_links', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_source_id'))
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_profile_id'))
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_evidence_type'))
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_evidence_id'))
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_document_id'))
        batch_op.drop_index(batch_op.f('ix_document_claim_evidence_links_claim_id'))

    op.drop_table('document_claim_evidence_links')
    with op.batch_alter_table('career_experiment_reviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_reviews_submission_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_reviews_source_type'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_reviews_session_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_reviews_reviewer_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_reviews_profile_id'))

    op.drop_table('career_experiment_reviews')
    with op.batch_alter_table('career_experiment_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_results_submission_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_results_profile_id'))

    op.drop_table('career_experiment_results')
    with op.batch_alter_table('career_decision_journal_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_versions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_versions_entry_id'))

    op.drop_table('career_decision_journal_versions')
    with op.batch_alter_table('supported_path_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_supported_path_results_run_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_results_role_family'))
        batch_op.drop_index(batch_op.f('ix_supported_path_results_required_experiment_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_results_career_match_id'))

    op.drop_table('supported_path_results')
    with op.batch_alter_table('support_application_briefs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_supported_path_run_id'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_support_screening_id'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_status'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_job_loss_profile_id'))
        batch_op.drop_index(batch_op.f('ix_support_application_briefs_demo_marker'))

    op.drop_table('support_application_briefs')
    with op.batch_alter_table('skill_gap_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_status'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_skill_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_profile_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_priority_label'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_career_match_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_items_analysis_id'))

    op.drop_table('skill_gap_items')
    with op.batch_alter_table('skill_evidence_sources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_evidence_sources_source_type'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_sources_source_id'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_sources_skill_evidence_id'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_sources_profile_id'))

    op.drop_table('skill_evidence_sources')
    with op.batch_alter_table('skill_evidence_confidence', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_evidence_confidence_strength_label'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_confidence_skill_id'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_confidence_skill_evidence_id'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_confidence_profile_id'))
        batch_op.drop_index(batch_op.f('ix_skill_evidence_confidence_confidence_label'))

    op.drop_table('skill_evidence_confidence')
    with op.batch_alter_table('learning_recommendation_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_status'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_skill_gap_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_preferences_id'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_learning_recommendation_runs_career_match_id'))

    op.drop_table('learning_recommendation_runs')
    with op.batch_alter_table('job_requirement_evidence_matches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_requirement_id'))
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_match_category'))
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_evidence_strength'))
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_evidence_id'))
        batch_op.drop_index(batch_op.f('ix_job_requirement_evidence_matches_analysis_id'))

    op.drop_table('job_requirement_evidence_matches')
    with op.batch_alter_table('job_application_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_application_events_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_application_events_event_type'))
        batch_op.drop_index(batch_op.f('ix_job_application_events_created_by'))
        batch_op.drop_index(batch_op.f('ix_job_application_events_application_id'))

    op.drop_table('job_application_events')
    with op.batch_alter_table('interviews', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_interviews_user_id'))
        batch_op.drop_index(batch_op.f('ix_interviews_stage_type'))
        batch_op.drop_index(batch_op.f('ix_interviews_source'))
        batch_op.drop_index(batch_op.f('ix_interviews_profile_id'))
        batch_op.drop_index(batch_op.f('ix_interviews_preparation_status'))
        batch_op.drop_index(batch_op.f('ix_interviews_mock_session_status'))
        batch_op.drop_index(batch_op.f('ix_interviews_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_interviews_interview_result'))
        batch_op.drop_index(batch_op.f('ix_interviews_follow_up_status'))
        batch_op.drop_index(batch_op.f('ix_interviews_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_interviews_cv_document_id'))
        batch_op.drop_index(batch_op.f('ix_interviews_cover_letter_document_id'))
        batch_op.drop_index(batch_op.f('ix_interviews_application_id'))

    op.drop_table('interviews')
    with op.batch_alter_table('document_claims', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_claims_user_confirmation_state'))
        batch_op.drop_index(batch_op.f('ix_document_claims_status'))
        batch_op.drop_index(batch_op.f('ix_document_claims_section_id'))
        batch_op.drop_index(batch_op.f('ix_document_claims_profile_id'))
        batch_op.drop_index(batch_op.f('ix_document_claims_document_id'))
        batch_op.drop_index(batch_op.f('ix_document_claims_claim_type'))
        batch_op.drop_index(batch_op.f('ix_document_claims_blocked_for_export'))

    op.drop_table('document_claims')
    with op.batch_alter_table('career_hypothesis_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_hypothesis_versions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_hypothesis_versions_hypothesis_id'))

    op.drop_table('career_hypothesis_versions')
    with op.batch_alter_table('career_experiment_submissions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_submissions_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_submissions_status'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_submissions_session_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_submissions_profile_id'))

    op.drop_table('career_experiment_submissions')
    with op.batch_alter_table('career_decision_journal_entries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_title'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_status'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_review_date'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_privacy_scope'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_outcome_status'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_decision_type'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_career_slug'))
        batch_op.drop_index(batch_op.f('ix_career_decision_journal_entries_application_id'))

    op.drop_table('career_decision_journal_entries')
    with op.batch_alter_table('application_stage_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_stage_records_stage_type'))
        batch_op.drop_index(batch_op.f('ix_application_stage_records_result'))
        batch_op.drop_index(batch_op.f('ix_application_stage_records_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_stage_records_application_id'))

    op.drop_table('application_stage_records')
    with op.batch_alter_table('application_recalibration_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_recalibration_runs_status'))
        batch_op.drop_index(batch_op.f('ix_application_recalibration_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_recalibration_runs_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_application_recalibration_runs_application_id'))

    op.drop_table('application_recalibration_runs')
    with op.batch_alter_table('application_outcomes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_outcomes_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_outcomes_outcome'))
        batch_op.drop_index(batch_op.f('ix_application_outcomes_application_id'))

    op.drop_table('application_outcomes')
    with op.batch_alter_table('application_feedback', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_feedback_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_feedback_feedback_type'))
        batch_op.drop_index(batch_op.f('ix_application_feedback_application_id'))

    op.drop_table('application_feedback')
    with op.batch_alter_table('application_contacts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_contacts_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_contacts_application_id'))

    op.drop_table('application_contacts')
    with op.batch_alter_table('adaptive_experiment_recommendations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_user_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_user_confirmation_status'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_title'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_status'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_run_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_profile_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_priority_band'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_experiment_template_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_recommendations_career_experiment_session_id'))

    op.drop_table('adaptive_experiment_recommendations')
    with op.batch_alter_table('supported_path_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_support_screening_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_status'))
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_market_snapshot_id'))
        batch_op.drop_index(batch_op.f('ix_supported_path_runs_demo_marker'))

    op.drop_table('supported_path_runs')
    with op.batch_alter_table('support_screening_factors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_screening_factors_screening_id'))
        batch_op.drop_index(batch_op.f('ix_support_screening_factors_programme_id'))
        batch_op.drop_index(batch_op.f('ix_support_screening_factors_preliminary_label'))

    op.drop_table('support_screening_factors')
    with op.batch_alter_table('skill_gap_analyses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_user_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_status'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_role_template_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_profile_id'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_skill_gap_analyses_career_match_id'))

    op.drop_table('skill_gap_analyses')
    with op.batch_alter_table('skill_evidence', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_evidence_skill_inventory_id'))

    op.drop_table('skill_evidence')
    with op.batch_alter_table('research_responses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_responses_workflow_stage'))
        batch_op.drop_index(batch_op.f('ix_research_responses_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_responses_session_id'))
        batch_op.drop_index(batch_op.f('ix_research_responses_question_id'))
        batch_op.drop_index(batch_op.f('ix_research_responses_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_responses_participant_id'))

    op.drop_table('research_responses')
    with op.batch_alter_table('research_interaction_metrics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_interaction_metrics_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_interaction_metrics_session_id'))
        batch_op.drop_index(batch_op.f('ix_research_interaction_metrics_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_interaction_metrics_participant_id'))
        batch_op.drop_index(batch_op.f('ix_research_interaction_metrics_metric_name'))

    op.drop_table('research_interaction_metrics')
    with op.batch_alter_table('job_applications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_applications_user_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_title'))
        batch_op.drop_index(batch_op.f('ix_job_applications_status'))
        batch_op.drop_index(batch_op.f('ix_job_applications_roadmap_action_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_job_applications_cv_document_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_cover_letter_document_id'))
        batch_op.drop_index(batch_op.f('ix_job_applications_career_match_id'))

    op.drop_table('job_applications')
    with op.batch_alter_table('job_analysis_corrections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_analysis_corrections_user_id'))
        batch_op.drop_index(batch_op.f('ix_job_analysis_corrections_requirement_id'))
        batch_op.drop_index(batch_op.f('ix_job_analysis_corrections_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_analysis_corrections_analysis_id'))

    op.drop_table('job_analysis_corrections')
    with op.batch_alter_table('immediate_action_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_immediate_action_items_urgency'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_items_status'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_items_profile_id'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_items_plan_id'))

    op.drop_table('immediate_action_items')
    with op.batch_alter_table('document_sections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_sections_section_type'))
        batch_op.drop_index(batch_op.f('ix_document_sections_profile_id'))
        batch_op.drop_index(batch_op.f('ix_document_sections_document_id'))

    op.drop_table('document_sections')
    with op.batch_alter_table('career_match_factors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_match_factors_match_id'))
        batch_op.drop_index(batch_op.f('ix_career_match_factors_factor_type'))

    op.drop_table('career_match_factors')
    with op.batch_alter_table('career_hypotheses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_title'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_status'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_role_template_id'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_role_family'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_hypotheses_career_match_id'))

    op.drop_table('career_hypotheses')
    with op.batch_alter_table('career_experiment_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_roadmap_action_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_mode'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_hypothesis_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_experiment_template_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_sessions_career_match_id'))

    op.drop_table('career_experiment_sessions')
    with op.batch_alter_table('career_decisions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_decisions_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_decisions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_decisions_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_decisions_career_match_id'))

    op.drop_table('career_decisions')
    with op.batch_alter_table('application_document_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_document_versions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_document_versions_document_id'))

    op.drop_table('application_document_versions')
    with op.batch_alter_table('work_value_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_work_value_results_user_id'))
        batch_op.drop_index(batch_op.f('ix_work_value_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_work_value_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_work_value_results_demo_marker'))

    op.drop_table('work_value_results')
    with op.batch_alter_table('support_screenings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_screenings_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_screenings_status'))
        batch_op.drop_index(batch_op.f('ix_support_screenings_profile_id'))
        batch_op.drop_index(batch_op.f('ix_support_screenings_job_loss_profile_id'))
        batch_op.drop_index(batch_op.f('ix_support_screenings_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_support_screenings_country'))

    op.drop_table('support_screenings')
    with op.batch_alter_table('support_rules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_rules_rule_version'))
        batch_op.drop_index(batch_op.f('ix_support_rules_programme_version_id'))
        batch_op.drop_index(batch_op.f('ix_support_rules_programme_id'))
        batch_op.drop_index(batch_op.f('ix_support_rules_active'))

    op.drop_table('support_rules')
    with op.batch_alter_table('star_story_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_star_story_versions_story_id'))
        batch_op.drop_index(batch_op.f('ix_star_story_versions_profile_id'))

    op.drop_table('star_story_versions')
    with op.batch_alter_table('skills_inventory', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skills_inventory_user_id'))
        batch_op.drop_index(batch_op.f('ix_skills_inventory_skill_id'))
        batch_op.drop_index(batch_op.f('ix_skills_inventory_session_id'))
        batch_op.drop_index(batch_op.f('ix_skills_inventory_profile_id'))
        batch_op.drop_index(batch_op.f('ix_skills_inventory_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_skills_inventory_category'))

    op.drop_table('skills_inventory')
    with op.batch_alter_table('roadmap_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_versions_roadmap_id'))

    op.drop_table('roadmap_versions')
    with op.batch_alter_table('roadmap_milestones', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_milestones_roadmap_id'))

    op.drop_table('roadmap_milestones')
    with op.batch_alter_table('roadmap_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_events_user_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_events_roadmap_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_events_action_id'))

    op.drop_table('roadmap_events')
    with op.batch_alter_table('roadmap_checkins', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_checkins_user_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_checkins_roadmap_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_checkins_profile_id'))

    op.drop_table('roadmap_checkins')
    with op.batch_alter_table('roadmap_actions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_actions_user_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_actions_roadmap_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_actions_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_roadmap_actions_profile_id'))

    op.drop_table('roadmap_actions')
    with op.batch_alter_table('research_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_sessions_workflow_stage'))
        batch_op.drop_index(batch_op.f('ix_research_sessions_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_research_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_sessions_participant_id'))
        batch_op.drop_index(batch_op.f('ix_research_sessions_demo_marker'))

    op.drop_table('research_sessions')
    with op.batch_alter_table('research_consents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_consents_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_consents_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_consents_participant_id'))
        batch_op.drop_index(batch_op.f('ix_research_consents_consent_given'))

    op.drop_table('research_consents')
    with op.batch_alter_table('research_assignments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_assignments_workflow'))
        batch_op.drop_index(batch_op.f('ix_research_assignments_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_assignments_participant_id'))

    op.drop_table('research_assignments')
    with op.batch_alter_table('recommendation_feedback', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recommendation_feedback_recommendation_id'))

    op.drop_table('recommendation_feedback')
    with op.batch_alter_table('recommendation_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recommendation_events_recommendation_id'))
        batch_op.drop_index(batch_op.f('ix_recommendation_events_event_type'))

    op.drop_table('recommendation_events')
    with op.batch_alter_table('personality_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_personality_results_user_id'))
        batch_op.drop_index(batch_op.f('ix_personality_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_personality_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_personality_results_demo_marker'))

    op.drop_table('personality_results')
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_messages_conversation_id'))

    op.drop_table('messages')
    with op.batch_alter_table('learning_resource_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_versions_resource_id'))

    op.drop_table('learning_resource_versions')
    with op.batch_alter_table('learning_resource_verifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_verifications_verification_status'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_verifications_resource_id'))

    op.drop_table('learning_resource_verifications')
    with op.batch_alter_table('learning_resource_skills', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_skills_skill_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_skills_resource_id'))

    op.drop_table('learning_resource_skills')
    with op.batch_alter_table('learning_resource_objectives', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_objectives_resource_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_objectives_objective_key'))

    op.drop_table('learning_resource_objectives')
    with op.batch_alter_table('job_requirements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_requirements_user_confirmation_state'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_status'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_requirement_type'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_requirement_category'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_normalised_skill_id'))
        batch_op.drop_index(batch_op.f('ix_job_requirements_analysis_id'))

    op.drop_table('job_requirements')
    with op.batch_alter_table('job_readiness_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_readiness_results_readiness_label'))
        batch_op.drop_index(batch_op.f('ix_job_readiness_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_readiness_results_analysis_id'))

    op.drop_table('job_readiness_results')
    with op.batch_alter_table('job_analysis_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_analysis_versions_analysis_id'))

    op.drop_table('job_analysis_versions')
    with op.batch_alter_table('immediate_action_plans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_immediate_action_plans_user_id'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_plans_status'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_plans_profile_id'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_plans_job_loss_profile_id'))
        batch_op.drop_index(batch_op.f('ix_immediate_action_plans_demo_marker'))

    op.drop_table('immediate_action_plans')
    with op.batch_alter_table('change_readiness_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_change_readiness_results_user_id'))
        batch_op.drop_index(batch_op.f('ix_change_readiness_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_change_readiness_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_change_readiness_results_demo_marker'))

    op.drop_table('change_readiness_results')
    with op.batch_alter_table('career_transition_paths', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_title'))
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_simulation_id'))
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_role_slug'))
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_is_pareto_optimal'))
        batch_op.drop_index(batch_op.f('ix_career_transition_paths_demo_marker'))

    op.drop_table('career_transition_paths')
    with op.batch_alter_table('career_profile_entries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_profile_entries_user_confirmation_state'))
        batch_op.drop_index(batch_op.f('ix_career_profile_entries_source_id'))
        batch_op.drop_index(batch_op.f('ix_career_profile_entries_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_profile_entries_master_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_profile_entries_entry_type'))

    op.drop_table('career_profile_entries')
    with op.batch_alter_table('career_matches', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_matches_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_matches_title'))
        batch_op.drop_index(batch_op.f('ix_career_matches_status'))
        batch_op.drop_index(batch_op.f('ix_career_matches_session_id'))
        batch_op.drop_index(batch_op.f('ix_career_matches_role_template_id'))
        batch_op.drop_index(batch_op.f('ix_career_matches_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_matches_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_career_matches_category'))

    op.drop_table('career_matches')
    with op.batch_alter_table('career_interest_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_interest_results_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_interest_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_career_interest_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_interest_results_demo_marker'))

    op.drop_table('career_interest_results')
    with op.batch_alter_table('career_experiment_criteria', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_criteria_skill_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_criteria_rubric_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_criteria_criterion_id'))

    op.drop_table('career_experiment_criteria')
    with op.batch_alter_table('browser_job_captures', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_user_id'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_status'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_source_domain'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_requested_action'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_profile_id'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_extension_connection_id'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_content_hash'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_captured_at'))
        batch_op.drop_index(batch_op.f('ix_browser_job_captures_capture_method'))

    op.drop_table('browser_job_captures')
    with op.batch_alter_table('assessment_scores', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_scores_user_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_scores_session_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_scores_score_type'))
        batch_op.drop_index(batch_op.f('ix_assessment_scores_profile_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_scores_dimension'))
        batch_op.drop_index(batch_op.f('ix_assessment_scores_demo_marker'))

    op.drop_table('assessment_scores')
    with op.batch_alter_table('assessment_responses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_responses_user_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_responses_session_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_responses_profile_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_responses_module_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_responses_item_id'))

    op.drop_table('assessment_responses')
    with op.batch_alter_table('assessment_interpretations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_interpretations_user_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_interpretations_session_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_interpretations_profile_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_interpretations_demo_marker'))

    op.drop_table('assessment_interpretations')
    with op.batch_alter_table('application_documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_application_documents_user_id'))
        batch_op.drop_index(batch_op.f('ix_application_documents_status'))
        batch_op.drop_index(batch_op.f('ix_application_documents_readiness_status'))
        batch_op.drop_index(batch_op.f('ix_application_documents_profile_id'))
        batch_op.drop_index(batch_op.f('ix_application_documents_job_application_id'))
        batch_op.drop_index(batch_op.f('ix_application_documents_job_analysis_id'))
        batch_op.drop_index(batch_op.f('ix_application_documents_evidence_lock_status'))
        batch_op.drop_index(batch_op.f('ix_application_documents_document_type'))
        batch_op.drop_index(batch_op.f('ix_application_documents_demo_marker'))

    op.drop_table('application_documents')
    with op.batch_alter_table('ai_readiness_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_readiness_results_user_id'))
        batch_op.drop_index(batch_op.f('ix_ai_readiness_results_session_id'))
        batch_op.drop_index(batch_op.f('ix_ai_readiness_results_profile_id'))
        batch_op.drop_index(batch_op.f('ix_ai_readiness_results_demo_marker'))

    op.drop_table('ai_readiness_results')
    with op.batch_alter_table('advisor_comments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_advisor_comments_target_type'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_target_id'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_suggestion_type'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_status'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_share_id'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_profile_id'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_evidence_validation'))
        batch_op.drop_index(batch_op.f('ix_advisor_comments_adviser_role'))

    op.drop_table('advisor_comments')
    with op.batch_alter_table('support_programme_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_programme_versions_programme_id'))

    op.drop_table('support_programme_versions')
    with op.batch_alter_table('star_stories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_star_stories_user_id'))
        batch_op.drop_index(batch_op.f('ix_star_stories_status'))
        batch_op.drop_index(batch_op.f('ix_star_stories_quality_status'))
        batch_op.drop_index(batch_op.f('ix_star_stories_profile_id'))
        batch_op.drop_index(batch_op.f('ix_star_stories_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_star_stories_confidentiality_status'))

    op.drop_table('star_stories')
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmaps_user_id'))
        batch_op.drop_index(batch_op.f('ix_roadmaps_profile_id'))

    op.drop_table('roadmaps')
    with op.batch_alter_table('research_study_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_study_versions_study_id'))

    op.drop_table('research_study_versions')
    with op.batch_alter_table('research_questions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_questions_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_questions_instrument_type'))
        batch_op.drop_index(batch_op.f('ix_research_questions_construct'))
        batch_op.drop_index(batch_op.f('ix_research_questions_active'))

    op.drop_table('research_questions')
    with op.batch_alter_table('research_participants', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_participants_user_id'))
        batch_op.drop_index(batch_op.f('ix_research_participants_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_participants_status'))
        batch_op.drop_index(batch_op.f('ix_research_participants_pseudonymous_id'))
        batch_op.drop_index(batch_op.f('ix_research_participants_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_participants_demo_marker'))

    op.drop_table('research_participants')
    with op.batch_alter_table('research_originality_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_user_id'))
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_pseudonymous_id'))
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_research_originality_sessions_assigned_condition'))

    op.drop_table('research_originality_sessions')
    with op.batch_alter_table('research_export_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_export_runs_study_id'))
        batch_op.drop_index(batch_op.f('ix_research_export_runs_status'))

    op.drop_table('research_export_runs')
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recommendations_user_id'))
        batch_op.drop_index(batch_op.f('ix_recommendations_status'))
        batch_op.drop_index(batch_op.f('ix_recommendations_profile_id'))
        batch_op.drop_index(batch_op.f('ix_recommendations_category'))

    op.drop_table('recommendations')
    with op.batch_alter_table('recommendation_robustness_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recommendation_robustness_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_recommendation_robustness_runs_status'))
        batch_op.drop_index(batch_op.f('ix_recommendation_robustness_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_recommendation_robustness_runs_demo_marker'))

    op.drop_table('recommendation_robustness_runs')
    with op.batch_alter_table('rag_run_sources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rag_run_sources_rag_run_id'))

    op.drop_table('rag_run_sources')
    with op.batch_alter_table('rag_feedback', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rag_feedback_user_id'))
        batch_op.drop_index(batch_op.f('ix_rag_feedback_rag_run_id'))

    op.drop_table('rag_feedback')
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_profiles_user_id'))

    op.drop_table('profiles')
    with op.batch_alter_table('master_career_profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_master_career_profiles_user_id'))
        batch_op.drop_index(batch_op.f('ix_master_career_profiles_status'))
        batch_op.drop_index(batch_op.f('ix_master_career_profiles_profile_id'))
        batch_op.drop_index(batch_op.f('ix_master_career_profiles_demo_marker'))

    op.drop_table('master_career_profiles')
    with op.batch_alter_table('market_signal_results', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_market_signal_results_trend_label'))
        batch_op.drop_index(batch_op.f('ix_market_signal_results_signal_type'))
        batch_op.drop_index(batch_op.f('ix_market_signal_results_run_id'))
        batch_op.drop_index(batch_op.f('ix_market_signal_results_label'))

    op.drop_table('market_signal_results')
    with op.batch_alter_table('market_role_signals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_market_role_signals_snapshot_id'))
        batch_op.drop_index(batch_op.f('ix_market_role_signals_role_family'))

    op.drop_table('market_role_signals')
    with op.batch_alter_table('market_radar_preferences', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_market_radar_preferences_user_id'))
        batch_op.drop_index(batch_op.f('ix_market_radar_preferences_selected_hypothesis_id'))
        batch_op.drop_index(batch_op.f('ix_market_radar_preferences_profile_id'))
        batch_op.drop_index(batch_op.f('ix_market_radar_preferences_demo_marker'))

    op.drop_table('market_radar_preferences')
    with op.batch_alter_table('learning_resources', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resources_title'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_resource_type'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_quality_status'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_provider_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_level'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_last_verified_at'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_language'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_external_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_cost_type'))
        batch_op.drop_index(batch_op.f('ix_learning_resources_active'))

    op.drop_table('learning_resources')
    with op.batch_alter_table('learning_resource_comparisons', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_resource_comparisons_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_comparisons_profile_id'))
        batch_op.drop_index(batch_op.f('ix_learning_resource_comparisons_demo_marker'))

    op.drop_table('learning_resource_comparisons')
    with op.batch_alter_table('learning_preferences', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_preferences_user_id'))
        batch_op.drop_index(batch_op.f('ix_learning_preferences_profile_id'))

    op.drop_table('learning_preferences')
    with op.batch_alter_table('labour_market_sync_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_runs_status'))
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_runs_provider_id'))
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_runs_demo_marker'))

    op.drop_table('labour_market_sync_runs')
    with op.batch_alter_table('labour_market_sync_cursors', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_cursors_provider_id'))
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_cursors_cursor_status'))
        batch_op.drop_index(batch_op.f('ix_labour_market_sync_cursors_cursor_key'))

    op.drop_table('labour_market_sync_cursors')
    with op.batch_alter_table('job_skill_mentions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_skill_mentions_requirement_type'))
        batch_op.drop_index(batch_op.f('ix_job_skill_mentions_original_phrase'))
        batch_op.drop_index(batch_op.f('ix_job_skill_mentions_normalised_skill_id'))
        batch_op.drop_index(batch_op.f('ix_job_skill_mentions_job_id'))

    op.drop_table('job_skill_mentions')
    with op.batch_alter_table('job_posting_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_posting_versions_provider_event_id'))
        batch_op.drop_index(batch_op.f('ix_job_posting_versions_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_posting_versions_content_hash'))

    op.drop_table('job_posting_versions')
    with op.batch_alter_table('job_loss_profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_loss_profiles_user_id'))
        batch_op.drop_index(batch_op.f('ix_job_loss_profiles_status'))
        batch_op.drop_index(batch_op.f('ix_job_loss_profiles_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_loss_profiles_demo_marker'))

    op.drop_table('job_loss_profiles')
    with op.batch_alter_table('job_locations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_locations_municipality'))
        batch_op.drop_index(batch_op.f('ix_job_locations_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_locations_county'))
        batch_op.drop_index(batch_op.f('ix_job_locations_country'))
        batch_op.drop_index(batch_op.f('ix_job_locations_city'))

    op.drop_table('job_locations')
    with op.batch_alter_table('job_language_requirements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_language_requirements_requirement_type'))
        batch_op.drop_index(batch_op.f('ix_job_language_requirements_language'))
        batch_op.drop_index(batch_op.f('ix_job_language_requirements_job_id'))

    op.drop_table('job_language_requirements')
    with op.batch_alter_table('job_classifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_classifications_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_classifications_code'))
        batch_op.drop_index(batch_op.f('ix_job_classifications_classification_type'))

    op.drop_table('job_classifications')
    with op.batch_alter_table('job_analyses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_analyses_user_id'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_title'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_status'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_profile_id'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_input_type'))
        batch_op.drop_index(batch_op.f('ix_job_analyses_demo_marker'))

    op.drop_table('job_analyses')
    with op.batch_alter_table('esco_mappings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_esco_mappings_status'))
        batch_op.drop_index(batch_op.f('ix_esco_mappings_original_phrase'))
        batch_op.drop_index(batch_op.f('ix_esco_mappings_normalised_phrase'))
        batch_op.drop_index(batch_op.f('ix_esco_mappings_concept_id'))

    op.drop_table('esco_mappings')
    with op.batch_alter_table('esco_labels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_esco_labels_language'))
        batch_op.drop_index(batch_op.f('ix_esco_labels_label'))
        batch_op.drop_index(batch_op.f('ix_esco_labels_concept_id'))

    op.drop_table('esco_labels')
    with op.batch_alter_table('diagnostics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_diagnostics_user_id'))

    op.drop_table('diagnostics')
    with op.batch_alter_table('conversations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_conversations_user_id'))
        batch_op.drop_index(batch_op.f('ix_conversations_profile_id'))

    op.drop_table('conversations')
    with op.batch_alter_table('career_transition_simulations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_status'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_scenario_name'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_saved'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_preset'))
        batch_op.drop_index(batch_op.f('ix_career_transition_simulations_demo_marker'))

    op.drop_table('career_transition_simulations')
    with op.batch_alter_table('career_role_profile_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_role_profile_versions_slug'))
        batch_op.drop_index(batch_op.f('ix_career_role_profile_versions_role_profile_id'))

    op.drop_table('career_role_profile_versions')
    with op.batch_alter_table('career_experiment_rubrics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_rubrics_experiment_template_id'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_rubrics_active'))

    op.drop_table('career_experiment_rubrics')
    with op.batch_alter_table('career_comparisons', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_comparisons_user_id'))
        batch_op.drop_index(batch_op.f('ix_career_comparisons_profile_id'))
        batch_op.drop_index(batch_op.f('ix_career_comparisons_demo_marker'))

    op.drop_table('career_comparisons')
    with op.batch_alter_table('browser_extension_connections', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_user_id'))
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_token_hash'))
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_status'))
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_profile_id'))
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_expires_at'))
        batch_op.drop_index(batch_op.f('ix_browser_extension_connections_demo_marker'))

    op.drop_table('browser_extension_connections')
    with op.batch_alter_table('assessment_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_sessions_user_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_sessions_status'))
        batch_op.drop_index(batch_op.f('ix_assessment_sessions_profile_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_sessions_mode'))
        batch_op.drop_index(batch_op.f('ix_assessment_sessions_demo_marker'))

    op.drop_table('assessment_sessions')
    with op.batch_alter_table('advisor_shares', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_advisor_shares_user_id'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_token_hash'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_status'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_profile_id'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_permission_level'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_expires_at'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_advisor_shares_adviser_role'))

    op.drop_table('advisor_shares')
    with op.batch_alter_table('adaptive_experiment_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_runs_status'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_adaptive_experiment_runs_demo_marker'))

    op.drop_table('adaptive_experiment_runs')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    with op.batch_alter_table('support_programmes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_programmes_jurisdiction'))
        batch_op.drop_index(batch_op.f('ix_support_programmes_category'))
        batch_op.drop_index(batch_op.f('ix_support_programmes_authority'))
        batch_op.drop_index(batch_op.f('ix_support_programmes_active'))

    op.drop_table('support_programmes')
    with op.batch_alter_table('support_opportunity_links', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_opportunity_links_target_type'))
        batch_op.drop_index(batch_op.f('ix_support_opportunity_links_target_id'))
        batch_op.drop_index(batch_op.f('ix_support_opportunity_links_source_type'))
        batch_op.drop_index(batch_op.f('ix_support_opportunity_links_source_id'))
        batch_op.drop_index(batch_op.f('ix_support_opportunity_links_profile_id'))

    op.drop_table('support_opportunity_links')
    with op.batch_alter_table('skill_recency', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_recency_status'))
        batch_op.drop_index(batch_op.f('ix_skill_recency_skill_id'))
        batch_op.drop_index(batch_op.f('ix_skill_recency_profile_id'))

    op.drop_table('skill_recency')
    with op.batch_alter_table('skill_normalisation_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_normalisation_runs_status'))

    op.drop_table('skill_normalisation_runs')
    with op.batch_alter_table('research_studies', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_research_studies_study_mode'))
        batch_op.drop_index(batch_op.f('ix_research_studies_status'))
        batch_op.drop_index(batch_op.f('ix_research_studies_demo_marker'))

    op.drop_table('research_studies')
    with op.batch_alter_table('recommendation_system_card_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_recommendation_system_card_versions_version'))
        batch_op.drop_index(batch_op.f('ix_recommendation_system_card_versions_status'))

    op.drop_table('recommendation_system_card_versions')
    with op.batch_alter_table('rag_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_rag_runs_user_id'))
        batch_op.drop_index(batch_op.f('ix_rag_runs_run_origin'))
        batch_op.drop_index(batch_op.f('ix_rag_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_rag_runs_created_at'))

    op.drop_table('rag_runs')
    with op.batch_alter_table('originality_audit_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_target_type'))
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_target_id'))
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_profile_id'))
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_event_type'))
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_actor_type'))
        batch_op.drop_index(batch_op.f('ix_originality_audit_events_actor_id'))

    op.drop_table('originality_audit_events')
    with op.batch_alter_table('market_snapshots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_market_snapshots_status'))
        batch_op.drop_index(batch_op.f('ix_market_snapshots_region'))
        batch_op.drop_index(batch_op.f('ix_market_snapshots_country'))

    op.drop_table('market_snapshots')
    with op.batch_alter_table('market_signal_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_market_signal_runs_status'))
        batch_op.drop_index(batch_op.f('ix_market_signal_runs_profile_id'))
        batch_op.drop_index(batch_op.f('ix_market_signal_runs_demo_marker'))

    op.drop_table('market_signal_runs')
    with op.batch_alter_table('learning_providers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_providers_provider_name'))
        batch_op.drop_index(batch_op.f('ix_learning_providers_active'))

    op.drop_table('learning_providers')
    with op.batch_alter_table('labour_market_providers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_labour_market_providers_status'))
        batch_op.drop_index(batch_op.f('ix_labour_market_providers_provider_name'))
        batch_op.drop_index(batch_op.f('ix_labour_market_providers_enabled'))

    op.drop_table('labour_market_providers')
    with op.batch_alter_table('job_postings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_job_postings_work_mode'))
        batch_op.drop_index(batch_op.f('ix_job_postings_title'))
        batch_op.drop_index(batch_op.f('ix_job_postings_publication_time'))
        batch_op.drop_index(batch_op.f('ix_job_postings_provider_event_id'))
        batch_op.drop_index(batch_op.f('ix_job_postings_provider'))
        batch_op.drop_index(batch_op.f('ix_job_postings_municipality'))
        batch_op.drop_index(batch_op.f('ix_job_postings_last_provider_update'))
        batch_op.drop_index(batch_op.f('ix_job_postings_is_active'))
        batch_op.drop_index(batch_op.f('ix_job_postings_ingested_at'))
        batch_op.drop_index(batch_op.f('ix_job_postings_external_job_id'))
        batch_op.drop_index(batch_op.f('ix_job_postings_expiry_time'))
        batch_op.drop_index(batch_op.f('ix_job_postings_event_type'))
        batch_op.drop_index(batch_op.f('ix_job_postings_employer'))
        batch_op.drop_index(batch_op.f('ix_job_postings_demo_marker'))
        batch_op.drop_index(batch_op.f('ix_job_postings_county'))
        batch_op.drop_index(batch_op.f('ix_job_postings_country'))
        batch_op.drop_index(batch_op.f('ix_job_postings_content_hash'))
        batch_op.drop_index(batch_op.f('ix_job_postings_city'))

    op.drop_table('job_postings')
    with op.batch_alter_table('innovation_audit_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_target_type'))
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_target_id'))
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_profile_id'))
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_event_type'))
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_actor_type'))
        batch_op.drop_index(batch_op.f('ix_innovation_audit_events_actor_id'))

    op.drop_table('innovation_audit_events')
    with op.batch_alter_table('fear_transforms', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fear_transforms_profile_id'))

    op.drop_table('fear_transforms')
    with op.batch_alter_table('fairness_audit_runs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_fairness_audit_runs_status'))
        batch_op.drop_index(batch_op.f('ix_fairness_audit_runs_demo_marker'))

    op.drop_table('fairness_audit_runs')
    with op.batch_alter_table('external_provider_cache', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_external_provider_cache_provider_name'))
        batch_op.drop_index(batch_op.f('ix_external_provider_cache_expires_at'))
        batch_op.drop_index(batch_op.f('ix_external_provider_cache_cache_key'))

    op.drop_table('external_provider_cache')
    with op.batch_alter_table('esco_concepts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_esco_concepts_preferred_label'))
        batch_op.drop_index(batch_op.f('ix_esco_concepts_esco_uri'))
        batch_op.drop_index(batch_op.f('ix_esco_concepts_concept_type'))

    op.drop_table('esco_concepts')
    with op.batch_alter_table('career_role_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_role_templates_title'))
        batch_op.drop_index(batch_op.f('ix_career_role_templates_role_family'))

    op.drop_table('career_role_templates')
    with op.batch_alter_table('career_role_profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_role_profiles_title'))
        batch_op.drop_index(batch_op.f('ix_career_role_profiles_status'))
        batch_op.drop_index(batch_op.f('ix_career_role_profiles_slug'))
        batch_op.drop_index(batch_op.f('ix_career_role_profiles_career_family'))

    op.drop_table('career_role_profiles')
    with op.batch_alter_table('career_experiment_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_experiment_templates_title'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_templates_target_role_family'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_templates_difficulty'))
        batch_op.drop_index(batch_op.f('ix_career_experiment_templates_active'))

    op.drop_table('career_experiment_templates')
    with op.batch_alter_table('assessment_options', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_options_item_id'))

    op.drop_table('assessment_options')
    with op.batch_alter_table('assessment_modules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_modules_assessment_id'))

    op.drop_table('assessment_modules')
    with op.batch_alter_table('assessment_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_items_module_id'))
        batch_op.drop_index(batch_op.f('ix_assessment_items_dimension'))

    op.drop_table('assessment_items')
    with op.batch_alter_table('assessment_definitions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assessment_definitions_version'))

    op.drop_table('assessment_definitions')
    # End initial schema downgrade.
