"""
Data models for Response Generation Agent
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from agents.retrieval.models import ChunkResult


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring system"""

    # Relevance score thresholds
    min_relevance_threshold: float = 0.25
    standard_relevance_threshold: float = 0.3
    complex_query_relevance_threshold: float = 0.35

    # Length thresholds for different query types
    factual_query_min_words: int = 8
    comparison_query_min_words: int = 20
    default_min_words: int = 12

    # Confidence adjustment factors
    strong_uncertainty_penalty: float = 0.6
    moderate_uncertainty_penalty: float = 0.8
    weak_uncertainty_penalty: float = 0.9
    max_specificity_boost: float = 1.15
    specificity_boost_per_item: float = 0.05

    # Length adjustment factors
    very_short_penalty: float = 0.7   # < 5 words
    short_penalty: float = 0.85       # < 10 words
    adequate_penalty: float = 0.95    # < 15 words

    # Minimum confidence to distinguish from no-confidence
    min_confidence_threshold: float = 0.01

    # Query term matching threshold for relevance
    query_term_match_threshold: float = 0.3


class CitationStyle(Enum):
    """Citation formatting styles"""
    NUMBERED = "numbered"  # [1], [2], [3]
    INLINE = "inline"      # (Source: Car Insurance Terms)
    FOOTNOTE = "footnote"  # ¹, ², ³


@dataclass
class Citation:
    """Individual citation information"""
    id: str
    product_name: str
    document_type: str
    source_file: str
    section_hierarchy: List[str]
    relevance_score: float
    
    def format_citation(self, style: CitationStyle, citation_number: int = None) -> str:
        """Format citation according to specified style"""
        source_info = f"{self.product_name} {self.document_type}"
        
        if self.section_hierarchy:
            source_info += f" - {' > '.join(self.section_hierarchy)}"
        
        if style == CitationStyle.NUMBERED:
            return f"[{citation_number}]"
        elif style == CitationStyle.INLINE:
            return f"(Source: {source_info})"
        elif style == CitationStyle.FOOTNOTE:
            footnote_symbols = ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹", "¹⁰"]
            if citation_number and citation_number <= len(footnote_symbols):
                return footnote_symbols[citation_number - 1]
            return f"[{citation_number}]"
        
        return f"[{citation_number}]"
    
    def get_full_reference(self, citation_number: int = None) -> str:
        """Get full reference for citation list"""
        source_info = f"{self.product_name} {self.document_type}"
        if self.section_hierarchy:
            source_info += f" - {' > '.join(self.section_hierarchy)}"
        
        prefix = f"[{citation_number}] " if citation_number else ""
        return f"{prefix}{source_info} (Relevance: {self.relevance_score:.2f})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary"""
        return {
            "id": self.id,
            "product_name": self.product_name,
            "document_type": self.document_type,
            "source_file": self.source_file,
            "section_hierarchy": self.section_hierarchy,
            "relevance_score": self.relevance_score
        }


@dataclass
class ResponseRequest:
    """Request for response generation"""
    original_query: str
    context_chunks: List[ChunkResult]
    citation_style: CitationStyle = CitationStyle.NUMBERED
    max_response_length: int = 1000
    include_confidence_score: bool = True
    confidence_config: ConfidenceConfig = None
    
    @property
    def has_context(self) -> bool:
        """Check if request has any context chunks"""
        return bool(self.context_chunks)
    
    @property
    def context_summary(self) -> Dict[str, Any]:
        """Get summary of context chunks"""
        if not self.context_chunks:
            return {"total_chunks": 0, "products": [], "avg_relevance": 0.0}

        products = list(set(chunk.product_name for chunk in self.context_chunks))

        # Calculate average relevance with None handling
        valid_scores = []
        for chunk in self.context_chunks:
            if hasattr(chunk, 'relevance_score') and chunk.relevance_score is not None:
                try:
                    score = float(chunk.relevance_score)
                    if 0.0 <= score <= 1.0:
                        valid_scores.append(score)
                except (ValueError, TypeError):
                    continue

        avg_relevance = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        # Handle document types (both string and enum)
        doc_types = []
        for chunk in self.context_chunks:
            if hasattr(chunk, 'document_type') and chunk.document_type:
                if hasattr(chunk.document_type, 'value'):
                    doc_types.append(chunk.document_type.value)
                else:
                    doc_types.append(str(chunk.document_type))

        return {
            "total_chunks": len(self.context_chunks),
            "products": products,
            "avg_relevance": avg_relevance,
            "document_types": list(set(doc_types))
        }


@dataclass
class ResponseResult:
    """Result from response generation"""
    answer: str
    citations: List[Citation]
    confidence_score: float
    context_used: int
    context_available: int
    has_sufficient_context: bool
    reasoning: str
    
    def format_response(self, include_citations: bool = True, include_confidence: bool = False) -> str:
        """Format the complete response with citations"""
        response_parts = [self.answer]
        
        if include_citations and self.citations:
            response_parts.append("\n\n**Sources:**")
            for i, citation in enumerate(self.citations, 1):
                response_parts.append(citation.get_full_reference(i))
        
        if include_confidence and self.confidence_score > 0:
            confidence_text = f"\n\n*Confidence: {self.confidence_score:.1%}*"
            response_parts.append(confidence_text)
        
        return "\n".join(response_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "answer": self.answer,
            "citations": [
                {
                    "id": citation.id,
                    "product_name": citation.product_name,
                    "document_type": citation.document_type,
                    "source_file": citation.source_file,
                    "section_hierarchy": citation.section_hierarchy,
                    "relevance_score": citation.relevance_score
                }
                for citation in self.citations
            ],
            "confidence_score": self.confidence_score,
            "context_used": self.context_used,
            "context_available": self.context_available,
            "has_sufficient_context": self.has_sufficient_context,
            "reasoning": self.reasoning,
            "formatted_response": self.format_response(include_citations=True, include_confidence=True)
        }
