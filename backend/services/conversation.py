"""
Conversation management service
"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from ..models.database_models import (
    Conversation, Message, create_conversation, create_message,
    get_conversation_with_messages, update_conversation_title
)

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and message history"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_new_conversation(self, title: str, model: str) -> Conversation:
        """Create a new conversation"""
        return create_conversation(self.db, title, model)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        """Add a message to a conversation"""
        return create_message(self.db, conversation_id, role, content)
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation with its messages"""
        return get_conversation_with_messages(self.db, conversation_id)
    
    def update_title(self, conversation_id: str, new_title: str) -> bool:
        """Update conversation title"""
        return update_conversation_title(self.db, conversation_id, new_title)
    
    def get_context_messages(
        self, 
        conversation_id: str, 
        limit: int = 20,
        include_system: bool = True
    ) -> List[Dict]:
        """Get messages formatted for LLM context"""
        
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = []
        
        # Get recent messages
        context_messages = conversation.get_messages_for_context(limit)
        
        for msg in context_messages:
            # Include or exclude system messages based on parameter
            if msg.role == "system" and not include_system:
                continue
                
            messages.append({
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
        
        return messages
    
    def format_messages_for_display(self, conversation_id: str) -> List[Dict]:
        """Format messages for frontend display"""
        
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        formatted_messages = []
        
        for msg in sorted(conversation.messages, key=lambda m: m.created_at):
            formatted_messages.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "preview": msg.content_preview
            })
        
        return formatted_messages
    
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation"""
        
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return {}
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "model": conversation.model,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": conversation.message_count,
            "last_message_preview": (
                conversation.messages[-1].content_preview 
                if conversation.messages 
                else None
            )
        }
    
    def auto_generate_title(self, conversation_id: str) -> bool:
        """Auto-generate a title from the first user message"""
        
        conversation = self.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return False
        
        # Find the first user message
        first_user_message = None
        for msg in sorted(conversation.messages, key=lambda m: m.created_at):
            if msg.role == "user":
                first_user_message = msg
                break
        
        if not first_user_message:
            return False
        
        # Generate title from message
        new_title = self._generate_title_from_message(first_user_message.content)
        
        # Update if different from current title and not already customized
        if new_title != conversation.title and conversation.title == "New Conversation":
            return self.update_title(conversation_id, new_title)
        
        return False
    
    def _generate_title_from_message(self, message: str, max_length: int = 50) -> str:
        """Generate a conversation title from a message"""
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
    
    def cleanup_old_conversations(self, keep_count: int = 100) -> int:
        """Clean up old conversations, keeping the most recent ones"""
        
        try:
            # Get all conversations ordered by update time (newest first)
            conversations = self.db.query(Conversation)\
                .order_by(Conversation.updated_at.desc())\
                .all()
            
            if len(conversations) <= keep_count:
                return 0
            
            # Delete oldest conversations
            conversations_to_delete = conversations[keep_count:]
            deleted_count = 0
            
            for conv in conversations_to_delete:
                self.db.delete(conv)
                deleted_count += 1
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} old conversations")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up conversations: {e}")
            self.db.rollback()
            return 0