"""
Health check endpoints
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db, check_database_health
from ..schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint
    """
    try:
        # Check database
        db_healthy = await check_database_health()
        
        # Basic response
        return HealthResponse(
            status="healthy" if db_healthy else "unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            details={
                "database": "ok" if db_healthy else "error",
                "backend": "ok"
            }
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            details={
                "error": str(e),
                "database": "error",
                "backend": "error"
            }
        )