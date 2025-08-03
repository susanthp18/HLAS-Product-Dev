"""
Embedding Agent Module

Responsible for converting raw insurance documents into structured, 
multi-faceted vector indexes.
"""

from .embedding_agent import EmbeddingAgent
from .chunking_strategies import (
    MarkdownChunker,
    FAQChunker,
    BenefitsTableChunker
)
from .metadata_enricher import MetadataEnricher

__all__ = [
    'EmbeddingAgent',
    'MarkdownChunker',
    'FAQChunker', 
    'BenefitsTableChunker',
    'MetadataEnricher'
] 