# HLAS Insurance Agent System - Comprehensive Documentation

This directory contains detailed documentation for each component of the HLAS Insurance Agent System, a sophisticated multi-agent AI system for processing and querying insurance policy documents.

## Documentation Structure

### Core Agents
- **[Embedding Agent](./01_embedding_agent.md)** - Document processing and vectorization
- **[Intent Router Agent](./02_intent_router_agent.md)** - Query classification and routing
- **[Retrieval Agent](./03_retrieval_agent.md)** - Multi-vector hybrid search
- **[Response Generation Agent](./04_response_generation_agent.md)** - Answer synthesis and formatting

### System Components
- **[API Layer](./05_api_layer.md)** - FastAPI REST endpoints and services
- **[Frontend Interface](./06_frontend_interface.md)** - Web-based chat interface
- **[Configuration System](./07_configuration_system.md)** - Central configuration management
- **[Data Sources](./08_data_sources.md)** - Insurance document structure and content

### Architecture & Design
- **[System Architecture](./09_system_architecture.md)** - Overall system design and data flow
- **[Technical Stack](./10_technical_stack.md)** - Technologies, dependencies, and deployment

## System Overview

The HLAS Insurance Agent System is a production-ready AI-powered insurance information system that processes 7 insurance products (Car, Travel, Family, Hospital, Maid, Home, Early) across 3 document types (Terms, FAQs, Benefits) to provide accurate, cited responses to customer queries.

### Key Features
- **Multi-Agent Architecture**: Specialized agents for different aspects of query processing
- **Advanced Search**: Multi-vector hybrid search with cross-encoder reranking
- **Grounded Responses**: All answers backed by source citations
- **Real-time Processing**: Sub-3-second response times
- **Production Ready**: Complete API, frontend, and monitoring capabilities

### Agent Pipeline Flow
1. **User Query** → Intent Router Agent (classifies intent and extracts entities)
2. **Intent Classification** → Retrieval Agent (finds relevant document chunks)
3. **Context Chunks** → Response Generation Agent (synthesizes final answer)
4. **Formatted Response** → User (with citations and confidence scores)

Each agent is designed with specific responsibilities, clear interfaces, and comprehensive error handling to ensure reliable operation in production environments.
