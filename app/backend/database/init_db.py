from app.backend.database.connection import get_engine
from app.backend.models.base import Base
import app.backend.models # noqa: F401
from app.backend.utils.logger import logger

def init_db():
    """Initializes tables in database."""
    engine = get_engine()
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")

if __name__ == "__main__":
    init_db()
