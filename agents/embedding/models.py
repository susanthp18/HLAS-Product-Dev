"""
Data models for the Embedding Agent
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid


class DocumentType(Enum):
    """Types of insurance documents"""
    TERMS = "Terms"
    FAQ = "FAQ"
    BENEFITS_SUMMARY = "Benefits Summary"


class ProductType(Enum):
    """Insurance product types"""
    CAR = "Car"
    EARLY = "Early"
    FAMILY = "Family"
    HOME = "Home"
    HOSPITAL = "Hospital"
    MAID = "Maid"
    TRAVEL = "Travel"


@dataclass
class DocumentChunk:
    """Represents a chunk of an insurance document"""
    # Metadata
    product_name: ProductType
    policy_name: str
    document_type: DocumentType
    source_file: str
    
    # Content
    content: str
    
    # Optional metadata
    section_hierarchy: List[str] = field(default_factory=list)
    question: Optional[str] = None
    is_table_data: bool = False
    
    # Generated fields
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    summary: Optional[str] = None
    hypothetical_questions: List[str] = field(default_factory=list)
    
    # Embeddings (will be populated during processing)
    content_embedding: Optional[List[float]] = None
    summary_embedding: Optional[List[float]] = None
    hypothetical_question_embedding: Optional[List[float]] = None
    
    def to_weaviate_object(self) -> Dict[str, Any]:
        """Convert to Weaviate-compatible object"""
        return {
            "product_name": self.product_name.value,
            "policy_name": self.policy_name,
            "document_type": self.document_type.value,
            "source_file": self.source_file,
            "section_hierarchy": self.section_hierarchy,
            "is_table_data": self.is_table_data,
            "content": self.content,
            "question": self.question or "",
            "chunk_id": self.chunk_id,
            # Temporary fields for vectorization
            "summary": self.summary or "",
            "hypothetical_questions": " ".join(self.hypothetical_questions) if self.hypothetical_questions else ""
        }


@dataclass
class ProductDocuments:
    """Groups documents for a single insurance product"""
    product_type: ProductType
    terms_file: Optional[str] = None
    faq_file: Optional[str] = None
    benefits_file: Optional[str] = None
    
    def get_policy_name(self) -> str:
        """Infer policy name from product type"""
        policy_names = {
            ProductType.CAR: "Car Protect360",
            ProductType.EARLY: "Early Protect360 Plus",
            ProductType.FAMILY: "Family Protect360",
            ProductType.HOME: "Home Protect360",
            ProductType.HOSPITAL: "Hospital Protect360",
            ProductType.MAID: "Maid Protect360 PRO",
            ProductType.TRAVEL: "Travel Protect360"
        }
        return policy_names.get(self.product_type, f"{self.product_type.value} Insurance") 