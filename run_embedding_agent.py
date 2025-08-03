"""
Main script to run the Embedding Agent
"""

import os
from agents.embedding import EmbeddingAgent
from config import Config


def main():
    """Run the embedding agent pipeline"""
    
    # Validate configuration
    Config.validate()
    
    # Initialize agent
    print("Initializing Embedding Agent...")
    agent = EmbeddingAgent(
        source_dir=Config.SOURCE_DIR,
        gemini_api_key=Config.GEMINI_API_KEY,
        weaviate_host=Config.WEAVIATE_HOST,
        weaviate_port=Config.WEAVIATE_PORT
    )
    
    try:
        # Run the pipeline
        chunks = agent.run()
        
        # Example searches
        print("\n=== Example Searches ===")
        
        # Example 1: Search for car insurance coverage
        print("\n1. Searching for: 'What is covered under car insurance?'")
        results = agent.search("What is covered under car insurance?", search_type="hybrid", limit=3)
        for i, result in enumerate(results):
            print(f"\n  Result {i+1}:")
            print(f"  - Product: {result['properties']['product_name']}")
            print(f"  - Type: {result['properties']['document_type']}")
            print(f"  - Content: {result['properties']['content'][:200]}...")
        
        # Example 2: Search for maid insurance benefits
        print("\n2. Searching for: 'How much medical coverage for maid?'")
        results = agent.search("How much medical coverage for maid?", search_type="questions", limit=3)
        for i, result in enumerate(results):
            print(f"\n  Result {i+1}:")
            print(f"  - Product: {result['properties']['product_name']}")
            print(f"  - Question: {result['properties']['question']}")
            print(f"  - Content: {result['properties']['content'][:200]}...")
        
        # Example 3: Search for travel insurance claims
        print("\n3. Searching for: 'How to make a travel insurance claim?'")
        results = agent.search("How to make a travel insurance claim?", search_type="hybrid", limit=3)
        for i, result in enumerate(results):
            print(f"\n  Result {i+1}:")
            print(f"  - Product: {result['properties']['product_name']}")
            print(f"  - Type: {result['properties']['document_type']}")
            print(f"  - Content: {result['properties']['content'][:200]}...")
    
    finally:
        # Clean up
        agent.close()
        print("\n✅ Embedding Agent execution complete!")


if __name__ == "__main__":
    main() 