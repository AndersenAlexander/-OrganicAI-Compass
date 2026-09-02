# OrganicAI Compass Knowledge Base Audit

## Scope and existing knowledge

The RAG directory contains 19 Markdown documents. Seventeen legacy documents cover responsible AI, AI literacy, methodology, privacy and voice data, talent discovery, assessment, evidence, Career Resilience, learning, market/application workflows, interview guidance, and contextual support material. The current index contains 196 chunks with unique IDs and source metadata.

The presentation layer already adds two canonical documents: `organicai_compass_master_knowledge.md` (41 numbered platform sections) and `organicai_compass_defence_qa.md` (110 defence and demo questions). The Coach already has an explicit grounding policy, persisted profile-context assembly, semantic retrieval, lexical fallback, and a provider-safe deterministic response path. ElevenLabs runs either as a native Agent with externally synchronized static knowledge or, when deliberately configured, through the Custom LLM endpoint.

## Duplicate and outdated material

The legacy assessment, evidence, Career Resilience, market/application, interview, privacy/voice, methodology, and responsible-AI documents overlap with the canonical documents. They remain useful supporting retrieval material, but the master knowledge and defence bank are the presentation source of truth; no legacy document should be treated as a competing user-state source.

The README previously described the Coach as searching static knowledge before every answer. That was too broad for personal questions. The Knowledge Base screen previously called every relevance score semantic even though lexical fallback is an intended mode. Both descriptions have been aligned with runtime behavior.

## Missing topics and implementation boundary

Before this grounding pass, user-context routing existed as policy but static chunks were still fetched and inserted into the generation prompt for personal questions. The Coach now skips static retrieval for those questions and supplies only authenticated persisted context. This covers profile, career hypotheses, Evidence Passport, experiments, roadmap, employment journey, and Decision Journal state without allowing the KB to invent it.

Native ElevenLabs Agents cannot consume OrganicAI's local RAG index at runtime. Their static canonical knowledge must be synchronized through the ElevenLabs Agent configuration. Native mode must state that personal state is unavailable unless a configured Custom LLM path supplies authenticated context.

## Deliberate exclusions

No document claims clinical validity, psychometric validity, hiring prediction, employment suitability, legal eligibility, current labour-market truth, fairness certification, production readiness, or guaranteed outcomes. Live provider behavior and provider-side retention settings remain deployment-specific verification work.
