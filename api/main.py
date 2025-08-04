"""
HLAS Insurance API Main Application

FastAPI application providing REST endpoints for the insurance agent system.
"""

import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from .models import (
    QueryRequest, QueryResponse, HealthCheckResponse,
    ErrorResponse, AgentPipelineStatus, CitationResponse,
    ConversationRequest, SessionCreateRequest
)
from .conversation_models import ConversationHistory, ConversationSummary
from .services import InsuranceAgentService
from .whatsapp import WhatsAppWebhook
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="HLAS Insurance Agent API",
    description="AI-powered insurance information system using advanced agent pipeline",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the insurance agent service
print("🚀 Initializing Insurance Agent Service...")
agent_service = InsuranceAgentService()
print("✅ Insurance Agent Service initialized")

# Check conversation service status
if hasattr(agent_service, 'conversation_service') and agent_service.conversation_service:
    print("✅ Conversation service is available")
else:
    print("⚠️  Conversation service is NOT available")

# Initialize WhatsApp webhook
whatsapp_webhook = WhatsAppWebhook(agent_service)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    error_details = {
        "path": str(request.url),
        "method": request.method,
        "traceback": traceback.format_exc()
    }
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details=error_details,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        ).dict()
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "HLAS Insurance Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        print("🔍 Health check: Starting agent health check...")
        # Check agent status
        agents_status = await agent_service.check_agents_health()
        print(f"✅ Health check: Agent status retrieved: {agents_status}")

        return HealthCheckResponse(
            status="healthy",
            version="0.1.0",
            agents_status=agents_status,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.get("/agents/status", response_model=AgentPipelineStatus)
async def get_agents_status():
    """Get detailed status of all agents in the pipeline"""
    try:
        status = await agent_service.get_detailed_agent_status()
        return AgentPipelineStatus(**status)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse)
async def query_insurance(request: QueryRequest):
    """
    Main endpoint for insurance queries.
    
    Processes user questions through the complete agent pipeline:
    1. Intent Router Agent - Analyzes and classifies the query
    2. Retrieval Agent - Finds relevant document chunks
    3. Response Generation Agent - Synthesizes the final answer
    """
    start_time = time.time()
    
    try:
        # Validate request
        if not request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="Query cannot be empty"
            )

        # Log the incoming request
        print(f"🔍 API: Processing query request")
        print(f"   Query: {request.query[:100]}...")
        print(f"   Session ID: {request.session_id}")
        print(f"   Max results: {request.max_results}")
        
        # Process query through agent pipeline
        result = await agent_service.process_query(
            query=request.query,
            session_id=request.session_id,
            max_results=request.max_results,
            include_citations=request.include_citations,
            include_confidence=request.include_confidence
        )
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        print(f"✅ API: Query processed successfully")
        print(f"   Processing time: {processing_time_ms:.1f}ms")
        print(f"   Answer length: {len(result['answer'])} chars")
        print(f"   Citations: {len(result['citations'])}")
        print(f"   Session ID in response: {result.get('session_id')}")
        
        # Convert citations to response format
        citations = [
            CitationResponse(
                id=citation["id"],
                product_name=citation["product_name"],
                document_type=citation["document_type"],
                source_file=citation["source_file"],
                section_hierarchy=citation["section_hierarchy"],
                relevance_score=citation["relevance_score"]
            )
            for citation in result["citations"]
        ]
        
        return QueryResponse(
            answer=result["answer"],
            session_id=result.get("session_id"),
            citations=citations,
            confidence_score=result["confidence_score"],
            context_used=result["context_used"],
            context_available=result["context_available"],
            has_sufficient_context=result["has_sufficient_context"],
            reasoning=result["reasoning"],
            formatted_response=result["formatted_response"],
            processing_time_ms=processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@app.post("/query/simple")
async def query_insurance_simple(request: QueryRequest):
    """
    Simplified endpoint that returns just the formatted response as plain text.
    Useful for basic integrations that don't need the full response structure.
    """
    try:
        result = await agent_service.process_query(
            query=request.query,
            session_id=request.session_id,
            max_results=request.max_results,
            include_citations=request.include_citations,
            include_confidence=request.include_confidence
        )

        return {"response": result["formatted_response"]}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@app.get("/webhook")
async def webhook_verify(request: Request):
    """
    WhatsApp webhook verification endpoint.
    Meta sends a GET request to verify the webhook URL.
    """
    return await whatsapp_webhook.verify_webhook(request)


@app.post("/webhook")
async def webhook_receive(request: Request):
    """
    WhatsApp webhook endpoint for receiving messages.
    Processes incoming WhatsApp messages through the insurance agent pipeline.
    """
    return await whatsapp_webhook.handle_webhook(request)


@app.get("/whatsapp/status")
async def whatsapp_status():
    """
    Get WhatsApp integration status and configuration info.
    """
    return whatsapp_webhook.get_webhook_info()


@app.post("/conversation/session", response_model=Dict[str, str])
async def create_conversation_session(request: SessionCreateRequest):
    """
    Create a new conversation session for tracking conversation history.
    """
    try:
        print(f"🔧 API: Creating conversation session")
        print(f"   User ID: {request.user_id}")
        print(f"   Platform: {request.platform}")

        session = agent_service.create_conversation_session(
            user_id=request.user_id,
            platform=request.platform
        )

        if session:
            print(f"✅ API: Session created successfully: {session.session_id}")
            return {"session_id": session.session_id}
        else:
            print(f"❌ API: Failed to create session - service unavailable")
            raise HTTPException(
                status_code=503,
                detail="Conversation service unavailable"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@app.get("/conversation/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(session_id: str, limit: Optional[int] = None):
    """
    Get conversation history for a specific session.
    """
    try:
        history = agent_service.get_conversation_history(session_id, limit)

        if history:
            return history
        else:
            raise HTTPException(
                status_code=404,
                detail="Session not found or conversation service unavailable"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@app.get("/conversation/summary", response_model=ConversationSummary)
async def get_conversation_summary(days: int = 30):
    """
    Get conversation summary statistics.
    """
    try:
        summary = agent_service.get_conversation_summary(days)

        if summary:
            return summary
        else:
            raise HTTPException(
                status_code=503,
                detail="Conversation service unavailable"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation summary: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
