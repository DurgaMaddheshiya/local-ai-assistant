"""
Local LLM service using Ollama
"""
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama local LLM"""
    
    def __init__(self):
        self.base_url = settings.ollama_host.rstrip('/')
        self.timeout = settings.ollama_timeout
        self.current_model = settings.ollama_model
    
    async def check_connection(self) -> Dict:
        """Check if Ollama is running and accessible"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "url": self.base_url,
                        "response_time": response.elapsed.total_seconds()
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status_code}",
                        "url": self.base_url
                    }
                    
        except httpx.ConnectError:
            return {
                "status": "disconnected",
                "error": "Connection refused - Ollama may not be running",
                "url": self.base_url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": self.base_url
            }
    
    async def get_models(self) -> List[Dict]:
        """Get list of available models"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    for model in data.get("models", []):
                        models.append({
                            "name": model.get("name"),
                            "size": self._format_size(model.get("size", 0)),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest"),
                            "details": model.get("details", {})
                        })
                    
                    return models
                else:
                    logger.error(f"Failed to get models: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []
    
    async def get_current_model(self) -> Dict:
        """Get information about the current model"""
        try:
            models = await self.get_models()
            
            # Find the current model
            for model in models:
                if model["name"] == self.current_model:
                    return model
            
            # If current model not found, return first available
            if models:
                return models[0]
            
            return {"name": "unknown", "status": "not_found"}
            
        except Exception as e:
            logger.error(f"Error getting current model: {e}")
            return {"name": "error", "error": str(e)}
    
    async def set_model(self, model_name: str) -> bool:
        """Set the current model to use"""
        try:
            # Check if model exists
            models = await self.get_models()
            available_models = [m["name"] for m in models]
            
            if model_name in available_models:
                self.current_model = model_name
                logger.info(f"Model changed to: {model_name}")
                return True
            else:
                logger.error(f"Model not found: {model_name}. Available: {available_models}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting model: {e}")
            return False
    
    async def generate_response(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        images: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict, None]:
        """Generate a response from the LLM using /api/chat (supports multimodal)"""

        model_to_use = model or self.current_model

        # Build messages list for /api/chat
        api_messages = []
        for msg in messages:
            entry = {"role": msg["role"], "content": msg["content"]}
            # Attach images to the last user message
            if images and msg["role"] == "user" and msg is messages[-1]:
                entry["images"] = images
            api_messages.append(entry)

        payload = {
            "model": model_to_use,
            "messages": api_messages,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:

                    if response.status_code != 200:
                        error_msg = f"Ollama API error: HTTP {response.status_code}"
                        logger.error(error_msg)
                        yield {"error": error_msg, "done": True}
                        return

                    full_response = ""

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                # /api/chat returns chunk.message.content
                                content = chunk.get("message", {}).get("content", "")
                                done = chunk.get("done", False)

                                if content:
                                    full_response += content
                                    yield {"content": content, "done": done, "model": model_to_use}

                                if done:
                                    logger.info(f"Generated response length: {len(full_response)}")
                                    break

                            except json.JSONDecodeError as e:
                                logger.error(f"JSON decode error: {e}")
                                continue

        except Exception as e:
            error_msg = f"Error generating response: {e}"
            logger.error(error_msg)
            yield {"error": error_msg, "done": True}
    
    async def generate_single_response(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        images: Optional[List[str]] = None
    ) -> Dict:
        """Generate a complete response (non-streaming)"""

        full_response = ""
        error = None

        async for chunk in self.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            images=images
        ):
            if "error" in chunk:
                error = chunk["error"]
                break
            if "content" in chunk:
                full_response += chunk["content"]
            if chunk.get("done", False):
                break

        if error:
            return {"error": error}

        return {"content": full_response, "model": model or self.current_model}
    
    def _format_messages_for_ollama(self, messages: List[Dict]) -> str:
        """Format conversation messages for Ollama prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add the assistant prompt at the end
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant: "
        return prompt
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"