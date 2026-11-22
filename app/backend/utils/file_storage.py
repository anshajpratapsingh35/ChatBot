import hashlib
import os
import uuid
from pathlib import Path
from typing import Tuple
from app.backend.core.config import settings
from app.backend.utils.logger import logger

class FileStorageManager:
    """Safely manages local file persistence, uniqueness, hashing, and cleanup."""

    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def save_document(filename: str, content: bytes) -> Tuple[str, str, str]:
        """
        Saves a document file safely.
        Returns: (file_id, absolute_path, sha256_hash)
        """
        sha256_hash = FileStorageManager.calculate_sha256(content)
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        safe_filename = f"{file_id}{ext}"
        target_path = Path(settings.DOCUMENTS_DIR) / safe_filename
        
        with open(target_path, "wb") as f:
            f.write(content)
            
        logger.info(f"Saved document '{filename}' as '{safe_filename}' (SHA-256: {sha256_hash[:8]}...)")
        return file_id, str(target_path), sha256_hash

    @staticmethod
    def save_image(filename: str, content: bytes) -> Tuple[str, str]:
        """
        Saves an uploaded image.
        Returns: (image_id, absolute_path)
        """
        image_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower() or ".png"
        safe_filename = f"{image_id}{ext}"
        target_path = Path(settings.IMAGES_DIR) / safe_filename
        
        with open(target_path, "wb") as f:
            f.write(content)
            
        logger.info(f"Saved image as '{safe_filename}'")
        return image_id, str(target_path)

    @staticmethod
    def save_audio(content: bytes, ext: str = ".mp3") -> Tuple[str, str]:
        """
        Saves an audio clip (recorded voice or synthesized speech).
        Returns: (audio_id, absolute_path)
        """
        audio_id = str(uuid.uuid4())
        if not ext.startswith("."):
            ext = f".{ext}"
        safe_filename = f"{audio_id}{ext}"
        target_path = Path(settings.AUDIO_DIR) / safe_filename
        
        with open(target_path, "wb") as f:
            f.write(content)
            
        logger.info(f"Saved audio as '{safe_filename}'")
        return audio_id, str(target_path)

    @staticmethod
    def delete_file(filepath: str) -> bool:
        """Deletes file if it exists."""
        try:
            p = Path(filepath)
            if p.exists() and p.is_file():
                p.unlink()
                logger.info(f"Deleted file: {filepath}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {filepath}: {e}")
        return False
