# OrganicAI Compass Master Knowledge

## 1. Platform overview

OrganicAI Compass is a master's-dissertation research prototype for human-centred career exploration, learning planning, and practical preparation for work in an AI-shaped environment. It connects self-reflection, an exploratory Human Potential Map, deterministic career hypotheses, evidence review, bounded career experiments, an editable roadmap, market and application workflows, interview practice, and an optional text or voice AI Coach.

The platform is decision support, not an automated career-decision or hiring system. It does not diagnose a person, predict career success, certify employability, or decide which career someone should choose.

## 2. Purpose and research question

The research investigates how personal reflection, retrieval-grounded AI guidance, voice interaction, visible evidence, and adaptive recommendations can support meaningful action while preserving user agency, transparency, and control. The public research framework separates technical implementation evidence from empirical claims about benefit, trust, or outcomes.

The implemented prototype can support functional and RAG evaluation. Participant benefit, predictive validity, psychometric validity, real-world fairness, and improved employment outcomes have not been established and require separate empirical research.

## 3. Human-centred AI philosophy

OrganicAI Compass treats AI as a tool for explanation, comparison, drafting, reflection, and option generation. Human beings retain goals, values, context, ethical responsibility, confirmation authority, and final decisions.

Outputs remain inspectable and correctable. The system should increase agency rather than create passive dependence, surveillance, or pressure to accept a generated interpretation.

## 4. How OrganicAI Compass works

The core journey is: Human Diagnostic, Human Potential Map, deeper capability assessment, Career Hypotheses, Evidence Passport, Career Experiments, recommendations and learning, Human-AI Growth Roadmap, Market/Application workflow, Interview Journey, reflection, and explicit decisions. My Journey summarizes persisted workflow markers and links back into these modules.

Static platform facts come from the curated Knowledge Base. Questions about a particular user must use authenticated, persisted records belonging to that user's active profile. Missing user records must be reported as unavailable rather than invented from generic knowledge.

## 5. Human Diagnostic

The Human Diagnostic is a structured self-reflection workflow. It captures preference-oriented signals such as interests, values, work-style tendencies, learning preferences, concerns about AI, and broad orientation. Its questions are original prototype material and are not a clinical or proprietary psychometric test.

Submitted responses can produce a versioned exploratory interpretation. The diagnostic is self-report: it does not prove aptitude, personality, job suitability, or skill competence, and users can correct or reject interpretations.

## 6. Human Potential Map

The Human Potential Map visualizes the current profile interpretation, including tendencies, strengths, values, creative orientation, AI-collaboration style, contribution domains, and development opportunities. It is a reviewable map of current signals rather than a fixed identity or prediction.

Viewing the map does not change authoritative state. Profile feedback and confirmations use explicit user actions and are stored with ownership checks and history.

## 7. Career Compatibility

Career Compatibility presents candidate role directions derived by versioned deterministic rules from assessment records and role templates. Results expose separate dimensions, explanations, supporting signals, caution signals, missing skills, and transition considerations.

Compatibility is exploratory. A result is neither proof of professional suitability nor a probability of hiring or success, and market demand is not allowed to rewrite preference-based Natural Fit.

## 8. Career hypotheses

A career direction is called a hypothesis because it is provisional and testable. It combines current diagnostic, assessment, capability, evidence, readiness, and source metadata while preserving uncertainty and version history.

Hypotheses can be compared, explored, accepted into a user-controlled workflow, superseded, or tested through experiments. The platform must not call them predictions, guarantees, or employer judgments.

## 9. Deterministic scoring

Career scoring is implemented in versioned application code, currently including `career-scoring-v2-four-layer` and the `human-discovery-career-hypothesis` version 2 rule set. The primary hypothesis dimensions use explicit weights: Natural Fit 0.32, Capability Fit 0.24, Evidence Strength 0.16, Transition Feasibility 0.18, and AI Augmentation Opportunity 0.10.

The LLM does not calculate or alter these scores. It may explain stored inputs, outputs, limitations, and trade-offs in plain language. The weights are prototype decision-support rules, not statistically validated probabilities.

## 10. Natural Fit

Natural Fit represents compatibility with stated interests, work values, and work-style preferences. Its internal composition is interest match 50 percent, values match 28 percent, and work-style compatibility 22 percent.

Natural Fit excludes employment history, skill level, portfolio evidence, certification, salary, market demand, budget, and time availability. An experiment does not silently change it because practical evidence is different from stated preference.

## 11. Capability Fit

Capability Fit represents relevant current capability signals. Its prototype calculation combines skills match, AI readiness/opportunity, and broad professional-experience exposure. Self-reported skills can contribute, but self-report is not the same as demonstrated capability.

Confirmed experiment evidence may make a bounded adjustment to relevant capability interpretation. It must not be presented as certification, professional readiness, or an employer assessment.

## 12. Evidence Strength

Evidence Strength represents what can currently be supported for skills relevant to a career hypothesis. It distinguishes self-report from experience, projects, certification, practical exercises, career experiments, portfolio work, professional work, mentor review, and user-confirmed external evidence.

The value is deterministic and can change when relevant evidence is explicitly reviewed, confirmed, corrected, rejected, or becomes stale. The Coach can explain the value but cannot calculate or modify it.

## 13. Transition Feasibility

Transition Feasibility represents how practical it currently appears to pursue a direction under stated conditions. It uses change readiness and current development gaps, and the wider workflow can expose time, budget, learning, market, or support constraints separately.

Feasibility is not preference and must not modify Natural Fit. It is a planning aid, not a forecast of whether the transition will succeed.

## 14. AI Opportunity

AI Opportunity, stored as AI Augmentation Opportunity in scoring metadata, reflects AI-literacy and practical AI-readiness responses. It highlights where AI might augment tasks or learning in a role family.

It is not an automation probability, labour-market forecast, or judgment of human value. It contributes a bounded component to a hypothesis and should be interpreted alongside evidence and human responsibility.

## 15. Career Experiments

Career Experiments are small, reversible role simulations chosen from a deterministic catalogue. They target evidence gaps with clear instructions, deliverables, allowed tools, completion criteria, and a transparent rubric.

Submitting an experiment does not certify a skill or decide a career. Deterministic evaluation creates observable results and reviewable evidence proposals; the user still controls whether proposed evidence becomes authoritative.

## 16. Evidence Passport

The Evidence Passport is the persisted source of evidence records, confidence labels, provenance, recency, related roles, and outstanding verification needs. It distinguishes Unverified, Self-reported, Supported, Demonstrated, Practically verified, and Professionally evidenced states.

It preserves historical evidence rather than deleting older records merely because confidence changes. Static Knowledge Base text must never invent which Passport records a user has.

## 17. Practical verification

Practical verification requires relevant observable work and sufficient deterministic rubric support. In the current experiment logic, low-scoring observations remain in the review but do not become evidence; a linked priority gap requires direct assessment and the practical-verification threshold.

Course completion records learning exposure and is capped at Supported evidence. A polished explanation, an AI-generated draft, or an experiment being marked complete is not by itself practical verification.

## 18. Adaptive evidence loop

The adaptive loop is: Human Diagnostic, Career Hypothesis, Evidence Gap, Career Experiment, Evidence Proposal, user review, and bounded recalibration. Gap states include missing, outdated, conflicting, insufficient, self-report-only, and partial.

Proposals remain provisional until the user accepts or edits them. Confirmed evidence can update Evidence Strength and, where relevant, Capability Fit for the linked hypothesis; Natural Fit and Transition Feasibility remain unchanged by that evidence event.

## 19. Human-AI Growth Roadmap

The roadmap organizes user-owned actions into seven-day, thirty-day, and six-month horizons. Actions expose reason, first step, success criteria, time estimate, provenance, status, progress, and optional links to recommendations, hypotheses, evidence gaps, or experiments.

Generated or rule-based recalibration is a proposal. Applying changes, adding an experiment, completing an action, postponing it, or changing status requires an explicit user action and creates traceable state or events.

## 20. Career Resilience

Career Resilience connects hypotheses, evidence gaps, bounded experiments, recalibration, supported paths, and optional job-loss support. Its purpose is to help a user test and strengthen possible directions without pretending uncertainty has disappeared.

Supported-path and public-support outputs use cautious labels and preserve unknowns. Official authorities, not OrganicAI Compass, decide legal eligibility, benefits, or programme funding.

## 21. Market Radar

Market Radar displays observed signals from configured provider data or clearly labelled demo fixtures. Provider states can be live, cached, stale, demo, or unavailable, and records preserve freshness and provenance.

Observed samples are not forecasts, exhaustive market intelligence, or hiring probabilities. Demo vacancies are fictional and must never be represented as current external truth.

## 22. Job Analyzer

Job Analyzer accepts a saved posting, supported allowlisted URL, pasted text, or confirmed browser capture. It sanitizes and bounds imported content, extracts requirements deterministically, and records source location, method, time, confidence, and version.

Extracted requirements are proposals until the user accepts, edits, reclassifies, or rejects them. Evidence mapping is based on confirmed requirements and persisted Evidence Passport records.

## 23. Application Tracker

Application Tracker stores user-owned applications, stages, contacts, next actions, outcomes, and related events. Records can link to a confirmed analysis version and evidence/readiness snapshots.

The platform does not submit applications automatically, predict recruiter or ATS outcomes, or change the roadmap merely because an application status changed. Recalibration suggestions require explicit review.

## 24. Interview Journey

Interview Journey connects an application or job analysis to stage-aware preparation, plausible questions, STAR stories, text mock sessions, optional voice, reflection, outcome capture, follow-up drafts, and Offer Review. Stage and lifecycle states are explicit and persisted.

Generated questions are practice possibilities, not predictions of employer wording. Interview output must not infer honesty, personality, intelligence, anxiety, accent, cultural fit, protected attributes, or employability.

## 25. STAR Stories

STAR Stories structure Situation, Task, Action, Result, and Reflection. The system checks clarity, user ownership, evidence links, confidentiality, unsupported claims, and relevance while preserving canonical and job-specific adaptations.

The Coach may help organize or refine a true story, but it must not invent an experience, metric, employer fact, or complete fictional success story. Polished wording does not strengthen evidence by itself.

## 26. Mock Interview and Panel Interview

Text mock interviews are a complete workflow. Optional voice sessions and deterministic panel simulations provide additional practice with turn history and observable feedback.

Feedback focuses on relevance, structure, specificity, evidence use, completeness, clarity, unsupported claims, reflection, and question coverage. It is not a hidden total employability score and does not simulate a real employer decision.

## 27. Reflection

Post-interview reflection separates employer-confirmed feedback, user observation, user interpretation, and system suggestion. This source separation prevents an AI interpretation from being mistaken for an employer fact.

Recording a reflection is an explicit user action. Reflection can inform a proposed next step but does not automatically rewrite a profile, hypothesis, Evidence Passport, or roadmap.

## 28. Offer Review

Offer Review organizes confirmed facts, missing information, user priorities, trade-offs, questions, negotiation topics, and unresolved risks. Unknown fields remain visible rather than being filled with plausible guesses.

The module is decision support only. It does not provide authoritative legal, tax, pension, immigration, or financial advice and does not accept or reject an offer for the user.

## 29. Decision Journal

The Decision Journal stores deliberate user decisions with options, assumptions, evidence links, uncertainty, confidence, reversibility, reasoning, later outcome, and lessons. It can link hypotheses, experiments, analyses, applications, interviews, and adviser input.

System suggestions, AI explanations, evidence observations, adviser comments, and user decisions remain separate. Entries are versioned, and journal activity never changes the roadmap automatically.

## 30. My Journey

My Journey is a persisted progress overview. It reads workflow markers such as diagnostic and assessment status, hypothesis decisions, experiment states, pending evidence review, application activity, interview activity, and offer-review counts.

It is not a second scoring engine and does not infer completion from a generated suggestion. It provides links back to the source module where the user can review or act.

## 31. Recommendations

Recommendations are explainable, source-aware suggestions connected to profile signals, hypotheses, evidence gaps, retrieved knowledge, and first actions where available. Users can accept, reject, complete, give feedback, or explicitly add a recommendation to the roadmap.

Recommendations do not silently mutate authoritative records and are not statements of ideal fit, guaranteed benefit, or professional certainty. External learning-resource identity must come from curated or authorized provider data rather than LLM invention.

## 32. AI Coach

OrganicAI Coach supports text, continuous live voice, and a voice-message fallback. The text Coach combines authenticated profile context with retrieved Knowledge Base chunks, source metadata, confidence, ethical notes, and a provider-safe deterministic fallback.

The Coach explains and proposes; it does not calculate deterministic scores, confirm evidence, make irreversible decisions, fabricate missing user data, or claim external facts without an approved source. Voice answers should normally be shorter than text answers.

## 33. ElevenLabs voice integration

In live mode the browser requests an authenticated, short-lived ElevenLabs conversation token from the backend and uses WebRTC for microphone audio, turn detection, transcription, speech generation, interruption, and agent audio. API keys, bearer secrets, authorization headers, and conversation tokens remain server-side or ephemeral and must not appear in logs or UI.

Two deployment modes exist. With OrganicAI Custom LLM enabled, ElevenLabs can stream turns through OrganicAI's Coach/RAG generator. With Custom LLM disabled, the verified runtime uses the configured native ElevenLabs agent; OrganicAI still owns authentication, token minting, UI transcript rendering, consent, and fallbacks, but local per-turn RAG metadata is not produced. Text Coach remains available if ElevenLabs fails.

## 34. RAG architecture

The RAG pipeline reads Markdown files from `backend/knowledge_base`, splits headings into bounded overlapping chunks, assigns IDs using document, section index, and chunk index, embeds content, and stores source metadata in a local vector index. Search uses semantic similarity when compatible embeddings are available and a conservative lexical fallback when the embedding provider is unavailable.

Retrieved documents are treated as untrusted reference text inside a protected context boundary. Prompt-injection-like chunks are excluded, low-relevance results produce an insufficient-context response, and sources remain visible for evaluation.

## 35. Persistence

User-owned state is stored through SQLAlchemy models and versioned records. Local development can use SQLite; staging and production architecture supports PostgreSQL with Alembic migrations. Profiles, assessments, hypotheses, evidence, roadmap actions, applications, interviews, and decisions have explicit ownership and persistence boundaries.

Whether Coach transcripts persist depends on privacy preferences. Live audio is not stored by OrganicAI by default; provider-side handling depends on configured provider controls and must not be overstated.

## 36. Authentication and privacy

Protected resources use authenticated ownership checks. Provider credentials and signing secrets are backend settings and are not exposed to the frontend. Token creation is authenticated and rate-limited, and cross-user profiles, conversations, recommendations, roadmap actions, and other records are rejected.

Privacy controls include consent and preferences, conversation-history choices, voice-transcript choices, export/deletion workflows, data minimization, and provider-boundary documentation. Production deployment still requires reviewed secrets, TLS, backups, monitoring, provider controls, and legal/privacy review.

## 37. Human control and explicit confirmation

An interpretation, calculation, suggestion, generated draft, or simulation is not a user decision. Explicit confirmation is required before evidence, career direction, roadmap action, application state, interview outcome, recalibration, or personal decision becomes authoritative where the relevant workflow defines that boundary.

The AI cannot bypass confirmation tools. If a request asks the Coach to make the final career choice, it should decline and help the user compare evidence, values, uncertainties, trade-offs, and reversible experiments.

## 38. Explainability

Explainability is implemented through separate dimension scores, rule and scoring versions, source categories, retrieved-source metadata, provenance, visible evidence states, before/after recalibration records, uncertainty labels, confidence notes, and ethical cautions.

Retrieval similarity is not a correctness probability, and deterministic scores are not validated probabilities. Explanations must state what data was used, what was excluded, and what remains unknown.

## 39. Limitations

OrganicAI Compass is an internal demonstration and controlled-evaluation prototype, not a public-production-ready or clinically validated service. It has no recorded participant-outcome, psychometric, hiring-validity, real-world fairness, or career-success study.

Provider availability and data freshness vary. Market coverage is partial, demo content can be synthetic, RAG can miss relevant context, LLMs can produce errors, in-memory live-turn metadata is single-process, and generated content requires human review.

## 40. Future development

Future work includes controlled participant evaluation, stronger RAG evaluation, production deployment and monitoring, reviewed PostgreSQL operations, provider acceptance in target environments, expanded accessibility validation, legal/privacy review, penetration testing, shared live-turn metadata storage, and measured performance work.

Future work must remain labelled as planned until evidence exists. A roadmap item or architecture document is not proof that a capability is deployed, effective, certified, or complete.

## 41. Master's dissertation context

The dissertation contribution is the integration of source-separated self-report, explicit evidence-review boundaries, deterministic and provenance-bearing exploration tools, retrieval-grounded coaching, and user-controlled cross-module workflow state in an implemented prototype.

Academic defensibility depends on bounded claims: the repository supports technical implementation, functional behavior, and synthetic engineering evidence where labelled. It does not establish that the platform improves careers, predicts suitability, eliminates bias, or produces better hiring outcomes.
