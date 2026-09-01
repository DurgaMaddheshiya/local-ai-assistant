"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    model_config = {"from_attributes": True}


# Message schemas
class MessageBase(BaseSchema):
    """Base message schema"""
    role: str = Field(..., description="Message role: system, user, assistant, tool")
    content: str = Field(..., description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    conversation_id: str = Field(..., description="Conversation ID")


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: str
    conversation_id: str
    created_at: datetime


# Conversation schemas
class ConversationBase(BaseSchema):
    """Base conversation schema"""
    title: str = Field(..., max_length=200, description="Conversation title")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    model: Optional[str] = Field(None, description="AI model to use")


class ConversationUpdate(BaseSchema):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, max_length=200, description="New title")


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetail(ConversationResponse):
    """Schema for detailed conversation with messages"""
    messages: List[MessageResponse] = []


# Chat schemas
class ChatRequest(BaseSchema):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    model: Optional[str] = Field(None, description="Override default model")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature setting")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    stream: bool = Field(True, description="Enable streaming response")
    incognito: bool = Field(False, description="Incognito mode - do not save to database")


class ChatResponse(BaseSchema):
    """Schema for chat response"""
    conversation_id: str
    message_id: str
    content: str
    model: str
    created_at: datetime


class StreamChunk(BaseSchema):
    """Schema for streaming response chunks"""
    content: str
    done: bool = False
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


# Model schemas
class ModelInfo(BaseSchema):
    """Schema for model information"""
    name: str
    size: Optional[str] = None
    modified_at: Optional[datetime] = None
    digest: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ModelResponse(BaseSchema):
    """Schema for model list response"""
    models: List[ModelInfo] = []


class ModelSelectionRequest(BaseSchema):
    """Schema for model selection request"""
    model: str = Field(..., description="Model name to select")


# Settings schemas
class SettingsResponse(BaseSchema):
    """Schema for settings response"""
    current_model: str
    ollama_host: str
    temperature: float
    max_tokens: int
    context_length: int
    system_prompt: str


class SettingsUpdate(BaseSchema):
    """Schema for updating settings"""
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    system_prompt: Optional[str] = None


# System schemas
class SystemStatus(BaseSchema):
    """Schema for system status"""
    backend: str = "ok"
    ollama: str
    model: str
    mode: str = "local"
    database: str = "ok"
    timestamp: datetime


class HealthResponse(BaseSchema):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str
    details: Optional[Dict[str, Any]] = None


# Error schemas
class ErrorResponse(BaseSchema):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime