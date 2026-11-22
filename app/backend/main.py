from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.backend.core.config import settings
from app.backend.core.security import limiter
from app.backend.database.init_db import init_db
from app.backend.api.chat_router import router as chat_router
from app.backend.api.document_router import router as document_router
from app.backend.api.audio_router import router as audio_router
from app.backend.api.health_router import router as health_router
from app.backend.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and warmup."""
    logger.info("Initializing Multimodal AI Companion Backend...")
    try:
        init_db()
        logger.info("Database schema verified and initialized.")
    except Exception as e:
        logger.error(f"Startup database initialization error: {e}")
    yield
    logger.info("Shutting down Multimodal AI Companion Backend...")

app = FastAPI(
    title="Multimodal AI Companion API",
    description="Enterprise-grade Multimodal AI Platform combining text, vision, audio, RAG, and emotional support.",
    version="1.0.0",
    lifespan=lifespan
)

# Attach SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
origins = [
    f"http://localhost:{settings.FRONTEND_PORT}",
    f"http://127.0.0.1:{settings.FRONTEND_PORT}",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check server logs."}
    )

# Register API Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.include_router(audio_router)

@app.get("/")
def root():
    return {
        "name": "Multimodal AI Companion API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
