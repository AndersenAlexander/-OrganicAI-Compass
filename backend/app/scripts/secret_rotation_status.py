from __future__ import annotations

import json

from app.config import active_provider_secret, get_settings
from app.db.url import redact_database_url
from app.services.secret_readiness import SECRET_SPECS, _is_placeholder, classify_secret


MIN_LENGTHS = {
    "SECRET_KEY": 32,
    "DATABASE_URL": 12,
    "OPENAI_API_KEY": 20,
    "ELEVENLABS_API_KEY": 20,
    "ELEVENLABS_AGENT_ID": 8,
    "ELEVENLABS_WEBHOOK_SECRET": 32,
    "CUSTOM_LLM_SECRET": 32,
    "WEBHOOK_SECRET": 32,
    "DATA_EXPORT_ENCRYPTION_KEY": 32,
    "DELETION_LEDGER_HMAC_KEY": 32,
    "EMAIL_PROVIDER_SECRET": 12,
    "SMTP_PASSWORD": 12,
}


def main() -> int:
    settings = get_settings()
    items = []
    blocking = 0
    for name, (attr, attestation_attr) in SECRET_SPECS.items():
        value = getattr(settings, attr, None)
        configured_value = active_provider_secret(value)
        classification = classify_secret(name, settings)
        min_length = MIN_LENGTHS.get(name, 1)
        item = {
            "name": name,
            "configured": configured_value is not None,
            "placeholder": _is_placeholder(str(value)),
            "minimumLengthPassed": bool(configured_value and len(str(configured_value)) >= min_length),
            "rotationEvidencePresent": bool(getattr(settings, attestation_attr)) if attestation_attr else None,
            "status": classification.status,
            "blocking": classification.blocking,
        }
        if name == "DATABASE_URL":
            item["redactedUrl"] = redact_database_url(str(value or ""))
        if classification.blocking:
            blocking += 1
        items.append(item)
    payload = {
        "formatVersion": 1,
        "environment": settings.app_env,
        "status": "passed" if blocking == 0 else "blocked",
        "blockingFindingCount": blocking,
        "items": items,
        "secretValuesIncluded": False,
    }
    print(json.dumps(payload, indent=2))
    return 0 if blocking == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
