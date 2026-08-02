from openai import AsyncOpenAI

from app.config import get_settings


async def transcribe_audio(file_path: str) -> str:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Voice service is not configured.")

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    with open(file_path, "rb") as audio_file:
        transcription = await client.audio.transcriptions.create(
            model=settings.openai_transcription_model,
            file=audio_file,
        )

    return transcription.text.strip()
