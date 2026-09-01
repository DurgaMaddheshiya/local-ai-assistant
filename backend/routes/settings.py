"""
Settings management endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SettingsResponse, SettingsUpdate
from ..models.database_models import get_setting, set_setting
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _mask_key(key: str) -> str:
    """Return masked version for display, empty string if not set."""
    if not key:
        return ""
    return key[:4] + "••••••••" + key[-4:] if len(key) > 8 else "••••••••"


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Get current application settings
    """
    try:
        current_settings = SettingsResponse(
            current_model=get_setting(db, "current_model", settings.ollama_model),
            ollama_host=settings.ollama_host,
            temperature=float(get_setting(db, "temperature", str(settings.default_temperature))),
            max_tokens=int(get_setting(db, "max_tokens", str(settings.default_max_tokens))),
            context_length=int(get_setting(db, "context_length", str(settings.default_context_length))),
            system_prompt=get_setting(db, "system_prompt", settings.default_system_prompt),
            openai_api_key=_mask_key(get_setting(db, "openai_api_key", "")),
            gemini_api_key=_mask_key(get_setting(db, "gemini_api_key", "")),
            claude_api_key=_mask_key(get_setting(db, "claude_api_key", "")),
        )
        
        return current_settings
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve settings",
                "detail": str(e)
            }
        )


@router.patch("/settings")
async def update_settings(
    updates: SettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application settings
    """
    try:
        updated_fields = []
        
        # Update model if provided
        if updates.model is not None:
            set_setting(db, "current_model", updates.model)
            updated_fields.append("model")
        
        # Update temperature if provided
        if updates.temperature is not None:
            set_setting(db, "temperature", str(updates.temperature))
            updated_fields.append("temperature")
        
        # Update max_tokens if provided
        if updates.max_tokens is not None:
            set_setting(db, "max_tokens", str(updates.max_tokens))
            updated_fields.append("max_tokens")
        
        # Update system prompt if provided
        if updates.system_prompt is not None:
            set_setting(db, "system_prompt", updates.system_prompt)
            updated_fields.append("system_prompt")

        # Update API keys if provided (only save if non-empty and not masked)
        if updates.openai_api_key is not None and "••" not in updates.openai_api_key:
            set_setting(db, "openai_api_key", updates.openai_api_key)
            updated_fields.append("openai_api_key")

        if updates.gemini_api_key is not None and "••" not in updates.gemini_api_key:
            set_setting(db, "gemini_api_key", updates.gemini_api_key)
            updated_fields.append("gemini_api_key")

        if updates.claude_api_key is not None and "••" not in updates.claude_api_key:
            set_setting(db, "claude_api_key", updates.claude_api_key)
            updated_fields.append("claude_api_key")
        
        # Get updated settings
        updated_settings = SettingsResponse(
            current_model=get_setting(db, "current_model", settings.ollama_model),
            ollama_host=settings.ollama_host,
            temperature=float(get_setting(db, "temperature", str(settings.default_temperature))),
            max_tokens=int(get_setting(db, "max_tokens", str(settings.default_max_tokens))),
            context_length=int(get_setting(db, "context_length", str(settings.default_context_length))),
            system_prompt=get_setting(db, "system_prompt", settings.default_system_prompt),
            openai_api_key=_mask_key(get_setting(db, "openai_api_key", "")),
            gemini_api_key=_mask_key(get_setting(db, "gemini_api_key", "")),
            claude_api_key=_mask_key(get_setting(db, "claude_api_key", "")),
        )
        
        return {
            "message": "Settings updated successfully",
            "updated_fields": updated_fields,
            "settings": updated_settings
        }
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to update settings",
                "detail": str(e)
            }
        )


@router.get("/settings/theme")
async def get_theme(db: Session = Depends(get_db)):
    """
    Get current theme setting
    """
    try:
        theme = get_setting(db, "theme", "light")
        return {"theme": theme}
        
    except Exception as e:
        logger.error(f"Error getting theme: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get theme",
                "detail": str(e)
            }
        )


@router.post("/settings/theme")
async def set_theme(
    theme: str,
    db: Session = Depends(get_db)
):
    """
    Set theme (light/dark)
    """
    try:
        if theme not in ["light", "dark"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid theme",
                    "detail": "Theme must be 'light' or 'dark'"
                }
            )
        
        set_setting(db, "theme", theme)
        
        return {
            "message": f"Theme set to {theme}",
            "theme": theme
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting theme: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to set theme",
                "detail": str(e)
            }
        )