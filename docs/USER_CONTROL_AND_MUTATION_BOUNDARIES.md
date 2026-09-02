# User Control and Mutation Boundaries

This matrix describes the authoritative-state boundary of OrganicAI Compass. A suggestion, calculation, or generated text is not a user decision and is not confirmed evidence.

| Area | Normal state/action | Classification | Authoritative mutation boundary |
|---|---|---|---|
| Human Diagnostic | Render questions and calculate an interpretation from submitted answers | System/automatic, non-authoritative interpretation | A user submission stores the response and resulting profile version; the interpretation remains exploratory and correctable. |
| Human Potential Map | View current profile interpretation and provenance | Read-only | No silent mutation from viewing. |
| Career Hypotheses | Generate or display candidate directions | Proposal-only / system suggestion | A hypothesis becomes active only through the existing explicit selection/confirmation flow. |
| Evidence gaps and experiments | Rank a bounded experiment and record its context | Proposal-only | Starting, submitting, evaluating, accepting, or rejecting an experiment is explicit; completion does not create confirmed evidence. |
| Evidence Passport | Review source, confidence, recency, and proposal | User-confirmed mutation | Only the dedicated review/confirmation action creates or changes confirmed evidence. |
| Roadmap, learning and recommendations | Present generated actions or resource suggestions | Proposal-only | Roadmap additions, progress, feedback, and status changes use explicit user actions. |
| Market/application | Show source-aware job/requirement analysis and draft materials | Proposal-only | Requirement confirmation, Evidence Lock, application creation, stage changes, and document-use actions require explicit confirmation. |
| Interview Journey | Create practice prompts and observable response feedback | System/automatic, non-authoritative feedback | A user explicitly records reflection, outcome, or follow-up state; feedback is not a hiring decision. |
| Recalibration | Calculate an explanation and suggested adjustment | Proposal-only | A user must review and confirm a recalibration; it is not applied merely because a new signal exists. |
| Advisor collaboration | Prepare scoped, expiring proposals and audit information | Proposal-only | An adviser cannot directly mutate authoritative profile state; user scope, expiry, revoke, and proposal acceptance control access. |
| Decision Journal | Display system context and possible trade-offs | Read-only / proposal-only | A journal record is created only by the user's deliberate decision action. |
| Originality simulations | Persist deterministic experiment, Pareto, robustness, or synthetic audit runs | System/automatic, non-authoritative research record | A run appends a provenance-bearing record and does not mutate profile, hypothesis, Evidence Passport, roadmap, application, or Decision Journal state. |

## Operating principles

1. User-owned records are accessed only through the authenticated ownership boundary.
2. System output is labelled as an interpretation, suggestion, or scenario where applicable.
3. Explicit confirmation is required before evidence, direction, roadmap, application, outcome, recalibration, or user decision becomes authoritative.
4. Insufficient prerequisites produce an empty, unavailable, or insufficient-data state rather than a fabricated fallback.
5. Demo and synthetic records remain visibly separate from real user-entered records.
