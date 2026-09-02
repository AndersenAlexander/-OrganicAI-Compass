# OrganicAI Compass Defence Question Bank

## A. General platform questions

### A1. What is OrganicAI Compass?

OrganicAI Compass is a master's-dissertation research prototype for human-centred career exploration, evidence review, learning, and employment preparation in an AI-shaped world. It connects reflection, deterministic decision support, retrieval-grounded coaching, practical experiments, and user-controlled action without choosing a career for the user.

### A2. Who is the platform for?

It is designed primarily for adults, students, lifelong learners, and professionals exploring change, growth, or human-AI collaboration. It is not an employer screening tool and must not be used to rank applicants.

### A3. What problem does the platform address?

It addresses fragmented guidance, uncertainty about AI and work, weak evidence visibility, and the gap between reflection and practical action. The prototype brings these concerns into one traceable journey while keeping decisions human-led.

### A4. What is the main user journey?

The journey moves from Human Diagnostic and Human Potential Map to deeper assessment, Career Hypotheses, Evidence Passport, Career Experiments, Roadmap, applications, interviews, reflection, and explicit decisions. My Journey summarizes persisted progress and links back to the source modules.

### A5. Is OrganicAI Compass a career test?

It contains structured self-reflection and deterministic career exploration, but it is not a validated psychometric or employment test. Results are exploratory hypotheses that users can inspect, correct, reject, and test.

### A6. Is it a job-search platform?

It includes Market Radar, Job Analyzer, Application Studio, Application Tracker, and Interview Journey, but it is broader than job search. These modules support preparation and evidence review; they do not auto-apply or guarantee outcomes.

### A7. What makes the platform human-centred?

The system separates facts, evidence, interpretations, suggestions, and user decisions. It requires explicit confirmation at authoritative boundaries and makes uncertainty, provenance, and limitations visible.

### A8. What is the most important design principle?

AI may support thinking, explanation, and drafting, but human beings retain values, responsibility, confirmation authority, and final decisions. The platform should expand agency rather than replace judgment.

## B. Research and academic questions

### B1. What is the research purpose?

The research explores whether a human-centred combination of reflection, grounded AI, voice, evidence, and adaptive guidance can support meaningful action while preserving agency and transparency. The prototype supplies an implemented artifact and evaluation framework, not proof of participant benefit.

### B2. What are the main research themes?

The public framework covers human-centred guidance, retrieval grounding, personalized action, and interaction or trust. Corresponding evaluation concerns include relevance, source grounding, usability, transparency, perceived control, and latency.

### B3. What is the artifact contribution?

The artifact integrates source-separated self-report, deterministic scoring, evidence review, experiments, market and interview workflows, RAG coaching, and explicit confirmation boundaries. Its contribution is the integrated, traceable design rather than a claim of predictive career accuracy.

### B4. Is the platform empirically validated?

No participant-outcome, psychometric-validity, hiring-validity, or career-success study is recorded. Those claims are intentionally excluded and would require separately designed empirical research.

### B5. How is this work academically defensible?

Claims are bounded to implemented technical behavior, transparent methods, provenance, and reproducible tests. Limitations distinguish engineering evidence from causal, psychological, fairness, or employment-outcome claims.

### B6. What methodology shaped the artifact?

The repository reflects a design-and-implementation approach: identify the human guidance problem, translate principles into requirements, build the prototype, and evaluate functional and RAG behavior. Controlled participant evaluation is future work rather than something the software tests can establish.

### B7. What can be evaluated now?

Functional workflows, access boundaries, deterministic calculations, persistence, retrieval behavior, source visibility, failure resilience, and selected usability tasks can be evaluated now. Perceived benefit, trust, long-term outcomes, and predictive validity require human studies.

### B8. Why is claim discipline important?

Career and AI systems can sound authoritative even when evidence is limited. Claim discipline prevents prototype scores, synthetic fixtures, generated text, or local provider tests from being misrepresented as scientific validation or production certification.

## C. AI and architecture

### C1. What role does AI play?

AI explains, summarizes, drafts, compares options, and supports reflection. It is not the authority for deterministic scores, evidence confirmation, career choice, hiring decisions, or user-owned state changes.

### C2. What is the high-level architecture?

The frontend is a React and TypeScript application, while FastAPI exposes authenticated application services and SQLAlchemy-backed persistence. RAG, provider adapters, deterministic engines, and optional voice services sit behind server-side boundaries.

### C3. Does the LLM calculate career scores?

No. Versioned deterministic application code calculates the career dimensions and experiment rubrics. The LLM may explain stored results but cannot calculate or alter them.

### C4. What is deterministic and what is LLM-generated?

Assessment scoring, hypothesis dimensions, experiment rubrics, evidence-state rules, readiness summaries, and many workflow proposals use deterministic code. Conversational explanations and some drafts may be LLM-generated, but they remain bounded by retrieved context, persisted records, and explicit confirmation.

### C5. What prevents hallucinations?

The Coach receives retrieved Knowledge Base chunks, authenticated user context, source metadata, and an explicit policy not to invent missing facts. Low-context and provider-failure paths return bounded fallbacks, although no system can guarantee that an LLM never makes an error.

### C6. Why use RAG rather than fine-tuning?

RAG keeps platform facts inspectable, replaceable, attributable, and independently indexable without changing model weights. It is a better fit for a prototype whose implementation and policies evolve and whose answers need visible sources and explicit insufficiency states.

### C7. How are prompt injections handled?

Retrieved documents are labelled untrusted reference material, and the application checks for suspicious instruction patterns before building context. Flagged chunks are excluded, while system and application instructions remain authoritative.

### C8. Can AI mutate the application directly?

Only registered, bounded commands and explicit user actions may change supported state. Explanatory text by itself cannot confirm evidence, apply a roadmap recalibration, record an application outcome, or create a user decision.

## D. Scoring methodology

### D1. What are the five career dimensions?

The dimensions are Natural Fit, Capability Fit, Evidence Strength, Transition Feasibility, and AI Augmentation Opportunity. They are shown separately so preference, current capability, proof, practical constraints, and AI readiness are not collapsed into one unexplained number.

### D2. What is Natural Fit?

Natural Fit reflects stated interests, work values, and work-style preferences. It excludes employment history, demonstrated evidence, market demand, salary, budget, and time constraints.

### D3. What is Capability Fit?

Capability Fit reflects current relevant skills, AI readiness, transferable coverage, and broad experience signals. Self-reported capability can contribute but must not be described as demonstrated evidence.

### D4. What is Evidence Strength?

Evidence Strength reflects how well relevant capability is currently supported by recorded evidence. It distinguishes self-report and learning exposure from projects, experiments, professional work, independent review, and practical verification.

### D5. What is Transition Feasibility?

Transition Feasibility reflects readiness and current development gaps under practical constraints. It helps with planning but is not a success probability and does not change Natural Fit.

### D6. What is AI Opportunity?

AI Opportunity reflects AI literacy and practical AI readiness that may support augmentation in a role family. It is not a forecast of automation or job loss.

### D7. What weights are used for the combined hypothesis score?

The current prototype weights are Natural Fit 0.32, Capability Fit 0.24, Evidence Strength 0.16, Transition Feasibility 0.18, and AI Augmentation Opportunity 0.10. These are versioned decision-support rules, not statistically validated probabilities.

### D8. Are the scores objective truth?

No. They are reproducible outputs from declared inputs, role templates, and versioned prototype rules. Transparency and repeatability do not make them psychologically or professionally definitive.

### D9. Can one experiment change Natural Fit?

No, not in the current evidence calibration rules. An experiment can affect Evidence Strength and sometimes relevant Capability Fit, but it does not rewrite stated interests, values, or work-style preferences.

### D10. Why does Evidence Strength change?

It changes when relevant evidence is added, reviewed, confirmed, corrected, rejected, or affected by recency rules. The change is deterministic and linked to provenance rather than an LLM opinion.

## E. Evidence and experiments

### E1. What is the difference between self-reported and practically verified evidence?

Self-reported evidence is a user's declaration of capability or experience. Practical verification requires relevant observable work and sufficient rubric support, with provenance and review preserved.

### E2. Does completing a course verify a skill?

No. Course completion records learning exposure and is capped at Supported evidence in the current rules. Stronger claims require practical, project, professional, or independently reviewed evidence.

### E3. What is an evidence gap?

An evidence gap means capability may exist but practical, dated, or reviewable support is missing, partial, conflicting, or outdated. It is uncertainty, not proof that the user lacks ability.

### E4. What is a skill gap?

A skill gap means the currently declared capability level is below what the hypothesis or role template expects. It can motivate learning, while an evidence gap may instead motivate demonstration or review.

### E5. How are career experiments chosen?

The adaptive ranking uses transparent evidence-gain, relevance, feasibility, cost, risk, redundancy, and preference factors. It avoids recommending duplicate work when relevant practical evidence already exists.

### E6. How are experiments evaluated?

A deterministic rubric rates observable submitted content against versioned criteria and weights. The LLM does not calculate the score, and the result is not certification or an employment assessment.

### E7. What happens after an experiment?

The system stores the deterministic result and creates reviewable evidence proposals where the thresholds and relevance rules are met. The user must accept, edit, or reject a proposal before it becomes authoritative Evidence Passport data.

### E8. Can a weak experiment become evidence?

Low rubric observations remain visible in the review but do not become evidence records. A linked priority gap also requires direct assessment and the stronger practical-verification threshold before being treated as closed.

### E9. What happens when all evidence gaps are closed?

The system can return an evidence-sufficient state and avoid recommending redundant experiments. That state still does not prove employability, guarantee success, or force a career decision.

### E10. Can AI invent evidence?

No. Generated text, polished wording, or an AI explanation cannot create authoritative evidence. Evidence must come through the persisted source and explicit review workflow.

## F. Career recommendations

### F1. Why call a result a career hypothesis?

The result combines incomplete, changing signals and therefore needs testing rather than prediction language. Calling it a hypothesis keeps uncertainty and user agency visible.

### F2. Can the AI decide which career the user should choose?

No. The Coach should decline the final choice and help compare evidence, values, constraints, trade-offs, and reversible experiments instead.

### F3. Does a high score mean the role is ideal?

No. A high score means the current prototype rules found stronger alignment in the available inputs. It is not proof of ideal fit, professional suitability, hiring probability, or future satisfaction.

### F4. How are recommendations explained?

Recommendations expose profile signals, evidence gaps, retrieved sources, reasons, first actions, cautions, and uncertainty where available. Users can accept, reject, complete, or give feedback explicitly.

### F5. Can market demand override personal preference?

No. Market signals remain a separate source and do not rewrite Natural Fit. The user may choose to weigh market information in a decision, but the system should show the trade-off rather than conceal it.

### F6. What happens when evidence conflicts?

The system preserves a conflicting or uncertain evidence state and can recommend clarification, refreshed evidence, or a bounded experiment. It should not average away a meaningful conflict or claim certainty.

### F7. Can recommendations change automatically?

The system can generate new proposals or recalibration explanations from changed records, but authoritative decisions require the defined review action. History and versions preserve what changed and why.

## G. Roadmap

### G1. What is the Human-AI Growth Roadmap?

It is an editable, persisted action plan across seven-day, thirty-day, and six-month horizons. Actions include reasons, first steps, success criteria, progress, and provenance.

### G2. Why is explicit roadmap confirmation required?

Generated recommendations and experiments are proposals, not commitments. Explicit confirmation prevents the AI or a background event from silently changing the user's plan.

### G3. Does completing an experiment add it to the roadmap?

No. An experiment remains outside the roadmap until the user explicitly confirms the roadmap action through the dedicated workflow.

### G4. Can the roadmap adapt?

Yes, but adaptation is presented as a transparent proposal based on recorded progress, blockers, or check-ins. The user chooses which proposed changes to apply.

### G5. What data does a roadmap action store?

It can store horizon, title, description, reason, first step, success criteria, time estimate, priority, status, progress, notes, provenance, and links to recommendations or experiments. Events and versions support traceability.

### G6. Does the Coach control productivity?

No. Roadmap guidance is flexible and explicitly not a judgment of productivity or worth. Users can start, postpone, skip, edit, complete, or remove actions.

### G7. What happens if no roadmap exists?

The Coach should say that no persisted roadmap is available and offer to open or generate the roadmap workflow. It must not invent actions and claim they are already saved.

## H. Employment journey

### H1. What is Market Radar?

Market Radar shows observed signals from configured, cached, or clearly labelled demo data with freshness and provenance. It does not provide exhaustive live intelligence or hiring forecasts.

### H2. What does Job Analyzer do?

It extracts bounded, source-aware requirements from saved postings, supported URLs, pasted text, or confirmed captures. Each requirement remains reviewable until the user confirms, edits, reclassifies, or rejects it.

### H3. What is Application Studio?

Application Studio creates versioned CV or cover-letter drafts whose factual claims are linked to evidence states. Unsupported high-risk claims can be blocked or replaced with safer wording.

### H4. Does the platform auto-apply?

No. Export is local structured JSON and printable HTML, and the user remains responsible for review and submission. The system makes no ATS-success guarantee.

### H5. What does Application Tracker store?

It stores user-owned applications, status, organization, next actions, contacts, stage events, evidence snapshots, and outcomes. State changes are explicit and traceable.

### H6. How does Interview Journey work?

It connects a role or application to preparation, plausible practice questions, STAR stories, mock sessions, reflection, outcome capture, follow-up drafts, and offer review. Text mode remains complete when optional voice is unavailable.

### H7. What are STAR Stories?

They are evidence-aware structures for Situation, Task, Action, Result, and Reflection. The system can improve structure but must not invent experiences or unsupported metrics.

### H8. What does mock-interview feedback assess?

It assesses observable answer properties such as relevance, structure, specificity, evidence use, clarity, completeness, unsupported claims, and requirement coverage. It must not infer personality, honesty, intelligence, emotion, protected attributes, or employability.

### H9. What does Offer Review do?

It organizes known facts, unknowns, user priorities, trade-offs, questions, and risks. It does not provide authoritative legal, tax, pension, immigration, or financial advice.

### H10. What is the Decision Journal for?

It records explicit decisions, options, evidence, assumptions, uncertainty, reversibility, reasoning, outcomes, and lessons. System suggestions and adviser input remain separate from the user's decision.

## I. Privacy, ethics, and human control

### I1. How is privacy preserved?

Protected records use authenticated ownership checks, while provider secrets stay on the backend. Consent, persistence preferences, data minimization, export, deletion, and provider boundaries are documented and enforced where implemented.

### I2. What data survives refresh?

Persisted user-owned records such as profiles, assessments, hypotheses, evidence, roadmap actions, applications, interviews, and decisions survive refresh. Ephemeral UI state and non-persisted conversations may not, depending on privacy preferences and the specific workflow.

### I3. Does the platform store all conversations?

No. Conversation and voice-transcript persistence depend on user privacy settings. A usable ephemeral flow remains possible where configured.

### I4. Is live audio stored?

OrganicAI does not store live audio files by default. Provider-side processing and retention depend on the configured provider controls and must be verified separately rather than assumed.

### I5. Can another user access my profile context?

Protected routes verify resource ownership, and the Coach drops invalid cross-user profile context. The Custom LLM endpoint also rejects profile, conversation, recommendation, and roadmap records that do not belong to the validated user.

### I6. What remains a human decision?

Career choice, evidence confirmation, roadmap application, application and interview outcomes, offer decisions, and personal journal entries remain human-controlled. AI suggestions cannot silently become these authoritative states.

### I7. Is the platform safe for clinical or legal decisions?

No. It is not a clinical, psychological, legal, financial, or safety-critical decision service. Users should consult qualified and official sources for high-impact matters.

### I8. How are sensitive facts handled in interviews?

The system should use only user-provided facts and must not infer legal status, protected attributes, private constraints, honesty, or mental state. Voice and answers are evaluated only for observable practice properties.

## J. ElevenLabs and voice

### J1. What role does ElevenLabs play?

ElevenLabs provides the live WebRTC media session, microphone transport, turn detection, transcription, speech generation, and agent orchestration. OrganicAI provides authenticated token minting, consent UI, shared transcript rendering, and fallback paths.

### J2. Does ElevenLabs have access to the OpenAI key?

OrganicAI does not send its OpenAI API key to the browser or as an ElevenLabs conversation token. In Custom LLM mode ElevenLabs calls an authenticated OrganicAI endpoint, and OrganicAI calls its configured provider server-side.

### J3. What happens if ElevenLabs is unavailable?

The live voice session returns a safe error and the user can continue with text Coach or the separate voice-message fallback where enabled. Text interaction does not depend on a successful ElevenLabs connection.

### J4. Does voice interaction change scoring?

No. Voice is an interaction channel and does not change deterministic scoring authority. A spoken explanation cannot confirm evidence or alter a career hypothesis by itself.

### J5. What is native ElevenLabs mode?

When OrganicAI Custom LLM is disabled, the configured ElevenLabs agent handles its own model conversation while OrganicAI still controls authentication, token issuance, consent, transcripts, and fallbacks. Local per-turn RAG metadata is not produced in that mode.

### J6. What is Custom LLM mode?

When enabled and securely configured, ElevenLabs streams text turns to OrganicAI's OpenAI-compatible endpoint, which uses the same Coach context and RAG generator as text chat. It requires a reachable HTTPS backend and a server-side bearer secret.

### J7. Are voice answers different from text answers?

They follow the same safety and human-control principles, but spoken responses should normally be shorter and avoid reading technical metadata aloud. Text can provide more detail and visible source information.

## K. Technical implementation

### K1. How is the Knowledge Base loaded?

The loader reads Markdown files from `backend/knowledge_base`, splits sections at headings, and chunks long sections with overlap. Chunk IDs include document name, section index, and chunk index.

### K2. How does semantic retrieval work?

Document chunks and the query are embedded, then ranked by cosine similarity. The response includes document, section, excerpt, rank, and similarity metadata for the selected context.

### K3. What happens when embeddings are unavailable?

The service uses conservative lexical overlap against the persisted index. If retrieval itself is unavailable or no source meets the threshold, the Coach returns an explicit insufficient or general-guidance state.

### K4. Are retrieval scores probabilities?

No. A similarity score describes vector or lexical closeness under the retrieval method. It is not a probability that an answer is correct.

### K5. How are chunk IDs kept unique?

New chunks use document, section index, and chunk index. Runtime code also normalizes IDs from legacy indexes that reused a document-level ID, but reindexing is the proper repair.

### K6. How is data persisted?

SQLAlchemy models store user-owned domain records and Alembic manages schema migrations. SQLite is suitable for local development, while the deployment architecture supports PostgreSQL for controlled staging and production work.

### K7. How does the Coach get user context?

The backend validates the active profile against the authenticated user and builds a compact read-only context from persisted domain records. Invalid or unavailable records are omitted rather than substituted from another user or the static KB.

### K8. What happens if OpenAI is unavailable?

The Coach uses a safe deterministic fallback for supported intents and preserves text availability. RAG can also use local hash embeddings or lexical fallback depending on which provider operation failed.

## L. Limitations

### L1. What are the main limitations of the prototype?

There is no recorded participant-outcome, psychometric, hiring-validity, or real-world fairness study. Provider availability, market coverage, RAG recall, LLM accuracy, performance, and production operations remain limited or environment-dependent.

### L2. Is the system production-ready?

No. It is an internal demonstration and controlled-evaluation candidate. Production would require reviewed infrastructure, TLS, secrets, backups, monitoring, provider controls, accessibility work, legal/privacy review, and security testing.

### L3. Does the prototype prove fairness?

No. Synthetic fairness checks are engineering fixtures only and do not prove real-world fairness, absence of bias, compliance, or certification.

### L4. Does it predict employment outcomes?

No. The system does not estimate hiring, employability, career success, or employer decisions. Application and interview records are observations and user-controlled workflow states.

### L5. Are market signals complete?

No. They are provider- and sample-bounded, and may be live, cached, stale, demo, or unavailable. Demo data is fictional and must not be presented as current market truth.

### L6. Can RAG eliminate hallucinations?

No. RAG improves traceability and constrains context, but retrieval can miss information and a model can still make errors. Source visibility, insufficiency responses, tests, and human review remain necessary.

## M. Future development

### M1. What would be required for production deployment?

Production requires reviewed PostgreSQL operations, migrations, TLS, secret management, backup and recovery, monitoring, incident response, provider acceptance, privacy controls, accessibility validation, penetration testing, and operational ownership. Each item must be verified in the target environment.

### M2. What research should happen next?

Controlled participant studies should evaluate usability, perceived agency, source comprehension, trust, and usefulness. Longer-term studies would be needed before making claims about learning, career behavior, or outcomes.

### M3. How could RAG improve?

Future work can add formal retrieval and groundedness evaluations, better metadata filters, freshness checks, query routing, reranking, and shared production indexing. Improvements should preserve lexical fallback and explicit insufficient-context behavior.

### M4. How could voice improve?

Future work can evaluate accessibility and conversational usability, validate provider retention controls, improve shared metadata storage, and compare native-agent with Custom-LLM grounding. These are evaluation and operations tasks, not reasons to weaken the working text fallback.

## N. Critical examiner questions

### N1. Is this just a chatbot with extra screens?

No. The repository contains versioned deterministic scoring, domain persistence, evidence provenance, explicit mutation boundaries, experiments, applications, interviews, decision records, and RAG observability. The chatbot is one explanation interface over those systems, not the source of their authority.

### N2. Why should anyone trust prototype weights?

They should trust them only as transparent, reproducible prototype rules, not as scientific truth. The system exposes versions, factors, exclusions, and limitations precisely so the rules can be inspected and challenged.

### N3. Are you disguising recommendations as human decisions?

The design explicitly separates system suggestion, AI explanation, adviser input, evidence observation, and user decision. Dedicated confirmation actions and version history protect that boundary.

### N4. Could a fluent AI answer still mislead the user?

Yes, which is why the policy requires fact-versus-suggestion language, source grounding, uncertainty, concise claims, and refusal to invent missing records. Human review remains necessary, especially for high-impact decisions.

### N5. Why not use one overall career score?

One score would conceal important differences between preference, capability, evidence, practical constraints, and AI readiness. Separate dimensions make trade-offs and missing evidence more inspectable.

### N6. What is genuinely original here?

The defensible contribution is the integrated architecture: source-separated self-report, evidence review, deterministic and provenance-bearing exploration, retrieval-grounded explanation, and explicit cross-module confirmation boundaries. It is not a claim that each individual algorithm is novel.

### N7. Does local ElevenLabs success prove production readiness?

No. It proves that the configured local token, permission, WebRTC, transcription, response, and fallback path worked in a real regression. Production readiness requires target-environment networking, provider controls, observability, scaling, security, and operational review.

### N8. What if the user has no evidence?

The platform should show limited evidence and unresolved gaps, not infer inability or invent proof. It can suggest learning or a small reversible experiment while preserving uncertainty.

### N9. What if all providers fail?

Deterministic domain workflows and persisted records remain available, and text Coach has bounded local fallbacks for supported questions. Live voice, embeddings, external market data, and generative answers may degrade, but the application should communicate that state instead of fabricating availability.
