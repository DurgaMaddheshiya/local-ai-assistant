"""
Model manager service — tracks the active model and validates availability
"""
import logging
from typing import Dict, List, Optional
from .llm import OllamaService
from ..config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages local model selection and availability checks"""

    def __init__(self):
        self._ollama = OllamaService()

    async def list_available(self) -> List[Dict]:
        """Return models currently installed in Ollama"""
        return await self._ollama.get_models()

    async def is_model_available(self, model_name: str) -> bool:
        """Check whether a specific model is installed"""
        models = await self.list_available()
        available = [m["name"] for m in models]
        return model_name in available

    async def get_recommended_model(self) -> Optional[str]:
        """
        Return the configured model if available,
        otherwise return the first installed model, or None.
        """
        models = await self.list_available()
        if not models:
            return None

        names = [m["name"] for m in models]
        if settings.ollama_model in names:
            return settings.ollama_model

        return names[0]

    async def validate_model(self, model_name: str) -> Dict:
        """
        Validate that a model is installed and return status info.
        Returns a dict with 'valid', 'model', and optional 'suggestion'.
        """
        available = await self.list_available()
        names = [m["name"] for m in available]

        if model_name in names:
            return {"valid": True, "model": model_name}

        suggestion = names[0] if names else None
        return {
            "valid": False,
            "model": model_name,
            "available_models": names,
            "suggestion": suggestion,
            "install_command": f"ollama pull {model_name}"
        }
