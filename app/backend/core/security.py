import os
from typing import Tuple
from fastapi import HTTPException, UploadFile, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.backend.core.config import settings
from app.backend.utils.logger import logger

# Initialize SlowAPI rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])

# Magic bytes signatures for file verification
MAGIC_SIGNATURES = {
    # PDF starts with %PDF-
    "pdf": [b"%PDF-"],
    # DOCX is a zip file starting with PK\x03\x04
    "docx": [b"PK\x03\x04"],
    # JPEG starts with \xFF\xD8\xFF
    "jpeg": [b"\xFF\xD8\xFF"],
    "jpg": [b"\xFF\xD8\xFF"],
    # PNG starts with \x89PNG\r\n\x1a\n
    "png": [b"\x89PNG\r\n\x1a\n"],
    # WEBP starts with RIFF....WEBP
    "webp": [b"RIFF"],
    # Audio WAV starts with RIFF....WAVE
    "wav": [b"RIFF"],
    # MP3 ID3 header or sync word
    "mp3": [b"ID3", b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2"],
}

class SecurityValidator:
    @staticmethod
    def validate_file_size(content: bytes, max_mb: int = None) -> bool:
        max_bytes = (max_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum allowed size of {max_mb or settings.MAX_UPLOAD_SIZE_MB}MB."
            )
        return True

    @staticmethod
    def validate_document(filename: str, content: bytes, content_type: str = None) -> Tuple[bool, str]:
        SecurityValidator.validate_file_size(content)
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        if ext not in ["pdf", "docx", "txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported document format '.{ext}'. Supported formats are: PDF, DOCX, TXT."
            )

        # Signature verification for binary types
        if ext in MAGIC_SIGNATURES:
            signatures = MAGIC_SIGNATURES[ext]
            header = content[:16]
            if not any(header.startswith(sig) for sig in signatures):
                raise HTTPException(
                    status_code=400,
                    detail=f"File content signature does not match expected {ext.upper()} format."
                )

        return True, ext

    @staticmethod
    def validate_image(filename: str, content: bytes, content_type: str = None) -> Tuple[bool, str]:
        SecurityValidator.validate_file_size(content, max_mb=10)
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format '.{ext}'. Supported: JPG, JPEG, PNG, WEBP."
            )

        if ext in MAGIC_SIGNATURES:
            signatures = MAGIC_SIGNATURES[ext]
            header = content[:16]
            if not any(header.startswith(sig) for sig in signatures):
                raise HTTPException(
                    status_code=400,
                    detail=f"Image signature mismatch. Corrupted or invalid {ext.upper()} file."
                )

        return True, ext

    @staticmethod
    def validate_audio(filename: str, content: bytes, content_type: str = None) -> Tuple[bool, str]:
        SecurityValidator.validate_file_size(content, max_mb=25)
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        if ext not in ["wav", "mp3", "ogg", "m4a", "webm"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format '.{ext}'. Supported: WAV, MP3, OGG, M4A, WEBM."
            )
        return True, ext
