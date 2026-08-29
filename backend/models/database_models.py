"""
SQLAlchemy database models for Local AI Assistant
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import relationship
from ..database import Base


def generate_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())


class Conversation(Base):
    """Conversation model for storing chat conversations"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"

    @property
    def message_count(self):
        """Get the count of messages in this conversation"""
        return len(self.messages) if self.messages else 0

    def get_messages_for_context(self, limit: int = 50):
        """Get messages for AI context, excluding system messages from history"""
        if not self.messages:
            return []
        
        # Get recent messages, excluding system messages from the middle
        # Keep the latest system message if it exists
        messages = sorted(self.messages, key=lambda m: m.created_at)
        
        # Find the most recent system message
        system_messages = [m for m in messages if m.role == "system"]
        user_assistant_messages = [m for m in messages if m.role in ["user", "assistant"]]
        
        # Take the last system message (if any) and recent user/assistant messages
        context_messages = []
        if system_messages:
            context_messages.append(system_messages[-1])
        
        # Add recent user/assistant messages
        context_messages.extend(user_assistant_messages[-limit:])
        
        # Sort by creation time
        return sorted(context_messages, key=lambda m: m.created_at)


class Message(Base):
    """Message model for storing individual chat messages"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # system, user, assistant, tool
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"

    @property
    def content_preview(self):
        """Get a preview of the message content (first 100 characters)"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."


class Setting(Base):
    """Settings model for storing application configuration"""
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value[:50]}...)>"


# Utility functions for database operations
def create_conversation(db, title: str, model: str) -> Conversation:
    """Create a new conversation"""
    conversation = Conversation(
        title=title,
        model=model
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def create_message(db, conversation_id: str, role: str, content: str) -> Message:
    """Create a new message"""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update conversation timestamp
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = datetime.utcnow()
        db.commit()
    
    return message


def get_conversation_with_messages(db, conversation_id: str) -> Conversation:
    """Get a conversation with its messages"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_conversations_list(db, limit: int = 50, offset: int = 0):
    """Get a list of conversations ordered by most recent"""
    return db.query(Conversation)\
        .order_by(Conversation.updated_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()


def search_conversations(db, query: str, limit: int = 20):
    """Search conversations by title or message content"""
    search_term = f"%{query}%"
    
    # Search by title
    title_results = db.query(Conversation)\
        .filter(Conversation.title.ilike(search_term))\
        .order_by(Conversation.updated_at.desc())\
        .limit(limit)\
        .all()
    
    # Search by message content
    message_results = db.query(Conversation)\
        .join(Message)\
        .filter(Message.content.ilike(search_term))\
        .order_by(Conversation.updated_at.desc())\
        .limit(limit)\
        .all()
    
    # Combine and deduplicate results
    seen_ids = set()
    combined_results = []
    
    for conv in title_results + message_results:
        if conv.id not in seen_ids:
            seen_ids.add(conv.id)
            combined_results.append(conv)
    
    return combined_results[:limit]


def update_conversation_title(db, conversation_id: str, new_title: str) -> bool:
    """Update conversation title"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.title = new_title
        conversation.updated_at = datetime.utcnow()
        db.commit()
        return True
    return False


def delete_conversation(db, conversation_id: str) -> bool:
    """Delete a conversation and all its messages"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False


def get_setting(db, key: str, default_value: str = None) -> str:
    """Get a setting value"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else default_value


def set_setting(db, key: str, value: str) -> Setting:
    """Set a setting value"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
    else:
        setting = Setting(key=key, value=value)
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    return setting


def delete_all_conversations(db) -> int:
    """Delete all conversations and messages (for clear data functionality)"""
    count = db.query(Conversation).count()
    db.query(Message).delete()
    db.query(Conversation).delete()
    db.commit()
    return count


def get_conversation_stats(db):
    """Get conversation statistics"""
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(Message).count()
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages
    }