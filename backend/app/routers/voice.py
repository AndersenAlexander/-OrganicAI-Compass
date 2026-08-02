import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.speech_to_text import transcribe_audio
from app.services.text_to_speech import synthesize_speech

router = APIRouter()


class TranscriptionResponse(BaseModel):
    transcript: str


class SpeechRequest(BaseModel):
    text: str


class SpeechResponse(BaseModel):
    audio_url: str


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(file: UploadFile = File(...)) -> TranscriptionResponse:
    suffix = Path(file.filename or "voice-message.webm").suffix or ".webm"
    temp_path = ""

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())

        transcript = await transcribe_audio(temp_path)
        return TranscriptionResponse(transcript=transcript)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="We could not transcribe the audio.") from error
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.post("/speak", response_model=SpeechResponse)
async def speak(request: SpeechRequest) -> SpeechResponse:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required.")

    try:
        audio_url = await synthesize_speech(request.text)
        return SpeechResponse(audio_url=audio_url)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="The voice response could not be generated.") from error
