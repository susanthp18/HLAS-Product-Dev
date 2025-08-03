# 🚀 HLAS Insurance Assistant - Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Weaviate** running locally (port 8080)
3. **Gemini API Key** from Google AI Studio
4. **Insurance documents** processed and indexed

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
EMBEDDING_MODEL=models/embedding-001
```

### 3. Verify Configuration
```bash
python -c "from config import Config; Config.validate(); print('✅ Configuration valid')"
```

## Running the System

### Option 1: Complete Web Application

**Terminal 1 - Start API Server:**
```bash
python start_api.py
```
- API available at: http://localhost:8000
- Documentation: http://localhost:8000/docs

**Terminal 2 - Start Frontend:**
```bash
python start_frontend.py
```
- Frontend available at: http://localhost:3000
- Opens automatically in browser

### Option 2: API Only

```bash
python start_api.py
```

Test with curl:
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What is the windscreen excess for car insurance?",
       "include_citations": true,
       "include_confidence": true,
       "max_results": 5
     }'
```

### Option 3: Python Code

```python
from agents.intent_router import IntentRouterAgent
from agents.retrieval import RetrievalAgent, RetrievalRequest, SearchStrategy
from agents.response_generation import ResponseGenerationAgent, ResponseRequest

# Initialize agents
intent_router = IntentRouterAgent()
retrieval_agent = RetrievalAgent()
response_agent = ResponseGenerationAgent()

# Process query
query = "What is the windscreen excess for car insurance?"

# Step 1: Intent Classification
intent = intent_router.classify_intent(query)

# Step 2: Document Retrieval
retrieval_request = RetrievalRequest(intent, top_k=5, search_strategy=SearchStrategy.MULTI_VECTOR)
context_chunks = retrieval_agent.retrieve(retrieval_request)

# Step 3: Response Generation
response_request = ResponseRequest(query, context_chunks)
response_result = response_agent.generate_response(response_request)

# Get formatted answer
print(response_result.format_response(include_citations=True, include_confidence=True))

# Cleanup
retrieval_agent.close()
```

## System Health Check

Visit http://localhost:8000/health or http://localhost:8000/agents/status to check system status.

## Available Insurance Products

- **Car Insurance** - Vehicle coverage and protection
- **Travel Insurance** - Trip and travel-related coverage
- **Family Insurance** - Family health and protection plans
- **Hospital Insurance** - Medical and hospitalization coverage
- **Maid Insurance** - Domestic helper protection
- **Home Insurance** - Property and contents coverage
- **Early Insurance** - Early life and child protection

## Example Queries

- "What is the windscreen excess for car insurance?"
- "How do I make a claim?"
- "Compare Family and Hospital insurance medical coverage"
- "What are the age limits for travel insurance?"
- "Tell me about maid insurance coverage"
- "What documents do I need for insurance application?"

## Troubleshooting

### Common Issues

1. **"Configuration validation failed"**
   - Check your `.env` file exists and has correct values
   - Verify Gemini API key is valid

2. **"Vector database connection failed"**
   - Ensure Weaviate is running on localhost:8080
   - Check if insurance documents are indexed

3. **"No results found"**
   - Verify documents are properly embedded and indexed
   - Try more specific queries related to available products

4. **API connection errors**
   - Ensure API server is running on port 8000
   - Check for port conflicts

### Getting Help

1. Check system status: http://localhost:8000/agents/status
2. View API documentation: http://localhost:8000/docs
3. Check logs in terminal where servers are running

## Next Steps

1. **Customize**: Modify prompts and configurations in agent files
2. **Extend**: Add new insurance products or document types
3. **Deploy**: Set up production environment with proper security
4. **Monitor**: Implement logging and monitoring for production use

---

🎯 **Ready to go!** Your HLAS Insurance Assistant is now operational and ready to help customers with their insurance questions.
