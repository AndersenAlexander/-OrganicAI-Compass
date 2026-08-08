from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    transcript: str


class SpeechRequest(BaseModel):
    text: str


class SpeechResponse(BaseModel):
    audio_url: str
