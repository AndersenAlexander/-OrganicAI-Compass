import uuid
from pathlib import Path

import httpx

from app.config import get_settings

VOICE_DIR = Path("app/media/voice")


async def synthesize_speech(text: str) -> str:
    settings = get_settings()
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise RuntimeError("Voice service is not configured.")

    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"response-{uuid.uuid4()}.mp3"
    output_path = VOICE_DIR / filename
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"

    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {
            "stability": 0.55,
            "similarity_boost": 0.75,
            "style": 0.25,
            "use_speaker_boost": True,
        },
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        output_path.write_bytes(response.content)

    return f"/media/voice/{filename}"
