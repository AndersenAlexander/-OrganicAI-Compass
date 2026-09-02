from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import get_settings

INTENDED = {
    "audioSaving": "disabled",
    "transcriptRetention": "minimum-operational-or-scheduled-deletion",
    "zeroRetention": "preferred-when-available",
    "postCallAudioWebhook": "disabled",
    "postCallTranscriptWebhook": "enabled-only-when-required",
    "webhookAuthentication": "hmac-required",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-agent-id", default="")
    parser.add_argument("--confirmation-text", default="")
    args = parser.parse_args()
    settings = get_settings()
    apply_allowed = (
        args.apply
        and settings.elevenlabs_privacy_configuration_apply_enabled
        and args.confirm_agent_id
        and args.confirm_agent_id == (settings.elevenlabs_agent_id or "")
        and args.confirmation_text == "APPLY ORGANICAI ELEVENLABS PRIVACY SETTINGS"
    )
    report = {
        "mode": "apply" if args.apply else "dry-run",
        "applyExecuted": bool(apply_allowed),
        "intended": INTENDED,
        "actual": {
            "audioSaving": settings.elevenlabs_audio_saving_status,
            "transcriptRetention": settings.elevenlabs_retention_status,
            "zeroRetention": settings.elevenlabs_zero_retention_status,
            "webhookAuthentication": "configured" if settings.elevenlabs_webhook_secret else "unknown",
        },
        "comparison": "manual-action-required",
        "agentModified": False,
        "secretValuesIncluded": False,
    }
    out = Path("..") / "reports" / "provider-validation" / "elevenlabs-privacy-diff.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not args.apply or apply_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
