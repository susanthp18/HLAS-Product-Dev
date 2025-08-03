"""
Insurance Policy Processing Agents

This package contains all the agents for processing insurance documents:
- Embedding Agent: Converts documents into multi-faceted vector indexes
- Intent Router Agent: Analyzes user queries and routes them to appropriate agents
- Retrieval Agent: Finds the most relevant document chunks using advanced search
- Response Generation Agent: Synthesizes retrieved context into human-readable answers
- Vector Indexing Agent: Manages vector database operations
- Flow Agents: Product-specific conversation flows
- Policy Agents: Summarization and comparison
- Question/Response Agents: Query handling and response generation
"""

from .embedding import EmbeddingAgent
from .intent_router import IntentRouterAgent
from .retrieval import RetrievalAgent
from .response_generation import ResponseGenerationAgent

__version__ = "0.1.0"
__all__ = ['EmbeddingAgent', 'IntentRouterAgent', 'RetrievalAgent', 'ResponseGenerationAgent']