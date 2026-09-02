from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.diagnostic import Diagnostic
from app.models.career_resilience import CareerEvidenceGap, CareerHypothesis
from app.models.learning import LearningPreferences
from app.models.profile import Profile
from app.models.recommendation import Recommendation, RecommendationEvent, RecommendationFeedback
from app.models.roadmap import Roadmap
from app.services.career_resilience_engine import EVIDENCE_GAP_STATUSES, _evidence_state_for_skill

def names(items): return [item.get("name") if isinstance(item,dict) else str(item) for item in items or []]


def current_evidence_gaps(db: Session, profile: Profile, rows: list[CareerEvidenceGap], hypotheses: dict[str, CareerHypothesis]) -> list[CareerEvidenceGap]:
    """Return unresolved gaps from the persisted evidence graph, without mutating it.

    A completed experiment can create practical evidence before another page has
    refreshed the denormalized CareerEvidenceGap row.  The evidence state is
    the authoritative read model for a recommendation decision in that gap.
    """
    return [
        row
        for row in rows
        if (state := _evidence_state_for_skill(db, profile.id, row.skill_id, hypotheses.get(row.hypothesis_id)))["status"] in EVIDENCE_GAP_STATUSES
    ]

def build_recommendation_context(db: Session, profile: Profile) -> dict:
    data = profile.data
    feedback = data.get("user_feedback", {})
    diagnostic = db.get(Diagnostic, profile.diagnostic_id) if profile.diagnostic_id else None
    answers = diagnostic.payload if diagnostic else {}
    primary = data.get("primary_archetype", {})
    primary_name = feedback.get("archetype_override") or (primary.get("name") if isinstance(primary, dict) else primary)
    strengths = names(data.get("strengths", []))
    adjusted = feedback.get("strength_adjustments", {})
    confirmed = [name for name in strengths if adjusted.get(name, 50) >= 50]
    previous = db.scalars(select(Recommendation).where(Recommendation.profile_id == profile.id)).all()
    accepted = [item.title for item in previous if item.status in {"accepted", "in_progress", "completed"}]
    rejected = [item.title for item in previous if item.status == "rejected"]
    roadmap = db.scalar(select(Roadmap).where(Roadmap.profile_id == profile.id).order_by(Roadmap.created_at.desc()))
    hypotheses = db.scalars(
        select(CareerHypothesis)
        .where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.status == "active")
        .order_by(CareerHypothesis.current_alignment_score.desc(), CareerHypothesis.title)
    ).all()
    hypothesis_titles = {item.id: item.title for item in hypotheses}
    active_hypothesis_ids = [item.id for item in hypotheses]
    gap_query = select(CareerEvidenceGap).where(CareerEvidenceGap.profile_id == profile.id)
    if active_hypothesis_ids:
        gap_query = gap_query.where(or_(CareerEvidenceGap.hypothesis_id.is_(None), CareerEvidenceGap.hypothesis_id.in_(active_hypothesis_ids)))
    else:
        gap_query = gap_query.where(CareerEvidenceGap.hypothesis_id.is_(None))
    gaps = current_evidence_gaps(
        db,
        profile,
        db.scalars(gap_query.order_by(CareerEvidenceGap.importance.desc(), CareerEvidenceGap.capability_label)).all(),
        {item.id: item for item in hypotheses},
    )
    preference = db.scalar(select(LearningPreferences).where(LearningPreferences.profile_id == profile.id))
    preference_signals = []
    if preference:
        preference_signals = [str(item) for item in (preference.preferred_content_formats_json or []) if str(item).strip()]
        preference_signals.append(f"about {preference.available_hours_per_week:g} hours per week")
        if preference.monthly_learning_budget is not None:
            preference_signals.append("monthly learning budget set")
    return {
        "primary_archetype": primary_name,
        "confirmed_strengths": confirmed,
        "values": names(data.get("values", [])),
        "learning_preferences": preference_signals or answers.get("preferred_learning_style", []),
        "ai_experience": answers.get("ai_experience", "unknown"),
        "ai_confidence": answers.get("ai_confidence", 0),
        "tools_used": answers.get("ai_tools_used", []),
        "fears": answers.get("fears", data.get("fears", [])),
        "goals": answers.get("ai_help_goals", []),
        "interests": answers.get("interests", []),
        "orientations": answers.get("preferred_orientation", []),
        "contribution_domains": names(data.get("contribution_domains", [])),
        "active_hypotheses": [{"title": item.title, "version": item.current_version_number} for item in hypotheses[:3]],
        "evidence_gaps": [
            {
                "capability": item.capability_label or item.skill_id.replace("_", " ").title(),
                "hypothesis": hypothesis_titles.get(item.hypothesis_id, "your active career direction"),
                "reason": item.reason,
                "importance": item.importance,
            }
            for item in gaps
        ][:4],
        "accepted_recommendations": accepted,
        "rejected_patterns": rejected,
        "hidden_recommendations": feedback.get("hidden_recommendations", []),
        "recent_roadmap_focus": [
            item.get("title")
            for key in ("seven_days", "thirty_days", "six_months")
            for item in roadmap.data.get(key, [])
        ] if roadmap else [],
        "feedback_applied": bool(feedback),
        "diagnostic_completeness": min(1, len([value for value in answers.values() if value]) / 12) if answers else .35,
    }


def archive_resolved_evidence_gap_recommendations(db: Session, profile: Profile) -> int:
    """Archive only still-suggested recommendations bound to resolved gaps.

    The generation-time source context identifies a gap-bound suggestion
    without touching accepted, in-progress, completed, or rejected records.
    Generic exploratory recommendations have no evidence-gap source and remain
    available.
    """
    hypotheses = db.scalars(
        select(CareerHypothesis).where(
            CareerHypothesis.profile_id == profile.id,
            CareerHypothesis.status == "active",
        )
    ).all()
    active_hypothesis_ids = [item.id for item in hypotheses]
    hypothesis_titles = {item.id: item.title for item in hypotheses}
    gap_query = select(CareerEvidenceGap).where(CareerEvidenceGap.profile_id == profile.id)
    if active_hypothesis_ids:
        gap_query = gap_query.where(or_(CareerEvidenceGap.hypothesis_id.is_(None), CareerEvidenceGap.hypothesis_id.in_(active_hypothesis_ids)))
    else:
        gap_query = gap_query.where(CareerEvidenceGap.hypothesis_id.is_(None))
    current_gaps = current_evidence_gaps(
        db,
        profile,
        db.scalars(gap_query).all(),
        {item.id: item for item in hypotheses},
    )
    active_pairs = {
        (hypothesis_titles.get(item.hypothesis_id, "your active career direction"), item.capability_label or item.skill_id.replace("_", " ").title())
        for item in current_gaps
    }
    archived = 0
    for recommendation in db.scalars(
        select(Recommendation).where(
            Recommendation.profile_id == profile.id,
            Recommendation.status == "suggested",
        )
    ).all():
        signals = recommendation.profile_signals_json or []
        gap_labels = {
            str(item.get("signal") or "")
            for item in signals
            if isinstance(item, dict) and item.get("source") == "evidence_gap" and str(item.get("signal") or "").strip()
        }
        source_hypotheses = {
            str(item.get("signal") or "")
            for item in signals
            if isinstance(item, dict) and item.get("source") == "career_hypothesis" and str(item.get("signal") or "").strip()
        }
        if not gap_labels or not source_hypotheses:
            continue
        if any((title, gap) in active_pairs for title in source_hypotheses for gap in gap_labels):
            continue
        recommendation.status = "archived"
        db.add(
            RecommendationEvent(
                recommendation_id=recommendation.id,
                user_id=profile.user_id,
                event_type="archived_resolved_evidence_gap",
                metadata_json={"reason": "The gap that scoped this suggestion is no longer unresolved."},
            )
        )
        archived += 1
    if archived:
        db.commit()
    return archived
