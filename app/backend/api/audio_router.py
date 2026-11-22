import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.backend.schemas.audio_schema import TranscribeResponse, SynthesizeRequest, SynthesizeResponse
from app.backend.services.audio_service import audio_service
from app.backend.core.security import SecurityValidator
from app.backend.core.config import settings
from app.backend.utils.file_storage import FileStorageManager
from app.backend.utils.logger import logger

router = APIRouter(prefix="/api/audio", tags=["Audio Services"])

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio_file(file: UploadFile = File(...)):
    """Transcribes an uploaded voice audio file to text."""
    content = await file.read()
    SecurityValidator.validate_audio(file.filename, content, file.content_type)
    
    ext = file.filename.split(".")[-1]
    _, audio_path = FileStorageManager.save_audio(content, ext=f".{ext}")
    
    text = await audio_service.transcribe_audio(audio_path)
    return TranscribeResponse(
        text=text,
        audio_path=audio_path
    )

@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_text_to_audio(payload: SynthesizeRequest):
    """Synthesizes text into natural spoken speech (MP3)."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    try:
        audio_id, audio_path = await audio_service.synthesize_speech(
            text=payload.text,
            voice=payload.voice
        )
        filename = os.path.basename(audio_path)
        audio_url = f"/api/audio/file/{filename}"
        return SynthesizeResponse(audio_url=audio_url)
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file/{filename}")
def stream_audio_file(filename: str):
    """Streams a synthesized audio file."""
    # Sanitize filename
    safe_name = os.path.basename(filename)
    file_path = Path(settings.AUDIO_DIR) / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path=file_path, media_type="audio/mpeg", filename=safe_name)
