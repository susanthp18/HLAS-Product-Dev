"""
Conversation History Models

Pydantic models for conversation history storage and management.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class MessageType(Enum):
    """Type of message in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""
    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session identifier")
    message_type: MessageType = Field(..., description="Type of message")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Message timestamp")
    
    # Additional metadata for assistant messages
    confidence_score: Optional[float] = Field(None, description="Confidence score for assistant responses")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="Citations used in response")
    processing_time_ms: Optional[float] = Field(None, description="Processing time for assistant responses")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456",
                "session_id": "session_abc123",
                "message_type": "user",
                "content": "What is the windscreen excess for car insurance?",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ConversationSession(BaseModel):
    """Conversation session containing multiple messages"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier if available")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session start time")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last activity timestamp")
    message_count: int = Field(0, description="Number of messages in session")
    is_active: bool = Field(True, description="Whether session is active")
    
    # Session metadata
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="User IP address")
    platform: Optional[str] = Field(None, description="Platform (web, whatsapp, etc.)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "user_id": "user_456",
                "start_time": "2024-01-15T10:00:00Z",
                "last_activity": "2024-01-15T10:30:00Z",
                "message_count": 4,
                "is_active": True,
                "platform": "web"
            }
        }


class ConversationHistory(BaseModel):
    """Complete conversation history for a session"""
    session: ConversationSession = Field(..., description="Session information")
    messages: List[ConversationMessage] = Field(default_factory=list, description="List of messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session": {
                    "session_id": "session_abc123",
                    "start_time": "2024-01-15T10:00:00Z",
                    "last_activity": "2024-01-15T10:30:00Z",
                    "message_count": 2,
                    "is_active": True,
                    "platform": "web"
                },
                "messages": [
                    {
                        "message_id": "msg_1",
                        "session_id": "session_abc123",
                        "message_type": "user",
                        "content": "What is car insurance?",
                        "timestamp": "2024-01-15T10:00:00Z"
                    },
                    {
                        "message_id": "msg_2",
                        "session_id": "session_abc123",
                        "message_type": "assistant",
                        "content": "Car insurance provides financial protection...",
                        "timestamp": "2024-01-15T10:00:05Z",
                        "confidence_score": 0.95,
                        "processing_time_ms": 1250.5
                    }
                ]
            }
        }


class ConversationSummary(BaseModel):
    """Summary statistics for conversation history"""
    total_sessions: int = Field(..., description="Total number of sessions")
    total_messages: int = Field(..., description="Total number of messages")
    active_sessions: int = Field(..., description="Number of active sessions")
    average_session_length: float = Field(..., description="Average messages per session")
    date_range: Dict[str, str] = Field(..., description="Date range of conversations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 150,
                "total_messages": 600,
                "active_sessions": 12,
                "average_session_length": 4.0,
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-15T23:59:59Z"
                }
            }
        }
