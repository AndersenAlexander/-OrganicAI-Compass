# Evidence calibration loop

OrganicAI Compass treats a career direction as a testable hypothesis:

`Human Diagnostic → Career Hypothesis → Evidence Gap → Career Experiment → Evidence Proposal → Recalibration`

The loop is deterministic and works offline. It does not estimate hiring probability, employability, psychological traits, or guaranteed fit.

## Epistemic boundaries

Important factors carry explicit source categories: `SELF_REPORT`, `DIAGNOSTIC`, `DEEP_DIVE`, `EVIDENCE`, `EXPERIMENT`, `MARKET`, `SUPPORT`, `USER_CONFIRMED`, and `SYSTEM_DERIVED`. Diagnostic signals and self-report remain visible separately from evidence records and system interpretation.

Career Hypotheses expose qualitative fit bands such as `Currently plausible`, `Worth exploring`, `Mixed signal`, and `Insufficient evidence`. They preserve diagnostic/profile versions, source breakdown, supporting and caution signals, missing/conflicting evidence, user decision state, and version history.

## Evidence gaps

`CareerEvidenceGap` is persistent and linked to a profile, hypothesis, career match, and capability. Statuses are `MISSING`, `OUTDATED`, `CONFLICTING`, `INSUFFICIENT`, `SELF_REPORT_ONLY`, or `PARTIAL`.

The engine distinguishes:

- `skill_gap`: the current declared capability is low enough that a learning task may be appropriate;
- `evidence_gap`: capability may exist, but practical, dated, or independently reviewable support is missing or incomplete.

Missing evidence is uncertainty, not proof of inability. The API exposes both `/profiles/{profile_id}/career-evidence-gaps` and the existing `/profiles/{profile_id}/evidence-gaps` decision-support endpoint.

## Experiments and evidence proposals

Experiments retain the existing deterministic catalogue and rubric. They can be linked to a hypothesis and evidence gap, carry expected evidence gain, and remain outside My Roadmap until the user explicitly confirms the Roadmap action. Their lifecycle includes suggested/planned/in-progress/submitted/evaluated states.

Evaluation stores actual evidence gain separately from expected gain. It creates `CareerEvidenceProposal` records in `PENDING_REVIEW` with `PROVISIONAL` verification state. Provisional experiment rows are excluded from the authoritative Evidence Passport. No diagnostic signal, AI explanation, experiment completion, or rubric result silently promotes evidence.

The user can `accept`, `edit`, or `reject` a proposal. Accept/edit creates a user-confirmed Passport record with source, category, date, verification state, relevance, recency, linked hypothesis/experiment/gap, and provenance. Reject leaves the Passport unchanged; rejecting previously accepted evidence removes that confirmed source and supports downward recalibration.

## Recalibration and “What changed?”

Only the linked hypothesis is recalibrated after a confirmed proposal. A new `CareerHypothesisVersion` and `CareerRecalibrationRun` preserve before/after state, changed dimensions, rule version, source provenance, and the explanation. Natural fit and transition feasibility are not rewritten by an evidence event.

The UI labels the comparison `What changed and why?` and shows the evidence event, affected hypothesis, before/after interpretation, rule version, and unchanged dimensions. The explanation explicitly states that evidence support is bounded and does not establish professional readiness or predict hiring success.

## Ownership, migration, and limitations

All hypothesis, gap, experiment, proposal, Passport, and recalibration routes are profile-owned and use the existing authorization boundary. Migration `0006_evidence_calibration_loop` follows `0005_human_diagnostic_v2`; there is one Alembic head.

The deterministic rubric evaluates submitted text/artefact metadata using transparent rules. It cannot prove long-term team performance, production deployment, certification, or employment outcome. Market/support signals remain limitations unless separately evaluated by their existing modules.
