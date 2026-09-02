# Interview-to-outcome workflow

OrganicAI Compass connects an explicit Application Tracker record to an Interview Journey record, stage-aware preparation, plausible practice questions, STAR stories, text-first mock interviews, observable feedback, post-interview reflection, outcome capture, proposal-first recalibration, and Offer Review.

## Safety boundaries

- Interview stages and lifecycle status are explicit. Application stage changes require a separate user confirmation.
- Generated questions are labelled as plausible practice questions. The system does not predict employer wording or hiring outcomes.
- Questions preserve generated versions and support keep, edit, dismiss, archive, and user-created states.
- STAR stories preserve canonical and job-specific adaptations. Evidence support is shown as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `SELF_REPORT_ONLY`, `UNSUPPORTED`, or `NEEDS_REVIEW`; polished wording is never treated as evidence.
- Mock feedback is deterministic where possible and uses observable relevance, structure, specificity, evidence use, completeness, clarity, unsupported claims, and requirement coverage. It does not assess personality, honesty, emotion, accent, intelligence, cultural fit, or employability.
- Text mode is complete without voice. Voice is optional, raw audio is not retained by default, and transcript storage requires explicit confirmation and remains editable or deletable.
- Reflection separates employer-confirmed feedback, user observation, user interpretation, and system suggestions. Outcomes preserve their source and do not infer a reason that was not recorded.
- Recalibration is a `PROPOSED_CHANGE`. Accept, edit, or reject is explicit; Career Hypotheses, Evidence Passport, Human Potential Map, and Roadmap are not mutated by an interview alone.
- Offer Review keeps missing information visible and exposes trade-offs against user priorities. It does not provide legal, tax, pension, or authoritative financial advice.

## Deterministic demo story

The demo seed includes:

- Application: `Human-Centred AI Product Strategist`
- Confirmed requirements: stakeholder communication, product thinking, AI familiarity, structured problem solving, and analytics exposure
- Stage: Hiring Manager
- Plausible practice question: `Tell me about a time you converted ambiguous requirements into a structured recommendation.`
- Linked evidence: `Career Experiment #CE-demo-structured-recommendation` with a visible partial-support state
- A reusable canonical STAR library, text mock session, separated reflection, proposed recalibration, and offer review with unknown fields preserved

The scenario is deterministic demo content, not a hiring prediction or evidence update.

## Additive migration

Migration `0008_interview_outcome_safety` adds lifecycle, requirement-set, question-state, STAR-support, panel-feedback, transcript-storage, reflection-source, offer-version, and recalibration-proposal fields. It is additive and keeps the previous Interview Journey API compatible.
