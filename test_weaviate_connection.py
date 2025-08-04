#!/usr/bin/env python3
"""
Test script to debug Weaviate connection and search issues
"""

import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
import google.generativeai as genai
from config import Config

def test_weaviate_connection():
    """Test basic Weaviate connection and operations"""
    print("🔧 Testing Weaviate connection...")
    
    try:
        # Initialize client
        client = weaviate.connect_to_local(
            host=Config.WEAVIATE_HOST, 
            port=Config.WEAVIATE_PORT
        )
        
        print(f"✅ Connected to Weaviate at {Config.WEAVIATE_HOST}:{Config.WEAVIATE_PORT}")
        
        # Check if collection exists
        collection_name = "InsuranceDocumentChunk"
        if client.collections.exists(collection_name):
            print(f"✅ Collection '{collection_name}' exists")
            
            # Get collection
            collection = client.collections.get(collection_name)
            
            # Test simple query
            print("🔍 Testing simple query...")
            try:
                response = collection.query.fetch_objects(limit=1)
                print(f"✅ Simple query successful. Found {len(response.objects)} objects")
                
                if response.objects:
                    obj = response.objects[0]
                    print(f"   Sample object properties: {list(obj.properties.keys())}")
                
            except Exception as e:
                print(f"❌ Simple query failed: {e}")
            
            # Test keyword search
            print("🔍 Testing keyword search...")
            try:
                response = collection.query.bm25(
                    query="insurance",
                    limit=1
                )
                print(f"✅ Keyword search successful. Found {len(response.objects)} objects")
                
            except Exception as e:
                print(f"❌ Keyword search failed: {e}")
            
            # Test vector search with Gemini embedding
            print("🔍 Testing vector search...")
            try:
                # Configure Gemini
                genai.configure(api_key=Config.GEMINI_API_KEY)
                
                # Generate embedding
                query_result = genai.embed_content(
                    model=Config.EMBEDDING_MODEL,
                    content="What is covered under car insurance?"
                )
                query_embedding = query_result['embedding']
                
                # Test vector search
                response = collection.query.near_vector(
                    near_vector=query_embedding,
                    target_vector="content_embedding",
                    limit=1,
                    return_metadata=['distance']
                )
                print(f"✅ Vector search successful. Found {len(response.objects)} objects")
                
                if response.objects:
                    obj = response.objects[0]
                    print(f"   Distance: {obj.metadata.distance}")
                    print(f"   Product: {obj.properties.get('product_name', 'N/A')}")
                
            except Exception as e:
                print(f"❌ Vector search failed: {e}")
            
            # Test hybrid search
            print("🔍 Testing hybrid search...")
            try:
                response = collection.query.hybrid(
                    query="car insurance coverage",
                    alpha=0.7,
                    target_vector="content_embedding",
                    limit=1,
                    return_metadata=['distance', 'score']
                )
                print(f"✅ Hybrid search successful. Found {len(response.objects)} objects")
                
            except Exception as e:
                print(f"❌ Hybrid search failed: {e}")
                
        else:
            print(f"❌ Collection '{collection_name}' does not exist")
            
        # Close connection
        client.close()
        print("✅ Connection closed successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_weaviate_connection()
