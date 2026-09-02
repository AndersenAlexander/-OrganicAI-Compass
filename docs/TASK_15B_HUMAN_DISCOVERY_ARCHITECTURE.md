# Task 15B Human Discovery Architecture

Date: 2026-08-09

## Rationale

Task 15B consolidates the existing Diagnostic, Human Potential, Assessment, Career Compatibility, Career Hypotheses, Evidence Passport, and Career Experiments modules into one explainable career-discovery journey. The change does not add a competing assessment engine and does not introduce a database migration.

The central rule is that historical experience must not be treated as the same thing as natural preference. Career directions are presented as provisional, testable hypotheses, not as psychological diagnoses, hiring probabilities, or guaranteed outcomes.

## Diagnostic Role

Diagnostic remains the lightweight Natural Discovery layer. It captures preference-oriented information such as interests, preferred activities, values, work-style tendencies, learning style, and broad orientation. Existing skill and AI-use fields remain available for backward compatibility, but they are explicitly excluded from Natural Fit and used only as optional prefill for later confirmation.

## Assessment Role

Assessment remains the deeper capability, evidence, readiness, and constraints layer. It confirms or edits values already provided through Natural Discovery, then adds current skills, AI capability, professional context, evidence status, change readiness, goals, and constraints. Prefill is returned to the frontend but does not create persisted assessment responses until the user starts/saves the assessment.

## Fit Dimensions

Natural Fit answers: what professional activities currently appear compatible with the user's stated preferences. Inputs include interests, work values, and work style. It excludes job title, years of experience, certification, portfolio evidence, salary, budget, time availability, market demand, and historical employment.

Capability Fit answers: what relevant capability the user currently appears to possess. Inputs include current skills, experience signal, AI readiness, and transferable skill coverage. Self-reported capability can contribute to capability fit, but it is not the same as demonstrated evidence.

Evidence Strength answers: what the user can currently demonstrate. Inputs include evidence status for relevant skills and Evidence Passport style records such as practical/project/professional evidence. Self-reported skill and course completion are kept distinct from practical verification.

Transition Feasibility answers: how feasible it is to pursue the direction under current conditions. Inputs include change readiness, missing skills, learning exposure, and constraint/readiness signals. These variables do not modify Natural Fit.

Market Fit and Support Fit are preserved as separate concepts. Task 15B does not collapse them into Natural Fit, Capability Fit, or Evidence Strength.

## Source Of Truth

Raw user input remains in its existing domain records. Profile data now includes a Natural Discovery snapshot and assessment prefill payload. Assessment scoring consumes confirmed assessment responses and generated score snapshots. Evidence Passport records remain the source for demonstrated evidence. Career Hypotheses combine these sources into versioned dimension outputs.

The hierarchy is:

1. Raw Diagnostic and Assessment input.
2. Profile Natural Discovery snapshot and optional assessment prefill.
3. Capability assessment scores and skill inventory.
4. Evidence Passport / equivalent evidence records.
5. Constraint and readiness signals.
6. Career Hypothesis dimensions.

This avoids one massive table while giving every overlapping concept a defined role.

## Scoring And Versioning

The modified rule set is deterministic and versioned as `human-discovery-career-hypothesis` `v2`. Assessment sessions and career matches use `career-scoring-v2-four-layer`.

Career hypothesis alignment remains available for backward compatibility as a combined presentation score, but the UI now exposes separate dimensions:

- Natural Fit
- Capability Fit
- Evidence Strength
- Transition Feasibility
- AI Opportunity

Legacy component scores remain in metadata as `legacy_component_scores` and explicit `source_of_truth` metadata records which input category feeds each dimension.

## User Journey

The workspace navigation now presents the core journey in this order:

1. Natural Discovery
2. Human Potential Map
3. Capability Assessment
4. Career Hypotheses
5. Evidence Passport
6. Career Experiments
7. Supported Paths / Market / Application / Interview modules

This is guidance, not a rigid lock. Downstream modules remain accessible where they already were.

## Human Potential

Human Potential now uses cautious language around natural tendencies and strength signals. It includes natural tendency, capability, evidence, and development-opportunity sections in generated profile data. It does not claim innate talent, fixed aptitude, or psychological diagnosis.

## Career Hypotheses

Career matches now include `hypothesis_dimensions`, direct `dimension_scores`, `dimension_labels`, and `dimension_explanations`. A strong Natural Fit with weak Evidence Strength remains worth testing and can point the user toward a Career Experiment. Strong historical experience can improve Capability Fit or Evidence Strength without automatically becoming Natural Fit.

## Recalibration

Career Experiment recalibration now records which dimension changed. Experiment results can strengthen Evidence Strength and, where appropriate, Capability Fit. They do not silently change Natural Fit or Transition Feasibility unless a future rule explicitly supports that.

## Backward Compatibility

No schema migration was added. Existing Diagnostic fields, Assessment responses, CareerMatch alignment score, factors, and downstream routes remain compatible. Demo mode was updated only enough to demonstrate the four-layer separation; general `demo-profile` fallback removal is deferred to Task 15C.

## Limitations

Weights are prototype decision-support rules, not statistically validated psychological or labor-market predictions. The system does not claim scientific proof of career suitability, employability probability, or career success probability. Market Fit and Support Fit are preserved but not fully redesigned in Task 15B.
