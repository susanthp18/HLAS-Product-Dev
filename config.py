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

    # MongoDB Configuration
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT: int = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "hlas_insurance")
    MONGODB_COLLECTION: str = os.getenv("MONGODB_COLLECTION", "conversation_history")
    
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

    @classmethod
    def get_mongodb_url(cls) -> str:
        """Get full MongoDB URL"""
        return f"mongodb://{cls.MONGODB_HOST}:{cls.MONGODB_PORT}"