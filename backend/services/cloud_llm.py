"""
Cloud LLM service - supports OpenAI, Google Gemini, Anthropic Claude
Routes requests to appropriate provider based on model name prefix.
"""
import asyncio
import json
import logging
import os
import random
import time
from typing import AsyncGenerator, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

# Model prefix mapping
OPENAI_MODELS  = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
GEMINI_MODELS  = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
CLAUDE_MODELS  = ["claude-3-5-sonnet", "claude-3-5-haiku", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]


def get_provider(model: str) -> str:
    """Detect provider from model name."""
    m = model.lower()
    if any(m.startswith(x) for x in ["gpt-", "o1-", "o3-"]):
        return "openai"
    if m.startswith("gemini"):
        return "gemini"
    if m.startswith("claude"):
        return "claude"
    return "ollama"


def get_stealth_headers():
    """Generate randomized headers to avoid detection"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    ]
    
    # Use custom agent from environment if set by launcher
    stealth_agent = os.environ.get('STEALTH_USER_AGENT', random.choice(user_agents))
    
    headers = {
        "User-Agent": stealth_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }
    
    return headers


async def stealth_delay():
    """Random delay to avoid pattern detection"""
    base_delay = float(os.environ.get('STEALTH_DELAY', '0.2'))
    actual_delay = base_delay + random.uniform(0.05, 0.3)
    await asyncio.sleep(actual_delay)


class CloudLLMService:
    """Routes LLM requests to OpenAI / Gemini / Claude."""

    def __init__(self, openai_key: str = "", gemini_key: str = "", claude_key: str = ""):
        self.openai_key = openai_key
        self.gemini_key = gemini_key
        self.claude_key = claude_key

    # ── OpenAI ────────────────────────────────────────────────────────────

    async def _stream_openai(
        self, messages: List[Dict], model: str,
        temperature: float, max_tokens: int
    ) -> AsyncGenerator[Dict, None]:
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
            **get_stealth_headers()  # Add stealth headers
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            await stealth_delay()  # Random delay
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST",
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers, json=payload
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        yield {"error": f"OpenAI error {resp.status_code}: {body.decode()}", "done": True}
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield {"content": "", "done": True, "model": model}
                                return
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                done  = chunk["choices"][0].get("finish_reason") is not None
                                if delta:
                                    yield {"content": delta, "done": done, "model": model}
                                if done:
                                    return
                            except Exception:
                                continue
        except Exception as e:
            yield {"error": str(e), "done": True}

    # ── Gemini ────────────────────────────────────────────────────────────

    async def _stream_gemini(
        self, messages: List[Dict], model: str,
        temperature: float, max_tokens: int,
        images: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict, None]:
        # Convert messages to Gemini format
        contents = []
        system_text = ""
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            elif m["role"] == "user":
                # If this is the last user message and we have images, add them
                parts = [{"text": m["content"]}]
                if images and m == messages[-1]:  # Only add images to latest user message
                    for img_b64 in images:
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_b64
                            }
                        })
                contents.append({"role": "user", "parts": parts})
            elif m["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": m["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": min(max_tokens, 8192),  # Gemini max limit is 8192
            }
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        # Use generateContent (non-streaming) and chunk manually for better compatibility
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
        
        try:
            await stealth_delay()  # Random delay
            async with httpx.AsyncClient(
                timeout=120,
                headers=get_stealth_headers()  # Add stealth headers
            ) as client:
                resp = await client.post(url, json=payload)
                
                if resp.status_code != 200:
                    error_body = resp.text
                    yield {"error": f"Gemini error {resp.status_code}: {error_body}", "done": True}
                    return
                
                result = resp.json()
                candidates = result.get("candidates", [])
                if not candidates:
                    yield {"error": "No response from Gemini", "done": True}
                    return
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts or "text" not in parts[0]:
                    yield {"error": "Invalid response format from Gemini", "done": True}
                    return
                
                full_text = parts[0]["text"]
                
                # Chunk the response for streaming effect (send 10 chars at a time)
                chunk_size = 10
                for i in range(0, len(full_text), chunk_size):
                    chunk = full_text[i:i + chunk_size]
                    is_done = (i + chunk_size >= len(full_text))
                    yield {"content": chunk, "done": is_done, "model": model}
                    if not is_done:
                        # Small delay for streaming effect
                        await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            yield {"error": str(e), "done": True}

    # ── Claude ────────────────────────────────────────────────────────────

    async def _stream_claude(
        self, messages: List[Dict], model: str,
        temperature: float, max_tokens: int,
        images: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict, None]:
        system_text = ""
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m["content"]
            else:
                # If this is the last user message and we have images, format with images
                if m["role"] == "user" and images and m == messages[-1]:
                    content_blocks = [{"type": "text", "text": m["content"]}]
                    for img_b64 in images:
                        content_blocks.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64
                            }
                        })
                    api_messages.append({"role": "user", "content": content_blocks})
                else:
                    api_messages.append({"role": m["role"], "content": m["content"]})

        headers = {
            "x-api-key": self.claude_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            **get_stealth_headers()  # Add stealth headers
        }
        payload = {
            "model": model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if system_text:
            payload["system"] = system_text

        try:
            await stealth_delay()  # Random delay
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST",
                    "https://api.anthropic.com/v1/messages",
                    headers=headers, json=payload
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        yield {"error": f"Claude error {resp.status_code}: {body.decode()}", "done": True}
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                chunk = json.loads(line[6:])
                                if chunk.get("type") == "content_block_delta":
                                    text = chunk.get("delta", {}).get("text", "")
                                    if text:
                                        yield {"content": text, "done": False, "model": model}
                                elif chunk.get("type") == "message_stop":
                                    yield {"content": "", "done": True, "model": model}
                                    return
                            except Exception:
                                continue
        except Exception as e:
            yield {"error": str(e), "done": True}

    # ── Public API ────────────────────────────────────────────────────────

    async def generate_response(
        self, messages: List[Dict], model: str,
        temperature: float = 0.7, max_tokens: int = 2048,
        images: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict, None]:
        provider = get_provider(model)

        if provider == "openai":
            if not self.openai_key:
                yield {"error": "OpenAI API key not set. Add it in Settings → API Keys.", "done": True}
                return
            # Attach images to last user message if provided
            if images:
                msgs = list(messages)
                for i in range(len(msgs) - 1, -1, -1):
                    if msgs[i]["role"] == "user":
                        msgs[i] = {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": msgs[i]["content"]},
                                *[{"type": "image_url",
                                   "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                                  for img in images]
                            ]
                        }
                        break
                messages = msgs
            async for chunk in self._stream_openai(messages, model, temperature, max_tokens):
                yield chunk

        elif provider == "gemini":
            if not self.gemini_key:
                yield {"error": "Gemini API key not set. Add it in Settings → API Keys.", "done": True}
                return
            async for chunk in self._stream_gemini(messages, model, temperature, max_tokens, images):
                yield chunk

        elif provider == "claude":
            if not self.claude_key:
                yield {"error": "Claude API key not set. Add it in Settings → API Keys.", "done": True}
                return
            async for chunk in self._stream_claude(messages, model, temperature, max_tokens, images):
                yield chunk

        else:
            yield {"error": f"Unknown cloud provider for model: {model}", "done": True}
