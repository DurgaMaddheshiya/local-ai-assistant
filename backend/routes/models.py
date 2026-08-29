"""
Model management endpoints
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import ModelResponse, ModelInfo, ModelSelectionRequest
from ..services.llm import OllamaService
from ..models.database_models import get_setting, set_setting

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models", response_model=ModelResponse)
async def get_available_models():
    """
    Get list of available local models
    """
    try:
        ollama_service = OllamaService()
        
        # Check Ollama connection first
        connection_status = await ollama_service.check_connection()
        if connection_status["status"] != "connected":
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Ollama service unavailable",
                    "detail": connection_status.get("error", "Unknown error"),
                    "ollama_host": settings.ollama_host
                }
            )
        
        # Get models
        models_data = await ollama_service.get_models()
        
        models = []
        for model_data in models_data:
            models.append(ModelInfo(
                name=model_data["name"],
                size=model_data.get("size"),
                modified_at=model_data.get("modified_at"),
                digest=model_data.get("digest"),
                details=model_data.get("details")
            ))
        
        return ModelResponse(models=models)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve models",
                "detail": str(e)
            }
        )


@router.get("/models/current")
async def get_current_model(db: Session = Depends(get_db)):
    """
    Get currently selected model
    """
    try:
        # Get from database settings
        current_model = get_setting(db, "current_model", settings.ollama_model)
        
        ollama_service = OllamaService()
        ollama_service.current_model = current_model
        
        # Get model info
        model_info = await ollama_service.get_current_model()
        
        return {
            "current_model": current_model,
            "model_info": model_info,
            "default_model": settings.ollama_model
        }
        
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get current model",
                "detail": str(e)
            }
        )


@router.post("/models/select")
async def select_model(
    request: ModelSelectionRequest, 
    db: Session = Depends(get_db)
):
    """
    Select a model to use for chat
    """
    try:
        ollama_service = OllamaService()
        
        # Check if model exists
        success = await ollama_service.set_model(request.model)
        
        if not success:
            # Get available models for error message
            available_models = await ollama_service.get_models()
            model_names = [m["name"] for m in available_models]
            
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Model not found",
                    "detail": f"Model '{request.model}' is not available",
                    "available_models": model_names
                }
            )
        
        # Save to database
        set_setting(db, "current_model", request.model)
        
        logger.info(f"Model selected: {request.model}")
        
        return {
            "message": f"Model changed to {request.model}",
            "model": request.model,
            "previous_model": settings.ollama_model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting model: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to select model",
                "detail": str(e)
            }
        )