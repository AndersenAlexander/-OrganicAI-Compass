# OrganicAI Compass User-Context Question Sources

This policy is intentionally outside `backend/knowledge_base`, so it is not indexed as if it contained facts about a particular user. Static Knowledge Base material explains the platform; authenticated persisted records answer questions containing "my", "for me", or an equivalent request for personal state.

| Question pattern | Required source | Missing-data behavior |
| --- | --- | --- |
| What is OrganicAI Compass? | `STATIC_KB` | State that Knowledge Base context is unavailable if retrieval cannot support the answer. |
| How does deterministic scoring work? | `STATIC_KB` | Do not substitute an invented formula. |
| What is my current career direction? | `CAREER_HYPOTHESIS` | Say that no active persisted hypothesis is available. |
| What is my strongest career hypothesis? | `CAREER_HYPOTHESIS` | Report only active persisted hypotheses and preserve uncertainty. |
| What is still unresolved for my direction? | `CAREER_HYPOTHESIS` | Use persisted unresolved gaps; do not invent a gap. |
| What evidence has been practically verified? / What evidence has been practically verified for me? | `EVIDENCE_PASSPORT` | Say that no practically verified evidence is present in current context. |
| Which skills still need verification? | `EVIDENCE_PASSPORT` | Use persisted evidence gaps or state that none are available. |
| What is in my Evidence Passport? | `EVIDENCE_PASSPORT` | Summarize only persisted evidence and confidence states. |
| Which experiment did I complete? | `EXPERIMENT` | Use persisted experiment sessions and results. |
| What did that experiment verify? | `EXPERIMENT` | Use the persisted deterministic result and evidence-created metadata; completion alone is not verification. |
| What is my next useful experiment? | `EXPERIMENT` | Use a persisted recommendation if available; otherwise offer to open the experiment workflow without claiming it is saved. |
| What is in my roadmap? | `ROADMAP` | Use persisted roadmap actions or say no roadmap is available. |
| What is my next roadmap action? | `ROADMAP` | Use current action status and priority, not a generic Knowledge Base suggestion. |
| What applications do I currently have? | `EMPLOYMENT_JOURNEY` | Use persisted application records and statuses. |
| What interview stage am I in? | `EMPLOYMENT_JOURNEY` | Use the latest persisted interview record. |
| Do I have an offer review? | `EMPLOYMENT_JOURNEY` | Use persisted offer-review state only. |
| What decision did I record? | `DECISION_JOURNAL` | Use persisted journal entries and keep system suggestions separate from the user decision. |
| What are my strengths or values? | `USER_PROFILE` | Use the owned active profile or state that profile context is unavailable. |

Mixed questions should preserve both boundaries. For example, "What does Evidence Strength mean, and what is mine?" needs the definition from `STATIC_KB` and the user's value from `EVIDENCE_PASSPORT` or the current `CAREER_HYPOTHESIS`; if the persisted value is missing, only the definition may be answered.
