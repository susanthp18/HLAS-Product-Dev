"""
Weaviate vector store interface for embedding storage
"""

from typing import List, Optional, Dict, Any
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Configure, Property, DataType
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content

from .models import DocumentChunk
from config import Config


class WeaviateVectorStore:
    """Interface for Weaviate vector database operations"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, gemini_api_key: str = None):
        """Initialize Weaviate client"""
        self.client = weaviate.connect_to_local(host=host, port=port)
        
        # Configure Gemini for embeddings
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        self.collection_name = "InsuranceDocumentChunk"
        
    def create_schema(self):
        """Create the Weaviate schema for insurance documents"""
        if self.client.collections.exists(self.collection_name):
            print(f"Collection {self.collection_name} already exists. Deleting...")
            self.client.collections.delete(self.collection_name)
        
        # Create collection with multi-vector configuration
        self.client.collections.create(
            name=self.collection_name,
            properties=[
                # Metadata Properties
                Property(name="product_name", data_type=DataType.TEXT),
                Property(name="policy_name", data_type=DataType.TEXT),
                Property(name="document_type", data_type=DataType.TEXT),
                Property(name="source_file", data_type=DataType.TEXT),
                Property(name="section_hierarchy", data_type=DataType.TEXT_ARRAY),
                Property(name="is_table_data", data_type=DataType.BOOL),
                
                # Content Properties
                Property(name="content", data_type=DataType.TEXT),
                Property(name="question", data_type=DataType.TEXT),
                Property(name="chunk_id", data_type=DataType.TEXT),
                
                # Temporary fields for vectorization
                Property(name="summary", data_type=DataType.TEXT),
                Property(name="hypothetical_questions", data_type=DataType.TEXT),
            ],
            # Configure multiple named vectors
            vectorizer_config=[
                Configure.NamedVectors.none(name="content_embedding"),
                Configure.NamedVectors.none(name="summary_embedding"),
                Configure.NamedVectors.none(name="hypothetical_question_embedding"),
            ]
        )
        
        print(f"Created collection: {self.collection_name}")
    
    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for chunks using Gemini"""
        for chunk in chunks:
            try:
                # Generate content embedding
                if chunk.content:
                    content_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=chunk.content[:2048]  # Limit length
                    )
                    chunk.content_embedding = content_result['embedding']
                
                # Generate summary embedding
                if chunk.summary:
                    summary_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=chunk.summary
                    )
                    chunk.summary_embedding = summary_result['embedding']
                
                # Generate hypothetical questions embedding
                if chunk.hypothetical_questions:
                    questions_text = " ".join(chunk.hypothetical_questions)
                    questions_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=questions_text[:2048]  # Limit length
                    )
                    chunk.hypothetical_question_embedding = questions_result['embedding']
                    
            except Exception as e:
                print(f"Error generating embeddings for chunk {chunk.chunk_id}: {e}")
        
        return chunks

    def generate_embeddings_with_progress(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Generate embeddings for chunks using Gemini with detailed progress tracking"""

        for i, chunk in enumerate(chunks, 1):
            print(f"🔄 [{i:3d}/{len(chunks)}] Embedding: {chunk.product_name} - {chunk.document_type} (Chunk {chunk.chunk_index})", end=" ", flush=True)

            try:
                embeddings_generated = 0

                # Generate content embedding
                if chunk.content:
                    content_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=chunk.content[:2048]  # Limit length
                    )
                    chunk.content_embedding = content_result['embedding']
                    embeddings_generated += 1

                # Generate summary embedding
                if chunk.summary:
                    summary_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=chunk.summary
                    )
                    chunk.summary_embedding = summary_result['embedding']
                    embeddings_generated += 1

                # Generate hypothetical questions embedding
                if chunk.hypothetical_questions:
                    questions_text = " ".join(chunk.hypothetical_questions)
                    questions_result = genai.embed_content(
                        model=Config.EMBEDDING_MODEL,
                        content=questions_text[:2048]  # Limit length
                    )
                    chunk.hypothetical_question_embedding = questions_result['embedding']
                    embeddings_generated += 1

                print(f"✅ ({embeddings_generated} embeddings)")

            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}...")

            # Show periodic summary
            if i % 50 == 0:
                print(f"📈 Milestone: {i}/{len(chunks)} chunks embedded ({i/len(chunks)*100:.1f}%)")

        print(f"✅ Embedding generation complete: {len(chunks)} chunks processed")
        return chunks

    def insert_chunks(self, chunks: List[DocumentChunk], batch_size: int = 100):
        """Insert chunks into Weaviate using batch operations"""
        collection = self.client.collections.get(self.collection_name)
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            with collection.batch.dynamic() as batch:
                for chunk in batch_chunks:
                    # Prepare vectors
                    vectors = {}
                    if chunk.content_embedding:
                        vectors["content_embedding"] = chunk.content_embedding
                    if chunk.summary_embedding:
                        vectors["summary_embedding"] = chunk.summary_embedding
                    if chunk.hypothetical_question_embedding:
                        vectors["hypothetical_question_embedding"] = chunk.hypothetical_question_embedding
                    
                    # Add object to batch
                    batch.add_object(
                        properties=chunk.to_weaviate_object(),
                        vector=vectors
                    )
            
            print(f"Inserted batch {i//batch_size + 1} ({len(batch_chunks)} chunks)")
    
    def search_content(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search using content embeddings"""
        return self._search_vector(query, "content_embedding", limit)
    
    def search_summary(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search using summary embeddings"""
        return self._search_vector(query, "summary_embedding", limit)
    
    def search_questions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search using hypothetical question embeddings"""
        return self._search_vector(query, "hypothetical_question_embedding", limit)
    
    def hybrid_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform hybrid search across all vector types"""
        # Get results from all vector types
        content_results = self.search_content(query, limit)
        summary_results = self.search_summary(query, limit)
        question_results = self.search_questions(query, limit)
        
        # Combine and deduplicate results
        all_results = {}
        
        # Add results with scores
        for result in content_results:
            chunk_id = result['properties']['chunk_id']
            all_results[chunk_id] = result
        
        for result in summary_results:
            chunk_id = result['properties']['chunk_id']
            if chunk_id not in all_results:
                all_results[chunk_id] = result
        
        for result in question_results:
            chunk_id = result['properties']['chunk_id']
            if chunk_id not in all_results:
                all_results[chunk_id] = result
        
        # Return top results
        return list(all_results.values())[:limit]
    
    def _search_vector(self, query: str, vector_name: str, limit: int) -> List[Dict[str, Any]]:
        """Internal method to search a specific vector"""
        collection = self.client.collections.get(self.collection_name)
        
        # Generate query embedding
        query_result = genai.embed_content(
            model=Config.EMBEDDING_MODEL,
            content=query
        )
        query_embedding = query_result['embedding']
        
        # Perform search
        response = collection.query.near_vector(
            near_vector=query_embedding,
            target_vector=vector_name,
            limit=limit,
            return_metadata=['distance']
        )
        
        results = []
        for obj in response.objects:
            results.append({
                'properties': dict(obj.properties),
                'distance': obj.metadata.distance
            })
        
        return results
    
    def close(self):
        """Close the Weaviate connection"""
        self.client.close() 