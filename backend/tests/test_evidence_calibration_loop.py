from sqlalchemy import func, select

from app.models.assessment import SkillEvidence
from app.models.career_resilience import CareerEvidenceProposal, CareerExperimentSession, CareerHypothesis, CareerRecalibrationRun
from app.services.career_resilience_engine import (
    create_experiment_session,
    ensure_hypotheses_from_matches,
    evidence_passport,
    list_evidence_proposals,
    list_profile_evidence_gaps,
    review_evidence_proposal,
    start_experiment,
    submit_experiment,
    evaluate_experiment,
)
from app.services.assessment_engine import complete_assessment_session, upsert_responses
from app.models.assessment import AssessmentSession, CareerMatch
from app.models.profile import Profile
from app.models.user import User
from app.services.demo_seed_service import demo_assessment_responses

from test_career_resilience_engine import session


def _profile_with_matches(db):
    user = User(name="Calibration User", email="calibration@example.test", hashed_password="x")
    db.add(user)
    db.flush()
    profile = Profile(user_id=user.id, diagnostic_id="diagnostic", data={"profile_version": "profile-v1"})
    db.add(profile)
    db.flush()
    assessment = AssessmentSession(profile_id=profile.id, user_id=user.id, mode="complete", status="in_progress", consent_accepted=True)
    db.add(assessment)
    db.flush()
    upsert_responses(db, assessment, demo_assessment_responses())
    complete_assessment_session(db, assessment, profile)
    match = db.scalar(select(CareerMatch).where(CareerMatch.profile_id == profile.id).order_by(CareerMatch.alignment_score.desc()))
    db.commit()
    return user, profile, match


def _evaluated(db):
    user, profile, match = _profile_with_matches(db)
    gaps = list_profile_evidence_gaps(db, profile)["gaps"]
    gap = next(item for item in gaps if item["hypothesis_id"])
    created = create_experiment_session(
        db,
        profile,
        {"experiment_template_id": "ai-product-explainable-recommendation-interface", "career_match_id": match.id, "hypothesis_id": gap["hypothesis_id"], "evidence_gap_id": gap["id"], "user_confirmed": True},
        user.id,
    )
    row = db.get(CareerExperimentSession, created["id"])
    start_experiment(db, row)
    submit_experiment(db, row, {"text_response": "A concrete prototype with user research, product reasoning, validation checklist, accessibility notes, and tradeoffs." * 2, "project_url": "https://example.test/calibration", "completion_notes": "Bounded artifact submitted for deterministic review.", "time_spent_minutes": 120, "reflection": {"note": "The experiment clarified the remaining evidence gap."}})
    evaluated = evaluate_experiment(db, row)
    return user, profile, match, gap, evaluated


def test_hypothesis_exposes_source_breakdown_and_explicit_gap_kinds():
    db = session()
    _, profile, _ = _profile_with_matches(db)
    hypotheses = ensure_hypotheses_from_matches(db, profile)
    gaps = list_profile_evidence_gaps(db, profile)
    assert hypotheses
    assert all(item.source_breakdown_json.get("SYSTEM_DERIVED") is None for item in hypotheses)
    assert all(item["status"] in {"MISSING", "OUTDATED", "CONFLICTING", "INSUFFICIENT", "SELF_REPORT_ONLY", "PARTIAL"} for item in gaps["gaps"])
    assert any(item["gap_kind"] == "evidence_gap" for item in gaps["gaps"])
    assert all("SYSTEM_DERIVED" in item["source_types"] for item in gaps["gaps"] if item["source_types"])


def test_evaluation_persists_deterministic_evidence_and_keeps_proposals_pending_review():
    db = session()
    _, profile, _, _, evaluated = _evaluated(db)
    proposals = list_evidence_proposals(db, profile)
    assert evaluated["status"] == "evaluated"
    assert proposals and all(item["status"] == "PENDING_REVIEW" for item in proposals)
    assert all(item["verification_state"] == "PROVISIONAL" for item in proposals)
    assert evaluated["result"]["actual_evidence_gain"]["authoritative_evidence_created"] is True
    passport = evidence_passport(db, profile.id)
    assert any(skill["evidence_sources"] for skill in passport["skills"])


def test_accepting_proposal_updates_only_affected_hypothesis_and_preserves_versions():
    db = session()
    _, profile, match, gap, _ = _evaluated(db)
    proposal = db.scalar(
        select(CareerEvidenceProposal)
        .where(
            CareerEvidenceProposal.profile_id == profile.id,
            CareerEvidenceProposal.hypothesis_id == gap["hypothesis_id"],
        )
        .order_by(CareerEvidenceProposal.created_at)
    )
    assert proposal is not None
    hypothesis = db.get(CareerHypothesis, proposal.hypothesis_id)
    before_version = hypothesis.current_version_number
    other = db.scalars(select(CareerHypothesis).where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.id != hypothesis.id)).first()
    result = review_evidence_proposal(db, profile, proposal.id, {"decision": "accept", "note": "I confirm this bounded project evidence."}, profile.user_id)
    assert result["authoritative_update"] is True
    assert result["proposal"]["status"] == "ACCEPTED"
    assert result["proposal"]["verification_state"] == "USER_CONFIRMED"
    assert result["recalibration"]["hypothesis_id"] == hypothesis.id
    assert result["recalibration"]["before"]["hypothesis"]["version"] == before_version
    assert result["recalibration"]["after"]["hypothesis"]["version"] == before_version + 1
    assert db.scalar(select(func.count()).select_from(CareerRecalibrationRun).where(CareerRecalibrationRun.hypothesis_id == hypothesis.id)) == 1
    if other:
        assert db.scalar(select(func.count()).select_from(CareerRecalibrationRun).where(CareerRecalibrationRun.hypothesis_id == other.id)) == 0
    assert any(skill["evidence_sources"] for skill in result["evidence_passport"]["skills"])


def test_rejecting_confirmed_proposal_supports_downward_recalibration():
    db = session()
    _, profile, _, gap, _ = _evaluated(db)
    proposal = db.scalar(
        select(CareerEvidenceProposal)
        .where(
            CareerEvidenceProposal.profile_id == profile.id,
            CareerEvidenceProposal.hypothesis_id == gap["hypothesis_id"],
        )
        .order_by(CareerEvidenceProposal.created_at)
    )
    accepted = review_evidence_proposal(db, profile, proposal.id, {"decision": "accept"}, profile.user_id)
    rejected = review_evidence_proposal(db, profile, proposal.id, {"decision": "reject", "reason": "The artifact was corrected and should not be used."}, profile.user_id)
    assert accepted["proposal"]["status"] == "ACCEPTED"
    assert rejected["proposal"]["status"] == "REJECTED"
    assert rejected["recalibration"]["after"]["hypothesis"]["uncertainty_label"] == "Higher uncertainty"
    assert rejected["recalibration"]["changed_recommendations"][0]["change"] <= 0
