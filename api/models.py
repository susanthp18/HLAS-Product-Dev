"""
API Data Models

Pydantic models for API request/response validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class QueryRequest(BaseModel):
    """Request model for insurance queries"""
    query: str = Field(..., description="User's insurance question", min_length=1, max_length=500)
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    include_citations: bool = Field(True, description="Whether to include source citations")
    include_confidence: bool = Field(True, description="Whether to include confidence score")
    max_results: int = Field(5, description="Maximum number of context chunks to retrieve", ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the windscreen excess for car insurance?",
                "session_id": "session_abc123",
                "include_citations": True,
                "include_confidence": True,
                "max_results": 5
            }
        }


class CitationResponse(BaseModel):
    """Citation information in API response"""
    id: str
    product_name: str
    document_type: str
    source_file: str
    section_hierarchy: List[str]
    relevance_score: float


class QueryResponse(BaseModel):
    """Response model for insurance queries"""
    answer: str = Field(..., description="Generated answer to the user's question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    citations: List[CitationResponse] = Field(default_factory=list, description="Source citations")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0)")
    context_used: int = Field(..., description="Number of context chunks used in the answer")
    context_available: int = Field(..., description="Total number of context chunks available")
    has_sufficient_context: bool = Field(..., description="Whether sufficient context was available")
    reasoning: str = Field(..., description="Reasoning about response quality")
    formatted_response: str = Field(..., description="Complete formatted response with citations")
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The windscreen excess for car insurance is $100 [1]. This applies to windscreen replacement or repair coverage [1].",
                "citations": [
                    {
                        "id": "cite_1",
                        "product_name": "Car",
                        "document_type": "Terms",
                        "source_file": "Car_Terms.txt",
                        "section_hierarchy": ["Windscreen Cover"],
                        "relevance_score": 0.95
                    }
                ],
                "confidence_score": 0.92,
                "context_used": 1,
                "context_available": 3,
                "has_sufficient_context": True,
                "reasoning": "Used 3 context chunks from 1 product(s): Car | Average relevance score: 0.85 | Confidence score: 0.92 | Assessment: Sufficient context available to provide a comprehensive answer",
                "formatted_response": "The windscreen excess for car insurance is $100 [1]. This applies to windscreen replacement or repair coverage [1].\n\n**Sources:**\n[1] Car Terms - Windscreen Cover (Relevance: 0.95)",
                "processing_time_ms": 1250.5
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    agents_status: Dict[str, str] = Field(..., description="Status of individual agents")
    timestamp: str = Field(..., description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Query cannot be empty",
                "details": {"field": "query", "constraint": "min_length"},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class AgentPipelineStatus(BaseModel):
    """Status of the agent pipeline"""
    intent_router: str = Field(..., description="Intent Router Agent status")
    retrieval: str = Field(..., description="Retrieval Agent status") 
    response_generation: str = Field(..., description="Response Generation Agent status")
    vector_database: str = Field(..., description="Vector database connection status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent_router": "healthy",
                "retrieval": "healthy",
                "response_generation": "healthy",
                "vector_database": "connected"
            }
        }


class ConversationRequest(BaseModel):
    """Request model for conversation history operations"""
    session_id: Optional[str] = Field(None, description="Session ID to retrieve history for")
    limit: Optional[int] = Field(10, description="Maximum number of messages to retrieve", ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "limit": 10
            }
        }


class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    user_id: Optional[str] = Field(None, description="User identifier")
    platform: str = Field("web", description="Platform (web, whatsapp, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_456",
                "platform": "web"
            }
        }
