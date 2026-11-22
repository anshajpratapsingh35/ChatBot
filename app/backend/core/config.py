import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_ENV: str = "development"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    FRONTEND_PORT: int = 8501
    DEBUG: bool = True

    # Database
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "multimodal_companion_db"
    DATABASE_URL: Optional[str] = None
    DB_FALLBACK_SQLITE: bool = True

    # Storage
    STORAGE_DIR: str = str(BASE_DIR / "app" / "storage")
    DOCUMENTS_DIR: str = str(BASE_DIR / "app" / "storage" / "documents")
    IMAGES_DIR: str = str(BASE_DIR / "app" / "storage" / "images")
    AUDIO_DIR: str = str(BASE_DIR / "app" / "storage" / "audio")
    MAX_UPLOAD_SIZE_MB: int = 25

    # Allowed File Types
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/webp", "image/jpg"
    ]
    ALLOWED_DOC_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/m4a", "audio/webm", "audio/x-m4a"
    ]

    # AI Provider
    AI_PROVIDER: str = "gemini"  # "gemini" or "openai"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Model Configuration
    CHAT_MODEL: str = "gemini-2.0-flash"
    VISION_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSIONS: int = 768

    # RAG settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    SIMILARITY_THRESHOLD: float = 0.55
    TOP_K_CHUNKS: int = 4

    # Audio Engine
    TTS_ENGINE: str = "edge-tts"  # "edge-tts" or "gtts"
    TTS_VOICE: str = "en-US-AriaNeural"

    # Emotion & Safety
    EMOTION_SUPPORT_ENABLED: bool = True
    SAFETY_FILTER_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        password_part = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        return f"mysql+pymysql://{self.DB_USER}{password_part}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def ensure_directories(self) -> None:
        for path_str in [self.STORAGE_DIR, self.DOCUMENTS_DIR, self.IMAGES_DIR, self.AUDIO_DIR]:
            p = Path(path_str)
            p.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
