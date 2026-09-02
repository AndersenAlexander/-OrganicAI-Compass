# OrganicAI Compass — Presentation Coach Script

Use the explicit Demo Mode profile only. It is synthetic, resettable data with reviewed experiment material; do not describe it as participant evidence or a real person's career record. Keep text answers to one or three sentences and use voice only for short platform explanations or clearly available personal context.

## A. 3–4 minute demo

| Question | Expected source | Demonstrate / say |
| --- | --- | --- |
| What is OrganicAI Compass? | `STATIC_KB` | Human-centred master's research prototype joining reflection, deterministic hypotheses, evidence, experiments, roadmap, employment preparation, and grounded coaching. It is decision support, not a hiring or career-decision system. |
| Why was this platform created? | `STATIC_KB` | It explores whether grounded AI, reflection, visible evidence, and practical action can support agency during AI-related career change. It does not claim improved employment outcomes. |
| Does the LLM calculate my career scores? | `STATIC_KB` | No. Versioned application rules calculate stored dimensions; the Coach can only explain them. |
| What is my current career hypothesis? | `CAREER_HYPOTHESIS` | Read the active persisted hypothesis and call it a testable direction, never a prediction. |
| What evidence has been practically verified for my current direction? | `EVIDENCE_PASSPORT` | Read only persisted Evidence Passport state and distinguish it from self-report. |
| Can you choose my career for me? | `STATIC_KB` | No. The Coach can compare evidence, values, uncertainty, and reversible experiments; the final decision remains human. |

## B. 8–10 minute full demonstration

Start in Demo Mode, open `/coach/demo-profile`, and keep the browser Network panel visible if appropriate. The demo profile contains a reviewed career experiment and synthetic persisted evidence. The source column is the required routing boundary, not merely a preferred topic.

| # | Question | Required source | Answer concepts / oral check |
| --- | --- | --- | --- |
| 1 | What is OrganicAI Compass? | `STATIC_KB` | Human-centred research prototype; career exploration and preparation; user remains in control. |
| 2 | Why was this platform created? | `STATIC_KB` | Research purpose: agency, grounded AI, reflection, evidence, and action; no outcome claim. |
| 3 | Does the LLM calculate my career scores? | `STATIC_KB` | No; scoring is deterministic, versioned application logic. The LLM may explain, never calculate or alter scores. |
| 4 | What is my current career hypothesis? | `CAREER_HYPOTHESIS` | Active persisted direction only; provisional and testable, not a prediction. |
| 5 | What evidence has been practically verified for my current direction? | `EVIDENCE_PASSPORT` | Persisted verified skill IDs or an honest unavailable response; do not infer evidence from the KB. |
| 6 | Which evidence gaps remain unresolved? | `EVIDENCE_PASSPORT` | Persisted active-hypothesis gaps only; a gap is uncertainty to investigate, not proof of inability. |
| 7 | What experiment should reduce that uncertainty? | `EXPERIMENT` | Inspect persisted experiments and linked gaps/results. Do not present a generic static recommendation as a saved experiment. |
| 8 | What happens after an experiment is reviewed? | `STATIC_KB` | Deterministic evaluation can create an evidence proposal; user review/confirmation is still required before authoritative evidence and bounded recalibration. |
| 9 | How does Evidence Passport differ from self-reported skills? | `STATIC_KB` | Passport records provenance, confidence, recency, and verification state; self-report is one weaker evidence category, not practical verification. |
| 10 | Can you choose my career for me? | `STATIC_KB` | No final choice or suitability verdict; compare evidence, values, trade-offs, and reversible next steps. |
| 11 | What is the Human-AI Growth Roadmap? | `STATIC_KB` | Editable seven-day, thirty-day, and six-month actions. Proposals require explicit user application or editing. |
| 12 | Why did you use RAG rather than fine-tuning? | `STATIC_KB` | Curated facts stay inspectable, updateable, attributable, and bounded without training a model on changing documentation. RAG still has retrieval limitations. |
| 13 | What happens if OpenAI is unavailable? | `STATIC_KB` | The Coach uses its safe local fallback where supported; deterministic workflow data remains available and the UI reports degradation rather than fabricating a provider result. |
| 14 | What role does ElevenLabs play? | `STATIC_KB` | Optional live WebRTC audio: microphone transport, turn detection, transcription, speech, and interruption. OrganicAI controls authentication, tokens, text fallback, and the Custom-LLM boundary. |
| 15 | What are the main limitations of this prototype? | `STATIC_KB` | No participant-outcome, psychometric, hiring-validity, fairness, or production-readiness proof; provider, market, retrieval, operations, and external review limits remain explicit. |

### Source-routing rehearsal rule

For questions 4–7, the HTTP response should expose the specified `question_source` in `retrieval_status`, return no static KB sources for the personal-state answer, and report `retrieval_mode: not_requested`. If the required persisted record is absent, the correct answer is that it is unavailable—not a generic platform explanation.

After question 7, refresh the Coach page and repeat questions 4-7. Each response must continue to use the demo profile's persisted hypothesis, Evidence Passport, and experiment state. Do not confuse chat-history display settings with persisted workflow state.

## C. Examiner challenge questions

These are answer concepts, not a marketing script. Answer from the implementation and state uncertainty where evidence is missing.

| # | Examiner question | Expected answer concepts |
| --- | --- | --- |
| 1 | What is scientifically novel about this platform? | Integrated, inspectable architecture linking source-separated reflection, deterministic hypotheses, evidence review, experiments, RAG explanation, and user confirmation; not a claim that every component is novel. |
| 2 | What is rule-based versus AI-generated? | Scores, experiment evaluation, lifecycle states, ownership checks, and persistence rules are deterministic; AI explains, drafts, reflects, and proposes. |
| 3 | Why not use a standard psychometric career test? | The prototype is a transparent self-reflection workflow, not a clinical or proprietary psychometric instrument; it does not claim psychometric validity. |
| 4 | What prevents confirmation bias? | Visible supporting and caution signals, uncertainty, separate evidence categories, competing hypotheses, reversible experiments, and user correction reduce—not eliminate—confirmation bias. |
| 5 | How do you know recommendations are correct? | The prototype does not claim correctness; it exposes inputs and trade-offs and requires evaluation with users and outcomes. |
| 6 | How do you validate practical evidence? | Observable work, deterministic rubric support, provenance, and explicit review; completion, a course, or polished AI text alone is insufficient. |
| 7 | Why is one experiment not enough to prove competence? | A bounded task samples limited behaviour and context; repeated, independent, and relevant evidence is needed before stronger claims. |
| 8 | How does recalibration work? | Reviewed deterministic experiment evidence can update the linked hypothesis' Evidence Strength and bounded Capability Fit; it does not silently change Natural Fit or make a decision. |
| 9 | Can an LLM manipulate the score indirectly? | It has no score-writing authority. It may explain inputs, but evidence, experiments, roadmap changes, and decisions require governed application actions. |
| 10 | Are weights scientifically validated? | No; they are versioned, transparent prototype rules for inspection and challenge, not probabilities or validated causal models. |
| 11 | Why separate Natural Fit from Capability Fit? | Preferences and values answer a different question from current skills and experience; separation exposes trade-offs and avoids conflating interest with competence. |
| 12 | Why is Evidence Strength separate from capability? | A claimed capability and support for that claim are distinct. Evidence provenance and verification must remain visible. |
| 13 | Can market demand override personal preference? | No. Market observations are separate, bounded context and cannot rewrite preference-based Natural Fit. |
| 14 | Why call a result a hypothesis? | It is provisional, testable, versioned, and revisable; it is not a career prediction, diagnosis, or hiring judgment. |
| 15 | What prevents an experiment from becoming an automatic career commitment? | Explicit review and confirmation boundaries; completed work creates a proposal, not a final decision or automatic roadmap mutation. |
| 16 | What happens when evidence conflicts? | Preserve provenance and uncertainty, show the conflict, and seek additional or corrected evidence rather than averaging it into false certainty. |
| 17 | What happens when all current gaps are closed? | The system reports that state; it does not infer mastery, employability, or a final career choice. Further independent evidence may still matter. |
| 18 | How are self-report and demonstrated work distinguished? | They have separate evidence types, confidence labels, provenance, recency, and verification requirements. |
| 19 | What does the Evidence Passport persist? | Evidence records, sources, confidence/strength labels, recency, role relationships, and outstanding verification needs. |
| 20 | Does the Coach change the Evidence Passport? | No. The Coach has no authority to create verified evidence; relevant workflow actions require user confirmation. |
| 21 | What happens after an experiment is reviewed? | Deterministic results can create reviewable evidence proposals and bounded recalibration inputs; user confirmation remains the authority boundary. |
| 22 | How are experiment rubrics explained? | Criteria, weights, outputs, and limitations are visible as deterministic prototype logic, not hidden employer assessment. |
| 23 | What does RAG add beyond a system prompt? | Retrieval supplies query-relevant, source-attributed, updateable documentation and allows insufficiency handling; it does not make a model infallible. |
| 24 | What happens when RAG retrieval is wrong? | The answer should be bounded or insufficient, sources remain inspectable, and feedback/evaluation can identify retrieval failures. Human review is still needed. |
| 25 | What does lexical fallback change? | It substitutes transparent term-overlap retrieval when embeddings are unavailable; it is less semantic and must be communicated as a limitation. |
| 26 | Why RAG rather than fine-tuning? | The KB can be audited, updated, constrained, and attributed without encoding mutable platform facts into model weights. |
| 27 | Can RAG eliminate hallucinations? | No. It improves grounding and traceability but can retrieve weak context or be misused; policies, thresholds, tests, and review remain necessary. |
| 28 | How are prompt injections handled? | Retrieved text is treated as untrusted reference material behind a protected instruction boundary; suspicious content is screened and low-quality context is rejected. |
| 29 | Why use ElevenLabs? | It provides the optional continuous conversational WebRTC layer; the platform keeps authentication, token minting, fallback, and data-boundary control. |
| 30 | Why not use only OpenAI voice? | Provider choice is an architectural trade-off. This prototype demonstrates ElevenLabs live conversation while preserving text and voice-message fallbacks rather than claiming universal provider superiority. |
| 31 | Does ElevenLabs receive the OpenAI key? | No. Provider credentials remain server-side; native ElevenLabs and Custom-LLM deployments have distinct boundaries. |
| 32 | Does voice interaction change scoring? | No. Voice is an interaction modality; deterministic domain scoring does not change because a question was spoken. |
| 33 | How is privacy protected? | Authentication and ownership checks, server-side secrets, consent/preferences, data minimisation, transcript controls, export/deletion workflows, and documented provider boundaries. |
| 34 | What would GDPR deployment require? | A lawful-basis and data-flow review, notices, retention/deletion handling, processor agreements, transfer analysis, security measures, rights handling, and legal review; none are claimed complete by the prototype. |
| 35 | What are the risks of career recommendation systems? | Overconfidence, bias, automation pressure, privacy leakage, stale market data, and unequal access; this design uses uncertainty, evidence separation, explainability, and human control as mitigations. |
| 36 | How would you evaluate fairness? | Define protected groups and outcomes ethically, obtain appropriate data and consent, test error and access disparities, audit qualitative harms, and avoid treating synthetic fixtures as fairness proof. |
| 37 | What metrics would a real longitudinal study use? | Task completion, usability, source comprehension, perceived agency, calibrated trust, evidence quality, action follow-through, harms, and carefully bounded outcome measures. |
| 38 | What would commercial deployment require? | Production database operations, migrations, TLS, secret management, backups, monitoring, incident response, accessibility, security/privacy review, provider validation, governance, and operational ownership. |
| 39 | Is the system production-ready? | No. It is a locally validated research prototype with explicit unresolved operational and empirical work. |
| 40 | Does it predict employment outcomes? | No. It does not estimate hiring, employability, career success, or employer decisions. |
| 41 | Does the profile diagnose psychology or personality? | No. It is reviewable self-report interpretation, not clinical diagnosis or a fixed identity. |
| 42 | Can it auto-apply for jobs or decide an offer? | No. Application and offer workflows are user-controlled decision support with explicit confirmation. |
| 43 | What remains unresolved academically? | Empirical usefulness, trust, agency effects, validity, fairness, and longer-term outcomes require controlled studies. |
| 44 | What wording should be avoided in the defence? | “Predicts,” “proves,” “objective,” “suitable for employment,” “production-ready,” “validated psychometric test,” and any claim that the LLM calculates scores. |

## Presentation safety reminders

- Say “current evidence suggests” or “hypothesis to test,” never “the system predicts your career.”
- Say “practically verified in this persisted demo record,” never “the system proved competence.”
- Say “provider unavailable; text and deterministic workflows remain available where designed,” never imply a failed provider succeeded.
- Do not read API keys, tokens, source IDs, raw prompts, or technical metadata aloud.
- Describe the demo profile as synthetic and resettable; it is not research-participant data.
