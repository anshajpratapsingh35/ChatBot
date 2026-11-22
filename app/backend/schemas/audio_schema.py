from typing import Optional
from pydantic import BaseModel

class TranscribeResponse(BaseModel):
    text: str
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = None
    audio_path: Optional[str] = None

class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None

class SynthesizeResponse(BaseModel):
    audio_url: str
    duration_estimate: Optional[float] = None
