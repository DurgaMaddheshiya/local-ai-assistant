"""
Database initialization utilities
"""
import logging
from ..database import init_database, get_database_info
from ..config import settings, ensure_directories
from .database_models import Setting, set_setting, get_setting

logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize the database and create default settings"""
    logger.info("Initializing database...")
    
    # Ensure directories exist
    ensure_directories(settings)
    
    # Initialize database
    init_database()
    
    # Set up default settings
    setup_default_settings()
    
    logger.info("Database initialization complete")


def setup_default_settings():
    """Set up default application settings in the database"""
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        default_settings = {
            "current_model": settings.ollama_model,
            "temperature": str(settings.default_temperature),
            "max_tokens": str(settings.default_max_tokens),
            "context_length": str(settings.default_context_length),
            "system_prompt": settings.default_system_prompt,
            "theme": "light",  # Default theme
            "app_version": settings.app_version
        }
        
        for key, value in default_settings.items():
            existing_setting = get_setting(db, key)
            if existing_setting is None:
                set_setting(db, key, value)
                logger.info(f"Set default setting: {key} = {value}")
        
    except Exception as e:
        logger.error(f"Error setting up default settings: {e}")
    finally:
        db.close()


def check_database_status():
    """Check database status and return information"""
    try:
        db_info = get_database_info()
        logger.info(f"Database status: {db_info['status']}")
        return db_info
    except Exception as e:
        logger.error(f"Error checking database status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # Initialize logging
    from ..config import setup_logging
    setup_logging(settings)
    
    # Initialize database
    initialize_database()
    
    # Check status
    status = check_database_status()
    print(f"Database status: {status}")