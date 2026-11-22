from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.backend.core.config import settings
from app.backend.utils.logger import logger

engine = None
SessionLocal = None
active_dialect = None

def get_engine():
    global engine, SessionLocal, active_dialect
    if engine is not None:
        return engine

    mysql_url = settings.get_database_url()
    try:
        logger.info(f"Connecting to MySQL database at {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}...")
        test_engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 2}
        )
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = test_engine
        active_dialect = "mysql"
        logger.info("Successfully connected to MySQL server.")
    except Exception as e:
        if settings.DB_FALLBACK_SQLITE:
            sqlite_path = f"{settings.STORAGE_DIR}/companion.db"
            logger.warning(
                f"MySQL connection failed ({e}). Falling back to local SQLite at {sqlite_path} "
                "for seamless offline/local development."
            )
            engine = create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False}
            )
            active_dialect = "sqlite"
        else:
            logger.error(f"Failed to connect to MySQL database: {e}")
            raise e

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session management."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def check_db_health() -> dict:
    """Verifies database connectivity."""
    try:
        curr_engine = get_engine()
        with curr_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "dialect": active_dialect or curr_engine.dialect.name,
            "connected": True
        }
    except Exception as err:
        return {
            "status": "unhealthy",
            "error": str(err),
            "connected": False
        }
