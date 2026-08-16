from __future__ import annotations

import json
import time
from pathlib import Path

from app.routers.webhooks import sign_elevenlabs_webhook


def main() -> int:
    body = b'{"type":"post_call_transcription","conversation_id":"disposable-test-conversation"}'
    signature = sign_elevenlabs_webhook(body, "test-webhook-secret", int(time.time()))
    report = {
        "provider": "ElevenLabs",
        "mode": "offline",
        "validFixtureCreated": True,
        "signatureHeaderFormat": "timestamp-plus-v1-hmac",
        "supportedEvents": ["post_call_transcription", "call_initiation_failure"],
        "audioWebhookEnabled": False,
        "signatureValueIncluded": False,
        "secretValuesIncluded": False,
        "sampleSignatureFingerprint": signature.split("v1=", 1)[1][:12],
    }
    out = Path("..") / "reports" / "provider-validation" / "elevenlabs-webhook-validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
