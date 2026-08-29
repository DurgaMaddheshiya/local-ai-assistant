"""
System status and information endpoints
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db, check_database_health
from ..schemas import SystemStatus
from ..services.llm import OllamaService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """
    Get comprehensive system status including Ollama and model status
    """
    try:
        # Check database
        db_healthy = await check_database_health()
        
        # Check Ollama service
        ollama_service = OllamaService()
        ollama_status = await ollama_service.check_connection()
        
        # Get current model status
        current_model = "unknown"
        if ollama_status["status"] == "connected":
            model_info = await ollama_service.get_current_model()
            current_model = model_info.get("name", "unknown")
        
        return SystemStatus(
            backend="ok",
            ollama=ollama_status["status"],
            model=current_model,
            mode="local",
            database="ok" if db_healthy else "error",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"System status error: {e}")
        return SystemStatus(
            backend="error",
            ollama="error",
            model="unknown",
            mode="local",
            database="error",
            timestamp=datetime.utcnow()
        )