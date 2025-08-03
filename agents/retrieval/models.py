"""
Data models for Retrieval Agent
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import json

from agents.intent_router.models import IntentClassification


class SearchStrategy(Enum):
    """Search strategy types for retrieval"""
    HYBRID = "hybrid"
    CONTENT_ONLY = "content_only"
    SUMMARY_ONLY = "summary_only"
    QUESTIONS_ONLY = "questions_only"
    MULTI_VECTOR = "multi_vector"


@dataclass
class RetrievalRequest:
    """
    Request object for the Retrieval Agent
    
    This represents the "work order" from the Intent Router Agent
    """
    intent_classification: IntentClassification
    top_k: int = 5
    search_strategy: SearchStrategy = SearchStrategy.MULTI_VECTOR
    
    @property
    def query(self) -> str:
        """Get the original query"""
        return self.intent_classification.original_query
    
    @property
    def product_focus(self) -> List[str]:
        """Get the product focus list"""
        return self.intent_classification.product_focus
    
    @property
    def entities(self) -> List[str]:
        """Get the extracted entities"""
        return self.intent_classification.entities
    
    @property
    def is_purchase_intent(self) -> bool:
        """Get purchase intent flag"""
        return self.intent_classification.is_purchase_intent
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "intent_classification": self.intent_classification.to_dict(),
            "top_k": self.top_k,
            "search_strategy": self.search_strategy.value
        }


@dataclass
class ChunkResult:
    """
    Result object representing a retrieved document chunk
    
    Contains the retrieved text and rich metadata for downstream agents
    """
    content: str
    product_name: str
    document_type: str
    source_file: str
    section_hierarchy: List[str]
    relevance_score: float
    
    # Optional metadata
    chunk_id: Optional[str] = None
    policy_name: Optional[str] = None
    question: Optional[str] = None
    summary: Optional[str] = None
    is_table_data: bool = False
    
    # Search metadata
    search_method: Optional[str] = None
    original_distance: Optional[float] = None
    rerank_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "content": self.content,
            "product_name": self.product_name,
            "document_type": self.document_type,
            "source_file": self.source_file,
            "section_hierarchy": self.section_hierarchy,
            "relevance_score": self.relevance_score,
            "chunk_id": self.chunk_id,
            "policy_name": self.policy_name,
            "question": self.question,
            "summary": self.summary,
            "is_table_data": self.is_table_data,
            "search_method": self.search_method,
            "original_distance": self.original_distance,
            "rerank_score": self.rerank_score
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_weaviate_result(cls, properties: Dict[str, Any],
                           relevance_score: float,
                           search_method: str = None,
                           original_distance: float = None) -> 'ChunkResult':
        """Create ChunkResult from Weaviate search result properties"""

        return cls(
            content=properties.get('content', ''),
            product_name=properties.get('product_name', ''),
            document_type=properties.get('document_type', ''),
            source_file=properties.get('source_file', ''),
            section_hierarchy=properties.get('section_hierarchy', []),
            relevance_score=relevance_score,
            chunk_id=properties.get('chunk_id'),
            policy_name=properties.get('policy_name'),
            question=properties.get('question'),
            summary=properties.get('summary'),
            is_table_data=properties.get('is_table_data', False),
            search_method=search_method,
            original_distance=original_distance
        )


@dataclass
class SearchConfig:
    """Configuration for search parameters"""
    
    # Multi-vector weights
    question_weight: float = 0.6
    summary_weight: float = 0.25
    content_weight: float = 0.15
    
    # Search parameters
    hybrid_alpha: float = 0.7  # Balance between vector (1.0) and keyword (0.0) search

    # Relevance thresholds
    min_relevance_score: float = 0.1
    max_distance: float = 1.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "question_weight": self.question_weight,
            "summary_weight": self.summary_weight,
            "content_weight": self.content_weight,
            "hybrid_alpha": self.hybrid_alpha,
            "min_relevance_score": self.min_relevance_score,
            "max_distance": self.max_distance
        }


# Common insurance terms for query enhancement
INSURANCE_TERMS = {
    # Abbreviations and acronyms
    "ncd": "no claim discount",
    "fdw": "foreign domestic worker",
    "covid": "covid-19",
    "icu": "intensive care unit",
    "gp": "general practitioner",
    "a&e": "accident and emergency",
    
    # Common variations
    "helper": "domestic helper",
    "maid": "domestic helper",
    "car": "vehicle",
    "auto": "vehicle",
    "house": "home",
    "property": "home",
    "trip": "travel",
    "vacation": "travel",
    "holiday": "travel",
    
    # Insurance specific
    "excess": "deductible",
    "sum insured": "coverage limit",
    "premium": "insurance cost",
    "claim": "insurance claim",
    "policy": "insurance policy",
    "coverage": "insurance coverage",
    "benefit": "insurance benefit"
}
