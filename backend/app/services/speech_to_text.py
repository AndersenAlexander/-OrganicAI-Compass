from openai import AsyncOpenAI

from app.config import get_settings, resolve_active_openai_api_key


async def transcribe_audio(file_path: str) -> str:
    settings = get_settings()
    api_key = resolve_active_openai_api_key(settings)
    if not api_key:
        raise RuntimeError("Voice service is not configured.")

    client = AsyncOpenAI(api_key=api_key, timeout=30.0, max_retries=1)
    with open(file_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(
            model=settings.openai_transcription_model,
            file=audio_file,
        )

    return transcription.text.strip()
