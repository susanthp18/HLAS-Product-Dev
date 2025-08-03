"""
Content-aware chunking strategies for different document types
"""

import re
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
from .models import DocumentChunk, DocumentType, ProductType


class ChunkingStrategy(ABC):
    """Base class for chunking strategies"""
    
    @abstractmethod
    def chunk(self, content: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk the content and return a list of DocumentChunk objects"""
        pass


class MarkdownChunker(ChunkingStrategy):
    """
    Recursive Markdown Header Splitter for Terms documents.
    Respects the hierarchical structure of markdown documents.
    """
    
    def chunk(self, content: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk markdown content by headers"""
        chunks = []
        
        # Extract policy name from H1 if present
        policy_name = metadata.get('policy_name', '')
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            policy_name = h1_match.group(1).strip()
        
        # Split content by headers
        sections = self._split_by_headers(content)
        
        for section_hierarchy, section_content in sections:
            if section_content.strip():  # Skip empty sections
                chunk = DocumentChunk(
                    product_name=metadata['product_type'],
                    policy_name=policy_name,
                    document_type=DocumentType.TERMS,
                    source_file=metadata['source_file'],
                    content=section_content.strip(),
                    section_hierarchy=section_hierarchy
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_by_headers(self, content: str) -> List[Tuple[List[str], str]]:
        """Split content by markdown headers and maintain hierarchy"""
        sections = []
        current_hierarchy = []
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section if exists
                if current_content:
                    sections.append((
                        current_hierarchy.copy(),
                        '\n'.join(current_content).strip()
                    ))
                
                # Update hierarchy
                level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                
                # Truncate hierarchy to current level
                current_hierarchy = current_hierarchy[:level-1]
                current_hierarchy.append(header_text)
                
                # Reset content
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_content:
            sections.append((
                current_hierarchy.copy(),
                '\n'.join(current_content).strip()
            ))
        
        return sections


class FAQChunker(ChunkingStrategy):
    """
    Question-Answer pair chunker for FAQ documents.
    Each Q&A pair becomes an atomic chunk.
    """
    
    def chunk(self, content: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk FAQ content by Q&A pairs"""
        chunks = []
        
        # Split by "Q:" pattern
        qa_pairs = re.split(r'\nQ:\s*', content)
        
        for qa_pair in qa_pairs:
            if not qa_pair.strip():
                continue
                
            # Extract question and answer
            parts = qa_pair.split('\nA:', 1)
            if len(parts) == 2:
                question = parts[0].strip()
                answer = parts[1].strip()
                
                chunk = DocumentChunk(
                    product_name=metadata['product_type'],
                    policy_name=metadata.get('policy_name', ''),
                    document_type=DocumentType.FAQ,
                    source_file=metadata['source_file'],
                    content=answer,
                    question=question
                )
                chunks.append(chunk)
        
        return chunks


class BenefitsTableChunker(ChunkingStrategy):
    """
    Line-by-line chunker for Benefits/Tables documents.
    Each line represents a specific benefit and its value.
    """
    
    def chunk(self, content: str, metadata: dict) -> List[DocumentChunk]:
        """Chunk benefits table content line by line"""
        chunks = []
        current_table = None
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a table header
            if line.startswith('TABLE') and 'FROM' in line:
                current_table = line
                continue
            
            # Extract section title if present (for grouping related benefits)
            section_match = re.match(r'^([\w\s]+):\s*$', line)
            if section_match:
                section_title = section_match.group(1)
                continue
            
            # Create chunk for benefit line
            chunk = DocumentChunk(
                product_name=metadata['product_type'],
                policy_name=metadata.get('policy_name', ''),
                document_type=DocumentType.BENEFITS_SUMMARY,
                source_file=metadata['source_file'],
                content=line,
                is_table_data=True,
                section_hierarchy=[current_table] if current_table else []
            )
            chunks.append(chunk)
        
        return chunks


class ChunkerFactory:
    """Factory for creating appropriate chunker based on document type"""
    
    @staticmethod
    def get_chunker(file_path: str) -> ChunkingStrategy:
        """Return appropriate chunker based on file extension"""
        if file_path.endswith('_Terms.md'):
            return MarkdownChunker()
        elif file_path.endswith('_FAQs.txt'):
            return FAQChunker()
        elif file_path.endswith('_Tables.txt'):
            return BenefitsTableChunker()
        else:
            raise ValueError(f"Unknown document type for file: {file_path}") 