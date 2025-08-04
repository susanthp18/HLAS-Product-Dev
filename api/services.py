"""
API Services

Business logic layer that orchestrates the agent pipeline for API endpoints.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.intent_router import IntentRouterAgent
from agents.retrieval import RetrievalAgent, RetrievalRequest, SearchStrategy
from agents.response_generation import ResponseGenerationAgent, ResponseRequest, CitationStyle
from .conversation_service import ConversationService
from .conversation_models import MessageType
from config import Config


class InsuranceAgentService:
    """
    Service class that orchestrates the complete agent pipeline.
    
    This class manages the interaction between:
    1. Intent Router Agent - Query analysis and classification
    2. Retrieval Agent - Document chunk retrieval
    3. Response Generation Agent - Answer synthesis
    """
    
    def __init__(self):
        """Initialize all agents in the pipeline"""
        self.intent_router = None
        self.retrieval_agent = None
        self.response_agent = None
        self.conversation_service = None
        self._initialize_agents()
        self._initialize_conversation_service()
    
    def _initialize_agents(self):
        """Initialize all agents with error handling"""
        try:
            print("🔧 InsuranceAgentService: Initializing Intent Router...")
            self.intent_router = IntentRouterAgent(gemini_api_key=Config.GEMINI_API_KEY)
            print("✅ InsuranceAgentService: Intent Router initialized")

            print("🔧 InsuranceAgentService: Initializing Retrieval Agent...")
            self.retrieval_agent = RetrievalAgent(
                weaviate_host=Config.WEAVIATE_HOST,
                weaviate_port=Config.WEAVIATE_PORT,
                gemini_api_key=Config.GEMINI_API_KEY
            )
            print("✅ InsuranceAgentService: Retrieval Agent initialized")

            print("🔧 InsuranceAgentService: Initializing Response Agent...")
            self.response_agent = ResponseGenerationAgent(gemini_api_key=Config.GEMINI_API_KEY)
            print("✅ InsuranceAgentService: Response Agent initialized")

        except Exception as e:
            print(f"❌ InsuranceAgentService: Error initializing agents: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _initialize_conversation_service(self):
        """Initialize conversation service with error handling"""
        try:
            print(f"🔧 InsuranceAgentService: Initializing conversation service...")
            self.conversation_service = ConversationService()
            print(f"✅ InsuranceAgentService: Conversation service initialized successfully")
        except Exception as e:
            print(f"❌ InsuranceAgentService: Could not initialize conversation service: {e}")
            import traceback
            traceback.print_exc()
            self.conversation_service = None
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 5,
        include_citations: bool = True,
        include_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query through the complete agent pipeline.
        
        Args:
            query: User's insurance question
            session_id: Session ID for conversation tracking
            max_results: Maximum number of context chunks to retrieve
            include_citations: Whether to include citations in response
            include_confidence: Whether to include confidence score
            
        Returns:
            Dictionary containing the complete response data
        """

        # Auto-generate session ID if not provided
        if not session_id and self.conversation_service:
            try:
                print(f"🔧 InsuranceAgentService: Auto-generating session ID")
                new_session = self.conversation_service.create_session(
                    user_id="auto_generated",
                    platform="api"
                )
                session_id = new_session.session_id
                print(f"✅ InsuranceAgentService: Auto-generated session ID: {session_id}")
            except Exception as e:
                print(f"❌ InsuranceAgentService: Could not auto-generate session: {e}")
                session_id = None

        # Store user message in conversation history
        if self.conversation_service and session_id:
            try:
                print(f"📝 InsuranceAgentService: Storing user message for session {session_id}")
                self.conversation_service.add_message(
                    session_id=session_id,
                    message_type=MessageType.USER,
                    content=query
                )
                print(f"✅ InsuranceAgentService: User message stored successfully")
            except Exception as e:
                print(f"❌ InsuranceAgentService: Could not store user message: {e}")
                import traceback
                traceback.print_exc()
        elif not self.conversation_service:
            print(f"⚠️  InsuranceAgentService: Conversation service not available")
        elif not session_id:
            print(f"ℹ️  InsuranceAgentService: No session_id available, skipping conversation storage")

        # Step 1: Intent Classification
        intent_classification = self.intent_router.classify_intent(query)
        
        # Step 2: Document Retrieval
        retrieval_request = RetrievalRequest(
            intent_classification=intent_classification,
            top_k=max_results,
            search_strategy=SearchStrategy.MULTI_VECTOR
        )
        
        context_chunks = self.retrieval_agent.retrieve(retrieval_request)
        
        # Step 3: Response Generation
        response_request = ResponseRequest(
            original_query=query,
            context_chunks=context_chunks,
            citation_style=CitationStyle.NUMBERED,
            include_confidence_score=include_confidence
        )
        
        response_result = self.response_agent.generate_response(response_request)

        # Store assistant response in conversation history
        if self.conversation_service and session_id:
            try:
                print(f"📝 InsuranceAgentService: Storing assistant response for session {session_id}")
                self.conversation_service.add_message(
                    session_id=session_id,
                    message_type=MessageType.ASSISTANT,
                    content=response_result.answer,
                    confidence_score=response_result.confidence_score,
                    citations=[citation.to_dict() for citation in response_result.citations],
                    processing_time_ms=None  # Will be calculated in API layer
                )
                print(f"✅ InsuranceAgentService: Assistant response stored successfully")
            except Exception as e:
                print(f"❌ InsuranceAgentService: Could not store assistant message: {e}")
                import traceback
                traceback.print_exc()
        elif not self.conversation_service:
            print(f"⚠️  InsuranceAgentService: Conversation service not available for storing response")
        elif not session_id:
            print(f"ℹ️  InsuranceAgentService: No session_id available, skipping response storage")

        # Return structured result with session_id
        result = response_result.to_dict()
        result["session_id"] = session_id
        return result
    
    async def check_agents_health(self) -> Dict[str, str]:
        """Check the health status of all agents"""
        health_status = {}
        
        # Check Intent Router
        try:
            if self.intent_router:
                # Just check if it exists, don't actually call it
                health_status["intent_router"] = "healthy"
            else:
                health_status["intent_router"] = "unhealthy: not initialized"
        except Exception as e:
            health_status["intent_router"] = f"unhealthy: {str(e)}"
        
        # Check Retrieval Agent
        try:
            # Simple connectivity test
            if hasattr(self.retrieval_agent, 'client') and self.retrieval_agent.client:
                health_status["retrieval"] = "healthy"
            else:
                health_status["retrieval"] = "unhealthy: no client connection"
        except Exception as e:
            health_status["retrieval"] = f"unhealthy: {str(e)}"
        
        # Check Response Generation Agent
        try:
            if hasattr(self.response_agent, 'model') and self.response_agent.model:
                health_status["response_generation"] = "healthy"
            else:
                health_status["response_generation"] = "unhealthy: no model loaded"
        except Exception as e:
            health_status["response_generation"] = f"unhealthy: {str(e)}"
        
        return health_status
    
    async def get_detailed_agent_status(self) -> Dict[str, str]:
        """Get detailed status information for each agent"""
        status = {}
        print("🔍 InsuranceAgentService: Starting detailed agent status check...")

        # Intent Router status
        try:
            print("🔍 Checking Intent Router status...")
            if self.intent_router:
                status["intent_router"] = "operational"
                print("✅ Intent Router: operational")
            else:
                status["intent_router"] = "not_initialized"
                print("❌ Intent Router: not_initialized")
        except Exception as e:
            status["intent_router"] = "error"
            print(f"❌ Intent Router: error - {str(e)}")

        # Retrieval Agent status
        try:
            print("🔍 Checking Retrieval Agent status...")
            if self.retrieval_agent and hasattr(self.retrieval_agent, 'client'):
                print("🔍 Retrieval Agent: Testing vector database connection...")
                # Test vector database connection
                collection = self.retrieval_agent.client.collections.get('InsuranceDocumentChunk')
                if collection:
                    status["retrieval"] = "operational"
                    print("✅ Retrieval Agent: operational - collection found")
                else:
                    status["retrieval"] = "collection_not_found"
                    print("❌ Retrieval Agent: collection_not_found")
            else:
                status["retrieval"] = "not_initialized"
                print("❌ Retrieval Agent: not_initialized - no client")
        except Exception as e:
            status["retrieval"] = f"error: {str(e)}"
            print(f"❌ Retrieval Agent: error - {str(e)}")

        # Response Generation Agent status
        try:
            print("🔍 Checking Response Generation Agent status...")
            if self.response_agent and hasattr(self.response_agent, 'model'):
                status["response_generation"] = "operational"
                print("✅ Response Generation Agent: operational")
            else:
                status["response_generation"] = "not_initialized"
                print("❌ Response Generation Agent: not_initialized - no model")
        except Exception as e:
            status["response_generation"] = "error"
            print(f"❌ Response Generation Agent: error - {str(e)}")

        # Vector Database status
        try:
            print("🔍 Checking Vector Database status...")
            if self.retrieval_agent and hasattr(self.retrieval_agent, 'client'):
                print("🔍 Vector Database: Testing basic connectivity...")
                collections = self.retrieval_agent.client.collections.list_all()
                collection_names = [c.name for c in collections]
                print(f"🔍 Vector Database: Found collections: {collection_names}")
                status["vector_database"] = "connected"
                print("✅ Vector Database: connected")
            else:
                status["vector_database"] = "disconnected"
                print("❌ Vector Database: disconnected - no client")
        except Exception as e:
            status["vector_database"] = f"error: {str(e)}"
            print(f"❌ Vector Database: error - {str(e)}")

        print(f"🔍 InsuranceAgentService: Final status: {status}")
        return status

    def create_conversation_session(self, user_id: Optional[str] = None, platform: str = "web"):
        """Create a new conversation session"""
        if not self.conversation_service:
            return None

        try:
            return self.conversation_service.create_session(
                user_id=user_id,
                platform=platform
            )
        except Exception as e:
            print(f"Error creating conversation session: {e}")
            return None

    def get_conversation_history(self, session_id: str, limit: Optional[int] = None):
        """Get conversation history for a session"""
        if not self.conversation_service:
            return None

        try:
            return self.conversation_service.get_conversation_history(session_id, limit)
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return None

    def get_conversation_summary(self, days: int = 30):
        """Get conversation summary statistics"""
        if not self.conversation_service:
            return None

        try:
            return self.conversation_service.get_conversation_summary(days)
        except Exception as e:
            print(f"Error getting conversation summary: {e}")
            return None

    def __del__(self):
        """Cleanup resources when service is destroyed"""
        try:
            if self.retrieval_agent:
                self.retrieval_agent.close()
            if self.conversation_service:
                self.conversation_service.close()
        except Exception:
            pass
