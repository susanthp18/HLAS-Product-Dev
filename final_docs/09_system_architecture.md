# System Architecture - Overall System Design and Data Flow

## Overview

The HLAS Insurance Agent System implements a sophisticated multi-agent architecture designed for production-scale insurance information processing. The system follows a modular, microservices-inspired design where specialized AI agents collaborate through well-defined interfaces to process user queries and generate accurate, cited responses from insurance policy documents.

## Core Purpose

**What it achieves**: Scalable, accurate, and maintainable AI-powered insurance information system
**Why this architecture**: Separation of concerns, specialized optimization, and production reliability
**How it works**: Multi-agent pipeline with vector search, LLM processing, and comprehensive monitoring

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Layer     │    │  Agent Pipeline │
│   Interface     │◄──►│   (FastAPI)     │◄──►│   Orchestrator  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │  Configuration  │◄────────────┤
                       │     System      │             │
                       └─────────────────┘             │
                                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent Pipeline                                    │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│  Intent Router  │  Retrieval      │  Response       │   Embedding         │
│     Agent       │    Agent        │ Generation      │     Agent           │
│                 │                 │    Agent        │                     │
│ • Query Analysis│ • Multi-Vector  │ • Answer        │ • Document          │
│ • Intent Class. │   Search        │   Synthesis     │   Processing        │
│ • Entity Extract│ • Reranking     │ • Citation      │ • Vector            │
│ • Product Focus │ • Filtering     │   Generation    │   Generation        │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Vector Store  │
                    │   (Weaviate)    │
                    │                 │
                    │ • Multi-Vector  │
                    │   Embeddings    │
                    │ • Metadata      │
                    │ • Search Index  │
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │  Data Sources   │
                    │                 │
                    │ • 7 Products    │
                    │ • 3 Doc Types   │
                    │ • 21 Documents  │
                    └─────────────────┘
```

## Agent Pipeline Architecture

### 1. Intent Router Agent
**Role**: Query analysis and classification gateway
**Responsibilities**:
- Classify user intent into 5 categories (PRODUCT_INQUIRY, COMPARISON_INQUIRY, PURCHASE_INQUIRY, GENERAL_INQUIRY, CHITCHAT)
- Extract relevant insurance products from query
- Identify key entities and concepts
- Determine purchase intent signals

**Input**: Raw user query string
**Output**: Structured IntentClassification object
**Technology**: Gemini 2.5 Flash with rule-based enhancement

### 2. Retrieval Agent
**Role**: Intelligent document search and context gathering
**Responsibilities**:
- Execute multi-vector hybrid search across document embeddings
- Apply product-specific filtering based on intent classification
- Perform cross-encoder reranking for maximum relevance
- Balance results for comparison queries

**Input**: IntentClassification + search parameters
**Output**: Ranked list of relevant ChunkResult objects
**Technology**: Weaviate vector database + cross-encoder reranking

### 3. Response Generation Agent
**Role**: Answer synthesis and quality assurance
**Responsibilities**:
- Generate grounded responses based exclusively on retrieved context
- Create comprehensive citations for all factual claims
- Assess response quality and confidence scoring
- Format responses for optimal user experience

**Input**: User query + retrieved context chunks
**Output**: Complete ResponseResult with answer, citations, and quality metrics
**Technology**: Gemini 2.0 Flash with structured prompting

### 4. Embedding Agent
**Role**: Document processing and vector index creation
**Responsibilities**:
- Process insurance documents through content-aware chunking
- Generate multi-vector embeddings (content, summary, questions)
- Enrich chunks with AI-generated metadata
- Populate and maintain Weaviate vector database

**Input**: Raw insurance documents from Source directory
**Output**: Populated vector database ready for search
**Technology**: Gemini embedding models + Weaviate ingestion

## Data Flow Architecture

### Query Processing Flow
```
1. User Query
   ↓
2. Frontend Interface (JavaScript)
   ↓ HTTP POST /query
3. API Layer (FastAPI)
   ↓ Service orchestration
4. Intent Router Agent
   ↓ IntentClassification
5. Retrieval Agent
   ↓ ChunkResult[]
6. Response Generation Agent
   ↓ ResponseResult
7. API Response Formatting
   ↓ JSON response
8. Frontend Display
   ↓
9. User sees formatted answer with citations
```

### Document Processing Flow
```
1. Source Documents (21 files)
   ↓
2. Embedding Agent - Document Loading
   ↓
3. Content-Aware Chunking (650+ chunks)
   ↓
4. AI Metadata Enrichment
   ↓
5. Multi-Vector Embedding Generation
   ↓
6. Weaviate Database Ingestion
   ↓
7. Search-Ready Vector Index
```

## Component Integration Patterns

### Agent Communication
**Pattern**: Request-Response with structured data objects
**Benefits**: Type safety, clear interfaces, easy testing
**Implementation**: Pydantic models for all inter-agent communication

```python
# Example integration pattern
intent_classification = intent_router.classify_intent(query)
retrieval_request = RetrievalRequest(intent_classification=intent_classification)
context_chunks = retrieval_agent.retrieve(retrieval_request)
response_request = ResponseRequest(original_query=query, context_chunks=context_chunks)
response_result = response_agent.generate_response(response_request)
```

### Error Handling Strategy
**Pattern**: Graceful degradation with fallback responses
**Implementation**: Each agent provides fallback behavior for upstream failures
**Monitoring**: Comprehensive error logging and health monitoring

### Configuration Management
**Pattern**: Centralized configuration with environment-specific overrides
**Implementation**: Single Config class with validation and environment variable support
**Benefits**: Consistent settings across all components

## Scalability Architecture

### Horizontal Scaling
**Stateless Design**: All agents are stateless and support concurrent requests
**Load Balancing**: API layer can be horizontally scaled behind load balancer
**Database Scaling**: Weaviate supports clustering for large-scale deployments

### Performance Optimization
**Caching Strategy**: Response caching for common queries (planned)
**Batch Processing**: Optimized batch sizes for embedding generation and database operations
**Connection Pooling**: Efficient database connection management

### Resource Management
**Memory Optimization**: Lazy loading of models and efficient memory usage
**CPU Utilization**: Parallel processing where appropriate
**I/O Optimization**: Efficient database queries and API calls

## Security Architecture

### API Security
**Authentication**: Ready for API key or OAuth integration
**Input Validation**: Comprehensive request validation using Pydantic
**Rate Limiting**: Planned implementation for production deployment
**CORS Configuration**: Configurable CORS for frontend integration

### Data Security
**API Key Management**: Secure handling of external API keys
**Data Encryption**: HTTPS for all external communications
**Access Control**: Planned role-based access control
**Audit Logging**: Comprehensive logging for security monitoring

### Infrastructure Security
**Network Security**: Secure communication between components
**Container Security**: Docker security best practices
**Secrets Management**: Environment-based secret management

## Monitoring and Observability

### Health Monitoring
**Component Health**: Individual agent health checks
**System Health**: Overall system status monitoring
**Database Health**: Vector database connectivity and performance
**API Health**: Endpoint availability and response times

### Performance Metrics
**Response Times**: End-to-end query processing times
**Accuracy Metrics**: Response quality and relevance scoring
**Resource Usage**: Memory, CPU, and database utilization
**Error Rates**: Component-level error tracking

### Logging Strategy
**Structured Logging**: JSON-formatted logs for easy parsing
**Correlation IDs**: Request tracking across components
**Error Context**: Detailed error information for debugging
**Performance Logging**: Query performance and optimization data

## Deployment Architecture

### Development Environment
```
Local Machine:
├── Python Application (all agents)
├── Local Weaviate (Docker)
├── Local Frontend (HTTP server)
└── Environment Variables (.env file)
```

### Production Environment
```
Cloud Infrastructure:
├── Load Balancer
├── API Instances (multiple)
├── Weaviate Cluster
├── CDN (for frontend)
├── Monitoring Stack
└── Secret Management
```

### Container Architecture
```dockerfile
# Multi-stage build for optimization
FROM python:3.9-slim as base
# Install dependencies
FROM base as app
# Copy application code
FROM app as production
# Production configuration
```

## Quality Assurance Architecture

### Testing Strategy
**Unit Tests**: Individual agent testing with mocked dependencies
**Integration Tests**: End-to-end pipeline testing
**Performance Tests**: Load testing and performance validation
**Quality Tests**: Response quality and accuracy validation

### Validation Framework
**Input Validation**: Comprehensive request validation
**Output Validation**: Response format and quality validation
**Configuration Validation**: System configuration validation
**Data Validation**: Document processing validation

### Continuous Integration
**Automated Testing**: CI/CD pipeline with comprehensive testing
**Quality Gates**: Quality thresholds for deployment
**Performance Monitoring**: Continuous performance validation
**Security Scanning**: Automated security vulnerability scanning

## Future Architecture Enhancements

### Planned Improvements
**Microservices**: Full microservices architecture with service mesh
**Event-Driven**: Event-driven architecture for real-time updates
**Multi-Model**: Support for multiple LLM providers and models
**Caching Layer**: Redis-based caching for improved performance
**Analytics**: Advanced analytics and user behavior tracking
**Auto-Scaling**: Kubernetes-based auto-scaling
**Multi-Region**: Multi-region deployment for global availability

### Technology Evolution
**Model Updates**: Support for newer and more capable models
**Vector Database**: Advanced vector database features and optimization
**Search Enhancement**: More sophisticated search and ranking algorithms
**Real-time Processing**: Stream processing for real-time updates
**Edge Computing**: Edge deployment for reduced latency
**AI/ML Pipeline**: MLOps pipeline for model management and updates

## Architecture Benefits

### Modularity
- **Separation of Concerns**: Each agent has a specific, well-defined responsibility
- **Independent Development**: Agents can be developed and deployed independently
- **Technology Flexibility**: Different agents can use different technologies as appropriate
- **Testing Isolation**: Each component can be tested in isolation

### Scalability
- **Horizontal Scaling**: Stateless design enables easy horizontal scaling
- **Performance Optimization**: Each component optimized for its specific task
- **Resource Efficiency**: Efficient resource utilization across components
- **Load Distribution**: Load can be distributed across multiple instances

### Maintainability
- **Clear Interfaces**: Well-defined interfaces between components
- **Configuration Management**: Centralized configuration for easy management
- **Error Handling**: Comprehensive error handling and recovery
- **Monitoring**: Extensive monitoring and observability

### Reliability
- **Fault Tolerance**: Graceful degradation when components fail
- **Health Monitoring**: Continuous health monitoring and alerting
- **Recovery Mechanisms**: Automatic recovery from transient failures
- **Quality Assurance**: Multiple layers of quality validation
