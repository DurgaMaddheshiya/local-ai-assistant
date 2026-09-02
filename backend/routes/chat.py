"""
Chat endpoints with streaming support
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ChatRequest, ChatResponse, StreamChunk
from ..services.llm import OllamaService
from ..services.cloud_llm import CloudLLMService, get_provider
from ..services.conversation import ConversationService
from ..models.database_models import (
    get_conversation_with_messages, create_conversation, create_message,
    get_setting
)
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _generate_title_from_message(message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first message"""
    if not message:
        return "New Conversation"
    
    # Clean up the message
    title = message.strip()
    
    # Remove common prefixes
    prefixes_to_remove = ["please", "can you", "could you", "help me", "i want to", "i need to"]
    title_lower = title.lower()
    
    for prefix in prefixes_to_remove:
        if title_lower.startswith(prefix):
            title = title[len(prefix):].strip()
            break
    
    # Capitalize first letter
    if title:
        title = title[0].upper() + title[1:]
    
    # Truncate if too long
    if len(title) > max_length:
        title = title[:max_length-3] + "..."
    
    return title or "New Conversation"


async def _prepare_messages_for_llm(
    db: Session, 
    conversation_id: str, 
    user_message: str
) -> List[Dict]:
    """Prepare message history for LLM including system prompt"""
    
    messages = []
    
    # Add system prompt
    system_prompt = get_setting(db, "system_prompt", settings.default_system_prompt)
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # Get conversation history if conversation exists
    if conversation_id:
        conversation = get_conversation_with_messages(db, conversation_id)
        if conversation and conversation.messages:
            # Get recent messages for context (excluding system messages from history)
            context_messages = conversation.get_messages_for_context(limit=20)
            
            for msg in context_messages:
                if msg.role != "system":  # Don't duplicate system messages
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint with streaming support
    """
    try:
        logger.info(f"Chat request: conversation_id={request.conversation_id}, stream={request.stream}")
        
        # Validate Ollama connection
        ollama_service = OllamaService()
        connection_status = await ollama_service.check_connection()
        
        if connection_status["status"] != "connected":
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI service unavailable",
                    "detail": connection_status.get("error", "Ollama is not running"),
                    "ollama_host": settings.ollama_host
                }
            )
        
        # Get or create conversation (skip in incognito mode)
        conversation_id = request.conversation_id
        conversation = None

        if request.incognito:
            # Incognito: use a temporary in-memory conversation ID, no DB
            conversation_id = conversation_id or f"incognito-{uuid.uuid4().hex[:8]}"
            logger.info(f"Incognito mode - conversation not saved: {conversation_id}")
        elif conversation_id:
            conversation = get_conversation_with_messages(db, conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Conversation not found",
                        "detail": f"No conversation found with ID: {conversation_id}"
                    }
                )
        else:
            # Create new conversation
            title = _generate_title_from_message(request.message)
            current_model = request.model or get_setting(db, "current_model", settings.ollama_model)
            conversation = create_conversation(db, title, current_model)
            conversation_id = conversation.id
            logger.info(f"Created new conversation: {conversation_id}")

        # Save user message (skip in incognito)
        if not request.incognito:
            user_message = create_message(db, conversation_id, "user", request.message)
        
        # Prepare messages for LLM
        messages = await _prepare_messages_for_llm(db, conversation_id, request.message)

        # Get settings
        temperature = request.temperature or float(get_setting(db, "temperature", str(settings.default_temperature)))
        max_tokens = request.max_tokens or int(get_setting(db, "max_tokens", str(settings.default_max_tokens)))
        
        # Validate max_tokens for different providers
        provider = get_provider(request.model or get_setting(db, "current_model", settings.ollama_model))
        if provider == "gemini":
            max_tokens = min(max_tokens, 8192)  # Gemini limit
        elif provider == "claude":  
            max_tokens = min(max_tokens, 4096)  # Claude limit
        elif provider == "openai":
            max_tokens = min(max_tokens, 16384) # GPT-4 limit
        
        model = request.model or get_setting(db, "current_model", settings.ollama_model)

        # Set the model in Ollama service
        await ollama_service.set_model(model)

        # Determine provider and pick service
        provider = get_provider(model)
        if provider != "ollama":
            openai_key = get_setting(db, "openai_api_key", "")
            gemini_key = get_setting(db, "gemini_api_key", "")
            claude_key = get_setting(db, "claude_api_key", "")
            llm_service = CloudLLMService(openai_key, gemini_key, claude_key)
        else:
            llm_service = ollama_service

        if request.stream:
            return StreamingResponse(
                _stream_chat_response(
                    llm_service, messages, conversation_id, db,
                    temperature, max_tokens, model,
                    incognito=request.incognito,
                    images=request.images
                ),
                media_type="text/plain"
            )
        else:
            if provider != "ollama":
                full = ""
                async for chunk in llm_service.generate_response(
                    messages=messages, model=model,
                    temperature=temperature, max_tokens=max_tokens,
                    images=request.images
                ):
                    if "error" in chunk:
                        raise HTTPException(status_code=500, detail={"error": chunk["error"]})
                    full += chunk.get("content", "")
                    if chunk.get("done"):
                        break
                response = {"content": full, "model": model}
            else:
                response = await ollama_service.generate_single_response(
                    messages=messages, model=model,
                    temperature=temperature, max_tokens=max_tokens,
                    images=request.images
                )

            if "error" in response:
                raise HTTPException(
                    status_code=500,
                    detail={"error": "AI generation failed", "detail": response["error"]}
                )

            # Save assistant response (skip in incognito)
            if not request.incognito:
                assistant_message = create_message(db, conversation_id, "assistant", response["content"])
                msg_id = assistant_message.id
            else:
                msg_id = str(uuid.uuid4())

            return ChatResponse(
                conversation_id=conversation_id,
                message_id=msg_id,
                content=response["content"],
                model=response["model"],
                created_at=datetime.utcnow()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Chat processing failed",
                "detail": str(e)
            }
        )


async def _stream_chat_response(
    llm_service,
    messages: List[Dict],
    conversation_id: str,
    db: Session,
    temperature: float,
    max_tokens: int,
    model: str,
    incognito: bool = False,
    images: Optional[List[str]] = None
):
    """Stream chat response chunks"""
    try:
        full_response = ""
        message_id = str(uuid.uuid4())

        async for chunk in llm_service.generate_response(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            images=images
        ):
            if "error" in chunk:
                # Send error chunk
                error_chunk = StreamChunk(
                    content=f"Error: {chunk['error']}",
                    done=True,
                    conversation_id=conversation_id
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
                return
            
            if "content" in chunk:
                content = chunk["content"]
                full_response += content
                
                # Send content chunk
                response_chunk = StreamChunk(
                    content=content,
                    done=chunk.get("done", False),
                    conversation_id=conversation_id,
                    message_id=message_id if chunk.get("done", False) else None
                )
                
                yield f"data: {response_chunk.model_dump_json()}\n\n"
                
                # Save complete response when done
                if chunk.get("done", False):
                    if not incognito:
                        create_message(db, conversation_id, "assistant", full_response)
                        logger.info(f"Saved assistant message: {len(full_response)} characters")
                    else:
                        logger.info(f"Incognito: skipped saving {len(full_response)} chars")
                    break
        
        # Send final done chunk if not already sent
        if not chunk.get("done", False):
            final_chunk = StreamChunk(
                content="",
                done=True,
                conversation_id=conversation_id,
                message_id=message_id
            )
            yield f"data: {final_chunk.model_dump_json()}\n\n"
            
            # Save response if not already saved
            if full_response and not incognito:
                create_message(db, conversation_id, "assistant", full_response)
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        
        # Send error chunk
        error_chunk = StreamChunk(
            content=f"Streaming error: {str(e)}",
            done=True,
            conversation_id=conversation_id
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"


@router.post("/chat/stop")
async def stop_generation(conversation_id: str = None):
    """
    Stop ongoing generation (placeholder for future implementation)
    """
    # Note: In a production system, you'd maintain active generation sessions
    # and provide a way to cancel them. For now, this is a placeholder.
    
    return {
        "message": "Generation stop requested",
        "conversation_id": conversation_id,
        "note": "Stop functionality requires session management (future enhancement)"
    }


@router.get("/chat/models")
async def get_chat_models():
    """
    Get available models for chat (convenience endpoint)
    """
    try:
        ollama_service = OllamaService()
        
        # Check connection
        connection_status = await ollama_service.check_connection()
        if connection_status["status"] != "connected":
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "AI service unavailable",
                    "detail": connection_status.get("error", "Ollama is not running")
                }
            )
        
        models = await ollama_service.get_models()
        
        return {
            "models": models,
            "current_model": ollama_service.current_model,
            "ollama_host": settings.ollama_host
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat models: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get models",
                "detail": str(e)
            }
        )