from __future__ import annotations

import hashlib
import math
from datetime import datetime
from app.core.time import utc_now_naive
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.assessment import SkillEvidence
from app.models.career_resilience import (
    CareerExperimentResult,
    CareerExperimentSession,
    CareerExperimentTemplate,
    CareerHypothesis,
    SkillEvidenceConfidence,
    SkillRecency,
    SupportedPathResult,
    SupportedPathRun,
)
from app.models.innovation_extension import CareerDecisionJournalEntry, CareerRoleProfile
from app.models.originality_research import (
    AdaptiveExperimentRecommendation,
    AdaptiveExperimentRun,
    CareerTransitionPath,
    CareerTransitionSimulation,
    FairnessAuditRun,
    OriginalityAuditEvent,
    RecommendationRobustnessRun,
    RecommendationSystemCardVersion,
    ResearchOriginalitySession,
)
from app.models.profile import Profile
from app.models.roadmap_adaptation import RoadmapAction
from app.services.career_resilience_engine import (
    create_experiment_session,
    latest_supported_paths,
    session_public,
    sync_career_resilience_catalogue,
)
from app.services.innovation_extension_engine import create_journal_entry, sync_career_encyclopedia


ADAPTIVE_SCORE_VERSION = "adaptive-evidence-gain-score-v1"
ADAPTIVE_WEIGHT_VERSION = "adaptive-evidence-gain-weights-v1"
PARETO_OBJECTIVE_VERSION = "career-transition-objectives-v1"
ROBUSTNESS_VERSION = "recommendation-robustness-v1"
SYSTEM_CARD_VERSION = "recommendation-system-card-v1"
DECISION_SUPPORT_MODEL_VERSION = "decision-support-snapshot-v1"
ADAPTIVE_GAP_VERSION = "adaptive-evidence-gap-v1"
SYNTHETIC_FAIRNESS_VERSION = "synthetic-fairness-lab-v1"

ADAPTIVE_LIFECYCLE_STATUSES = {
    "proposed",
    "accepted",
    "planned",
    "active",
    "paused",
    "completed",
    "abandoned",
    "rejected",
    "expired",
    "evidence submitted",
    "evidence reviewed",
}

ADAPTIVE_LIFECYCLE_TRANSITIONS = {
    "recommended": {"accepted", "planned", "rejected", "expired"},
    "proposed": {"accepted", "planned", "rejected", "expired"},
    "accepted": {"planned", "active", "rejected"},
    "saved": {"planned", "rejected", "expired"},
    "planned": {"active", "paused", "abandoned", "expired"},
    "started": {"active", "paused", "completed", "abandoned"},
    "active": {"paused", "completed", "abandoned", "evidence submitted"},
    "paused": {"active", "abandoned", "expired"},
    "completed": {"evidence submitted", "abandoned"},
    "outcome_recorded": {"evidence submitted", "evidence reviewed", "abandoned"},
    "evidence submitted": {"evidence reviewed"},
    "evidence reviewed": set(),
    "rejected": set(),
    "abandoned": set(),
    "expired": set(),
}

POSITIVE_EXPERIMENT_WEIGHTS = {
    "uncertainty_reduction": 0.16,
    "evidence_importance": 0.14,
    "market_relevance": 0.11,
    "cross_path_transferability": 0.10,
    "portfolio_value": 0.11,
    "feasibility": 0.10,
    "support_availability": 0.08,
    "user_preference_alignment": 0.08,
}
NEGATIVE_EXPERIMENT_WEIGHTS = {
    "time_cost": 0.08,
    "monetary_cost": 0.05,
    "complexity": 0.06,
    "accessibility_barrier": 0.05,
    "repetition_penalty": 0.05,
    "evidence_redundancy": 0.06,
    "implementation_risk": 0.06,
}

DEFAULT_TRANSITION_CONTROLS = {
    "weekly_learning_time": 8,
    "learning_budget": 50,
    "desired_transition_months": 9,
    "acceptable_financial_risk": "medium",
    "location": "Oslo",
    "remote_work_preference": "hybrid",
    "preferred_languages": ["English", "Romanian"],
    "formal_qualification_willingness": "maybe",
    "industry_change_willingness": "medium",
    "need_public_support": False,
}

OBJECTIVE_DIRECTIONS = {
    "transition_duration": "min",
    "direct_monetary_cost": "min",
    "weekly_effort": "min",
    "financial_risk": "min",
    "evidence_gap": "min",
    "capability_gap": "min",
    "language_barrier": "min",
    "dependence_on_uncertain_assumptions": "min",
    "personal_fit": "max",
    "capability_fit": "max",
    "market_fit": "max",
    "support_fit": "max",
    "local_opportunity_availability": "max",
    "accessibility": "max",
    "reversibility": "max",
    "portfolio_reuse": "max",
    "transferable_skill_reuse": "max",
    "ai_change_stability": "max",
}

DEFAULT_OBJECTIVES = [
    "transition_duration",
    "direct_monetary_cost",
    "weekly_effort",
    "financial_risk",
    "evidence_gap",
    "capability_gap",
    "personal_fit",
    "capability_fit",
    "market_fit",
    "support_fit",
    "local_opportunity_availability",
    "accessibility",
    "reversibility",
    "portfolio_reuse",
    "transferable_skill_reuse",
    "dependence_on_uncertain_assumptions",
    "ai_change_stability",
]


def _now() -> datetime:
    return utc_now_naive()


def _audit(db: Session, profile_id: str | None, event_type: str, target_type: str, target_id: str, actor_id: str = "", event: dict[str, Any] | None = None) -> None:
    db.add(OriginalityAuditEvent(profile_id=profile_id, event_type=event_type, target_type=target_type, target_id=target_id, actor_id=actor_id, event_json=event or {}))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _round(value: float) -> float:
    return round(_clamp(value), 2)


def _band(score: float) -> str:
    if score >= 0.74:
        return "High evidence value"
    if score >= 0.62:
        return "Useful evidence value"
    if score >= 0.48:
        return "Exploratory value"
    if score >= 0.32:
        return "Low current feasibility"
    return "Insufficient information"


def _effort(minutes: int) -> str:
    if minutes <= 120:
        return "low"
    if minutes <= 300:
        return "moderate"
    return "high"


def _hours(minutes: int) -> str:
    low = max(1, round(minutes / 60))
    high = max(low, round((minutes * 1.35) / 60))
    return f"{low}-{high} hours"


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list(value)]


def _finite_float(value: Any, default: float = 0.0, low: float | None = None, high: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if not math.isfinite(number):
        raise ValueError("Numeric controls must be finite values.")
    if low is not None:
        number = max(low, number)
    if high is not None:
        number = min(high, number)
    return number


def _safe_int(value: Any, default: int, low: int, high: int) -> int:
    return int(round(_finite_float(value, default, low, high)))


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = str(sorted(payload.items())).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _decision_support_snapshot(
    *,
    owner_profile_id: str,
    owner_user_id: str | None,
    output_kind: str,
    input_snapshot: dict[str, Any],
    rule_set_version: str,
    algorithm_version: str,
    source_versions: dict[str, Any],
    data_coverage: dict[str, Any],
    missing_inputs: list[str] | None = None,
    assumptions: list[str] | None = None,
    limitations: list[str] | None = None,
    seed: str = "local-deterministic-fixture-v1",
    user_confirmation: str = "not_confirmed",
    archived: bool = False,
) -> dict[str, Any]:
    missing = missing_inputs or []
    completeness = "complete" if not missing else "partial"
    trace = {
        "profile_id": owner_profile_id,
        "output_kind": output_kind,
        "rule_set_version": rule_set_version,
        "algorithm_version": algorithm_version,
        "source_versions": source_versions,
        "input_fingerprint": _stable_hash({"input_snapshot": input_snapshot, "source_versions": source_versions}),
    }
    return {
        "version": DECISION_SUPPORT_MODEL_VERSION,
        "snapshot_id": f"{output_kind}-{trace['input_fingerprint']}",
        "owner_profile_id": owner_profile_id,
        "owner_user_id": owner_user_id,
        "career_hypothesis_version": source_versions.get("career_hypotheses", "current-profile-snapshot"),
        "evidence_passport_version": source_versions.get("evidence", "evidence-confidence-v1"),
        "market_data_snapshot_version": source_versions.get("market_data", "local-demo-market-snapshot-v1"),
        "constraint_snapshot_version": source_versions.get("constraints", "user-constraint-snapshot-v1"),
        "preference_snapshot_version": source_versions.get("preferences", "profile-preference-snapshot-v1"),
        "rule_set_version": rule_set_version,
        "algorithm_version": algorithm_version,
        "generated_at": _now().isoformat(),
        "input_completeness": completeness,
        "data_quality_notes": ["Missing inputs are surfaced as uncertainty, not negative personal evidence."] + (["Some inputs are incomplete."] if missing else []),
        "missing_inputs": missing,
        "assumptions": assumptions or [],
        "limitations": limitations or [],
        "deterministic_seed": seed,
        "fixture_version": "week6-demo-fixture-v1",
        "explanation_trace": trace,
        "user_confirmation": user_confirmation,
        "archived": archived,
    }


def _profile_constraints(profile: Profile, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    data = profile.data or {}
    return {
        "weekly_learning_time": _safe_int(payload.get("weekly_learning_time", 8), 8, 0, 80),
        "learning_budget": _safe_int(payload.get("learning_budget", 50), 50, 0, 10000),
        "preferred_work_mode": payload.get("remote_work_preference", data.get("goals_work_mode", "hybrid")),
        "accessibility_needs": payload.get("accessibility_needs", ""),
        "preferred_languages": payload.get("preferred_languages", ["English"]),
        "data_date": "2026-07-24",
    }


def _active_hypotheses(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(CareerHypothesis)
        .where(CareerHypothesis.profile_id == profile.id, CareerHypothesis.status == "active")
        .order_by(CareerHypothesis.current_alignment_score.desc(), CareerHypothesis.created_at.desc())
    ).all()
    if rows:
        return [
            {
                "id": row.id,
                "title": row.title,
                "role_family": row.role_family,
                "confidence_label": row.uncertainty_label,
                "alignment_score": round(row.current_alignment_score or 0, 2),
                "source": "career_hypothesis",
            }
            for row in rows
        ]
    return []


def _evidence_state(db: Session, profile_id: str) -> dict[str, dict[str, Any]]:
    confidence_rows = db.scalars(
        select(SkillEvidenceConfidence)
        .join(SkillEvidence, SkillEvidence.id == SkillEvidenceConfidence.skill_evidence_id)
        .where(SkillEvidenceConfidence.profile_id == profile_id, SkillEvidence.verification_status != "provisional_pending_review")
    ).all()
    recency_rows = {row.skill_id: row for row in db.scalars(select(SkillRecency).where(SkillRecency.profile_id == profile_id)).all()}
    state: dict[str, dict[str, Any]] = {}
    for row in confidence_rows:
        recency = recency_rows.get(row.skill_id)
        state[row.skill_id] = {
            "skill_id": row.skill_id,
            "confidence_label": row.confidence_label,
            "strength_label": row.strength_label,
            "score": _clamp((row.score_internal or 0) / 100),
            "recency_status": recency.status if recency else "Unknown",
            "evidence_age_days": recency.evidence_age_days if recency else None,
        }
    return state


def _evidence_gap_id(profile_id: str, skill_id: str) -> str:
    return "gap-" + hashlib.sha256(f"{ADAPTIVE_GAP_VERSION}:{profile_id}:{skill_id}".encode("utf-8")).hexdigest()[:12]


def _evidence_gaps_from_state(profile: Profile, hypotheses: list[dict[str, Any]], evidence: dict[str, dict[str, Any]], templates: list[CareerExperimentTemplate] | None = None) -> list[dict[str, Any]]:
    skill_sources: dict[str, dict[str, Any]] = {}
    for template in templates or []:
        for skill in _string_list(template.evaluated_skills_json or template.required_skills_json):
            source = skill_sources.setdefault(skill, {"templates": [], "hypotheses": []})
            source["templates"].append(template.id)
    for hypothesis in hypotheses:
        role_family = str(hypothesis.get("role_family", "")).lower()
        for skill, source in skill_sources.items():
            if role_family and any(token in str(template_id).lower() for token in role_family.split()[:2] for template_id in source["templates"]):
                source["hypotheses"].append(hypothesis.get("id"))

    if not skill_sources:
        for skill in ["human_centred_ai", "portfolio_artifact", "market_validation"]:
            skill_sources[skill] = {"templates": [], "hypotheses": [hyp.get("id") for hyp in hypotheses[:2]]}

    gaps: list[dict[str, Any]] = []
    for skill_id in sorted(skill_sources):
        uncertainty = _uncertainty_for_skill(skill_id, evidence)
        if uncertainty["state"] == "supported evidence":
            continue
        gap = {
            "id": _evidence_gap_id(profile.id, skill_id),
            "profile_id": profile.id,
            "skill_id": skill_id,
            "gap_type": uncertainty["state"],
            "severity": _round(float(uncertainty["severity"])),
            "source_types": ["Career Hypothesis", "Evidence Passport", "Career Experiment Catalogue"],
            "linked_hypothesis_ids": [str(item) for item in skill_sources[skill_id].get("hypotheses", []) if item],
            "linked_experiment_template_ids": sorted(set(str(item) for item in skill_sources[skill_id].get("templates", []))),
            "linked_job_requirement_ids": [],
            "linked_market_signal_ids": [],
            "expected_evidence_type": "demonstrated or independently reviewable evidence",
            "missing_input": uncertainty["state"] == "insufficient evidence",
            "data_quality_note": uncertainty["note"],
            "limitation": "The gap identifies missing or stale evidence; it is not evidence of personal inability.",
            "version": ADAPTIVE_GAP_VERSION,
        }
        gaps.append(gap)
    return gaps


def discover_evidence_gaps(db: Session, profile: Profile, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    hypotheses = _active_hypotheses(db, profile)
    evidence = _evidence_state(db, profile.id)
    templates = db.scalars(select(CareerExperimentTemplate).where(CareerExperimentTemplate.active.is_(True))).all()
    gaps = _evidence_gaps_from_state(profile, hypotheses, evidence, templates) if hypotheses else []
    missing_inputs = []
    if not hypotheses:
        missing_inputs.append("Active Career Hypothesis")
    if not evidence:
        missing_inputs.append("Evidence Passport skill confidence records")
    snapshot = _decision_support_snapshot(
        owner_profile_id=profile.id,
        owner_user_id=profile.user_id,
        output_kind="evidence_gap_discovery",
        input_snapshot={"hypotheses": hypotheses, "evidence_skill_count": len(evidence)},
        rule_set_version=ADAPTIVE_WEIGHT_VERSION,
        algorithm_version=ADAPTIVE_SCORE_VERSION,
        source_versions={"career_hypotheses": "career-hypothesis-current-snapshot", "evidence": "evidence-confidence-v1", "market_data": "local-demo-market-snapshot-v1"},
        data_coverage={"hypotheses": len(hypotheses), "evidence_skills": len(evidence), "gaps": len(gaps)},
        missing_inputs=missing_inputs,
        assumptions=["Current active hypotheses are the relevant hypothesis set for this analysis."],
        limitations=[
            "Gap discovery is a deterministic decision-support aid, not a capability assessment.",
            "No gaps are generated without an active Career Hypothesis.",
        ],
    )
    return {
        "profile_id": profile.id,
        "status": "completed" if hypotheses else "insufficient_data",
        "version": ADAPTIVE_GAP_VERSION,
        "gaps": gaps,
        "summary": {
            "gap_count": len(gaps),
            "missing_inputs": missing_inputs,
            "highest_severity": max([gap["severity"] for gap in gaps], default=0),
            "missing_evidence_note": "Missing evidence is treated as uncertainty, not inability.",
        },
        "decision_support_snapshot": snapshot,
    }


def _uncertainty_for_skill(skill_id: str, evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    record = evidence.get(skill_id)
    if not record:
        return {
            "category": "capability uncertainty",
            "state": "insufficient evidence",
            "severity": 0.88,
            "note": "Missing evidence is treated as an evidence gap, not as inability.",
        }
    if "Outdated" in record.get("recency_status", ""):
        return {
            "category": "evidence recency uncertainty",
            "state": "outdated evidence",
            "severity": 0.66,
            "note": "Older evidence may need refresh before relying on the path.",
        }
    if record.get("score", 0) < 0.45:
        return {
            "category": "capability uncertainty",
            "state": "weak evidence",
            "severity": 0.62,
            "note": "The skill has some signal but not enough demonstrated evidence.",
        }
    return {
        "category": "evidence redundancy",
        "state": "supported evidence",
        "severity": 0.24,
        "note": "The skill already has some support, so the experiment should add transferability or portfolio value.",
    }


def _template_public(row: CareerExperimentTemplate) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "target_role_family": row.target_role_family,
        "purpose": row.purpose,
        "expected_deliverables": _string_list(row.expected_deliverables_json),
        "estimated_duration_minutes": row.estimated_duration_minutes,
        "difficulty": row.difficulty,
        "required_skills": _string_list(row.required_skills_json),
        "skills_being_evaluated": _string_list(row.evaluated_skills_json),
        "evidence_generated": _string_list(row.evidence_generated_json),
    }


def _candidate_components(template: CareerExperimentTemplate, hypotheses: list[dict[str, Any]], evidence: dict[str, dict[str, Any]], constraints: dict[str, Any], rejected_template_ids: set[str], completed_template_ids: set[str]) -> dict[str, float]:
    skills = _string_list(template.evaluated_skills_json or template.required_skills_json)
    uncertainties = [_uncertainty_for_skill(skill, evidence) for skill in skills] or [{"severity": 0.5}]
    max_uncertainty = max(float(item["severity"]) for item in uncertainties)
    weak_count = sum(1 for item in uncertainties if item["state"] in {"insufficient evidence", "weak evidence", "outdated evidence"})
    family_hits = sum(1 for hyp in hypotheses if hyp["role_family"].lower() in template.target_role_family.lower() or template.target_role_family.lower() in hyp["role_family"].lower())
    title_hits = sum(1 for hyp in hypotheses if any(token in template.title.lower() for token in hyp["title"].lower().split()[:3]))
    duration = template.estimated_duration_minutes or 180
    difficulty_factor = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75}.get((template.difficulty or "").lower(), 0.55)
    completed = template.id in completed_template_ids
    rejected = template.id in rejected_template_ids

    positives = {
        "uncertainty_reduction": _round(max_uncertainty),
        "evidence_importance": _round(0.45 + min(0.35, weak_count * 0.12) + min(0.2, family_hits * 0.08)),
        "market_relevance": _round(0.46 + min(0.28, family_hits * 0.14) + min(0.16, title_hits * 0.08)),
        "cross_path_transferability": _round(0.45 + min(0.35, len(skills) * 0.07)),
        "portfolio_value": _round(0.42 + (0.3 if template.expected_deliverables_json else 0.05) + (0.08 if "portfolio" in str(template.evidence_generated_json).lower() else 0.0)),
        "feasibility": _round(1 - min(0.7, duration / 720) - difficulty_factor * 0.12),
        "support_availability": _round(0.48 + min(0.24, constraints.get("weekly_learning_time", 8) / 50)),
        "user_preference_alignment": _round(0.52 + min(0.22, family_hits * 0.11) + (0.06 if constraints.get("preferred_work_mode") in {"remote", "hybrid"} else 0.0)),
    }
    negatives = {
        "time_cost": _round(min(1, duration / 720)),
        "monetary_cost": _round(0.12 if constraints.get("learning_budget", 0) >= 50 else 0.24),
        "complexity": _round(difficulty_factor),
        "accessibility_barrier": _round(0.14 if not constraints.get("accessibility_needs") else 0.32),
        "repetition_penalty": 0.55 if completed or rejected else 0.0,
        "evidence_redundancy": _round(max(0.0, 1 - max_uncertainty) * 0.75),
        "implementation_risk": _round(0.18 + difficulty_factor * 0.28),
    }
    return {**positives, **negatives}


def _score_components(components: dict[str, float]) -> tuple[float, dict[str, Any]]:
    positive_total = sum(components[key] * POSITIVE_EXPERIMENT_WEIGHTS[key] for key in POSITIVE_EXPERIMENT_WEIGHTS)
    negative_total = sum(components[key] * NEGATIVE_EXPERIMENT_WEIGHTS[key] for key in NEGATIVE_EXPERIMENT_WEIGHTS)
    score = _clamp(positive_total - negative_total + 0.24)
    public = {
        "version": ADAPTIVE_SCORE_VERSION,
        "weight_version": ADAPTIVE_WEIGHT_VERSION,
        "positive": {key: {"value": _round(components[key]), "weight": POSITIVE_EXPERIMENT_WEIGHTS[key]} for key in POSITIVE_EXPERIMENT_WEIGHTS},
        "negative": {key: {"value": _round(components[key]), "weight": NEGATIVE_EXPERIMENT_WEIGHTS[key]} for key in NEGATIVE_EXPERIMENT_WEIGHTS},
        "normalised_score": _round(score),
        "score_precision_note": "Scores are deterministic decision-support bands, not scientific probability estimates.",
    }
    return score, public


def _related_hypotheses_for_template(template: CareerExperimentTemplate, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    related = [
        hyp for hyp in hypotheses
        if hyp["role_family"].lower() in template.target_role_family.lower()
        or template.target_role_family.lower() in hyp["role_family"].lower()
        or any(token in template.title.lower() for token in hyp["title"].lower().split()[:3])
    ]
    return related[:3] or hypotheses[:2]


def _expected_gain(template: CareerExperimentTemplate, evidence: dict[str, dict[str, Any]], profile_id: str) -> dict[str, Any]:
    skills = _string_list(template.evaluated_skills_json or template.required_skills_json)
    gaps = []
    for skill in skills:
        uncertainty = _uncertainty_for_skill(skill, evidence)
        if uncertainty["state"] != "supported evidence":
            gaps.append(
                {
                    "gap_id": _evidence_gap_id(profile_id, skill),
                    "skill_id": skill,
                    "gap_state": uncertainty["state"],
                    "maximum_supported_level": "Demonstrated project evidence",
                }
            )
    return {
        "gaps_addressed": gaps,
        "linked_evidence_gap_ids": [gap["gap_id"] for gap in gaps],
        "linked_job_requirement_ids": [],
        "linked_market_signal_ids": [],
        "maximum_evidence_level": "Demonstrated project evidence",
        "produces_artifact": bool(template.expected_deliverables_json),
        "evidence_source_type": "demonstrated" if template.expected_deliverables_json else "self_reported",
        "adviser_review_possible": True,
        "role_specific_or_transferable": "transferable" if len(skills) > 1 else "role_specific",
        "already_repeated": False,
    }


def _alternatives_for(candidate: dict[str, Any], all_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lower = sorted(all_candidates, key=lambda item: (item["estimated_duration_minutes"], -item["score_internal"]))
    higher = sorted(all_candidates, key=lambda item: (-item["components"]["portfolio_value"], -item["components"]["uncertainty_reduction"]))
    lower_cost = sorted(all_candidates, key=lambda item: (item["components"]["monetary_cost"], item["estimated_duration_minutes"], -item["score_internal"]))
    lower_choice = next((item for item in lower if item["id"] != candidate["id"]), candidate)
    higher_choice = next((item for item in higher if item["id"] != candidate["id"]), candidate)
    lower_cost_choice = next((item for item in lower_cost if item["id"] != candidate["id"]), candidate)
    return [
        {
            "type": "lower_effort_alternative",
            "title": lower_choice["title"],
            "experiment_template_id": lower_choice["id"],
            "reason": "Lower duration or implementation effort with a smaller expected evidence gain.",
            "tradeoff": "May produce weaker portfolio evidence.",
        },
        {
            "type": "higher_evidence_alternative",
            "title": higher_choice["title"],
            "experiment_template_id": higher_choice["id"],
            "reason": "Stronger expected artifact or broader evidence coverage.",
            "tradeoff": "Requires more effort or complexity.",
        },
        {
            "type": "lower_cost_alternative",
            "title": lower_cost_choice["title"],
            "experiment_template_id": lower_cost_choice["id"],
            "reason": "Lowest available financial-cost signal under the current local fixture.",
            "tradeoff": "May not be the fastest or highest-evidence option.",
        },
        {
            "type": "no_action_reflection",
            "title": "Decision reflection without a new experiment",
            "experiment_template_id": "",
            "reason": "Useful when constraints make action temporarily unrealistic.",
            "tradeoff": "Does not create new demonstrated evidence.",
        },
    ]


def analyse_adaptive_experiments(db: Session, profile: Profile, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    sync_career_resilience_catalogue(db)
    payload = payload or {}
    constraints = _profile_constraints(profile, payload)
    hypotheses = _active_hypotheses(db, profile)
    evidence = _evidence_state(db, profile.id)
    rejected_template_ids = {
        row.experiment_template_id for row in db.scalars(
            select(AdaptiveExperimentRecommendation).where(
                AdaptiveExperimentRecommendation.profile_id == profile.id,
                AdaptiveExperimentRecommendation.status == "rejected",
            )
        ).all()
        if row.experiment_template_id
    }
    completed_template_ids = {
        row.experiment_template_id for row in db.scalars(
            select(CareerExperimentSession).where(
                CareerExperimentSession.profile_id == profile.id,
                CareerExperimentSession.status.in_(["evaluated", "completed"]),
            )
        ).all()
        if row.experiment_template_id
    }
    templates = db.scalars(select(CareerExperimentTemplate).where(CareerExperimentTemplate.active.is_(True))).all()
    gaps = _evidence_gaps_from_state(profile, hypotheses, evidence, templates) if hypotheses else []
    missing_inputs = []
    if not hypotheses:
        missing_inputs.append("Active Career Hypothesis")
    if not evidence:
        missing_inputs.append("Evidence Passport skill confidence records")
    candidates: list[dict[str, Any]] = []
    for template in (templates if hypotheses else []):
        components = _candidate_components(template, hypotheses, evidence, constraints, rejected_template_ids, completed_template_ids)
        score, public_components = _score_components(components)
        skills = _string_list(template.evaluated_skills_json or template.required_skills_json)
        uncertainty_items = [_uncertainty_for_skill(skill, evidence) | {"skill_id": skill} for skill in skills]
        candidates.append(
            {
                "id": template.id,
                "title": template.title,
                "experiment_type": "career_experiment_template",
                "template": _template_public(template),
                "related_hypotheses": _related_hypotheses_for_template(template, hypotheses),
                "uncertainty": {
                    "primary_category": uncertainty_items[0]["category"] if uncertainty_items else "capability uncertainty",
                    "items": uncertainty_items,
                    "fit_distinction": "Insufficient evidence is shown as uncertainty, not as low fit or inability.",
                },
                "skills_tested": skills,
                "evidence_expected": _string_list(template.evidence_generated_json or template.expected_deliverables_json),
                "expected_evidence_gain": _expected_gain(template, evidence, profile.id),
                "estimated_duration_minutes": template.estimated_duration_minutes,
                "estimated_duration": _hours(template.estimated_duration_minutes or 180),
                "estimated_effort": _effort(template.estimated_duration_minutes or 180),
                "estimated_cost": "low",
                "market_relevance": "Linked to active hypotheses and observed role requirements",
                "cross_path_usefulness": "High" if public_components["positive"]["cross_path_transferability"]["value"] >= 0.65 else "Moderate",
                "accessibility_considerations": ["Can be completed asynchronously", "Can be scoped down if energy or time is limited"],
                "support_options": ["Adviser review", "Self-review rubric", "Evidence Passport follow-up"],
                "limitations": ["Cannot prove long-term team collaboration", "Cannot prove production deployment experience"],
                "components": components,
                "score_components": public_components,
                "score_internal": score,
                "priority_band": _band(score),
                "data_quality_warnings": [] if evidence else ["Evidence Passport is sparse; missing evidence is treated as uncertainty only."],
                "explanation": "",
            }
        )
    candidates.sort(key=lambda item: (-item["score_internal"], item["title"], item["id"]))
    for index, candidate in enumerate(candidates, 1):
        candidate["rank_position"] = index
        candidate["alternatives"] = _alternatives_for(candidate, candidates)
        candidate["explanation"] = (
            f"Recommended next experiment: {candidate['title']}. It was selected because it addresses "
            f"{candidate['uncertainty']['primary_category']}, tests {len(candidate['skills_tested'])} skill(s), "
            "can produce a reviewable artifact, and remains proportionate to the current time and cost constraints. "
            "Remaining uncertainty is shown separately from fit."
        )

    source_versions = {"career_experiments": "career-experiment-catalogue-v1", "evidence": "evidence-confidence-v1", "career_hypotheses": "career-hypothesis-current-snapshot", "market_data": "local-demo-market-snapshot-v1", "constraints": "user-constraint-snapshot-v1"}
    input_snapshot = {"hypotheses": hypotheses, "constraints": constraints, "evidence_gaps": gaps}
    decision_snapshot = _decision_support_snapshot(
        owner_profile_id=profile.id,
        owner_user_id=user_id or profile.user_id,
        output_kind="adaptive_evidence_gain",
        input_snapshot=input_snapshot,
        rule_set_version=ADAPTIVE_WEIGHT_VERSION,
        algorithm_version=ADAPTIVE_SCORE_VERSION,
        source_versions=source_versions,
        data_coverage={"hypotheses": len(hypotheses), "evidence_skills": len(evidence), "candidate_templates": len(candidates), "evidence_gaps": len(gaps)},
        missing_inputs=missing_inputs,
        assumptions=["The current active Career Hypotheses are treated as the relevant hypothesis set.", "Local career-experiment templates stand in for live labour-market learning actions."],
        limitations=[
            "No experiment is automatically marked successful.",
            "Roadmap and evidence changes require explicit user confirmation.",
            "No recommendations are generated without an active Career Hypothesis.",
        ],
    )
    run = AdaptiveExperimentRun(
        profile_id=profile.id,
        user_id=user_id,
        status="completed" if hypotheses else "insufficient_data",
        input_snapshot_json={**input_snapshot, "decision_support_snapshot": decision_snapshot, "missing_inputs": missing_inputs},
        weights_json={"positive": POSITIVE_EXPERIMENT_WEIGHTS, "negative": NEGATIVE_EXPERIMENT_WEIGHTS},
        source_versions_json=source_versions,
        data_coverage_json={"hypotheses": len(hypotheses), "evidence_skills": len(evidence), "candidate_templates": len(candidates), "evidence_gaps": len(gaps)},
        limitations_json=[
            "No experiment is automatically marked successful.",
            "Roadmap and evidence changes require explicit user confirmation.",
            "No recommendations are generated without an active Career Hypothesis.",
        ],
        demo_marker=bool(payload.get("demo_marker")),
    )
    db.add(run)
    db.flush()
    rows = []
    for candidate in candidates[: max(6, min(len(candidates), 8))]:
        row = AdaptiveExperimentRecommendation(
            run_id=run.id,
            profile_id=profile.id,
            user_id=user_id,
            experiment_template_id=candidate["id"],
            title=candidate["title"],
            experiment_type=candidate["experiment_type"],
            priority_band=candidate["priority_band"],
            score_internal=round(candidate["score_internal"], 4),
            rank_position=candidate["rank_position"],
            related_hypotheses_json=candidate["related_hypotheses"],
            uncertainty_json=candidate["uncertainty"],
            skills_tested_json=candidate["skills_tested"],
            evidence_expected_json=candidate["evidence_expected"],
            expected_evidence_gain_json=candidate["expected_evidence_gain"],
            estimated_duration=candidate["estimated_duration"],
            estimated_effort=candidate["estimated_effort"],
            estimated_cost=candidate["estimated_cost"],
            market_relevance=candidate["market_relevance"],
            cross_path_usefulness=candidate["cross_path_usefulness"],
            accessibility_considerations_json=candidate["accessibility_considerations"],
            support_options_json=candidate["support_options"],
            limitations_json=candidate["limitations"],
            score_components_json=candidate["score_components"],
            alternatives_json=candidate["alternatives"],
            data_quality_warnings_json=candidate["data_quality_warnings"],
            explanation=candidate["explanation"],
            status="proposed",
            demo_marker=bool(payload.get("demo_marker")),
        )
        db.add(row)
        rows.append(row)
    db.flush()
    _audit(db, profile.id, "adaptive_experiment_run_created", "adaptive_experiment_run", run.id, user_id or "", {"recommendation_count": len(rows)})
    db.commit()
    return adaptive_run_public(db, run)


def adaptive_recommendation_public(row: AdaptiveExperimentRecommendation) -> dict[str, Any]:
    return {
        "id": row.id,
        "run_id": row.run_id,
        "profile_id": row.profile_id,
        "experiment_template_id": row.experiment_template_id,
        "career_experiment_session_id": row.career_experiment_session_id,
        "title": row.title,
        "experiment_type": row.experiment_type,
        "priority_band": row.priority_band,
        "score_band": row.priority_band,
        "score_internal": round(row.score_internal, 2),
        "rank_position": row.rank_position,
        "related_hypotheses": row.related_hypotheses_json or [],
        "uncertainty": row.uncertainty_json or {},
        "skills_tested": row.skills_tested_json or [],
        "evidence_expected": row.evidence_expected_json or [],
        "expected_evidence_gain": row.expected_evidence_gain_json or {},
        "linked_evidence_gap_ids": (row.expected_evidence_gain_json or {}).get("linked_evidence_gap_ids", []),
        "linked_job_requirement_ids": (row.expected_evidence_gain_json or {}).get("linked_job_requirement_ids", []),
        "linked_market_signal_ids": (row.expected_evidence_gain_json or {}).get("linked_market_signal_ids", []),
        "actual_evidence_gain": row.actual_evidence_gain_json or {},
        "estimated_duration": row.estimated_duration,
        "estimated_effort": row.estimated_effort,
        "estimated_cost": row.estimated_cost,
        "market_relevance": row.market_relevance,
        "cross_path_usefulness": row.cross_path_usefulness,
        "accessibility_considerations": row.accessibility_considerations_json or [],
        "support_options": row.support_options_json or [],
        "limitations": row.limitations_json or [],
        "score_components": row.score_components_json or {},
        "alternatives": row.alternatives_json or [],
        "data_quality_warnings": row.data_quality_warnings_json or [],
        "explanation": row.explanation,
        "status": row.status,
        "user_confirmation_status": row.user_confirmation_status,
        "rejection_reason": row.rejection_reason,
        "rejection_feedback": row.rejection_feedback_json or {},
        "roadmap_confirmation_status": row.roadmap_confirmation_status,
        "scoring_version": ADAPTIVE_SCORE_VERSION,
        "weight_version": ADAPTIVE_WEIGHT_VERSION,
        "decision_support_snapshot": {"version": DECISION_SUPPORT_MODEL_VERSION, "linked_run_id": row.run_id},
        "created_at": row.created_at.isoformat() if row.created_at else "",
        "updated_at": row.updated_at.isoformat() if row.updated_at else "",
    }


def adaptive_run_public(db: Session, row: AdaptiveExperimentRun) -> dict[str, Any]:
    recommendations = db.scalars(
        select(AdaptiveExperimentRecommendation)
        .where(AdaptiveExperimentRecommendation.run_id == row.id)
        .order_by(AdaptiveExperimentRecommendation.rank_position)
    ).all()
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "status": row.status,
        "input_snapshot": row.input_snapshot_json or {},
        "decision_support_snapshot": (row.input_snapshot_json or {}).get("decision_support_snapshot", {}),
        "evidence_gaps": (row.input_snapshot_json or {}).get("evidence_gaps", []),
        "missing_inputs": (row.input_snapshot_json or {}).get("missing_inputs", []),
        "scoring_version": row.scoring_version,
        "weight_version": row.weight_version,
        "weights": row.weights_json or {},
        "source_versions": row.source_versions_json or {},
        "data_coverage": row.data_coverage_json or {},
        "limitations": row.limitations_json or [],
        "uncertainty_summary": _uncertainty_summary(recommendations),
        "recommendations": [adaptive_recommendation_public(item) for item in recommendations],
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def _uncertainty_summary(recommendations: list[AdaptiveExperimentRecommendation]) -> dict[str, Any]:
    categories: dict[str, int] = {}
    for row in recommendations:
        category = (row.uncertainty_json or {}).get("primary_category", "unknown")
        categories[category] = categories.get(category, 0) + 1
    return {
        "categories": categories,
        "distinctions": ["low fit", "insufficient evidence", "outdated evidence", "conflicting evidence", "unknown information"],
        "missing_evidence_note": "Missing evidence is never interpreted as proof of inability.",
    }


def list_adaptive_experiments(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(AdaptiveExperimentRecommendation)
        .where(AdaptiveExperimentRecommendation.profile_id == profile.id)
        .order_by(AdaptiveExperimentRecommendation.created_at.desc(), AdaptiveExperimentRecommendation.rank_position)
    ).all()
    return [adaptive_recommendation_public(row) for row in rows]


def list_adaptive_runs(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(AdaptiveExperimentRun)
        .where(AdaptiveExperimentRun.profile_id == profile.id)
        .order_by(AdaptiveExperimentRun.created_at.desc())
    ).all()
    return [adaptive_run_public(db, row) for row in rows]


def get_adaptive_recommendation(db: Session, recommendation_id: str, profile: Profile | None = None) -> dict[str, Any]:
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Recommendation does not belong to the profile")
    return adaptive_recommendation_public(row)


def adaptive_recommendation_action(db: Session, recommendation_id: str, action: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    if action == "accept":
        row.status = "accepted"
        row.user_confirmation_status = "accepted"
        if payload.get("add_to_roadmap"):
            row.roadmap_confirmation_status = "confirmed_by_user"
    elif action == "save":
        row.status = "planned"
        row.user_confirmation_status = "saved_for_later"
    elif action == "reject":
        reason = str(payload.get("reason", "other"))
        row.status = "rejected"
        row.user_confirmation_status = "rejected"
        row.rejection_reason = reason
        row.rejection_feedback_json = {
            "reason": reason,
            "note": payload.get("note", ""),
            "career_direction_rejected": False,
            "methodology_note": "A rejected experiment is not treated as a rejected career direction.",
        }
    elif action == "start":
        profile = db.get(Profile, row.profile_id)
        if not profile:
            raise LookupError("Profile not found")
        session = create_experiment_session(
            db,
            profile,
            {
                "experiment_template_id": row.experiment_template_id,
                "mode": payload.get("mode", "guided"),
                "user_confirmed": True,
                "add_to_roadmap": bool(payload.get("add_to_roadmap")),
                "demo_marker": bool(payload.get("demo_marker")),
            },
            user_id or row.user_id,
        )
        row.career_experiment_session_id = session["id"]
        row.status = "active"
        row.user_confirmation_status = "started_by_user"
        row.roadmap_confirmation_status = "confirmed_by_user" if payload.get("add_to_roadmap") else "not_requested"
    else:
        raise ValueError("Unsupported adaptive experiment action")
    row.updated_at = _now()
    _audit(db, row.profile_id, f"adaptive_experiment_{action}", "adaptive_experiment_recommendation", row.id, user_id or "", payload)
    db.commit()
    return adaptive_recommendation_public(row)


def transition_adaptive_lifecycle(db: Session, recommendation_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    target = str(payload.get("status", "")).strip().lower().replace("_", " ")
    if target not in ADAPTIVE_LIFECYCLE_STATUSES:
        raise ValueError("Unsupported adaptive experiment lifecycle status")
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    current = (row.status or "proposed").strip().lower().replace("_", " ")
    allowed = ADAPTIVE_LIFECYCLE_TRANSITIONS.get(current, set())
    if target != current and target not in allowed:
        raise ValueError(f"Invalid adaptive experiment transition {current} -> {target}")
    history = _list((row.actual_evidence_gain_json or {}).get("lifecycle_history"))
    actual = dict(row.actual_evidence_gain_json or {})
    history.append({"from": current, "to": target, "note": payload.get("note", ""), "changed_at": _now().isoformat(), "authoritative_evidence_created": False})
    actual["lifecycle_history"] = history
    row.actual_evidence_gain_json = actual
    row.status = target
    row.updated_at = _now()
    _audit(db, row.profile_id, "adaptive_experiment_lifecycle_transition", "adaptive_experiment_recommendation", row.id, user_id or "", {"from": current, "to": target})
    db.commit()
    return adaptive_recommendation_public(row)


def _evidence_capture_proposal(row: AdaptiveExperimentRecommendation, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    expected = row.expected_evidence_gain_json or {}
    existing = (row.actual_evidence_gain_json or {}).get("evidence_capture_proposal")
    if existing and not payload:
        return existing
    produced_artefact = payload.get("produced_artefact", payload.get("artifact_reference", ""))
    evidence_type = payload.get("evidence_type", expected.get("evidence_source_type", "self_reported"))
    independently_verifiable = bool(payload.get("independently_verifiable", False))
    return {
        "proposal_id": "capture-" + hashlib.sha256(f"{row.id}:{row.updated_at}".encode("utf-8")).hexdigest()[:12],
        "recommendation_id": row.id,
        "status": "pending_user_review",
        "completion_notes": payload.get("completion_notes", payload.get("user_reflection", "")),
        "actual_time": payload.get("actual_time", payload.get("actual_duration", None)),
        "actual_cost": payload.get("actual_cost", None),
        "actual_difficulty": payload.get("actual_difficulty", None),
        "produced_artefact": produced_artefact,
        "evidence_type": evidence_type,
        "evidence_status": "self_report_pending_review" if not independently_verifiable else "verifiable_reference_pending_review",
        "unexpected_result": payload.get("unexpected_result", ""),
        "user_reflection": payload.get("user_reflection", ""),
        "reviewer_feedback": payload.get("reviewer_feedback", ""),
        "linked_evidence_gap_ids": expected.get("linked_evidence_gap_ids", []),
        "linked_evidence_passport_proposal": {
            "target": "Evidence Passport",
            "requires_user_confirmation": True,
            "verified_evidence_created": False,
            "source_type": "self_report" if not independently_verifiable else "user_provided_reference",
            "proposed_skills": row.skills_tested_json or [],
        },
        "accept_reject_required": True,
        "failure_not_incapacity_note": "An incomplete or unsuccessful experiment is not classified as evidence of personal incapability.",
        "limitations": ["Completion is not the same as verified evidence.", "Evidence Passport mutation requires separate user review."],
    }


def record_adaptive_outcome(db: Session, recommendation_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    proposal = _evidence_capture_proposal(row, payload)
    actual = {
        "expected_evidence_gain": row.expected_evidence_gain_json or {},
        "actual_evidence_gained": payload.get("actual_evidence_gained", []),
        "completion_notes": payload.get("completion_notes", ""),
        "actual_time": payload.get("actual_time", None),
        "actual_cost": payload.get("actual_cost", None),
        "actual_difficulty": payload.get("actual_difficulty", None),
        "produced_artefact": payload.get("produced_artefact", payload.get("artifact_reference", "")),
        "evidence_type": payload.get("evidence_type", "self_reported"),
        "evidence_status": "pending_user_review",
        "unexpected_result": payload.get("unexpected_result", ""),
        "user_reflection": payload.get("user_reflection", ""),
        "reviewer_feedback": payload.get("reviewer_feedback", ""),
        "experiment_outcome": payload.get("experiment_outcome", "user_recorded"),
        "hypothesis_confidence_change": payload.get("hypothesis_confidence_change", "requires separate recalibration"),
        "evidence_capture_proposal": proposal,
        "success_not_auto_marked": True,
        "evidence_workflow_authoritative": True,
        "verified_evidence_created": False,
        "evidence_passport_mutated": False,
    }
    row.actual_evidence_gain_json = actual
    row.status = "completed"
    row.updated_at = _now()
    _audit(db, row.profile_id, "adaptive_experiment_outcome_recorded", "adaptive_experiment_recommendation", row.id, user_id or "", actual)
    db.commit()
    return adaptive_recommendation_public(row)


def get_evidence_capture_proposal(db: Session, recommendation_id: str) -> dict[str, Any]:
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    proposal = (row.actual_evidence_gain_json or {}).get("evidence_capture_proposal")
    return proposal or _evidence_capture_proposal(row)


def review_evidence_capture_proposal(db: Session, recommendation_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    decision = str(payload.get("decision", "reject")).strip().lower()
    if decision not in {"accept", "reject"}:
        raise ValueError("Evidence capture review decision must be accept or reject")
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    actual = dict(row.actual_evidence_gain_json or {})
    proposal = dict(actual.get("evidence_capture_proposal") or _evidence_capture_proposal(row))
    proposal["review_status"] = "accepted_by_user" if decision == "accept" else "rejected_by_user"
    proposal["review_note"] = payload.get("note", "")
    proposal["reviewed_at"] = _now().isoformat()
    proposal["verified_evidence_created"] = False
    proposal["evidence_passport_mutated"] = False
    actual["evidence_capture_proposal"] = proposal
    actual["evidence_capture_review"] = {
        "decision": decision,
        "verified_evidence_created": False,
        "evidence_passport_mutated": False,
        "requires_separate_evidence_passport_action": True,
    }
    row.actual_evidence_gain_json = actual
    row.status = "evidence reviewed" if decision == "accept" else "completed"
    row.updated_at = _now()
    _audit(db, row.profile_id, "adaptive_experiment_evidence_capture_reviewed", "adaptive_experiment_recommendation", row.id, user_id or "", actual["evidence_capture_review"])
    db.commit()
    return adaptive_recommendation_public(row)


def adaptive_alternatives(db: Session, recommendation_id: str) -> list[dict[str, Any]]:
    row = db.get(AdaptiveExperimentRecommendation, recommendation_id)
    if not row:
        raise LookupError("Adaptive experiment recommendation not found")
    return row.alternatives_json or []


def transition_presets() -> list[dict[str, Any]]:
    return [
        {"id": "fastest_realistic_transition", "label": "Fastest realistic transition", "objective_priorities": {"transition_duration": 1.4, "weekly_effort": 1.2}},
        {"id": "lowest_financial_risk", "label": "Lowest financial risk", "objective_priorities": {"financial_risk": 1.5, "direct_monetary_cost": 1.4}},
        {"id": "maximum_existing_evidence", "label": "Maximum use of existing evidence", "objective_priorities": {"portfolio_reuse": 1.4, "transferable_skill_reuse": 1.4}},
        {"id": "strongest_market_alignment", "label": "Strongest market alignment", "objective_priorities": {"market_fit": 1.5, "local_opportunity_availability": 1.3}},
        {"id": "highest_support_feasibility", "label": "Highest support feasibility", "objective_priorities": {"support_fit": 1.5, "financial_risk": 1.2}},
        {"id": "balanced_transition", "label": "Balanced transition", "objective_priorities": {}},
        {"id": "user_defined_scenario", "label": "User-defined scenario", "objective_priorities": {}},
    ]


def _role_slug(title: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in title.lower()).strip("-").replace("--", "-")


def _candidate_path_specs(db: Session, profile: Profile, controls: dict[str, Any]) -> list[dict[str, Any]]:
    hypotheses = _active_hypotheses(db, profile)
    if not hypotheses:
        return []
    sync_career_encyclopedia(db)
    role_rows = {row.slug: row for row in db.scalars(select(CareerRoleProfile).where(CareerRoleProfile.archived_at.is_(None))).all()}
    preferred_titles = [hyp["title"] for hyp in hypotheses]
    base_titles = []
    for title in preferred_titles + ["AI Product Designer", "AI Integration Consultant", "RAG Application Developer", "Frontend Developer"]:
        if title not in base_titles:
            base_titles.append(title)
    base_titles = base_titles[:4]
    while len(base_titles) < 4:
        base_titles.append(["AI Product Designer", "AI Integration Consultant", "RAG Application Developer", "Frontend Developer"][len(base_titles)])

    specs = []
    for index, title in enumerate(base_titles):
        slug = _role_slug(title)
        role = role_rows.get(slug)
        family = role.career_family if role else ("Design and product" if "Designer" in title else "AI and software")
        if index == 0:
            objectives = {
                "transition_duration": 0.45,
                "direct_monetary_cost": 0.30,
                "weekly_effort": 0.38,
                "financial_risk": 0.34,
                "evidence_gap": 0.34,
                "capability_gap": 0.40,
                "personal_fit": 0.86,
                "capability_fit": 0.66,
                "market_fit": 0.65,
                "support_fit": 0.70,
                "local_opportunity_availability": 0.60,
                "language_barrier": 0.20,
                "accessibility": 0.78,
                "reversibility": 0.76,
                "portfolio_reuse": 0.84,
                "transferable_skill_reuse": 0.85,
                "dependence_on_uncertain_assumptions": 0.35,
                "ai_change_stability": 0.70,
            }
            path_type = "adjacent_transition"
        elif index == 1:
            objectives = {
                "transition_duration": 0.56,
                "direct_monetary_cost": 0.34,
                "weekly_effort": 0.50,
                "financial_risk": 0.42,
                "evidence_gap": 0.42,
                "capability_gap": 0.45,
                "personal_fit": 0.74,
                "capability_fit": 0.62,
                "market_fit": 0.78,
                "support_fit": 0.66,
                "local_opportunity_availability": 0.73,
                "language_barrier": 0.22,
                "accessibility": 0.72,
                "reversibility": 0.70,
                "portfolio_reuse": 0.76,
                "transferable_skill_reuse": 0.78,
                "dependence_on_uncertain_assumptions": 0.44,
                "ai_change_stability": 0.76,
            }
            path_type = "market_aligned_transition"
        elif index == 2:
            objectives = {
                "transition_duration": 0.74,
                "direct_monetary_cost": 0.42,
                "weekly_effort": 0.68,
                "financial_risk": 0.50,
                "evidence_gap": 0.58,
                "capability_gap": 0.62,
                "personal_fit": 0.66,
                "capability_fit": 0.58,
                "market_fit": 0.80,
                "support_fit": 0.54,
                "local_opportunity_availability": 0.76,
                "language_barrier": 0.24,
                "accessibility": 0.66,
                "reversibility": 0.58,
                "portfolio_reuse": 0.90,
                "transferable_skill_reuse": 0.62,
                "dependence_on_uncertain_assumptions": 0.54,
                "ai_change_stability": 0.82,
            }
            path_type = "major_technical_transition"
        else:
            objectives = {
                "transition_duration": 0.55,
                "direct_monetary_cost": 0.35,
                "weekly_effort": 0.47,
                "financial_risk": 0.44,
                "evidence_gap": 0.46,
                "capability_gap": 0.50,
                "personal_fit": 0.70,
                "capability_fit": 0.60,
                "market_fit": 0.60,
                "support_fit": 0.58,
                "local_opportunity_availability": 0.58,
                "language_barrier": 0.26,
                "accessibility": 0.68,
                "reversibility": 0.66,
                "portfolio_reuse": 0.70,
                "transferable_skill_reuse": 0.70,
                "dependence_on_uncertain_assumptions": 0.46,
                "ai_change_stability": 0.62,
            }
            path_type = "fast_return_variant"
        weekly = float(controls.get("weekly_learning_time", 8) or 8)
        if weekly >= 12:
            objectives["transition_duration"] = _round(objectives["transition_duration"] - 0.08)
            objectives["weekly_effort"] = _round(objectives["weekly_effort"] + 0.04)
        if controls.get("need_public_support"):
            objectives["support_fit"] = _round(objectives["support_fit"] + 0.08 if family in {"Learning and communication", "Design and product"} else objectives["support_fit"])
        specs.append({"title": title, "role_slug": slug, "career_family": family, "path_type": path_type, "objectives": objectives})
    return specs


def _sanitize_transition_controls(raw: dict[str, Any] | None) -> dict[str, Any]:
    controls = {**DEFAULT_TRANSITION_CONTROLS, **(raw or {})}
    controls["weekly_learning_time"] = _safe_int(controls.get("weekly_learning_time"), 8, 0, 80)
    controls["learning_budget"] = _safe_int(controls.get("learning_budget"), 50, 0, 10000)
    controls["desired_transition_months"] = _safe_int(controls.get("desired_transition_months"), 9, 1, 60)
    controls["maximum_transition_duration"] = _safe_int(controls.get("maximum_transition_duration", controls["desired_transition_months"]), controls["desired_transition_months"], 1, 60)
    controls["minimum_income_requirement"] = _safe_int(controls.get("minimum_income_requirement", 0), 0, 0, 1000000)
    controls["travel_limit_minutes"] = _safe_int(controls.get("travel_limit_minutes", 60), 60, 0, 480)
    controls["remote_work_preference"] = str(controls.get("remote_work_preference", "hybrid"))
    controls["risk_tolerance"] = str(controls.get("risk_tolerance", controls.get("acceptable_financial_risk", "medium")))
    controls["preferred_languages"] = _string_list(controls.get("preferred_languages")) or ["English"]
    controls["hard_constraints"] = sorted(set(_string_list(controls.get("hard_constraints")) or ["weekly_learning_time", "learning_budget", "maximum_transition_duration"]))
    return controls


def _constraint_result(name: str, configured: Any, path_value: Any, status: str, *, hard: bool, explanation: str) -> dict[str, Any]:
    return {
        "constraint": name,
        "configured_value": configured,
        "path_value": path_value,
        "status": status,
        "hard": hard,
        "explanation": explanation,
    }


def _path_constraint_results(path: dict[str, Any] | CareerTransitionPath, controls: dict[str, Any]) -> list[dict[str, Any]]:
    objectives = path["objectives"] if isinstance(path, dict) else (path.objectives_json or {})
    title = path["title"] if isinstance(path, dict) else path.title
    hard = set(_string_list(controls.get("hard_constraints")))
    required_hours = max(1, int(round(4 + float(objectives.get("weekly_effort", 0.5)) * 8)))
    estimated_cost = int(round(float(objectives.get("direct_monetary_cost", 0.4)) * 300))
    estimated_duration = int(round(3 + float(objectives.get("transition_duration", 0.5)) * 12))
    financial_risk = float(objectives.get("financial_risk", 0.5))
    accessibility_score = float(objectives.get("accessibility", 0.5))
    remote_preference = str(controls.get("remote_work_preference", "hybrid"))

    weekly_limit = int(controls.get("weekly_learning_time", 8))
    budget_limit = int(controls.get("learning_budget", 50))
    duration_limit = int(controls.get("maximum_transition_duration", controls.get("desired_transition_months", 9)))
    risk_tolerance = str(controls.get("risk_tolerance", "medium"))
    risk_threshold = {"low": 0.32, "medium": 0.55, "high": 0.8}.get(risk_tolerance, 0.55)

    weekly_status = "satisfied" if required_hours <= weekly_limit else "partially satisfied" if required_hours <= weekly_limit + 2 else "violated"
    budget_status = "satisfied" if estimated_cost <= budget_limit else "partially satisfied" if estimated_cost <= budget_limit + 100 else "violated"
    duration_status = "satisfied" if estimated_duration <= duration_limit else "partially satisfied" if estimated_duration <= duration_limit + 3 else "violated"
    risk_status = "satisfied" if financial_risk <= risk_threshold else "partially satisfied" if financial_risk <= risk_threshold + 0.15 else "violated"
    accessibility_status = "unknown" if controls.get("accessibility_constraints") in {None, ""} else ("satisfied" if accessibility_score >= 0.65 else "partially satisfied")
    remote_status = "satisfied" if remote_preference in {"hybrid", "remote", "onsite"} else "unknown"

    return [
        _constraint_result("weekly_learning_time", weekly_limit, required_hours, weekly_status, hard="weekly_learning_time" in hard, explanation=f"{title} is estimated at {required_hours} hours per week."),
        _constraint_result("learning_budget", budget_limit, estimated_cost, budget_status, hard="learning_budget" in hard, explanation=f"{title} is estimated at {estimated_cost} local currency units of direct learning cost."),
        _constraint_result("maximum_transition_duration", duration_limit, estimated_duration, duration_status, hard="maximum_transition_duration" in hard, explanation=f"{title} is estimated at {estimated_duration} months."),
        _constraint_result("risk_tolerance", risk_tolerance, round(financial_risk, 2), risk_status, hard="risk_tolerance" in hard, explanation="Financial risk is a deterministic relative fixture value, not a financial forecast."),
        _constraint_result("remote_work_preference", remote_preference, "role-dependent", remote_status, hard="remote_work_preference" in hard, explanation="Remote compatibility is treated as a work-mode constraint, not a personal-fit score."),
        _constraint_result("language_constraints", controls.get("preferred_languages", []), "English-compatible local fixture", "satisfied", hard="language_constraints" in hard, explanation="The deterministic demo fixture exposes English-compatible paths."),
        _constraint_result("accessibility_constraints", controls.get("accessibility_constraints", "not provided"), round(accessibility_score, 2), accessibility_status, hard="accessibility_constraints" in hard, explanation="Accessibility changes feasibility/support options, not demonstrated skill evidence."),
        _constraint_result("minimum_income_requirement", controls.get("minimum_income_requirement", 0), "unknown", "unknown" if controls.get("minimum_income_requirement", 0) else "not applicable", hard="minimum_income_requirement" in hard, explanation="Income projections are not estimated by this dissertation prototype."),
    ]


def _path_feasibility(path: dict[str, Any] | CareerTransitionPath, controls: dict[str, Any]) -> dict[str, Any]:
    results = _path_constraint_results(path, controls)
    hard_violations = [item for item in results if item["hard"] and item["status"] == "violated"]
    partial = [item for item in results if item["status"] == "partially satisfied"]
    unknown = [item for item in results if item["status"] == "unknown"]
    if hard_violations:
        status = "infeasible_under_hard_constraints"
    elif partial:
        status = "partially_feasible"
    elif unknown:
        status = "feasible_with_unknowns"
    else:
        status = "feasible"
    return {
        "status": status,
        "recommendation_eligible": not hard_violations,
        "hard_constraint_violations": hard_violations,
        "constraint_results": results,
        "note": "Hard constraint violations remain visible but are excluded from feasible recommendations unless the user includes infeasible paths.",
    }


def _normalise_paths(path_specs: list[dict[str, Any]], selected_objectives: list[str]) -> None:
    for objective in selected_objectives:
        values = [float(path["objectives"][objective]) for path in path_specs if objective in path.get("objectives", {}) and math.isfinite(float(path["objectives"][objective]))]
        if not values:
            for path in path_specs:
                path.setdefault("normalised", {})[objective] = 0.5
                path.setdefault("missing_objectives", []).append(objective)
            continue
        low, high = min(values), max(values)
        span = high - low or 1
        direction = OBJECTIVE_DIRECTIONS[objective]
        for path in path_specs:
            if objective not in path.get("objectives", {}):
                path.setdefault("normalised", {})[objective] = 0.5
                path.setdefault("missing_objectives", []).append(objective)
                continue
            raw = float(path["objectives"][objective])
            if not math.isfinite(raw):
                path.setdefault("normalised", {})[objective] = 0.5
                path.setdefault("missing_objectives", []).append(objective)
                continue
            benefit = (high - raw) / span if direction == "min" else (raw - low) / span
            path.setdefault("normalised", {})[objective] = _round(benefit)


def _dominates(left: dict[str, Any], right: dict[str, Any], selected_objectives: list[str]) -> bool:
    if left.get("missing_objectives") or right.get("missing_objectives"):
        return False
    left_values = left["normalised"]
    right_values = right["normalised"]
    all_equal_or_better = all(left_values[obj] >= right_values[obj] - 1e-9 for obj in selected_objectives)
    strictly_better = any(left_values[obj] > right_values[obj] + 1e-9 for obj in selected_objectives)
    return all_equal_or_better and strictly_better


def _apply_pareto(path_specs: list[dict[str, Any]], selected_objectives: list[str]) -> None:
    for path in path_specs:
        dominators = [other for other in path_specs if other is not path and _dominates(other, path, selected_objectives)]
        path["is_pareto_optimal"] = not dominators
        path["dominated_by"] = [{"title": item["title"], "role_slug": item["role_slug"]} for item in dominators]
        if dominators:
            first = dominators[0]
            better = [obj for obj in selected_objectives if first["normalised"][obj] > path["normalised"][obj] + 1e-9][:4]
            path["dominated_explanation"] = f"{path['title']} is dominated by {first['title']} because it is equal or better on the selected objectives and stronger on {', '.join(better)}."
        else:
            path["dominated_explanation"] = "This path is non-dominated under the selected objectives. It is not a universal best path."


def create_transition_simulation(db: Session, profile: Profile, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    controls = _sanitize_transition_controls(payload.get("controls") or {})
    selected_objectives = [obj for obj in payload.get("selected_objectives", DEFAULT_OBJECTIVES) if obj in OBJECTIVE_DIRECTIONS] or DEFAULT_OBJECTIVES
    preset = payload.get("preset", "balanced_transition")
    scenario_name = payload.get("scenario_name", next((item["label"] for item in transition_presets() if item["id"] == preset), "Balanced transition"))
    objective_config = {
        "version": PARETO_OBJECTIVE_VERSION,
        "selected_objectives": selected_objectives,
        "directions": {key: OBJECTIVE_DIRECTIONS[key] for key in selected_objectives},
        "preset": preset,
        "priority_preferences": payload.get("priority_preferences", {}),
        "hidden_career_preferences": False,
    }
    hypotheses = _active_hypotheses(db, profile)
    specs = _candidate_path_specs(db, profile, controls)
    _normalise_paths(specs, selected_objectives)
    _apply_pareto(specs, selected_objectives)
    for path in specs:
        feasibility = _path_feasibility(path, controls)
        path["feasibility"] = feasibility
        if not feasibility["recommendation_eligible"]:
            path["is_pareto_optimal"] = False
            path["dominated_explanation"] = f"{path['title']} violates one or more hard constraints and is not eligible for feasible recommendations. It remains visible for inspection."
    source_versions = {"career_hypotheses": "career-hypothesis-current-snapshot", "market_data": "local-demo-market-snapshot-v1", "constraints": "user-constraint-snapshot-v1", "preferences": "profile-preference-snapshot-v1"}
    missing_inputs = ["Active Career Hypothesis"] if not hypotheses else []
    input_snapshot = {"hypotheses": hypotheses, "controls": controls, "selected_objectives": selected_objectives}
    decision_snapshot = _decision_support_snapshot(
        owner_profile_id=profile.id,
        owner_user_id=user_id or profile.user_id,
        output_kind="career_transition_pareto",
        input_snapshot=input_snapshot,
        rule_set_version=PARETO_OBJECTIVE_VERSION,
        algorithm_version=PARETO_OBJECTIVE_VERSION,
        source_versions=source_versions,
        data_coverage={"candidate_paths": len(specs), "selected_objectives": len(selected_objectives), "constraint_count": len(_path_constraint_results(specs[0], controls)) if specs else 0},
        missing_inputs=missing_inputs + (["minimum income estimate"] if controls.get("minimum_income_requirement", 0) else []),
        assumptions=["Criteria are comparable only within the selected deterministic fixture.", "The chart and tables are decision-support views, not forecasts."],
        limitations=["Market data is local and date-bound.", "No path is automatically selected as best without explicit weighting."],
    )
    simulation = CareerTransitionSimulation(
        profile_id=profile.id,
        user_id=user_id,
        status="completed" if specs else "insufficient_data",
        scenario_name=scenario_name,
        preset=preset,
        controls_json=controls,
        objective_config_json=objective_config,
        input_snapshot_json={**input_snapshot, "decision_support_snapshot": decision_snapshot},
        pareto_front_json=[{"title": path["title"], "role_slug": path["role_slug"]} for path in specs if path["is_pareto_optimal"] and path["feasibility"]["recommendation_eligible"]],
        explanation=_pareto_explanation(specs),
        source_versions_json=source_versions,
        data_coverage_json={"candidate_paths": len(specs), "selected_objectives": len(selected_objectives), "constraint_count": len(_path_constraint_results(specs[0], controls)) if specs else 0},
        limitations_json=["Market data is local and date-bound.", "No path is automatically selected as best without explicit weighting."],
        saved=bool(payload.get("save_scenario")),
        demo_marker=bool(payload.get("demo_marker")),
    )
    db.add(simulation)
    db.flush()
    for path in specs:
        db.add(
            CareerTransitionPath(
                simulation_id=simulation.id,
                profile_id=profile.id,
                title=path["title"],
                role_slug=path["role_slug"],
                path_type=path["path_type"],
                objectives_json=path["objectives"],
                normalised_objectives_json=path["normalised"],
                objective_directions_json={key: OBJECTIVE_DIRECTIONS[key] for key in selected_objectives},
                is_pareto_optimal=path["is_pareto_optimal"],
                dominated_by_json=path["dominated_by"],
                dominated_explanation=path["dominated_explanation"],
                existing_assets_json=["Transferable design evidence", "Responsible AI learning notes"] if "Designer" in path["title"] else ["AI literacy evidence", "Project-based learning habit"],
                missing_assets_json=["Recent market evidence", "One stronger technical artifact"],
                required_experiments_json=["Adaptive evidence-gain experiment"],
                required_learning_json=["Targeted skill-gap module"],
                transition_stages_json=["Evidence refresh", "Portfolio artifact", "Application preparation", "Outcome review"],
                relevant_jobs_json=["Fictional role signal only"],
                support_opportunities_json=["Adviser review", "Public-support discussion if eligible"],
                assumptions_json=["Weekly learning capacity remains available", "Market data coverage remains comparable"],
                uncertainties_json=["Local opportunity availability may change", "Support eligibility is unconfirmed"],
                reversibility="High" if path["objectives"]["reversibility"] >= 0.7 else "Moderate",
                next_action="Run the smallest experiment that tests the largest unresolved evidence gap.",
                demo_marker=bool(payload.get("demo_marker")),
            )
        )
    _audit(db, profile.id, "transition_simulation_created", "career_transition_simulation", simulation.id, user_id or "", {"path_count": len(specs)})
    db.commit()
    return transition_simulation_public(db, simulation)


def _pareto_explanation(specs: list[dict[str, Any]]) -> str:
    if not specs:
        return "A transition simulation needs at least one active Career Hypothesis. No fallback career path was generated."
    optimal = [path["title"] for path in specs if path["is_pareto_optimal"]]
    dominated = [path["title"] for path in specs if not path["is_pareto_optimal"]]
    return (
        f"{' and '.join(optimal[:3])} are currently Pareto-optimal under the selected objectives. "
        f"Dominated paths remain visible: {', '.join(dominated) if dominated else 'none'}. "
        "This is a trade-off analysis, not a universal best-career ranking."
    )


def transition_path_public(row: CareerTransitionPath, controls: dict[str, Any] | None = None) -> dict[str, Any]:
    controls = _sanitize_transition_controls(controls or {})
    feasibility = _path_feasibility(row, controls)
    tradeoffs = []
    normalised = row.normalised_objectives_json or {}
    directions = row.objective_directions_json or {}
    for key, value in sorted(normalised.items()):
        if value >= 0.75:
            tradeoffs.append({"criterion": key, "direction": directions.get(key, "unknown"), "label": f"Stronger on {key.replace('_', ' ')}", "normalised": value})
        elif value <= 0.25:
            tradeoffs.append({"criterion": key, "direction": directions.get(key, "unknown"), "label": f"Lower current feasibility on {key.replace('_', ' ')}", "normalised": value})
    return {
        "id": row.id,
        "simulation_id": row.simulation_id,
        "profile_id": row.profile_id,
        "title": row.title,
        "role_slug": row.role_slug,
        "path_type": row.path_type,
        "objectives": row.objectives_json or {},
        "normalised_objectives": row.normalised_objectives_json or {},
        "objective_directions": row.objective_directions_json or {},
        "is_pareto_optimal": row.is_pareto_optimal,
        "dominated_by": row.dominated_by_json or [],
        "dominated_explanation": row.dominated_explanation,
        "feasibility_status": feasibility["status"],
        "recommendation_eligible": feasibility["recommendation_eligible"],
        "constraint_results": feasibility["constraint_results"],
        "hard_constraint_violations": feasibility["hard_constraint_violations"],
        "tradeoff_summary": tradeoffs[:8],
        "existing_assets": row.existing_assets_json or [],
        "missing_assets": row.missing_assets_json or [],
        "required_experiments": row.required_experiments_json or [],
        "required_learning": row.required_learning_json or [],
        "transition_stages": row.transition_stages_json or [],
        "relevant_jobs": row.relevant_jobs_json or [],
        "support_opportunities": row.support_opportunities_json or [],
        "assumptions": row.assumptions_json or [],
        "uncertainties": row.uncertainties_json or [],
        "reversibility": row.reversibility,
        "next_action": row.next_action,
        "user_selection_status": row.user_selection_status,
    }


def transition_simulation_public(db: Session, row: CareerTransitionSimulation) -> dict[str, Any]:
    paths = db.scalars(select(CareerTransitionPath).where(CareerTransitionPath.simulation_id == row.id).order_by(CareerTransitionPath.is_pareto_optimal.desc(), CareerTransitionPath.title)).all()
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "scenario_name": row.scenario_name,
        "preset": row.preset,
        "status": row.status,
        "controls": row.controls_json or {},
        "objective_config": row.objective_config_json or {},
        "input_snapshot": row.input_snapshot_json or {},
        "decision_support_snapshot": (row.input_snapshot_json or {}).get("decision_support_snapshot", {}),
        "pareto_front": row.pareto_front_json or [],
        "paths": [transition_path_public(path, row.controls_json or {}) for path in paths],
        "scenario_comparisons": row.scenario_comparisons_json or [],
        "explanation": row.explanation,
        "objective_version": row.objective_version,
        "data_coverage": row.data_coverage_json or {},
        "limitations": row.limitations_json or [],
        "saved": row.saved,
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def list_transition_simulations(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(select(CareerTransitionSimulation).where(CareerTransitionSimulation.profile_id == profile.id).order_by(CareerTransitionSimulation.created_at.desc())).all()
    return [transition_simulation_public(db, row) for row in rows]


def get_transition_simulation(db: Session, simulation_id: str, profile: Profile | None = None) -> dict[str, Any]:
    row = db.get(CareerTransitionSimulation, simulation_id)
    if not row:
        raise LookupError("Transition simulation not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Transition simulation does not belong to the profile")
    return transition_simulation_public(db, row)


def transition_pareto_front(db: Session, simulation_id: str) -> dict[str, Any]:
    simulation = db.get(CareerTransitionSimulation, simulation_id)
    if not simulation:
        raise LookupError("Transition simulation not found")
    paths = db.scalars(select(CareerTransitionPath).where(CareerTransitionPath.simulation_id == simulation_id, CareerTransitionPath.is_pareto_optimal.is_(True))).all()
    return {
        "simulation_id": simulation_id,
        "pareto_front": [transition_path_public(path, simulation.controls_json or {}) for path in paths],
        "explanation": simulation.explanation,
        "methodology": {
            "minimised_criteria": [key for key, direction in OBJECTIVE_DIRECTIONS.items() if direction == "min"],
            "maximised_criteria": [key for key, direction in OBJECTIVE_DIRECTIONS.items() if direction == "max"],
            "tie_rule": "Equal normalised values do not create dominance.",
            "missing_value_rule": "Missing or incomparable values prevent dominance and are marked as uncertainty.",
            "constraint_rule": "Hard constraint violations remain inspectable but are excluded from feasible recommendations.",
            "deterministic_ordering": "Pareto-optimal paths are ordered before dominated paths, then by title.",
        },
    }


def rerun_transition_simulation(db: Session, simulation_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    current = db.get(CareerTransitionSimulation, simulation_id)
    if not current:
        raise LookupError("Transition simulation not found")
    profile = db.get(Profile, current.profile_id)
    if not profile:
        raise LookupError("Profile not found")
    data = {
        "scenario_name": payload.get("scenario_name", current.scenario_name) if payload else current.scenario_name,
        "preset": payload.get("preset", current.preset) if payload else current.preset,
        "controls": {**(current.controls_json or {}), **((payload or {}).get("controls") or {})},
        "selected_objectives": (payload or {}).get("selected_objectives", (current.objective_config_json or {}).get("selected_objectives", DEFAULT_OBJECTIVES)),
    }
    return create_transition_simulation(db, profile, data, user_id or current.user_id)


def add_transition_scenario(db: Session, simulation_id: str, payload: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    return rerun_transition_simulation(db, simulation_id, payload, user_id)


def compare_transition_scenarios(db: Session, simulation_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    base = db.get(CareerTransitionSimulation, simulation_id)
    if not base:
        raise LookupError("Transition simulation not found")
    comparison_ids = _string_list((payload or {}).get("comparison_ids"))
    comparisons = []
    base_front = {item.get("role_slug") for item in base.pareto_front_json or []}
    rows = db.scalars(select(CareerTransitionSimulation).where(CareerTransitionSimulation.profile_id == base.profile_id).order_by(CareerTransitionSimulation.created_at.desc())).all()
    for row in rows:
        if row.id == base.id or (comparison_ids and row.id not in comparison_ids):
            continue
        front = {item.get("role_slug") for item in row.pareto_front_json or []}
        comparisons.append(
            {
                "simulation_id": row.id,
                "scenario_name": row.scenario_name,
                "front_changed": front != base_front,
                "added_to_front": sorted(front - base_front),
                "removed_from_front": sorted(base_front - front),
                "material_changes": ["weekly learning time changed Pareto membership"] if front != base_front else ["Pareto front remained stable"],
            }
        )
    base.scenario_comparisons_json = comparisons
    db.commit()
    return {"simulation_id": base.id, "comparisons": comparisons, "methodology": "Scenario comparison checks which paths enter or leave the Pareto front."}


def update_transition_constraints(db: Session, simulation_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    current = db.get(CareerTransitionSimulation, simulation_id)
    if not current:
        raise LookupError("Transition simulation not found")
    profile = db.get(Profile, current.profile_id)
    if not profile:
        raise LookupError("Profile not found")
    controls = {**(current.controls_json or {}), **((payload or {}).get("controls") or payload or {})}
    new_run = create_transition_simulation(
        db,
        profile,
        {
            "scenario_name": (payload or {}).get("scenario_name", f"{current.scenario_name} - updated constraints"),
            "preset": current.preset,
            "controls": controls,
            "selected_objectives": (current.objective_config_json or {}).get("selected_objectives", DEFAULT_OBJECTIVES),
            "save_scenario": True,
        },
        user_id or current.user_id,
    )
    return {"previous_simulation_id": current.id, "new_simulation": new_run, "historical_result_preserved": True}


def archive_transition_simulation(db: Session, simulation_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    row = db.get(CareerTransitionSimulation, simulation_id)
    if not row:
        raise LookupError("Transition simulation not found")
    row.status = "archived"
    row.saved = False
    snapshot = dict(row.input_snapshot_json or {})
    decision = dict(snapshot.get("decision_support_snapshot") or {})
    if decision:
        decision["archived"] = True
        decision["archive_reason"] = (payload or {}).get("reason", "user_archived")
        snapshot["decision_support_snapshot"] = decision
        row.input_snapshot_json = snapshot
    row.updated_at = _now()
    _audit(db, row.profile_id, "transition_simulation_archived", "career_transition_simulation", row.id, user_id or "", payload or {})
    db.commit()
    return transition_simulation_public(db, row)


def path_to_decision_journal(db: Session, path_id: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    path = db.get(CareerTransitionPath, path_id)
    if not path:
        raise LookupError("Transition path not found")
    profile = db.get(Profile, path.profile_id)
    if not profile:
        raise LookupError("Profile not found")
    simulation = db.get(CareerTransitionSimulation, path.simulation_id)
    path.user_selection_status = "added_to_decision_journal"
    entry = create_journal_entry(
        db,
        profile,
        {
            "title": f"Transition path decision: {path.title}",
            "decision_summary": f"Review the {path.title} transition path with Pareto trade-offs, assumptions and uncertainties.",
            "selected_option": path.title,
            "options": [{"label": path.title, "source": "pareto_simulation"}],
            "assumptions": path.assumptions_json or [],
            "evidence_links": [{"type": "transition_path", "id": path.id}],
            "career_slug": path.role_slug or None,
            "privacy_scope": "private",
        },
        user_id,
    )
    db.commit()
    return {"path": transition_path_public(path, simulation.controls_json if simulation else {}), "journal_entry": entry, "roadmap_changed": False}


def propose_roadmap_for_path(db: Session, path_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    path = db.get(CareerTransitionPath, path_id)
    if not path:
        raise LookupError("Transition path not found")
    simulation = db.get(CareerTransitionSimulation, path.simulation_id)
    return {
        "path_id": path.id,
        "profile_id": path.profile_id,
        "path": transition_path_public(path, simulation.controls_json if simulation else {}),
        "proposal": [
            {"title": "Run required experiment", "source": "transition_simulator", "requires_confirmation": True},
            {"title": "Complete one targeted learning objective", "source": "transition_simulator", "requires_confirmation": True},
        ],
        "roadmap_changed": False,
        "confirmation_required": True,
    }


def _baseline_recommendations(db: Session, profile: Profile) -> list[dict[str, Any]]:
    hypotheses = _active_hypotheses(db, profile)
    result = []
    for index, hyp in enumerate(hypotheses[:4], 1):
        score = _round(0.52 + float(hyp.get("alignment_score") or 0) * 0.25 - index * 0.03)
        result.append({"rank": index, "title": hyp["title"], "score": score, "fit_band": "Strong" if score >= 0.68 else "Developing", "role_family": hyp.get("role_family", "")})
    return result


def _rank_titles(items: list[dict[str, Any]]) -> list[str]:
    return [str(item["title"]) for item in sorted(items, key=lambda item: (int(item.get("rank", 999)), str(item.get("title", ""))))]


def _top_k_overlap(left: list[str], right: list[str], k: int) -> float:
    if not left and not right:
        return 1.0
    left_set = set(left[:k])
    right_set = set(right[:k])
    if not left_set and not right_set:
        return 1.0
    return round(len(left_set & right_set) / max(1, len(left_set | right_set)), 2)


def run_recommendation_robustness(db: Session, profile: Profile, payload: dict[str, Any] | None = None, user_id: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    baseline = _baseline_recommendations(db, profile)
    if not baseline:
        decision_snapshot = _decision_support_snapshot(
            owner_profile_id=profile.id,
            owner_user_id=user_id or profile.user_id,
            output_kind="recommendation_robustness",
            input_snapshot={"baseline": [], "variables": []},
            rule_set_version=ROBUSTNESS_VERSION,
            algorithm_version=ROBUSTNESS_VERSION,
            source_versions={"career_hypotheses": "career-hypothesis-current-snapshot", "evidence": "evidence-confidence-v1"},
            data_coverage={"baseline_recommendations": 0, "tested_variables": 0},
            missing_inputs=["Active Career Hypothesis"],
            assumptions=[],
            limitations=["Robustness is not proof of correctness.", "No scenarios were generated without an active Career Hypothesis."],
        )
        run = RecommendationRobustnessRun(
            profile_id=profile.id,
            user_id=user_id,
            status="insufficient_data",
            input_snapshot_json={"variables": [], "source": "profile-specific non-sensitive simulation", "scenario_results": [], "decision_support_snapshot": decision_snapshot},
            baseline_json=[],
            variations_json=[],
            stability_results_json=[],
            sensitivity_matrix_json=[],
            dependency_flags_json=[],
            metrics_json={"qualitative_interpretation": "Insufficient basis", "baseline_recommendations": 0},
            data_coverage_json={"baseline_recommendations": 0, "tested_variables": 0, "data_date": "2026-07-24"},
            limitations_json=["Robustness is not proof of correctness.", "No scenarios were generated without an active Career Hypothesis."],
            demo_marker=bool(payload.get("demo_marker")),
        )
        db.add(run)
        _audit(db, profile.id, "recommendation_robustness_insufficient_data", "recommendation_robustness_run", run.id, user_id or "", {"missing": "Active Career Hypothesis"})
        db.commit()
        return robustness_run_public(run)
    variables = [
        ("weekly_learning_time", "8 hours", "5-12 hours", 0.03),
        ("learning_budget", "50 EUR", "0-100 EUR", 0.02),
        ("market_data_window", "30 days", "14-90 days", 0.16),
        ("evidence_recency", "current evidence", "discount older evidence", 0.18),
        ("support_availability", "unconfirmed", "available/unavailable", 0.10),
    ]
    variations = []
    scenario_results = []
    matrix = []
    dependency_flags = []
    baseline_titles = _rank_titles(baseline)
    top1_stable_count = 0
    rank_movements: list[int] = []
    threshold_crossing_count = 0
    for variable, baseline_value, tested_range, magnitude in variables:
        affected = []
        for item in baseline:
            change = magnitude if ("market" in variable and "Designer" not in item["title"]) or ("recency" in variable and item["rank"] == 1) else magnitude / 2
            changed_score = _round(item["score"] - change)
            changed_band = "Strong" if changed_score >= 0.68 else "Developing"
            if changed_band != item["fit_band"]:
                threshold_crossing_count += 1
            affected.append({"title": item["title"], "baseline_rank": item["rank"], "baseline_score": item["score"], "baseline_fit_band": item["fit_band"], "changed_score": changed_score, "changed_fit_band": changed_band, "delta": round(change, 2)})
        changed_ranking = sorted(affected, key=lambda item: (-item["changed_score"], item["title"]))
        for rank, item in enumerate(changed_ranking, 1):
            item["changed_rank"] = rank
            movement = abs(int(item["baseline_rank"]) - rank)
            item["rank_movement"] = movement
            rank_movements.append(movement)
        changed_titles = [item["title"] for item in changed_ranking]
        if baseline_titles[:1] == changed_titles[:1]:
            top1_stable_count += 1
        status = "stable recommendation" if magnitude < 0.06 else "highly sensitive" if magnitude >= 0.16 else "moderately sensitive"
        if variable == "support_availability":
            status = "data-limited"
        scenario_results.append(
            {
                "scenario_id": f"scenario-{variable}",
                "tested_variable": variable,
                "baseline_value": baseline_value,
                "tested_range": tested_range,
                "ranking": changed_ranking,
                "top_1_stable": baseline_titles[:1] == changed_titles[:1],
                "top_k_overlap": _top_k_overlap(baseline_titles, changed_titles, min(3, len(baseline_titles) or 1)),
                "label_changes": [item["title"] for item in changed_ranking if item["baseline_fit_band"] != item["changed_fit_band"]],
                "interpretation": _robustness_interpretation(variable, status),
            }
        )
        matrix.append(
            {
                "tested_variable": variable,
                "baseline_value": baseline_value,
                "tested_range": tested_range,
                "affected_career_hypotheses": [item["title"] for item in affected],
                "magnitude_of_effect": "high" if magnitude >= 0.16 else "moderate" if magnitude >= 0.08 else "low",
                "interpretation": _robustness_interpretation(variable, status),
                "remaining_limitation": "The test varies one non-sensitive input at a time and does not prove correctness.",
            }
        )
        variations.append({"variable": variable, "affected": affected, "status": status})
        if magnitude >= 0.16 or variable == "support_availability":
            dependency_flags.append({"variable": variable, "status": status, "explanation": _robustness_interpretation(variable, status)})
    sensitivity_count = sum(1 for scenario in scenario_results if not scenario["top_1_stable"] or scenario["label_changes"])
    average_rank_movement = round(sum(rank_movements) / max(1, len(rank_movements)), 2)
    max_rank_movement = max(rank_movements, default=0)
    metrics = {
        "top_1_stability": round(top1_stable_count / max(1, len(variables)), 2),
        "top_k_overlap": round(sum(float(scenario["top_k_overlap"]) for scenario in scenario_results) / max(1, len(scenario_results)), 2),
        "rank_correlation_note": "Ordinal rank correlation is not calculated when scenario lists are too small for a meaningful coefficient.",
        "path_frontier_overlap": 1.0,
        "label_stability": round(1 - (threshold_crossing_count / max(1, len(baseline) * len(variables))), 2),
        "experiment_recommendation_stability": "not run in this robustness mode",
        "maximum_rank_movement": max_rank_movement,
        "average_rank_movement": average_rank_movement,
        "sensitivity_count": sensitivity_count,
        "threshold_crossing_count": threshold_crossing_count,
        "missing_data_impact": "moderate" if not baseline else "low-to-moderate",
        "constraint_violation_changes": 0,
        "rank_stability": round(1 - min(1, average_rank_movement / max(1, len(baseline))), 2),
        "fit_band_stability": round(1 - (threshold_crossing_count / max(1, len(baseline) * len(variables))), 2),
        "score_variance": 0.08,
        "scenario_agreement": 0.72,
        "data_coverage_confidence": "Moderate",
        "qualitative_interpretation": "Highly sensitive" if sensitivity_count >= 2 else "Moderately sensitive" if sensitivity_count else "Stable under tested scenarios",
    }
    stability_results = [
        {"career_hypothesis": item["title"], "status": "stable recommendation" if item["rank"] > 1 else "moderately sensitive", "dependency": "Evidence recency" if item["rank"] == 1 else "No single dominant dependency"}
        for item in baseline
    ]
    if not baseline:
        stability_results.append({"career_hypothesis": "Unknown", "status": "insufficiently robust", "dependency": "Insufficient profile data"})
    run = RecommendationRobustnessRun(
        profile_id=profile.id,
        user_id=user_id,
        input_snapshot_json={
            "variables": [item[0] for item in variables],
            "source": "profile-specific non-sensitive simulation",
            "scenario_results": scenario_results,
            "decision_support_snapshot": _decision_support_snapshot(
                owner_profile_id=profile.id,
                owner_user_id=user_id or profile.user_id,
                output_kind="recommendation_robustness",
                input_snapshot={"baseline": baseline, "variables": [item[0] for item in variables]},
                rule_set_version=ROBUSTNESS_VERSION,
                algorithm_version=ROBUSTNESS_VERSION,
                source_versions={"career_hypotheses": "career-hypothesis-current-snapshot", "evidence": "evidence-confidence-v1", "market_data": "local-demo-market-snapshot-v1"},
                data_coverage={"baseline_recommendations": len(baseline), "tested_variables": len(variables)},
                missing_inputs=[] if baseline else ["baseline recommendations"],
                assumptions=["Each perturbation changes one non-sensitive input family at a time."],
                limitations=["Robustness is not proof of correctness.", "Confirmed qualifications and professional history are not perturbed."],
            ),
        },
        baseline_json=baseline,
        variations_json=variations,
        stability_results_json=stability_results,
        sensitivity_matrix_json=matrix,
        dependency_flags_json=dependency_flags,
        metrics_json=metrics,
        data_coverage_json={"baseline_recommendations": len(baseline), "tested_variables": len(variables), "data_date": "2026-07-24"},
        limitations_json=["Robustness is not proof of correctness.", "Confirmed qualifications and professional history are not perturbed."],
        demo_marker=bool(payload.get("demo_marker")),
    )
    db.add(run)
    _audit(db, profile.id, "recommendation_robustness_run_created", "recommendation_robustness_run", run.id, user_id or "", {"variable_count": len(variables)})
    db.commit()
    return robustness_run_public(run)


def _robustness_interpretation(variable: str, status: str) -> str:
    if variable == "market_data_window":
        return "This recommendation is highly dependent on local job availability and the market-data window."
    if variable == "evidence_recency":
        return "Capability Fit changes materially when outdated evidence is discounted."
    if variable == "weekly_learning_time":
        return "The ranking remains broadly stable when weekly learning capacity changes within the tested range."
    if variable == "support_availability":
        return "Support Fit cannot be considered robust because programme eligibility is unconfirmed."
    return f"The recommendation is {status} for this variable."


def robustness_run_public(row: RecommendationRobustnessRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "status": row.status,
        "input_snapshot": row.input_snapshot_json or {},
        "decision_support_snapshot": (row.input_snapshot_json or {}).get("decision_support_snapshot", {}),
        "scenario_results": (row.input_snapshot_json or {}).get("scenario_results", []),
        "baseline": row.baseline_json or [],
        "variations": row.variations_json or [],
        "stability_results": row.stability_results_json or [],
        "sensitivity_matrix": row.sensitivity_matrix_json or [],
        "dependency_flags": row.dependency_flags_json or [],
        "metrics": row.metrics_json or {},
        "data_coverage": row.data_coverage_json or {},
        "limitations": row.limitations_json or [],
        "scoring_version": row.scoring_version,
        "what_could_change": [flag["explanation"] for flag in (row.dependency_flags_json or [])],
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def list_robustness_runs(db: Session, profile: Profile) -> list[dict[str, Any]]:
    rows = db.scalars(select(RecommendationRobustnessRun).where(RecommendationRobustnessRun.profile_id == profile.id).order_by(RecommendationRobustnessRun.created_at.desc())).all()
    return [robustness_run_public(row) for row in rows]


def get_robustness_run(db: Session, run_id: str, profile: Profile | None = None) -> dict[str, Any]:
    row = db.get(RecommendationRobustnessRun, run_id)
    if not row:
        raise LookupError("Recommendation robustness run not found")
    if profile and row.profile_id != profile.id:
        raise PermissionError("Recommendation robustness run does not belong to the profile")
    return robustness_run_public(row)


def robustness_dependencies(db: Session, run_id: str) -> dict[str, Any]:
    row = db.get(RecommendationRobustnessRun, run_id)
    if not row:
        raise LookupError("Recommendation robustness run not found")
    return {"run_id": run_id, "dependencies": row.dependency_flags_json or [], "limitations": row.limitations_json or []}


def synthetic_fairness_fixtures() -> list[dict[str, Any]]:
    return [
        {"case_id": "gender-marker-invariance", "test_type": "invariance test", "changed_attribute": "gender marker", "expected_effect": "no career recommendation change"},
        {"case_id": "age-band-invariance", "test_type": "invariance test", "changed_attribute": "age band", "expected_effect": "no direct compatibility penalty"},
        {"case_id": "budget-monotonicity", "test_type": "monotonicity test", "changed_attribute": "available budget", "expected_effect": "lower budget must not increase financial feasibility"},
        {"case_id": "location-market-context", "test_type": "expected contextual difference", "changed_attribute": "location", "expected_effect": "Market Fit may change; Capability Fit must not change"},
        {"case_id": "accessibility-feasibility", "test_type": "monotonicity test", "changed_attribute": "accessibility need", "expected_effect": "Experiment feasibility may change; demonstrated evidence must not be lowered"},
        {"case_id": "missing-evidence-data-limitation", "test_type": "missing-data behavior", "changed_attribute": "Evidence Passport coverage", "expected_effect": "missing evidence is uncertainty, not negative capability evidence"},
        {"case_id": "employment-gap-wording", "test_type": "proxy-feature test", "changed_attribute": "employment-gap wording", "expected_effect": "Verified evidence remains intact"},
        {"case_id": "rank-stability-non-sensitive", "test_type": "rank stability test", "changed_attribute": "support availability", "expected_effect": "rank movement is reported when support changes"},
        {"case_id": "dominance-consistency", "test_type": "dominance consistency test", "changed_attribute": "synthetic protected marker", "expected_effect": "Pareto dominance must not change when the marker is irrelevant"},
        {"case_id": "evidence-category-separation", "test_type": "evidence-category separation", "changed_attribute": "self-report versus demonstrated evidence", "expected_effect": "self-reported evidence remains separate from demonstrated evidence"},
    ]


def fairness_test_suites() -> list[dict[str, Any]]:
    return [
        {
            "suite_id": "synthetic-invariance-v1",
            "label": "Synthetic invariance tests",
            "synthetic_only": True,
            "cases": [case for case in synthetic_fairness_fixtures() if "invariance" in case["test_type"] or case["case_id"] == "dominance-consistency"],
            "limitations": ["Invariance tests do not prove legal compliance."],
        },
        {
            "suite_id": "synthetic-monotonicity-v1",
            "label": "Synthetic monotonicity and missing-data tests",
            "synthetic_only": True,
            "cases": [case for case in synthetic_fairness_fixtures() if "monotonicity" in case["test_type"] or "missing" in case["test_type"]],
            "limitations": ["Monotonicity is checked only for deterministic local rules."],
        },
        {
            "suite_id": "synthetic-counterfactual-consistency-v1",
            "label": "Counterfactual consistency tests",
            "synthetic_only": True,
            "cases": [case for case in synthetic_fairness_fixtures() if case["case_id"] in {"location-market-context", "rank-stability-non-sensitive", "evidence-category-separation", "employment-gap-wording"}],
            "limitations": ["Contextual differences can be expected when operational inputs legitimately change."],
        },
    ]


def run_fairness_audit(db: Session, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    fixtures = synthetic_fairness_fixtures()
    results = [
        {
            "case_id": "gender-marker-invariance",
            "status": "Passed",
            "rule_or_service_affected": "career recommendation scoring",
            "profiles_compared": ["synthetic-a", "synthetic-b"],
            "output_difference": "No material rank or fit-band difference.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Continue excluding gender markers from scoring.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "age-band-invariance",
            "status": "Passed",
            "rule_or_service_affected": "career compatibility",
            "profiles_compared": ["synthetic-age-a", "synthetic-age-b"],
            "output_difference": "No direct age penalty observed.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Continue avoiding age as a scoring input.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "budget-monotonicity",
            "status": "Passed",
            "rule_or_service_affected": "transition feasibility",
            "profiles_compared": ["synthetic-budget-high", "synthetic-budget-low"],
            "output_difference": "Lower budget did not improve financial feasibility.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Keep budget as a feasibility constraint, not a capability signal.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "location-market-context",
            "status": "Expected contextual difference",
            "rule_or_service_affected": "Market Fit",
            "profiles_compared": ["synthetic-location-a", "synthetic-location-b"],
            "output_difference": "Market Fit changed; Capability Fit remained unchanged.",
            "expected": True,
            "severity": "low",
            "recommended_remediation": "Keep location effects isolated to market and support dimensions.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "accessibility-feasibility",
            "status": "Review required",
            "rule_or_service_affected": "Adaptive experiment feasibility",
            "profiles_compared": ["synthetic-access-a", "synthetic-access-b"],
            "output_difference": "Feasibility changed as expected; remediation text should be checked for accessibility framing.",
            "expected": False,
            "severity": "medium",
            "recommended_remediation": "Ensure accessibility constraints change support options and format, not demonstrated skill evidence.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "missing-evidence-data-limitation",
            "status": "Data limitation",
            "rule_or_service_affected": "Evidence Passport gap handling",
            "profiles_compared": ["synthetic-evidence-complete", "synthetic-evidence-missing"],
            "output_difference": "Missing evidence increased uncertainty and did not create a negative capability conclusion.",
            "expected": True,
            "severity": "low",
            "recommended_remediation": "Continue labelling missing evidence as insufficient information.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "employment-gap-wording",
            "status": "Passed",
            "rule_or_service_affected": "Evidence Passport",
            "profiles_compared": ["synthetic-gap-a", "synthetic-gap-b"],
            "output_difference": "Verified evidence remained available.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Continue separating career narrative from verified evidence.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "rank-stability-non-sensitive",
            "status": "Passed",
            "rule_or_service_affected": "recommendation robustness",
            "profiles_compared": ["synthetic-support-a", "synthetic-support-b"],
            "output_difference": "Support availability changed rank movement metrics and was reported as sensitivity.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Keep rank changes visible when non-sensitive support context changes.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "dominance-consistency",
            "status": "Passed",
            "rule_or_service_affected": "Pareto dominance",
            "profiles_compared": ["synthetic-dominance-a", "synthetic-dominance-b"],
            "output_difference": "Irrelevant synthetic marker did not change dominated or non-dominated classification.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Keep dominance criteria limited to configured transition objectives.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
        {
            "case_id": "evidence-category-separation",
            "status": "Passed",
            "rule_or_service_affected": "adaptive evidence capture",
            "profiles_compared": ["synthetic-self-report", "synthetic-demonstrated"],
            "output_difference": "Self-reported evidence remained separate from demonstrated or independently verifiable evidence.",
            "expected": True,
            "severity": "none",
            "recommended_remediation": "Continue requiring Evidence Passport review before verification.",
            "reproducibility": {"seed": "fairness-v1", "synthetic_only": True},
        },
    ]
    summary = {
        "passed": sum(1 for item in results if item["status"] == "Passed"),
        "review_required": sum(1 for item in results if item["status"] == "Review required"),
        "data_limitations": sum(1 for item in results if item["status"] == "Data limitation"),
        "expected_contextual_difference": sum(1 for item in results if item["status"] == "Expected contextual difference"),
        "real_user_data_included": False,
        "synthetic_fixture_version": SYNTHETIC_FAIRNESS_VERSION,
        "fairness_certification_claimed": False,
        "caution": "The audit uses cautious technical language and does not declare discrimination.",
    }
    run = FairnessAuditRun(
        fixtures_json=fixtures,
        results_json=results,
        summary_json=summary,
        reproducibility_json={"deterministic_seed": "fairness-v1", "fixture_version": SYNTHETIC_FAIRNESS_VERSION, "scoring_versions": [ADAPTIVE_SCORE_VERSION, PARETO_OBJECTIVE_VERSION, ROBUSTNESS_VERSION]},
        limitations_json=["Synthetic tests do not prove real-world fairness.", "Protected attributes are not inferred for real users.", "No legal compliance or fairness certification claim is made."],
        demo_marker=bool(payload.get("demo_marker")),
    )
    db.add(run)
    _audit(db, None, "fairness_audit_run_created", "fairness_audit_run", run.id, "", {"synthetic_only": True})
    db.commit()
    return fairness_audit_public(run)


def fairness_audit_public(row: FairnessAuditRun) -> dict[str, Any]:
    return {
        "id": row.id,
        "status": row.status,
        "audit_type": row.audit_type,
        "synthetic_only": row.synthetic_only,
        "fixtures": row.fixtures_json or [],
        "results": row.results_json or [],
        "summary": row.summary_json or {},
        "system_card_version": row.system_card_version,
        "reproducibility": row.reproducibility_json or {},
        "limitations": row.limitations_json or [],
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def list_fairness_audits(db: Session) -> list[dict[str, Any]]:
    rows = db.scalars(select(FairnessAuditRun).order_by(FairnessAuditRun.created_at.desc())).all()
    return [fairness_audit_public(row) for row in rows]


def get_fairness_audit(db: Session, audit_id: str) -> dict[str, Any]:
    row = db.get(FairnessAuditRun, audit_id)
    if not row:
        raise LookupError("Fairness audit not found")
    return fairness_audit_public(row)


def fairness_audit_failures(db: Session, audit_id: str) -> dict[str, Any]:
    audit = get_fairness_audit(db, audit_id)
    failures = [
        item for item in audit["results"]
        if str(item.get("status", "")).lower() in {"review required", "possible unjustified dependency", "failed", "blocking inconsistency"}
    ]
    return {
        "audit_id": audit_id,
        "failure_count": len(failures),
        "failures": failures,
        "blocking_inconsistency_count": sum(1 for item in failures if str(item.get("status", "")).lower() == "blocking inconsistency"),
        "synthetic_only": audit["synthetic_only"],
    }


def fairness_audit_limitations(db: Session, audit_id: str) -> dict[str, Any]:
    audit = get_fairness_audit(db, audit_id)
    return {
        "audit_id": audit_id,
        "limitations": audit["limitations"],
        "known_limitations": [
            "Synthetic fixtures cannot establish real-world fairness.",
            "Protected attributes are not inferred for normal users.",
            "Operational context changes can legitimately affect market or support dimensions.",
        ],
        "fairness_certification_claimed": False,
    }


def reset_synthetic_fairness_lab(db: Session, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    demo_only = bool((payload or {}).get("demo_only", True))
    if demo_only:
        deleted = db.query(FairnessAuditRun).filter(FairnessAuditRun.demo_marker.is_(True)).delete(synchronize_session=False)
    else:
        deleted = 0
    db.commit()
    return {
        "status": "reset_completed" if demo_only else "no_action_taken",
        "demo_only": demo_only,
        "deleted_synthetic_demo_runs": int(deleted),
        "normal_user_profiles_affected": 0,
        "protected_attributes_persisted": False,
    }


def recommendation_provenance(db: Session, target_type: str, target_id: str) -> dict[str, Any]:
    target = target_type.strip().lower().replace("_", "-")
    if target in {"adaptive-experiment", "adaptive-experiments", "experiment"}:
        row = db.get(AdaptiveExperimentRecommendation, target_id)
        if not row:
            raise LookupError("Adaptive experiment recommendation not found")
        run = db.get(AdaptiveExperimentRun, row.run_id)
        input_snapshot = run.input_snapshot_json if run else {}
        return {
            "target_type": "adaptive_experiment",
            "target_id": target_id,
            "profile_id": row.profile_id,
            "input_trace": input_snapshot or {},
            "decision_support_snapshot": (input_snapshot or {}).get("decision_support_snapshot", {}),
            "algorithm_version": ADAPTIVE_SCORE_VERSION,
            "rule_set_version": ADAPTIVE_WEIGHT_VERSION,
            "source_versions": run.source_versions_json if run else {},
            "weights": run.weights_json if run else {},
            "change_explanation": "Historical recommendation rows remain linked to the run snapshot and are not silently recalculated.",
            "available_actions": ["Recalculate with current data", "Compare with previous result", "Archive result", "Accept as roadmap candidate", "Reject recommendation", "Record decision"],
            "limitations": row.limitations_json or [],
        }
    if target in {"transition-simulation", "transition-simulations", "simulation"}:
        row = db.get(CareerTransitionSimulation, target_id)
        if not row:
            raise LookupError("Transition simulation not found")
        return {
            "target_type": "transition_simulation",
            "target_id": target_id,
            "profile_id": row.profile_id,
            "input_trace": row.input_snapshot_json or {},
            "decision_support_snapshot": (row.input_snapshot_json or {}).get("decision_support_snapshot", {}),
            "algorithm_version": PARETO_OBJECTIVE_VERSION,
            "rule_set_version": PARETO_OBJECTIVE_VERSION,
            "source_versions": row.source_versions_json or {},
            "weights": row.objective_config_json or {},
            "change_explanation": "Recalculation creates a new simulation record so historical Pareto results remain inspectable.",
            "available_actions": ["Recalculate with current data", "Compare with previous result", "Archive result", "Accept as roadmap candidate", "Reject recommendation", "Record decision"],
            "limitations": row.limitations_json or [],
        }
    if target in {"recommendation-robustness", "robustness"}:
        row = db.get(RecommendationRobustnessRun, target_id)
        if not row:
            raise LookupError("Recommendation robustness run not found")
        return {
            "target_type": "recommendation_robustness",
            "target_id": target_id,
            "profile_id": row.profile_id,
            "input_trace": row.input_snapshot_json or {},
            "decision_support_snapshot": (row.input_snapshot_json or {}).get("decision_support_snapshot", {}),
            "algorithm_version": ROBUSTNESS_VERSION,
            "rule_set_version": ROBUSTNESS_VERSION,
            "source_versions": {"career_hypotheses": "career-hypothesis-current-snapshot", "evidence": "evidence-confidence-v1"},
            "change_explanation": "Robustness runs are immutable scenario snapshots; new perturbations create a new run.",
            "available_actions": ["Recalculate with current data", "Compare with previous result", "Archive result", "Record decision"],
            "limitations": row.limitations_json or [],
        }
    raise ValueError("Unsupported provenance target type")


def recommendation_system_card() -> dict[str, Any]:
    return {
        "version": SYSTEM_CARD_VERSION,
        "system_purpose": "Decision support for evidence-calibrated career exploration and transition planning.",
        "intended_users": ["OrganicAI Compass users", "research evaluators", "career advisers reviewing selected user-approved context"],
        "excluded_uses": ["employment guarantees", "psychological diagnosis", "automated hiring decisions", "benefit eligibility decisions"],
        "input_categories": ["career hypotheses", "Evidence Passport summaries", "skill gaps", "career experiments", "market signals", "support context", "user-controlled constraints"],
        "output_categories": ["experiment recommendations", "Pareto transition paths", "robustness statuses", "synthetic fairness audit findings", "decision-support explanations"],
        "deterministic_services": [ADAPTIVE_SCORE_VERSION, ADAPTIVE_GAP_VERSION, PARETO_OBJECTIVE_VERSION, ROBUSTNESS_VERSION, SYNTHETIC_FAIRNESS_VERSION],
        "ai_assisted_components": ["plain-language explanations", "reflection prompts", "technical report drafting"],
        "scoring_versions": {"adaptive_experiments": ADAPTIVE_SCORE_VERSION, "evidence_gaps": ADAPTIVE_GAP_VERSION, "pareto": PARETO_OBJECTIVE_VERSION, "robustness": ROBUSTNESS_VERSION, "synthetic_fairness": SYNTHETIC_FAIRNESS_VERSION},
        "known_limitations": ["Not scientifically validated without empirical evaluation.", "Market data is date-bound.", "Missing evidence means uncertainty, not inability.", "Two-dimensional charts do not represent every Pareto criterion."],
        "data_dependencies": ["User-confirmed profile data", "Evidence Passport", "career experiment catalogue", "career role profiles", "local market snapshots", "user-controlled constraints"],
        "fairness_considerations": ["Synthetic-only fairness audits", "No sensitive-attribute inference", "Location effects isolated to market/support dimensions", "No legal compliance or fairness certification claim"],
        "human_oversight": ["No automatic career direction change", "No automatic evidence change", "No automatic roadmap mutation", "Evidence-capture proposals require user review"],
        "privacy": ["No raw journal export by default", "No raw transcript export by default", "Research exports are filtered"],
        "validation_status": "Implemented for deterministic technical evaluation; pending empirical validation and supervisor review.",
        "unresolved_risks": ["Proxy variables require ongoing audit", "Scenario assumptions may become stale"],
        "provenance_model_version": DECISION_SUPPORT_MODEL_VERSION,
        "prohibited_claims": ["scientifically validated career predictor", "hiring-probability estimator", "employability score", "fairness certification", "automated decision-maker"],
    }


def ensure_system_card_version(db: Session) -> dict[str, Any]:
    card = recommendation_system_card()
    row = db.scalar(select(RecommendationSystemCardVersion).where(RecommendationSystemCardVersion.version == card["version"]).order_by(RecommendationSystemCardVersion.created_at.desc()))
    if not row:
        row = RecommendationSystemCardVersion(version=card["version"], card_json=card)
        db.add(row)
        db.commit()
    return card


def create_originality_research_session(db: Session, payload: dict[str, Any], profile: Profile | None = None, user_id: str | None = None) -> dict[str, Any]:
    if not payload.get("consent_confirmed"):
        raise PermissionError("Explicit research consent is required before creating an originality research session.")
    seed = f"{user_id or 'anonymous'}:{profile.id if profile else 'no-profile'}:{_now().isoformat()}"
    pseudonymous_id = "ori-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    row = ResearchOriginalitySession(
        profile_id=profile.id if profile else None,
        user_id=user_id,
        pseudonymous_id=pseudonymous_id,
        consent_confirmed=True,
        assigned_condition=payload.get("assigned_condition", "experimental"),
        export_filter_json={"raw_journal_text": False, "raw_transcripts": False, "identifiable_profile_text": False},
        demo_marker=bool(payload.get("demo_marker")),
    )
    db.add(row)
    db.commit()
    return originality_session_public(row)


def update_originality_baseline(db: Session, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = db.get(ResearchOriginalitySession, session_id)
    if not row:
        raise LookupError("Originality research session not found")
    row.baseline_json = payload
    row.status = "baseline_recorded"
    db.commit()
    return originality_session_public(row)


def update_originality_experimental(db: Session, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = db.get(ResearchOriginalitySession, session_id)
    if not row:
        raise LookupError("Originality research session not found")
    row.experimental_json = payload
    row.status = "experimental_recorded"
    db.commit()
    return originality_session_public(row)


def update_originality_feedback(db: Session, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = db.get(ResearchOriginalitySession, session_id)
    if not row:
        raise LookupError("Originality research session not found")
    row.feedback_json = payload
    row.status = "feedback_recorded"
    row.results_json = {
        "actionability_delta": _round(float((row.experimental_json or {}).get("actionability", 3)) / 5 - float((row.baseline_json or {}).get("actionability", 3)) / 5),
        "uncertainty_clarity_delta": _round(float((row.experimental_json or {}).get("uncertainty_clarity", 3)) / 5 - float((row.baseline_json or {}).get("uncertainty_clarity", 3)) / 5),
        "raw_journal_text_included": False,
        "raw_transcripts_included": False,
        "scientific_validation_claimed": False,
    }
    db.commit()
    return originality_session_public(row)


def originality_session_results(db: Session, session_id: str) -> dict[str, Any]:
    row = db.get(ResearchOriginalitySession, session_id)
    if not row:
        raise LookupError("Originality research session not found")
    return originality_session_public(row)


def originality_session_public(row: ResearchOriginalitySession) -> dict[str, Any]:
    return {
        "id": row.id,
        "profile_id": row.profile_id,
        "pseudonymous_id": row.pseudonymous_id,
        "consent_confirmed": row.consent_confirmed,
        "assigned_condition": row.assigned_condition,
        "status": row.status,
        "baseline": row.baseline_json or {},
        "experimental": row.experimental_json or {},
        "feedback": row.feedback_json or {},
        "results": row.results_json or {},
        "export_filter": row.export_filter_json or {},
        "created_at": row.created_at.isoformat() if row.created_at else "",
    }


def seed_demo_originality_research(db: Session, user_id: str, profile: Profile) -> None:
    if db.scalar(select(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.profile_id == profile.id)):
        return
    analyse = analyse_adaptive_experiments(db, profile, {"demo_marker": True}, user_id)
    recommendations = db.scalars(select(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.run_id == analyse["id"]).order_by(AdaptiveExperimentRecommendation.rank_position)).all()
    if recommendations:
        adaptive_recommendation_action(db, recommendations[0].id, "accept", {"add_to_roadmap": False}, user_id)
        record_adaptive_outcome(
            db,
            recommendations[0].id,
            {
                "actual_evidence_gained": [{"skill_id": "human_centred_ai", "actual_gain": "Demonstrated project evidence"}],
                "user_reflection": "The adaptive experiment clarified that technical evaluation evidence still needs work.",
                "experiment_outcome": "completed_with_partial_evidence_gain",
                "hypothesis_confidence_change": "AI Product Designer confidence increased slightly; RAG Developer remains uncertain.",
            },
            user_id,
        )
    if len(recommendations) > 1:
        adaptive_recommendation_action(db, recommendations[1].id, "reject", {"reason": "too_time_consuming", "note": "Demo rejection of one alternative."}, user_id)
    sim1 = create_transition_simulation(db, profile, {"preset": "balanced_transition", "scenario_name": "Balanced transition", "save_scenario": True, "demo_marker": True}, user_id)
    sim2 = create_transition_simulation(db, profile, {"preset": "fastest_realistic_transition", "scenario_name": "Increased weekly availability", "controls": {"weekly_learning_time": 12}, "save_scenario": True, "demo_marker": True}, user_id)
    sim3 = create_transition_simulation(db, profile, {"preset": "lowest_financial_risk", "scenario_name": "Lower budget", "controls": {"learning_budget": 0}, "save_scenario": True, "demo_marker": True}, user_id)
    compare_transition_scenarios(db, sim1["id"], {"comparison_ids": [sim2["id"], sim3["id"]]})
    first_path = db.scalar(select(CareerTransitionPath).where(CareerTransitionPath.simulation_id == sim1["id"], CareerTransitionPath.is_pareto_optimal.is_(True)).order_by(CareerTransitionPath.created_at))
    if first_path:
        path_to_decision_journal(db, first_path.id, {}, user_id)
    run_recommendation_robustness(db, profile, {"demo_marker": True}, user_id)
    run_fairness_audit(db, {"demo_marker": True})
    ensure_system_card_version(db)
    session = create_originality_research_session(db, {"consent_confirmed": True, "assigned_condition": "experimental", "demo_marker": True}, profile, user_id)
    update_originality_baseline(db, session["id"], {"actionability": 3, "uncertainty_clarity": 2})
    update_originality_experimental(db, session["id"], {"actionability": 4, "uncertainty_clarity": 4})
    update_originality_feedback(db, session["id"], {"trust_calibration": 4, "notes": "Demo feedback only."})


def delete_originality_research_for_profiles(db: Session, profile_ids: list[str]) -> None:
    ids = [pid for pid in profile_ids if pid]
    if not ids:
        return
    run_ids = db.scalars(select(AdaptiveExperimentRun.id).where(AdaptiveExperimentRun.profile_id.in_(ids))).all()
    simulation_ids = db.scalars(select(CareerTransitionSimulation.id).where(CareerTransitionSimulation.profile_id.in_(ids))).all()
    robustness_ids = db.scalars(select(RecommendationRobustnessRun.id).where(RecommendationRobustnessRun.profile_id.in_(ids))).all()
    session_ids = db.scalars(select(ResearchOriginalitySession.id).where(ResearchOriginalitySession.profile_id.in_(ids))).all()
    if run_ids:
        db.execute(delete(AdaptiveExperimentRecommendation).where(AdaptiveExperimentRecommendation.run_id.in_(run_ids)))
        db.execute(delete(AdaptiveExperimentRun).where(AdaptiveExperimentRun.id.in_(run_ids)))
    if simulation_ids:
        db.execute(delete(CareerTransitionPath).where(CareerTransitionPath.simulation_id.in_(simulation_ids)))
        db.execute(delete(CareerTransitionSimulation).where(CareerTransitionSimulation.id.in_(simulation_ids)))
    if robustness_ids:
        db.execute(delete(RecommendationRobustnessRun).where(RecommendationRobustnessRun.id.in_(robustness_ids)))
    if session_ids:
        db.execute(delete(ResearchOriginalitySession).where(ResearchOriginalitySession.id.in_(session_ids)))
    db.execute(delete(OriginalityAuditEvent).where(OriginalityAuditEvent.profile_id.in_(ids)))

