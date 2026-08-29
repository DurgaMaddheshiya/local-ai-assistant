"""
Conversation management endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    ConversationResponse, ConversationCreate, ConversationUpdate,
    ConversationDetail, MessageResponse
)
from ..models.database_models import (
    get_conversations_list, create_conversation, get_conversation_with_messages,
    update_conversation_title, delete_conversation, search_conversations,
    delete_all_conversations, get_conversation_stats, get_setting
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


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, min_length=1)
):
    """
    Get list of conversations with optional search
    """
    try:
        if search:
            conversations = search_conversations(db, search, limit)
        else:
            conversations = get_conversations_list(db, limit, offset)
        
        result = []
        for conv in conversations:
            result.append(ConversationResponse(
                id=conv.id,
                title=conv.title,
                model=conv.model,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=conv.message_count
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve conversations",
                "detail": str(e)
            }
        )


@router.post("/conversations", response_model=ConversationResponse)
async def create_new_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation
    """
    try:
        # Get current model if not specified
        model = conversation.model or get_setting(db, "current_model", settings.ollama_model)
        
        # Create conversation
        new_conversation = create_conversation(db, conversation.title, model)
        
        return ConversationResponse(
            id=new_conversation.id,
            title=new_conversation.title,
            model=new_conversation.model,
            created_at=new_conversation.created_at,
            updated_at=new_conversation.updated_at,
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to create conversation",
                "detail": str(e)
            }
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation with its messages
    """
    try:
        conversation = get_conversation_with_messages(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Conversation not found",
                    "detail": f"No conversation found with ID: {conversation_id}"
                }
            )
        
        # Convert messages
        messages = []
        for msg in conversation.messages:
            messages.append(MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            ))
        
        # Sort messages by creation time
        messages.sort(key=lambda m: m.created_at)
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            model=conversation.model,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(messages),
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve conversation",
                "detail": str(e)
            }
        )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a conversation (e.g., rename)
    """
    try:
        # Check if conversation exists
        conversation = get_conversation_with_messages(db, conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Conversation not found",
                    "detail": f"No conversation found with ID: {conversation_id}"
                }
            )
        
        # Update title if provided
        if updates.title is not None:
            success = update_conversation_title(db, conversation_id, updates.title)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Failed to update conversation",
                        "detail": "Database update failed"
                    }
                )
        
        # Get updated conversation
        updated_conversation = get_conversation_with_messages(db, conversation_id)
        
        return ConversationResponse(
            id=updated_conversation.id,
            title=updated_conversation.title,
            model=updated_conversation.model,
            created_at=updated_conversation.created_at,
            updated_at=updated_conversation.updated_at,
            message_count=updated_conversation.message_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to update conversation",
                "detail": str(e)
            }
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages
    """
    try:
        success = delete_conversation(db, conversation_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Conversation not found",
                    "detail": f"No conversation found with ID: {conversation_id}"
                }
            )
        
        return {
            "message": "Conversation deleted successfully",
            "conversation_id": conversation_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to delete conversation",
                "detail": str(e)
            }
        )


@router.delete("/conversations")
async def delete_all_conversations_endpoint(
    confirm: bool = Query(False, description="Must be true to confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    Delete all conversations (requires confirmation)
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Confirmation required",
                "detail": "Must set confirm=true to delete all conversations"
            }
        )
    
    try:
        count = delete_all_conversations(db)
        
        return {
            "message": f"Successfully deleted {count} conversations",
            "deleted_count": count
        }
        
    except Exception as e:
        logger.error(f"Error deleting all conversations: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to delete conversations",
                "detail": str(e)
            }
        )


@router.get("/conversations/stats")
async def get_conversation_statistics(db: Session = Depends(get_db)):
    """
    Get conversation and message statistics
    """
    try:
        stats = get_conversation_stats(db)
        
        return {
            "total_conversations": stats["total_conversations"],
            "total_messages": stats["total_messages"],
            "database_path": settings.database_path
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to get statistics",
                "detail": str(e)
            }
        )