from __future__ import annotations


def processing_summary() -> dict:
    return {
        "provider": "OpenAI",
        "paths": [
            {"path": "chat-or-responses", "purpose": "coach response generation", "persistentObject": "not configured by OrganicAI"},
            {"path": "transcription", "purpose": "voice message transcription", "persistentObject": "not configured by OrganicAI"},
            {"path": "embeddings", "purpose": "RAG retrieval", "persistentObject": "local embedding cache only"},
        ],
        "retentionStatus": "manual-review-required",
        "deletionCapability": "retention-policy-only",
        "zeroRetentionStatus": "unknown",
    }
