"""
Retrieval Agent

The librarian of the system that finds the most relevant document chunks
using sophisticated multi-vector hybrid search strategies.
"""

import re
from typing import List, Dict, Any, Optional
import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
import google.generativeai as genai

from .models import (
    RetrievalRequest, ChunkResult, SearchStrategy, SearchConfig, 
    INSURANCE_TERMS
)
from agents.intent_router.models import IntentClassification
from config import Config


class RetrievalAgent:
    """
    Retrieval Agent for HLAS Insurance System
    
    Executes sophisticated multi-vector hybrid search to find the most
    relevant document chunks from Weaviate based on intent classification.
    """
    
    def __init__(self,
                 weaviate_host: str = None,
                 weaviate_port: int = None,
                 gemini_api_key: str = None,
                 search_config: SearchConfig = None):
        """Initialize the Retrieval Agent"""

        # Configuration
        self.weaviate_host = weaviate_host or Config.WEAVIATE_HOST
        self.weaviate_port = weaviate_port or Config.WEAVIATE_PORT
        self.gemini_api_key = gemini_api_key or Config.GEMINI_API_KEY
        self.search_config = search_config or SearchConfig()

        print(f"🔧 RetrievalAgent: Connecting to Weaviate at {self.weaviate_host}:{self.weaviate_port}")

        # Initialize Weaviate client
        try:
            self.client = weaviate.connect_to_local(
                host=self.weaviate_host,
                port=self.weaviate_port
            )
            print("✅ RetrievalAgent: Weaviate client connected successfully")

            # Test connection by listing collections
            collections = self.client.collections.list_all()
            collection_names = [c.name for c in collections]
            print(f"🔍 RetrievalAgent: Available collections: {collection_names}")

        except Exception as e:
            print(f"❌ RetrievalAgent: Failed to connect to Weaviate: {str(e)}")
            raise

        self.collection_name = "InsuranceDocumentChunk"
        print(f"🔧 RetrievalAgent: Target collection: {self.collection_name}")

        # Initialize Gemini for embeddings
        try:
            genai.configure(api_key=self.gemini_api_key)
            print("✅ RetrievalAgent: Gemini API configured")
        except Exception as e:
            print(f"❌ RetrievalAgent: Failed to configure Gemini API: {str(e)}")
            raise
    
    def retrieve(self, request: RetrievalRequest) -> List[ChunkResult]:
        """
        Main retrieval method
        
        Args:
            request: RetrievalRequest containing intent classification and parameters
            
        Returns:
            List of ChunkResult objects with relevance scores
        """
        try:
            # Step 1: Parse the Intent (Deconstruct the Work Order)
            query = self._enhance_query(request.query, request.entities)
            
            # Step 2: Construct the Filter (Precision)
            where_filter = self._build_product_filter(request.product_focus)
            
            # Step 3: Execute the Simple Hybrid Search (Relevance)
            candidates = self._execute_simple_hybrid_search(
                query=query,
                where_filter=where_filter,
                limit=request.top_k
            )

            # Step 4: Ensure balanced results for comparison queries
            if request.intent_classification.primary_intent.value == "COMPARISON_INQUIRY" and len(request.product_focus) > 1:
                final_results = self._balance_comparison_results(candidates, request.product_focus, request.top_k)
            else:
                final_results = candidates[:request.top_k]

            # Filter by minimum relevance score
            final_results = [
                result for result in final_results
                if result.relevance_score >= self.search_config.min_relevance_score
            ]
            
            return final_results
            
        except Exception as e:
            print(f"Error in retrieval: {e}")
            return []

    def _balance_comparison_results(self, results: List[ChunkResult], product_focus: List[str], target_count: int) -> List[ChunkResult]:
        """
        Ensure balanced representation of products in comparison queries.

        For comparison queries, we want to make sure we get results from all requested products,
        not just the highest-scoring ones from a single product.
        """

        if len(product_focus) <= 1:
            return results[:target_count]

        # Group results by product
        product_results = {}
        for result in results:
            product = result.product_name
            if product not in product_results:
                product_results[product] = []
            product_results[product].append(result)

        # Calculate how many results per product
        products_with_results = [p for p in product_focus if p in product_results]
        if not products_with_results:
            return results[:target_count]

        # For comparison queries, ensure at least 1 result per product
        min_per_product = 1
        remaining_slots = target_count - len(products_with_results)

        if remaining_slots > 0:
            extra_per_product = remaining_slots // len(products_with_results)
            remainder = remaining_slots % len(products_with_results)
        else:
            extra_per_product = 0
            remainder = 0

        balanced_results = []

        # Take results from each product (at least 1 per product)
        for i, product in enumerate(products_with_results):
            product_chunks = product_results[product]
            # Ensure at least 1 per product, plus extra allocation
            take_count = min_per_product + extra_per_product + (1 if i < remainder else 0)
            balanced_results.extend(product_chunks[:take_count])

        # If we still need more results, fill from the highest-scoring remaining
        if len(balanced_results) < target_count:
            used_ids = {result.chunk_id for result in balanced_results}
            remaining = [r for r in results if r.chunk_id not in used_ids]
            needed = target_count - len(balanced_results)
            balanced_results.extend(remaining[:needed])

        # Sort by relevance score to maintain quality
        balanced_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return balanced_results[:target_count]

    def _enhance_query(self, query: str, entities: List[str]) -> str:
        """Enhance query with insurance-specific term expansion"""
        
        enhanced_query = query.lower()
        
        # Expand insurance abbreviations and terms
        for abbrev, full_term in INSURANCE_TERMS.items():
            if abbrev in enhanced_query:
                enhanced_query = enhanced_query.replace(abbrev, f"{abbrev} {full_term}")
        
        # Add important entities to boost relevance
        if entities:
            # Add entities that aren't already in the query
            query_words = set(enhanced_query.split())
            additional_terms = []
            
            for entity in entities:
                entity_words = set(entity.lower().split())
                if not entity_words.issubset(query_words):
                    additional_terms.append(entity)
            
            if additional_terms:
                enhanced_query += " " + " ".join(additional_terms)
        
        return enhanced_query
    
    def _build_product_filter(self, product_focus: List[str]) -> Optional[Filter]:
        """Build Weaviate filter for product precision"""
        
        if not product_focus:
            return None
        
        if len(product_focus) == 1:
            # Single product filter
            return Filter.by_property("product_name").equal(product_focus[0])
        else:
            # Multiple products filter (OR condition)
            filters = [
                Filter.by_property("product_name").equal(product)
                for product in product_focus
            ]
            # Combine with OR
            combined_filter = filters[0]
            for filter_item in filters[1:]:
                combined_filter = combined_filter | filter_item
            return combined_filter

    def _execute_simple_hybrid_search(self,
                                    query: str,
                                    where_filter: Optional[Filter],
                                    limit: int) -> List[ChunkResult]:
        """Execute simple hybrid search combining keyword and semantic search"""

        collection = self.client.collections.get(self.collection_name)

        try:
            # Since we don't have a vectorizer configured, we'll combine:
            # 1. Keyword search (BM25)
            # 2. Vector search with manual embeddings

            # Get keyword search results
            keyword_results = self._keyword_search(collection, query, where_filter, limit)

            # Get vector search results
            vector_results = self._vector_search(collection, query, where_filter, limit, "content")

            # Combine and deduplicate results
            combined_results = self._combine_search_results(
                keyword_results,
                vector_results,
                self.search_config.hybrid_alpha,
                limit
            )

            return combined_results

        except Exception as e:
            print(f"Error in simple hybrid search: {e}")
            # Fallback to vector search only
            return self._vector_search(collection, query, where_filter, limit, "content")

    def _keyword_search(self, collection, query: str, where_filter: Optional[Filter], limit: int) -> List[ChunkResult]:
        """Execute keyword search using BM25"""
        try:
            if where_filter:
                response = collection.query.bm25(
                    query=query,
                    limit=limit,
                    filters=where_filter,
                    return_metadata=['score']
                )
            else:
                response = collection.query.bm25(
                    query=query,
                    limit=limit,
                    return_metadata=['score']
                )

            results = []
            for obj in response.objects:
                # Use BM25 score
                score = obj.metadata.score if obj.metadata and hasattr(obj.metadata, 'score') else 0.5

                chunk_result = ChunkResult.from_weaviate_result(
                    dict(obj.properties),
                    relevance_score=score,
                    search_method="keyword_bm25",
                    original_distance=None
                )
                results.append(chunk_result)

            return results

        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []

    def _combine_search_results(self, keyword_results: List[ChunkResult], vector_results: List[ChunkResult],
                               alpha: float, limit: int) -> List[ChunkResult]:
        """Combine keyword and vector search results"""

        # Create a map to combine results by content
        combined_map = {}

        # Add keyword results with weight (1 - alpha)
        keyword_weight = 1 - alpha
        for result in keyword_results:
            content_key = result.content[:100]  # Use first 100 chars as key
            if content_key not in combined_map:
                combined_map[content_key] = result
                combined_map[content_key].relevance_score *= keyword_weight
                combined_map[content_key].search_method = "hybrid_keyword"
            else:
                # If already exists, boost the score
                combined_map[content_key].relevance_score += result.relevance_score * keyword_weight * 0.5

        # Add vector results with weight alpha
        vector_weight = alpha
        for result in vector_results:
            content_key = result.content[:100]
            if content_key not in combined_map:
                combined_map[content_key] = result
                combined_map[content_key].relevance_score *= vector_weight
                combined_map[content_key].search_method = "hybrid_vector"
            else:
                # Combine scores
                combined_map[content_key].relevance_score += result.relevance_score * vector_weight
                combined_map[content_key].search_method = "hybrid_combined"

        # Sort by combined relevance score and return top results
        combined_results = list(combined_map.values())
        combined_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return combined_results[:limit]

    def _execute_hybrid_search(self,
                             query: str,
                             where_filter: Optional[Filter],
                             strategy: SearchStrategy,
                             limit: int,
                             request: RetrievalRequest) -> List[ChunkResult]:
        """Execute the multi-vector hybrid search"""
        
        collection = self.client.collections.get(self.collection_name)
        
        try:
            if strategy == SearchStrategy.MULTI_VECTOR:
                return self._multi_vector_search(collection, query, where_filter, limit, request)
            elif strategy == SearchStrategy.HYBRID:
                # For now, fall back to multi-vector search for hybrid
                # Weaviate's hybrid search requires different setup for multi-vector collections
                return self._multi_vector_search(collection, query, where_filter, limit, request)
            elif strategy == SearchStrategy.CONTENT_ONLY:
                return self._vector_search(collection, query, where_filter, limit, "content")
            elif strategy == SearchStrategy.SUMMARY_ONLY:
                return self._vector_search(collection, query, where_filter, limit, "summary")
            elif strategy == SearchStrategy.QUESTIONS_ONLY:
                return self._vector_search(collection, query, where_filter, limit, "questions")
            else:
                # Default to multi-vector
                return self._multi_vector_search(collection, query, where_filter, limit)
                
        except Exception as e:
            print(f"Error in search execution: {e}")
            return []
    
    def _multi_vector_search(self, collection, query: str, where_filter: Optional[Filter], limit: int, request: RetrievalRequest = None) -> List[ChunkResult]:
        """Execute multi-vector weighted search"""

        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)



        # Search against multiple vectors with weights
        search_queries = [
            {
                "vector": "hypothetical_question_embedding",
                "weight": self.search_config.question_weight,
                "embedding": query_embedding
            },
            {
                "vector": "summary_embedding",
                "weight": self.search_config.summary_weight,
                "embedding": query_embedding
            },
            {
                "vector": "content_embedding",
                "weight": self.search_config.content_weight,
                "embedding": query_embedding
            }
        ]

        results = []

        for search_query in search_queries:
            try:
                # Build the search with target vector specified and proper filtering
                if where_filter:
                    response = collection.query.near_vector(
                        near_vector=search_query["embedding"],
                        target_vector=search_query["vector"],  # Specify which vector to search
                        limit=limit,
                        filters=where_filter,  # Use the filters parameter
                        return_metadata=['distance']
                    )
                else:
                    response = collection.query.near_vector(
                        near_vector=search_query["embedding"],
                        target_vector=search_query["vector"],  # Specify which vector to search
                        limit=limit,
                        return_metadata=['distance']
                    )

                # Process results
                for obj in response.objects:
                    properties = dict(obj.properties)
                    distance = obj.metadata.distance if obj.metadata else 1.0

                    # Convert distance to relevance score (weighted)
                    relevance_score = (1 - min(distance, self.search_config.max_distance) / self.search_config.max_distance) * search_query["weight"]

                    chunk_result = ChunkResult.from_weaviate_result(
                        properties,
                        relevance_score=relevance_score,
                        search_method=f"multi_vector_{search_query['vector']}",
                        original_distance=distance
                    )

                    results.append(chunk_result)

            except Exception as e:
                print(f"Error in {search_query['vector']} search: {e}")
                continue

        # Combine and deduplicate results
        return self._deduplicate_and_sort(results, limit)
    
    def _hybrid_search(self, collection, query: str, where_filter: Optional[Filter], limit: int, vector_name: str) -> List[ChunkResult]:
        """Execute hybrid search (vector + keyword)"""
        
        try:
            # Build hybrid search with proper filtering and target vector
            if where_filter:
                response = collection.query.hybrid(
                    query=query,
                    alpha=self.search_config.hybrid_alpha,
                    limit=limit,
                    filters=where_filter,  # Use the filters parameter
                    target_vector="content_embedding",  # Specify target vector for multi-vector collections
                    return_metadata=['distance', 'score']
                )
            else:
                response = collection.query.hybrid(
                    query=query,
                    alpha=self.search_config.hybrid_alpha,
                    limit=limit,
                    target_vector="content_embedding",  # Specify target vector for multi-vector collections
                    return_metadata=['distance', 'score']
                )
            
            results = []
            for obj in response.objects:
                # Use hybrid score if available, otherwise convert distance
                if hasattr(obj.metadata, 'score') and obj.metadata.score is not None:
                    relevance_score = obj.metadata.score
                else:
                    distance = obj.metadata.distance if obj.metadata else 1.0
                    relevance_score = 1 - min(distance, self.search_config.max_distance) / self.search_config.max_distance

                chunk_result = ChunkResult.from_weaviate_result(
                    dict(obj.properties),
                    relevance_score=relevance_score,
                    search_method=f"hybrid_{vector_name}",
                    original_distance=obj.metadata.distance if obj.metadata else None
                )

                results.append(chunk_result)
            
            return results
            
        except Exception as e:
            print(f"Error in hybrid search: {e}")
            return []
    
    def _vector_search(self, collection, query: str, where_filter: Optional[Filter], limit: int, vector_name: str) -> List[ChunkResult]:
        """Execute pure vector search"""

        try:
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)

            # Map vector names to actual embedding field names
            vector_field_map = {
                "content": "content_embedding",
                "summary": "summary_embedding",
                "questions": "hypothetical_question_embedding"
            }

            vector_field = vector_field_map.get(vector_name, "content_embedding")

            # Build vector search with target vector specified and proper filtering
            if where_filter:
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    target_vector=vector_field,  # Specify which vector to search
                    limit=limit,
                    filters=where_filter,  # Use the filters parameter
                    return_metadata=['distance']
                )
            else:
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    target_vector=vector_field,  # Specify which vector to search
                    limit=limit,
                    return_metadata=['distance']
                )

            results = []
            for obj in response.objects:
                distance = obj.metadata.distance if obj.metadata else 1.0
                relevance_score = 1 - min(distance, self.search_config.max_distance) / self.search_config.max_distance

                chunk_result = ChunkResult.from_weaviate_result(
                    dict(obj.properties),
                    relevance_score=relevance_score,
                    search_method=f"vector_{vector_name}",
                    original_distance=distance
                )

                results.append(chunk_result)

            return results

        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
    
    def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query using Gemini"""

        try:
            # Handle empty or whitespace-only queries
            if not query or not query.strip():
                query = "general insurance information"

            result = genai.embed_content(
                model=Config.EMBEDDING_MODEL,
                content=query.strip()
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 3072  # Gemini embedding dimension
    
    def _deduplicate_and_sort(self, results: List[ChunkResult], limit: int) -> List[ChunkResult]:
        """Deduplicate results by content and sort by relevance score"""
        
        # Deduplicate by content (keep highest scoring)
        seen_content = {}
        for result in results:
            content_key = result.content[:100]  # Use first 100 chars as key
            if content_key not in seen_content or result.relevance_score > seen_content[content_key].relevance_score:
                seen_content[content_key] = result
        
        # Sort by relevance score (descending) and return top results
        deduplicated = list(seen_content.values())
        deduplicated.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return deduplicated[:limit]
    


    def close(self):
        """Clean up resources"""
        if hasattr(self, 'client'):
            self.client.close()
