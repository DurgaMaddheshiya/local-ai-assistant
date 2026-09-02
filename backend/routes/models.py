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
from ..services.cloud_llm import OPENAI_MODELS, GEMINI_MODELS, CLAUDE_MODELS, get_provider
from ..models.database_models import get_setting, set_setting

logger = logging.getLogger(__name__)

router = APIRouter()

CLOUD_MODELS = (
    [{"name": m, "provider": "openai", "size": "☁️ 🌐"} for m in OPENAI_MODELS] +
    [{"name": m, "provider": "gemini", "size": "☁️ 🌐"} for m in GEMINI_MODELS] +
    [{"name": m, "provider": "claude", "size": "☁️ 🌐"} for m in CLAUDE_MODELS]
)


@router.get("/models", response_model=ModelResponse)
async def get_available_models():
    """
    Get list of available models - local (Ollama) + cloud (OpenAI/Gemini/Claude)
    Returns cloud models even if Ollama is offline.
    """
    models = []

    # Try Ollama - but don't fail if it's offline
    try:
        ollama_service = OllamaService()
        connection_status = await ollama_service.check_connection()
        
        if connection_status["status"] == "connected":
            models_data = await ollama_service.get_models()
            for model_data in models_data:
                models.append(ModelInfo(
                    name=model_data["name"],
                    size=model_data.get("size"),
                    modified_at=model_data.get("modified_at"),
                    digest=model_data.get("digest"),
                    details=model_data.get("details")
                ))
        else:
            logger.warning(f"Ollama offline: {connection_status.get('error', 'unknown')}")
    except Exception as e:
        logger.warning(f"Ollama unavailable: {e}")

    # Always append cloud models (available regardless of Ollama)
    for cm in CLOUD_MODELS:
        models.append(ModelInfo(
            name=cm["name"],
            size=cm["size"],
            details={"provider": cm["provider"], "cloud": True}
        ))

    if not models:
        # Fallback - return at least cloud models as placeholder
        models.append(ModelInfo(name="gemini-1.5-flash", size="☁️ 🌐"))

    return ModelResponse(models=models)


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
        # Check if cloud model - no Ollama validation needed
        provider = get_provider(request.model)
        if provider != "ollama":
            set_setting(db, "current_model", request.model)
            return {
                "message": f"Model changed to {request.model}",
                "model": request.model,
                "provider": provider
            }

        ollama_service = OllamaService()
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