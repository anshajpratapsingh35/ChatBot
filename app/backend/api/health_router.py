from fastapi import APIRouter
from app.backend.database.connection import check_db_health
from app.backend.core.config import settings

router = APIRouter(tags=["Health & Status"])

@router.get("/api/health")
def health_check():
    """Returns real-time status of backend services, DB connectivity, and configured AI models."""
    db_status = check_db_health()
    
    return {
        "status": "healthy" if db_status.get("connected") else "degraded",
        "app_env": settings.APP_ENV,
        "database": db_status,
        "ai_provider": {
            "configured_provider": settings.AI_PROVIDER,
            "chat_model": settings.CHAT_MODEL,
            "vision_model": settings.VISION_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "gemini_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
            "openai_configured": bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here")
        },
        "tts_engine": settings.TTS_ENGINE,
        "emotion_support_enabled": settings.EMOTION_SUPPORT_ENABLED,
        "safety_filter_enabled": settings.SAFETY_FILTER_ENABLED
    }
