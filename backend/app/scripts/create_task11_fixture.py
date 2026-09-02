from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.core.time import utc_now_naive
from app.database import import_models
from app.db.migration_status import alembic_config
from app.models.conversation import Conversation
from app.models.diagnostic import Diagnostic
from app.models.message import Message
from app.models.profile import Profile
from app.models.rag_observability import RagFeedback, RagRun, RagRunSource
from app.models.recommendation import Recommendation, RecommendationEvent, RecommendationFeedback
from app.models.roadmap import Roadmap
from app.models.user import User
from app.services.database_admin import resolve_backend_path, write_json_atomic


def _now() -> datetime:
    return utc_now_naive()


def create_fixture(path: Path) -> dict[str, object]:
    fixture_path = resolve_backend_path(path)
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    if fixture_path.exists():
        fixture_path.unlink()

    database_url = f"sqlite:///{fixture_path.as_posix()}"
    config = alembic_config()
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    import_models()
    engine = create_engine(database_url)
    created_at = _now()
    try:
        with Session(engine) as session:
            user = User(
                id="fixture-user-001",
                name="OrganicAI Fixture User",
                email="fixture-user@organicai.local",
                hashed_password="fixture-hash-only",
                is_demo=True,
                demo_dataset_version=11,
                created_at=created_at,
                updated_at=created_at,
            )
            diagnostic = Diagnostic(
                id="fixture-diagnostic-001",
                user_id=user.id,
                payload={
                    "languages": ["English", "Romanian", "Norwegian"],
                    "romania": "Invatare responsabila cu inteligenta artificiala",
                    "romanianWithUtf8": "Invatare responsabila cu inteligenta artificiala in comunitati locale: învățare și grijă",
                    "norwegianWithUtf8": "Menneske og AI samarbeider på en ansvarlig måte",
                    "nullablePreference": None,
                    "consentConfirmed": True,
                },
                created_at=created_at,
            )
            profile = Profile(
                id="fixture-profile-001",
                user_id=user.id,
                diagnostic_id=diagnostic.id,
                data={
                    "archetype": "Collaborative systems thinker",
                    "strengths": ["evidence synthesis", "ethical reflection"],
                    "signals": {"romanian": "învățăm împreună", "norwegian": "ansvarlig samspill"},
                    "nullable_note": None,
                    "voiceMetadata": {"latestMode": "deterministic-fallback", "stored": True},
                },
                created_at=created_at,
            )
            conversation = Conversation(
                id="fixture-conversation-001",
                user_id=user.id,
                profile_id=profile.id,
                title="Task 11.1 fixture conversation",
                created_at=created_at,
                updated_at=created_at,
            )
            messages = [
                Message(
                    id="fixture-message-001",
                    conversation_id=conversation.id,
                    role="user",
                    content="How can I plan a responsible AI learning roadmap?",
                    input_mode="voice",
                    audio_url=None,
                    created_at=created_at,
                ),
                Message(
                    id="fixture-message-002",
                    conversation_id=conversation.id,
                    role="assistant",
                    content="Use a small experiment, document assumptions, and review privacy before collecting data.",
                    input_mode="text",
                    audio_url="/media/voice/fixture-latest.mp3",
                    created_at=created_at,
                ),
            ]
            recommendation = Recommendation(
                id="fixture-recommendation-001",
                user_id=user.id,
                profile_id=profile.id,
                category="learning",
                title="Run a privacy-first learning sprint",
                summary="A synthetic recommendation for validating PostgreSQL migration.",
                reason="The profile emphasizes ethical reflection and evidence synthesis.",
                profile_signals_json=["ethical reflection", "evidence synthesis"],
                rag_sources_json=[{"document": "fixture", "chunk": "privacy"}],
                score_components_json={"relevance": 0.92, "novelty": 0.44},
                retrieval_metadata_json={"provider": "local", "ragRunId": "fixture-rag-run-001"},
                relevance_score=0.92,
                confidence=0.88,
                effort="medium",
                impact="high",
                time_horizon="thirty_days",
                estimated_duration="2-4 weeks",
                prerequisites_json=[],
                first_action="Write a one-page experiment charter.",
                success_indicator="A reviewed plan exists before any real user data is collected.",
                ethical_cautions_json=["Do not collect personal data in this fixture."],
                what_to_verify_json=["Unicode", "JSON", "nullable values", "booleans"],
                status="suggested",
                generation_version="fixture-v1",
                created_at=created_at,
                updated_at=created_at,
            )
            roadmap = Roadmap(
                id="fixture-roadmap-001",
                user_id=user.id,
                profile_id=profile.id,
                data={
                    "milestones": [
                        {"id": "m1", "title": "Baseline", "complete": True},
                        {"id": "m2", "title": "PostgreSQL validation", "complete": False},
                    ],
                    "notes": {"romanian": "plan de învățare", "norwegian": "læringsplan"},
                    "nullableOwnerNote": None,
                },
                created_at=created_at,
            )
            rag_run = RagRun(
                id="fixture-rag-run-001",
                user_id=user.id,
                profile_id=profile.id,
                conversation_id=conversation.id,
                message_id=messages[0].id,
                query="responsible AI learning roadmap",
                query_normalized="responsible ai learning roadmap",
                mode="knowledge_base",
                run_origin="user",
                retrieval_top_k=4,
                relevance_threshold=0.1,
                retrieved_count=1,
                used_source_count=1,
                highest_similarity_score=0.91,
                average_similarity_score=0.91,
                retrieval_duration_ms=12,
                generation_duration_ms=21,
                total_duration_ms=33,
                embedding_model="fixture-embedding",
                generation_model="deterministic-fixture",
                provider="local",
                answer="A deterministic fixture answer.",
                confidence_note="Synthetic confidence metadata.",
                ethical_note="No personal data is present.",
                context_quality="sufficient",
                insufficient_context=False,
                prompt_injection_flag=False,
                status="completed",
                created_at=created_at,
            )
            rag_source = RagRunSource(
                id="fixture-rag-source-001",
                rag_run_id=rag_run.id,
                document_id="fixture-doc-001",
                document_name="Fixture Knowledge",
                chunk_id="fixture-chunk-001",
                section_title="Privacy",
                chunk_position=1,
                similarity_score=0.91,
                rank=1,
                was_used_in_context=True,
                source_excerpt="Synthetic excerpt for migration validation.",
                injection_risk=False,
                created_at=created_at,
            )
            rag_feedback = RagFeedback(
                id="fixture-rag-feedback-001",
                rag_run_id=rag_run.id,
                user_id=user.id,
                profile_id=profile.id,
                feedback_type="answer",
                rating="useful",
                reason_code="grounded",
                comment=None,
                source_id=None,
                created_at=created_at,
                updated_at=created_at,
            )
            recommendation_feedback = RecommendationFeedback(
                id="fixture-recommendation-feedback-001",
                recommendation_id=recommendation.id,
                user_id=user.id,
                rating=5,
                relevant=True,
                feedback_text=None,
                reason_code="useful",
                created_at=created_at,
            )
            recommendation_event = RecommendationEvent(
                id="fixture-recommendation-event-001",
                recommendation_id=recommendation.id,
                user_id=user.id,
                event_type="viewed",
                metadata_json={"source": "fixture", "preservedBoolean": True, "nullable": None},
                created_at=created_at,
            )
            session.add_all(
                [
                    user,
                    diagnostic,
                    profile,
                    conversation,
                    *messages,
                    recommendation,
                    recommendation_feedback,
                    recommendation_event,
                    roadmap,
                    rag_run,
                    rag_source,
                    rag_feedback,
                ]
            )
            session.commit()

        table_counts: dict[str, int] = {}
        with engine.connect() as connection:
            inspector = inspect(engine)
            for table in sorted(inspector.get_table_names()):
                quoted = '"' + table.replace('"', '""') + '"'
                table_counts[table] = int(connection.exec_driver_sql(f"SELECT COUNT(*) FROM {quoted}").scalar_one())
            fk_issues = list(connection.exec_driver_sql("PRAGMA foreign_key_check"))
            current_revision = connection.exec_driver_sql("SELECT version_num FROM alembic_version").fetchall()
    finally:
        engine.dispose()

    return {
        "fixturePath": str(fixture_path),
        "createdByAlembic": True,
        "syntheticDataOnly": True,
        "foreignKeyIssueCount": len(fk_issues),
        "rowCounts": table_counts,
        "schemaVersion": current_revision[0][0] if current_revision else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the Task 11.1 synthetic SQLite migration fixture.")
    parser.add_argument("--output", default="./tmp/task11-fixtures/organicai-fixture.db")
    parser.add_argument("--manifest", default="../reports/database-migrations/task11-fixture-manifest.json")
    args = parser.parse_args()
    try:
        result = create_fixture(Path(args.output))
        write_json_atomic(resolve_backend_path(args.manifest), result)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": exc.__class__.__name__, "message": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "success", **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
