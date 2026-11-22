"""
MySQL Database Initialization and Setup Helper.
Run this script to verify your MySQL credentials and create the database schema.
"""
import pymysql
from app.backend.core.config import settings
from app.backend.database.init_db import init_db
from app.backend.utils.logger import logger

def setup_mysql_database():
    logger.info("Attempting to connect to MySQL server to ensure database exists...")
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            logger.info(f"Database `{settings.DB_NAME}` verified/created on MySQL server.")
        conn.close()
        
        # Now run schema migration
        init_db()
        logger.info("All tables successfully generated in MySQL.")
    except Exception as e:
        logger.error(f"Could not initialize MySQL database directly: {e}")
        logger.info("Ensure MySQL service is started (e.g. via XAMPP or Windows Services).")

if __name__ == "__main__":
    setup_mysql_database()
