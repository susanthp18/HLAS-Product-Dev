"""
Upload a single product to Weaviate for testing
"""

import os
import weaviate
import google.generativeai as genai
from config import Config

def setup_weaviate_client():
    """Setup Weaviate client"""
    print("🔧 Connecting to Weaviate...")
    
    client = weaviate.Client(
        url=f"http://{Config.WEAVIATE_HOST}:{Config.WEAVIATE_PORT}",
        timeout_config=(5, 15)
    )
    
    # Test connection
    if client.is_ready():
        print("✅ Weaviate connection successful")
        return client
    else:
        print("❌ Weaviate connection failed")
        return None

def create_schema(client):
    """Create Weaviate schema"""
    print("🔧 Creating Weaviate schema...")
    
    # Delete existing schema if it exists
    try:
        client.schema.delete_all()
        print("   Deleted existing schema")
    except:
        pass
    
    # Define schema
    schema = {
        "classes": [
            {
                "class": "InsuranceDocument",
                "description": "Insurance product documents and content",
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The main content of the document chunk"
                    },
                    {
                        "name": "product_name",
                        "dataType": ["string"],
                        "description": "Name of the insurance product"
                    },
                    {
                        "name": "document_type",
                        "dataType": ["string"],
                        "description": "Type of document (Terms, Benefits, FAQs)"
                    },
                    {
                        "name": "source_file",
                        "dataType": ["string"],
                        "description": "Source file name"
                    },
                    {
                        "name": "section_hierarchy",
                        "dataType": ["string[]"],
                        "description": "Hierarchical section path"
                    }
                ]
            }
        ]
    }
    
    # Create schema
    client.schema.create(schema)
    print("✅ Schema created successfully")

def setup_gemini():
    """Setup Gemini API"""
    print("🔧 Setting up Gemini API...")
    
    if not Config.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment")
        return None
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    print("✅ Gemini API configured")
    return model

def create_embedding(text, model):
    """Create embedding for text using Gemini"""
    try:
        # Use Gemini's embedding model
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"❌ Error creating embedding: {e}")
        return None

def upload_sample_data(client, model):
    """Upload sample insurance data"""
    print("📝 Uploading sample data...")
    
    # Sample insurance content
    sample_documents = [
        {
            "content": "Car insurance provides comprehensive coverage for your vehicle against accidents, theft, and damage. Our motor insurance covers third-party liability, own damage, and personal accident benefits.",
            "product_name": "Motor",
            "document_type": "Terms",
            "source_file": "Motor_Terms.md",
            "section_hierarchy": ["Coverage", "Comprehensive"]
        },
        {
            "content": "What is covered under car insurance? Car insurance covers vehicle damage from accidents, theft, fire, natural disasters, and third-party liability. Personal accident cover is also included.",
            "product_name": "Motor",
            "document_type": "FAQs",
            "source_file": "Motor_FAQs.md",
            "section_hierarchy": ["Coverage", "FAQ"]
        },
        {
            "content": "Motor insurance benefits include 24/7 roadside assistance, cashless garage repairs, and no-claim bonus protection. Coverage extends to personal belongings in the vehicle.",
            "product_name": "Motor",
            "document_type": "Benefits",
            "source_file": "Motor_Benefits.md",
            "section_hierarchy": ["Benefits", "Additional"]
        },
        {
            "content": "Travel insurance covers medical emergencies, trip cancellation, lost baggage, and flight delays during your overseas trips. Coverage includes emergency evacuation and repatriation.",
            "product_name": "Travel",
            "document_type": "Terms",
            "source_file": "Travel_Terms.md",
            "section_hierarchy": ["Coverage", "Medical"]
        },
        {
            "content": "How much medical coverage does travel insurance provide? Travel insurance provides up to $1 million for overseas medical expenses, including hospitalization, surgery, and emergency treatment.",
            "product_name": "Travel",
            "document_type": "FAQs",
            "source_file": "Travel_FAQs.md",
            "section_hierarchy": ["Medical", "FAQ"]
        }
    ]
    
    uploaded_count = 0
    
    for i, doc in enumerate(sample_documents):
        print(f"   Processing document {i+1}/{len(sample_documents)}: {doc['product_name']} - {doc['document_type']}")
        
        # Create embedding
        embedding = create_embedding(doc['content'], model)
        if embedding is None:
            print(f"   ❌ Failed to create embedding for document {i+1}")
            continue
        
        # Upload to Weaviate
        try:
            client.data_object.create(
                data_object=doc,
                class_name="InsuranceDocument",
                vector=embedding
            )
            uploaded_count += 1
            print(f"   ✅ Uploaded document {i+1}")
        except Exception as e:
            print(f"   ❌ Failed to upload document {i+1}: {e}")
    
    print(f"✅ Uploaded {uploaded_count}/{len(sample_documents)} documents")
    return uploaded_count

def test_search(client):
    """Test search functionality"""
    print("\n🔍 Testing search functionality...")
    
    # Test queries
    test_queries = [
        "What is covered under car insurance?",
        "Travel medical coverage amount",
        "Motor insurance benefits"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        
        try:
            # Hybrid search (keyword + semantic)
            result = client.query.get("InsuranceDocument", [
                "content", "product_name", "document_type", "source_file"
            ]).with_hybrid(
                query=query,
                alpha=0.5  # Balance between keyword and semantic search
            ).with_limit(2).do()
            
            documents = result.get('data', {}).get('Get', {}).get('InsuranceDocument', [])
            
            if documents:
                for i, doc in enumerate(documents):
                    print(f"     Result {i+1}: {doc['product_name']} - {doc['document_type']}")
                    print(f"     Content: {doc['content'][:100]}...")
            else:
                print("     No results found")
                
        except Exception as e:
            print(f"     ❌ Search failed: {e}")

def main():
    """Main function"""
    print("🚀 Upload Single Product to Weaviate - Test Script")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return
    
    # Setup Weaviate
    client = setup_weaviate_client()
    if not client:
        return
    
    # Setup Gemini
    model = setup_gemini()
    if not model:
        return
    
    # Create schema
    create_schema(client)
    
    # Upload sample data
    uploaded_count = upload_sample_data(client, model)
    
    if uploaded_count > 0:
        # Test search
        test_search(client)
        
        print("\n" + "=" * 60)
        print("🎉 Test upload completed successfully!")
        print(f"📊 Uploaded {uploaded_count} sample documents")
        print("\nNext steps:")
        print("1. Restart your API server: python start_api.py")
        print("2. Test the frontend at: http://13.215.172.229:3000")
        print("3. Try queries like:")
        print("   - 'What is covered under car insurance?'")
        print("   - 'Travel medical coverage'")
        print("   - 'Motor insurance benefits'")
    else:
        print("\n❌ No documents were uploaded. Check the errors above.")

if __name__ == "__main__":
    main()
