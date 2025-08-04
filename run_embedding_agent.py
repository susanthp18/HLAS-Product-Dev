"""
Main script to run the Embedding Agent
"""

import os
from agents.embedding import EmbeddingAgent
from config import Config


def check_source_directory(source_dir):
    """Check and display source directory contents"""
    print(f"\n🔍 Checking source directory: {source_dir}")

    if not os.path.exists(source_dir):
        print(f"❌ Source directory '{source_dir}' does not exist!")
        return False

    # Find all supported files
    supported_extensions = ['.md', '.txt', '.pdf', '.docx']
    files_found = []

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                files_found.append(os.path.join(root, file))

    if not files_found:
        print(f"❌ No supported documents found in '{source_dir}'")
        print(f"   Supported formats: {', '.join(supported_extensions)}")
        return False

    print(f"✅ Found {len(files_found)} documents:")
    for file in files_found[:10]:  # Show first 10
        size = os.path.getsize(file)
        print(f"   📄 {file} ({size:,} bytes)")

    if len(files_found) > 10:
        print(f"   ... and {len(files_found) - 10} more files")

    return True


def check_weaviate_connection(host, port):
    """Check Weaviate connection"""
    print(f"\n🔍 Checking Weaviate connection: {host}:{port}")

    try:
        import weaviate
        client = weaviate.connect_to_local(host=host, port=port)

        # Test connection
        if client.is_ready():
            print("✅ Weaviate connection successful")

            # Check existing collections
            collections = client.collections.list_all()
            if collections:
                print(f"📊 Existing collections: {[c.name for c in collections]}")
            else:
                print("📊 No existing collections found")

            client.close()
            return True
        else:
            print("❌ Weaviate is not ready")
            return False

    except Exception as e:
        print(f"❌ Weaviate connection failed: {e}")
        return False


def check_gemini_api(api_key):
    """Check Gemini API connection"""
    print(f"\n🔍 Checking Gemini API connection...")

    if not api_key:
        print("❌ Gemini API key not provided")
        return False

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Test with a simple request
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")

        if response and response.text:
            print("✅ Gemini API connection successful")
            return True
        else:
            print("❌ Gemini API test failed - no response")
            return False

    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False


def main():
    """Run the embedding agent pipeline with status checks"""

    print("🚀 Starting Embedding Agent with Status Checks")
    print("=" * 60)

    # Step 1: Validate configuration
    print("\n📋 Step 1: Configuration Validation")
    try:
        Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return

    # Step 2: Check source directory
    print("\n📁 Step 2: Source Directory Check")
    if not check_source_directory(Config.SOURCE_DIR):
        print("❌ Cannot proceed without source documents")
        return

    # Step 3: Check Weaviate connection
    print("\n🔗 Step 3: Weaviate Connection Check")
    if not check_weaviate_connection(Config.WEAVIATE_HOST, Config.WEAVIATE_PORT):
        print("❌ Cannot proceed without Weaviate connection")
        return

    # Step 4: Check Gemini API
    print("\n🤖 Step 4: Gemini API Check")
    if not check_gemini_api(Config.GEMINI_API_KEY):
        print("❌ Cannot proceed without Gemini API")
        return

    # Step 5: Initialize agent
    print("\n🔧 Step 5: Agent Initialization")
    try:
        agent = EmbeddingAgent(
            source_dir=Config.SOURCE_DIR,
            gemini_api_key=Config.GEMINI_API_KEY,
            weaviate_host=Config.WEAVIATE_HOST,
            weaviate_port=Config.WEAVIATE_PORT
        )
        print("✅ Embedding Agent initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return

    try:
        # Step 6: Run the pipeline
        print("\n🚀 Step 6: Running Embedding Pipeline")
        print("=" * 40)
        chunks = agent.run()

        # Step 7: Verify results
        print(f"\n✅ Step 7: Pipeline Complete!")
        print(f"📊 Total chunks processed: {len(chunks)}")

        # Show sample of processed chunks
        if chunks:
            print(f"\n📋 Sample of processed chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"   Chunk {i+1}: {chunk.product_name} - {chunk.document_type}")
                print(f"   Content: {chunk.content[:100]}...")
                print(f"   Embeddings: Content={len(chunk.content_embedding)}, Summary={len(chunk.summary_embedding)}")
                print()

        # Step 8: Test search functionality
        print(f"\n🔍 Step 8: Testing Search Functionality")
        print("=" * 40)

        test_queries = [
            "What is covered under car insurance?",
            "How much medical coverage for maid?",
            "How to make a travel insurance claim?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            try:
                results = agent.search(query, search_type="hybrid", limit=2)
                if results:
                    print(f"   ✅ Found {len(results)} results")
                    for j, result in enumerate(results):
                        props = result['properties']
                        print(f"   Result {j+1}: {props.get('product_name', 'N/A')} - {props.get('document_type', 'N/A')}")
                        print(f"   Content: {props.get('content', 'N/A')[:100]}...")
                else:
                    print(f"   ⚠️  No results found")
            except Exception as e:
                print(f"   ❌ Search failed: {e}")

        # Step 9: Final verification
        print(f"\n🎉 Step 9: Final Verification")
        print("=" * 40)

        # Check Weaviate collections after ingestion
        try:
            import weaviate
            client = weaviate.connect_to_local(host=Config.WEAVIATE_HOST, port=Config.WEAVIATE_PORT)
            collections = client.collections.list_all()

            print(f"✅ Weaviate collections after ingestion:")
            for collection in collections:
                try:
                    count = collection.aggregate.over_all(total_count=True).total_count
                    print(f"   📊 {collection.name}: {count} objects")
                except:
                    print(f"   📊 {collection.name}: count unavailable")

            client.close()

        except Exception as e:
            print(f"❌ Final verification failed: {e}")

    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Step 10: Cleanup
        print(f"\n🧹 Step 10: Cleanup")
        try:
            agent.close()
            print("✅ Agent cleanup complete")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        print("\n" + "=" * 60)
        print("🏁 Embedding Agent Execution Complete!")
        print("=" * 60)


if __name__ == "__main__":
    main() 