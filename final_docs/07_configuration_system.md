# Configuration System - Central Configuration Management

## Overview

The Configuration System provides centralized management of all system settings, environment variables, and operational parameters for the HLAS Insurance Agent System. Built around a single `Config` class, it ensures consistent configuration across all agents and components while supporting environment-based deployment configurations.

## Core Purpose

**What it does**: Centralizes all system configuration in a single, validated, and accessible location
**Why it's needed**: Ensures consistent settings across agents and simplifies deployment configuration
**How it works**: Class-based configuration with environment variable support and validation

## Architecture Overview

```
Environment Variables → Config Class → Agent Initialization → System Operation
```

## Configuration Structure

### Main Configuration Class (`config.py`)
```python
"""
Configuration settings for Insurance Document Processing Agents
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """Central configuration for all agents"""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyAyiV7SsxfU7ldJGwIbN6C7IQZtag7z53M")
    
    # Weaviate Configuration
    WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
    WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    
    # Document Processing
    SOURCE_DIR: str = os.getenv("SOURCE_DIR", "Source")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    GENERATION_MODEL: str = "gemini-2.5-flash"
    
    # Chunking Parameters
    MAX_CHUNK_SIZE: int = 2048
    CHUNK_OVERLAP: int = 200
    
    # Batch Processing
    EMBEDDING_BATCH_SIZE: int = 50
    WEAVIATE_BATCH_SIZE: int = 100
    
    # Search Configuration
    DEFAULT_SEARCH_LIMIT: int = 5
    MAX_SEARCH_LIMIT: int = 20
    
    # Product Configuration
    INSURANCE_PRODUCTS = ["Car", "Early", "Family", "Home", "Hospital", "Maid", "Travel"]
    
    # Document Types
    DOCUMENT_EXTENSIONS = {
        "terms": "_Terms.md",
        "faq": "_FAQs.txt",
        "benefits": "_Tables.txt"
    }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        
        if not os.path.exists(cls.SOURCE_DIR):
            raise ValueError(f"Source directory not found: {cls.SOURCE_DIR}")
        
        return True
    
    @classmethod
    def get_weaviate_url(cls) -> str:
        """Get full Weaviate URL"""
        return f"http://{cls.WEAVIATE_HOST}:{cls.WEAVIATE_PORT}"
```

## Configuration Categories

### 1. API Keys and Authentication
**Purpose**: Secure access to external services

```python
# API Keys
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "default-key")
```

**Environment Variables**:
- `GEMINI_API_KEY`: Google Gemini API key for LLM and embedding services
- Future: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` for alternative models

**Security Considerations**:
- Never commit API keys to version control
- Use environment variables or secure key management
- Rotate keys regularly in production
- Implement key validation and error handling

### 2. Vector Database Configuration
**Purpose**: Connection settings for Weaviate vector database

```python
# Weaviate Configuration
WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))

@classmethod
def get_weaviate_url(cls) -> str:
    """Get full Weaviate URL"""
    return f"http://{cls.WEAVIATE_HOST}:{cls.WEAVIATE_PORT}"
```

**Environment Variables**:
- `WEAVIATE_HOST`: Weaviate server hostname (default: localhost)
- `WEAVIATE_PORT`: Weaviate server port (default: 8080)

**Deployment Scenarios**:
- **Development**: localhost:8080
- **Docker**: weaviate:8080 (container name)
- **Production**: weaviate.company.com:443 (with HTTPS)
- **Cloud**: managed Weaviate service URLs

### 3. Document Processing Configuration
**Purpose**: Settings for document loading and processing

```python
# Document Processing
SOURCE_DIR: str = os.getenv("SOURCE_DIR", "Source")

# Product Configuration
INSURANCE_PRODUCTS = ["Car", "Early", "Family", "Home", "Hospital", "Maid", "Travel"]

# Document Types
DOCUMENT_EXTENSIONS = {
    "terms": "_Terms.md",
    "faq": "_FAQs.txt", 
    "benefits": "_Tables.txt"
}
```

**Configuration Details**:
- **SOURCE_DIR**: Root directory for insurance documents
- **INSURANCE_PRODUCTS**: List of supported insurance products
- **DOCUMENT_EXTENSIONS**: File naming conventions for document types

**Validation**:
- Checks if SOURCE_DIR exists
- Validates document structure
- Ensures all required products have documents

### 4. AI Model Configuration
**Purpose**: Settings for LLM and embedding models

```python
# Embedding Configuration
EMBEDDING_MODEL: str = "gemini-embedding-001"
GENERATION_MODEL: str = "gemini-2.5-flash"

# Chunking Parameters
MAX_CHUNK_SIZE: int = 2048
CHUNK_OVERLAP: int = 200
```

**Model Settings**:
- **EMBEDDING_MODEL**: Model for generating vector embeddings
- **GENERATION_MODEL**: Model for text generation and classification
- **MAX_CHUNK_SIZE**: Maximum characters per document chunk
- **CHUNK_OVERLAP**: Overlap between adjacent chunks

**Performance Tuning**:
- Adjust chunk size based on model context limits
- Optimize overlap for semantic coherence
- Consider model-specific parameters

### 5. Batch Processing Configuration
**Purpose**: Performance optimization settings

```python
# Batch Processing
EMBEDDING_BATCH_SIZE: int = 50
WEAVIATE_BATCH_SIZE: int = 100
```

**Batch Settings**:
- **EMBEDDING_BATCH_SIZE**: Number of chunks to process simultaneously for embeddings
- **WEAVIATE_BATCH_SIZE**: Number of objects to insert in single Weaviate batch

**Performance Considerations**:
- Larger batches improve throughput but increase memory usage
- API rate limits may require smaller batches
- Network latency affects optimal batch sizes

### 6. Search Configuration
**Purpose**: Default search behavior and limits

```python
# Search Configuration
DEFAULT_SEARCH_LIMIT: int = 5
MAX_SEARCH_LIMIT: int = 20
```

**Search Settings**:
- **DEFAULT_SEARCH_LIMIT**: Default number of results to return
- **MAX_SEARCH_LIMIT**: Maximum allowed results per query

**User Experience**:
- Balance between relevance and response time
- Prevent excessive resource usage
- Allow customization for different use cases

## Environment Variable Management

### .env File Support
```bash
# .env file example
GEMINI_API_KEY=your-actual-api-key-here
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
SOURCE_DIR=Source

# Optional overrides
EMBEDDING_MODEL=gemini-embedding-001
GENERATION_MODEL=gemini-2.5-flash
```

### Environment-Specific Configurations

#### Development Environment
```bash
# Development settings
GEMINI_API_KEY=dev-api-key
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
SOURCE_DIR=Source
```

#### Production Environment
```bash
# Production settings
GEMINI_API_KEY=prod-api-key
WEAVIATE_HOST=weaviate.company.com
WEAVIATE_PORT=443
SOURCE_DIR=/app/data/Source
```

#### Docker Environment
```bash
# Docker settings
GEMINI_API_KEY=docker-api-key
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
SOURCE_DIR=/app/Source
```

## Configuration Validation

### Validation Methods
```python
@classmethod
def validate(cls) -> bool:
    """Validate configuration settings"""
    # Check required API keys
    if not cls.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required")
    
    # Validate file paths
    if not os.path.exists(cls.SOURCE_DIR):
        raise ValueError(f"Source directory not found: {cls.SOURCE_DIR}")
    
    # Validate numeric ranges
    if cls.WEAVIATE_PORT < 1 or cls.WEAVIATE_PORT > 65535:
        raise ValueError(f"Invalid WEAVIATE_PORT: {cls.WEAVIATE_PORT}")
    
    if cls.MAX_CHUNK_SIZE < 100:
        raise ValueError(f"MAX_CHUNK_SIZE too small: {cls.MAX_CHUNK_SIZE}")
    
    # Validate product configuration
    if not cls.INSURANCE_PRODUCTS:
        raise ValueError("INSURANCE_PRODUCTS cannot be empty")
    
    return True
```

### Startup Validation
```python
# In startup scripts
def main():
    try:
        Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        return
    
    # Continue with application startup
    agent = EmbeddingAgent(
        source_dir=Config.SOURCE_DIR,
        gemini_api_key=Config.GEMINI_API_KEY,
        weaviate_host=Config.WEAVIATE_HOST,
        weaviate_port=Config.WEAVIATE_PORT
    )
```

## Usage Patterns

### Agent Initialization
```python
# Embedding Agent
agent = EmbeddingAgent(
    source_dir=Config.SOURCE_DIR,
    gemini_api_key=Config.GEMINI_API_KEY,
    weaviate_host=Config.WEAVIATE_HOST,
    weaviate_port=Config.WEAVIATE_PORT
)

# Intent Router Agent
router = IntentRouterAgent(gemini_api_key=Config.GEMINI_API_KEY)

# Retrieval Agent
retrieval = RetrievalAgent(
    weaviate_host=Config.WEAVIATE_HOST,
    weaviate_port=Config.WEAVIATE_PORT,
    gemini_api_key=Config.GEMINI_API_KEY
)
```

### Dynamic Configuration Access
```python
# Access configuration values
embedding_model = Config.EMBEDDING_MODEL
batch_size = Config.EMBEDDING_BATCH_SIZE
products = Config.INSURANCE_PRODUCTS

# Build URLs
weaviate_url = Config.get_weaviate_url()

# Validate before use
if Config.validate():
    # Proceed with operations
    pass
```

### Configuration Override
```python
# Temporary override for testing
original_batch_size = Config.EMBEDDING_BATCH_SIZE
Config.EMBEDDING_BATCH_SIZE = 10  # Smaller batch for testing

try:
    # Run test with smaller batch
    test_embedding_process()
finally:
    # Restore original value
    Config.EMBEDDING_BATCH_SIZE = original_batch_size
```

## Security Best Practices

### API Key Management
```python
# Good: Use environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Bad: Hardcode in source
GEMINI_API_KEY = "AIzaSyAyiV7SsxfU7ldJGwIbN6C7IQZtag7z53M"  # Never do this!
```

### Secure Defaults
```python
# Provide secure defaults
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")  # Safe default
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))        # Reasonable timeout
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"  # Secure default
```

### Configuration Validation
```python
# Validate sensitive configurations
if Config.GEMINI_API_KEY == "default-key":
    raise ValueError("Please set a valid GEMINI_API_KEY")

if Config.DEBUG_MODE and Config.ENVIRONMENT == "production":
    raise ValueError("DEBUG_MODE should not be enabled in production")
```

## Deployment Configurations

### Docker Configuration
```dockerfile
# Dockerfile environment variables
ENV GEMINI_API_KEY=""
ENV WEAVIATE_HOST="weaviate"
ENV WEAVIATE_PORT="8080"
ENV SOURCE_DIR="/app/Source"

# Copy configuration
COPY config.py /app/
COPY .env /app/
```

### Kubernetes Configuration
```yaml
# ConfigMap for non-sensitive data
apiVersion: v1
kind: ConfigMap
metadata:
  name: hlas-config
data:
  WEAVIATE_HOST: "weaviate-service"
  WEAVIATE_PORT: "8080"
  SOURCE_DIR: "/app/Source"
  EMBEDDING_MODEL: "gemini-embedding-001"

---
# Secret for sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: hlas-secrets
type: Opaque
data:
  GEMINI_API_KEY: <base64-encoded-key>
```

### Cloud Deployment
```bash
# AWS Parameter Store
aws ssm put-parameter \
  --name "/hlas/gemini-api-key" \
  --value "your-api-key" \
  --type "SecureString"

# Azure Key Vault
az keyvault secret set \
  --vault-name "hlas-keyvault" \
  --name "gemini-api-key" \
  --value "your-api-key"

# Google Secret Manager
gcloud secrets create gemini-api-key \
  --data-file="api-key.txt"
```

## Configuration Testing

### Unit Tests
```python
import unittest
from unittest.mock import patch
from config import Config

class TestConfig(unittest.TestCase):
    
    def test_default_values(self):
        """Test default configuration values"""
        self.assertEqual(Config.WEAVIATE_HOST, "localhost")
        self.assertEqual(Config.WEAVIATE_PORT, 8080)
        self.assertEqual(Config.SOURCE_DIR, "Source")
    
    @patch.dict(os.environ, {"WEAVIATE_PORT": "9999"})
    def test_environment_override(self):
        """Test environment variable override"""
        # Reload config with new environment
        importlib.reload(config)
        self.assertEqual(Config.WEAVIATE_PORT, 9999)
    
    def test_validation_success(self):
        """Test successful validation"""
        with patch('os.path.exists', return_value=True):
            self.assertTrue(Config.validate())
    
    def test_validation_failure(self):
        """Test validation failure"""
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(ValueError):
                Config.validate()
```

### Integration Tests
```python
def test_agent_initialization_with_config():
    """Test that agents can be initialized with config values"""
    Config.validate()
    
    # Test each agent initialization
    embedding_agent = EmbeddingAgent(
        source_dir=Config.SOURCE_DIR,
        gemini_api_key=Config.GEMINI_API_KEY,
        weaviate_host=Config.WEAVIATE_HOST,
        weaviate_port=Config.WEAVIATE_PORT
    )
    
    intent_router = IntentRouterAgent(gemini_api_key=Config.GEMINI_API_KEY)
    
    # Verify agents are properly configured
    self.assertIsNotNone(embedding_agent)
    self.assertIsNotNone(intent_router)
```

## Future Enhancements

### Planned Features
- **Configuration Profiles**: Multiple configuration profiles for different environments
- **Dynamic Reloading**: Hot reload of configuration without restart
- **Configuration UI**: Web interface for configuration management
- **Validation Rules**: More sophisticated validation with custom rules
- **Configuration History**: Track configuration changes over time
- **Encrypted Configuration**: Encryption for sensitive configuration data
- **Configuration Templates**: Templates for common deployment scenarios
- **Health Checks**: Configuration-based health check endpoints
