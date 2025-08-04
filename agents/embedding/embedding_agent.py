"""
Main Embedding Agent that orchestrates the document processing pipeline
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from .models import DocumentChunk, ProductDocuments, ProductType, DocumentType
from .chunking_strategies import ChunkerFactory
from .metadata_enricher import MetadataEnricher
from .vector_store import WeaviateVectorStore


class EmbeddingAgent:
    """
    Main agent responsible for converting raw insurance documents 
    into structured, multi-faceted vector indexes
    """
    
    def __init__(self, 
                 source_dir: str = "Source",
                 gemini_api_key: str = None,
                 weaviate_host: str = "localhost",
                 weaviate_port: int = 8080):
        """
        Initialize the Embedding Agent
        
        Args:
            source_dir: Directory containing the source documents
            gemini_api_key: API key for Gemini
            weaviate_host: Weaviate host address
            weaviate_port: Weaviate port
        """
        self.source_dir = Path(source_dir)
        self.gemini_api_key = gemini_api_key
        
        # Initialize components
        self.enricher = MetadataEnricher(gemini_api_key)
        self.vector_store = WeaviateVectorStore(
            host=weaviate_host,
            port=weaviate_port,
            gemini_api_key=gemini_api_key
        )
        
        # Product documents storage
        self.product_documents: Dict[ProductType, ProductDocuments] = {}
        
    def run(self):
        """Execute the complete embedding pipeline"""
        print("Starting Embedding Agent Pipeline...")
        
        # Phase 1: Data Loading & Product Consolidation
        print("\n=== Phase 1: Data Loading & Product Consolidation ===")
        self._load_and_consolidate_documents()
        
        # Phase 2: Advanced Chunking & Metadata Enrichment
        print("\n=== Phase 2: Advanced Chunking & Metadata Enrichment ===")
        all_chunks = self._chunk_all_documents()
        
        # Phase 3: Multi-Vector Embedding Generation
        print("\n=== Phase 3: Multi-Vector Embedding Generation ===")
        enriched_chunks = self._enrich_chunks(all_chunks)
        embedded_chunks = self._generate_embeddings(enriched_chunks)
        
        # Phase 4: Weaviate Schema Design & Ingestion
        print("\n=== Phase 4: Weaviate Schema Design & Ingestion ===")
        self._setup_vector_store()
        self._ingest_chunks(embedded_chunks)
        
        print("\n✅ Embedding Agent Pipeline Complete!")
        print(f"Total chunks processed: {len(embedded_chunks)}")
        
        return embedded_chunks
    
    def _load_and_consolidate_documents(self):
        """Phase 1: Load and group files by product"""
        print("Scanning for insurance products...")
        
        # Define expected files for each product
        for product_name in ["Car", "Early", "Family", "Home", "Hospital", "Maid", "Travel"]:
            product_type = ProductType(product_name)
            product_docs = ProductDocuments(product_type=product_type)
            
            # Check for Terms file
            terms_path = self.source_dir / "Terms" / f"{product_name}_Terms.md"
            if terms_path.exists():
                product_docs.terms_file = str(terms_path)
                print(f"  ✓ Found {product_name} Terms: {terms_path.name}")
            
            # Check for FAQs file
            faq_path = self.source_dir / "FAQs" / f"{product_name}_FAQs.txt"
            if faq_path.exists():
                product_docs.faq_file = str(faq_path)
                print(f"  ✓ Found {product_name} FAQs: {faq_path.name}")
            
            # Check for Benefits/Tables file
            benefits_path = self.source_dir / "Benefits" / f"{product_name}_Tables.txt"
            if benefits_path.exists():
                product_docs.benefits_file = str(benefits_path)
                print(f"  ✓ Found {product_name} Benefits: {benefits_path.name}")
            
            self.product_documents[product_type] = product_docs
        
        print(f"\nTotal products identified: {len(self.product_documents)}")
    
    def _chunk_all_documents(self) -> List[DocumentChunk]:
        """Phase 2: Chunk all documents using appropriate strategies"""
        all_chunks = []
        
        for product_type, product_docs in self.product_documents.items():
            print(f"\nProcessing {product_type.value} insurance documents...")
            
            # Get policy name
            policy_name = product_docs.get_policy_name()
            
            # Process Terms document
            if product_docs.terms_file:
                chunks = self._chunk_document(
                    product_docs.terms_file,
                    product_type,
                    policy_name
                )
                all_chunks.extend(chunks)
                print(f"  - Terms document: {len(chunks)} chunks")
            
            # Process FAQs document
            if product_docs.faq_file:
                chunks = self._chunk_document(
                    product_docs.faq_file,
                    product_type,
                    policy_name
                )
                all_chunks.extend(chunks)
                print(f"  - FAQs document: {len(chunks)} chunks")
            
            # Process Benefits document
            if product_docs.benefits_file:
                chunks = self._chunk_document(
                    product_docs.benefits_file,
                    product_type,
                    policy_name
                )
                all_chunks.extend(chunks)
                print(f"  - Benefits document: {len(chunks)} chunks")
        
        print(f"\nTotal chunks created: {len(all_chunks)}")
        return all_chunks
    
    def _chunk_document(self, 
                       file_path: str, 
                       product_type: ProductType,
                       policy_name: str) -> List[DocumentChunk]:
        """Chunk a single document using the appropriate strategy"""
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Get appropriate chunker
        chunker = ChunkerFactory.get_chunker(file_path)
        
        # Prepare metadata
        metadata = {
            'product_type': product_type,
            'policy_name': policy_name,
            'source_file': os.path.basename(file_path)
        }
        
        # Chunk the content
        chunks = chunker.chunk(content, metadata)
        
        return chunks
    
    def _enrich_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Phase 3: Enrich chunks with summaries and hypothetical questions"""
        print(f"Enriching {len(chunks)} chunks with AI-generated metadata...")
        print("📊 Progress will be shown for each chunk...")

        enriched_chunks = []

        for i, chunk in enumerate(chunks, 1):
            print(f"🔄 [{i:3d}/{len(chunks)}] Processing: {chunk.product_name} - {chunk.document_type} (ID: {chunk.chunk_id[:8]})", end=" ", flush=True)

            try:
                # Enrich single chunk
                enriched_batch = self.enricher.enrich_chunks_batch([chunk])
                if enriched_batch:
                    enriched_chunks.extend(enriched_batch)
                    print("✅")
                else:
                    print("⚠️  (no enrichment)")
                    enriched_chunks.append(chunk)  # Keep original if enrichment fails

            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}...")
                enriched_chunks.append(chunk)  # Keep original if enrichment fails

            # Show periodic summary
            if i % 50 == 0:
                print(f"📈 Milestone: {i}/{len(chunks)} chunks processed ({i/len(chunks)*100:.1f}%)")

        print(f"✅ Enrichment complete: {len(enriched_chunks)} chunks enriched")
        return enriched_chunks
    
    def _generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for all chunks"""
        print(f"Generating multi-vector embeddings for {len(chunks)} chunks...")
        print("📊 Progress will be shown for each chunk...")

        # Generate embeddings using vector store with progress tracking
        embedded_chunks = self.vector_store.generate_embeddings_with_progress(chunks)
        
        # Count successful embeddings
        content_count = sum(1 for c in embedded_chunks if c.content_embedding)
        summary_count = sum(1 for c in embedded_chunks if c.summary_embedding)
        question_count = sum(1 for c in embedded_chunks if c.hypothetical_question_embedding)
        
        print(f"  - Content embeddings: {content_count}")
        print(f"  - Summary embeddings: {summary_count}")
        print(f"  - Question embeddings: {question_count}")
        
        return embedded_chunks
    
    def _setup_vector_store(self):
        """Setup Weaviate schema"""
        print("Setting up Weaviate schema...")
        self.vector_store.create_schema()
    
    def _ingest_chunks(self, chunks: List[DocumentChunk]):
        """Ingest chunks into Weaviate"""
        print(f"Ingesting {len(chunks)} chunks into Weaviate...")
        self.vector_store.insert_chunks(chunks)
        print("✓ Ingestion complete!")
    
    def search(self, query: str, search_type: str = "hybrid", limit: int = 5):
        """
        Search the vector store
        
        Args:
            query: Search query
            search_type: Type of search ("content", "summary", "questions", "hybrid")
            limit: Number of results to return
        """
        if search_type == "content":
            return self.vector_store.search_content(query, limit)
        elif search_type == "summary":
            return self.vector_store.search_summary(query, limit)
        elif search_type == "questions":
            return self.vector_store.search_questions(query, limit)
        else:
            return self.vector_store.hybrid_search(query, limit)
    
    def close(self):
        """Clean up resources"""
        self.vector_store.close() 