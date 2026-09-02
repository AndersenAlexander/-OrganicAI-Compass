from __future__ import annotations

import re
from typing import Literal


GroundingSource = Literal[
    "STATIC_KB",
    "USER_PROFILE",
    "CAREER_HYPOTHESIS",
    "EVIDENCE_PASSPORT",
    "EXPERIMENT",
    "ROADMAP",
    "EMPLOYMENT_JOURNEY",
    "DECISION_JOURNAL",
]


COACH_GROUNDING_POLICY = """
OrganicAI Coach grounding policy:
- Deterministic scores come from versioned application rules, never from the LLM. The LLM may explain but must not calculate or alter them.
- Separate platform facts, persisted user facts, and AI suggestions. Label a suggestion as a suggestion.
- Separate self-report, learning exposure, demonstrated evidence, and practically verified evidence.
- A career direction is a provisional hypothesis, not a prediction, diagnosis, suitability verdict, or hiring probability.
- Never claim employment suitability and never make an irreversible career decision for the user.
- State uncertainty when evidence or context is insufficient.
- For user-context questions, use only authenticated persisted context supplied by the application. If it is absent, say the information is unavailable; never fill it from static Knowledge Base text.
- For platform questions, use the retrieved OrganicAI Knowledge Base and do not invent features or external facts.
- Do not fabricate labour-market facts, vacancies, employer behavior, legal eligibility, provider state, or user records.
- Suggestions cannot confirm evidence, apply roadmap changes, record outcomes, or become user decisions without the explicit application action.
- Keep answers concise and conversational. Live-voice answers should normally be shorter than text answers and should not read technical metadata aloud.
""".strip()


_USER_CONTEXT_PATTERNS: tuple[tuple[GroundingSource, tuple[str, ...]], ...] = (
    (
        "DECISION_JOURNAL",
        (
            r"\bmy decision journal\b",
            r"\bwhat (?:career )?decision did i\b",
            r"\bwhat did i decide(?: and why)?\b",
            r"\bwhy did i decide\b",
            r"\bmy recorded decision\b",
        ),
    ),
    (
        "EMPLOYMENT_JOURNEY",
        (
            r"\bmy applications?\b",
            r"\bapplications? do i (?:currently )?have\b",
            r"\bmy interview (?:stage|status|journey)\b",
            r"\bwhat interview stage am i in\b",
            r"\bmy offer reviews?\b",
        ),
    ),
    (
        "ROADMAP",
        (
            r"\b(?:show|summarise|summarize) my roadmap\b",
            r"\bwhat is in my (?:current )?roadmap\b",
            r"\bmy next roadmap action\b",
        ),
    ),
    (
        "EXPERIMENT",
        (
            r"\bwhich experiment did i\b",
            r"\bwhat did (?:that|my) experiment verify\b",
            r"\bmy (?:completed|current|next|latest) experiment\b",
            r"\bnext useful experiment for me\b",
            r"\bwhat is my next useful experiment\b",
            r"\bwhat experiment should reduce that uncertainty\b",
        ),
    ),
    (
        "EVIDENCE_PASSPORT",
        (
            r"\bwhat evidence has been (?:practically )?verified(?: for (?:me|my))?\b",
            r"\bwhat (?:practically )?verified evidence do i have\b",
            r"\bwhich (?:of my )?skills? (?:still )?(?:need|needs) verification\b",
            r"\b(?:what|which) (?:of my )?evidence gaps? (?:still )?remain\b",
            r"\b(?:what|which) (?:important )?(?:of my )?evidence gaps? (?:are )?(?:still )?unresolved\b",
            r"\bmy evidence passport\b",
            r"\bmy (?:verified|demonstrated|self-reported) evidence\b",
        ),
    ),
    (
        "CAREER_HYPOTHESIS",
        (
            r"\bmy current career direction\b",
            r"\bmy current career hypothesis\b",
            r"\bmy strongest career hypothesis\b",
            r"\bwhich career hypothesis is (?:currently )?strongest\b",
            r"\bwhat is still unresolved for my (?:current )?(?:career )?(?:direction|hypothesis)\b",
            r"\bwhat is still unresolved\b",
        ),
    ),
    (
        "USER_PROFILE",
        (
            r"\bmy (?:current )?(?:strengths|values|profile|archetype|learning preferences?)\b",
            r"\bwhat does my profile say\b",
        ),
    ),
)


_SOURCE_CONTEXT_KEYS: dict[GroundingSource, str] = {
    "USER_PROFILE": "the top-level persisted profile fields",
    "CAREER_HYPOTHESIS": "career_evidence.current_hypotheses and career_evidence.unresolved_gaps",
    "EVIDENCE_PASSPORT": "career_evidence.practically_verified_skill_ids and career_evidence.unresolved_gaps",
    "EXPERIMENT": "career_evidence.recent_experiments",
    "ROADMAP": "roadmap_state and roadmap",
    "EMPLOYMENT_JOURNEY": "employment_journey",
    "DECISION_JOURNAL": "decision_journal",
    "STATIC_KB": "retrieved Knowledge Base sources",
}


def classify_grounding_source(message: str) -> GroundingSource:
    normalized = " ".join(message.lower().split())
    for source, patterns in _USER_CONTEXT_PATTERNS:
        if any(re.search(pattern, normalized) for pattern in patterns):
            return source
    return "STATIC_KB"


def grounding_source_instruction(source: GroundingSource) -> str:
    if source == "STATIC_KB":
        return (
            "Answer from retrieved Knowledge Base sources. Persisted profile context may personalize a clearly labelled "
            "suggestion, but it must not replace the platform facts."
        )
    return (
        f"This is a user-context question. Use only {_SOURCE_CONTEXT_KEYS[source]} from the authenticated compact profile "
        "context. If the required record is empty or absent, say it is unavailable. Do not infer an answer from static "
        "Knowledge Base text."
    )
