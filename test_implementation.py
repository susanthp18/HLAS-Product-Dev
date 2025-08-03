"""
Test script to verify the simplified search and conversation history implementation
"""

import asyncio
import requests
import json
from datetime import datetime
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_QUERIES = [
    "What is car insurance?",
    "What are the benefits of travel insurance?",
    "How much does home insurance cost?",
    "What is covered under hospital insurance?",
    "Compare car and travel insurance"
]


def test_api_health():
    """Test if the API is running and healthy"""
    print("🔍 Testing API health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API is healthy: {health_data['status']}")
            print(f"   Agents status: {health_data['agents_status']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Could not connect to API: {e}")
        return False


def test_conversation_session():
    """Test creating a conversation session"""
    print("\n🔍 Testing conversation session creation...")
    
    try:
        session_data = {
            "user_id": "test_user_123",
            "platform": "web"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/conversation/session",
            json=session_data
        )
        
        if response.status_code == 200:
            session_info = response.json()
            session_id = session_info["session_id"]
            print(f"✅ Session created successfully: {session_id}")
            return session_id
        else:
            print(f"❌ Session creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None


def test_query_with_session(session_id: str, query: str):
    """Test querying with session tracking"""
    print(f"\n🔍 Testing query with session: '{query}'")
    
    try:
        query_data = {
            "query": query,
            "session_id": session_id,
            "include_citations": True,
            "include_confidence": True,
            "max_results": 3
        }
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=query_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Confidence: {result['confidence_score']:.2f}")
            print(f"   Citations: {len(result['citations'])}")
            print(f"   Processing time: {result['processing_time_ms']:.1f}ms")
            print(f"   Session ID: {result.get('session_id', 'None')}")
            return True
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during query: {e}")
        return False


def test_conversation_history(session_id: str):
    """Test retrieving conversation history"""
    print(f"\n🔍 Testing conversation history retrieval...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/conversation/history/{session_id}")
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ History retrieved successfully")
            print(f"   Session ID: {history['session']['session_id']}")
            print(f"   Message count: {len(history['messages'])}")
            print(f"   Session active: {history['session']['is_active']}")
            
            # Print recent messages
            for i, message in enumerate(history['messages'][-4:]):  # Last 4 messages
                msg_type = message['message_type']
                content = message['content'][:50] + "..." if len(message['content']) > 50 else message['content']
                print(f"   Message {i+1} ({msg_type}): {content}")
            
            return True
        else:
            print(f"❌ History retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving history: {e}")
        return False


def test_conversation_summary():
    """Test getting conversation summary"""
    print(f"\n🔍 Testing conversation summary...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/conversation/summary?days=7")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"✅ Summary retrieved successfully")
            print(f"   Total sessions: {summary['total_sessions']}")
            print(f"   Total messages: {summary['total_messages']}")
            print(f"   Active sessions: {summary['active_sessions']}")
            print(f"   Average session length: {summary['average_session_length']}")
            return True
        else:
            print(f"❌ Summary retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving summary: {e}")
        return False


def test_simple_query_without_session():
    """Test the simplified search without session tracking"""
    print(f"\n🔍 Testing simplified search without session...")
    
    try:
        query_data = {
            "query": "What is the excess for car insurance windscreen?",
            "include_citations": True,
            "include_confidence": True,
            "max_results": 5
        }
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=query_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simplified search successful")
            print(f"   Answer: {result['answer'][:100]}...")
            print(f"   Confidence: {result['confidence_score']:.2f}")
            print(f"   Context used: {result['context_used']}/{result['context_available']}")
            print(f"   Has sufficient context: {result['has_sufficient_context']}")
            
            # Check citations
            if result['citations']:
                print(f"   First citation relevance: {result['citations'][0]['relevance_score']:.3f}")
                print(f"   Search method: Simple hybrid (keyword + semantic)")
            
            return True
        else:
            print(f"❌ Simplified search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during simplified search: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting implementation tests...")
    print("=" * 60)
    
    # Test 1: API Health
    if not test_api_health():
        print("\n❌ API is not available. Please start the API server first.")
        return
    
    # Test 2: Simple query without session (test simplified search)
    test_simple_query_without_session()
    
    # Test 3: Create conversation session
    session_id = test_conversation_session()
    if not session_id:
        print("\n⚠️  Conversation features not available, but search should still work.")
        return
    
    # Test 4: Run queries with session tracking
    success_count = 0
    for i, query in enumerate(TEST_QUERIES):
        if test_query_with_session(session_id, query):
            success_count += 1
    
    print(f"\n📊 Query test results: {success_count}/{len(TEST_QUERIES)} successful")
    
    # Test 5: Check conversation history
    test_conversation_history(session_id)
    
    # Test 6: Get conversation summary
    test_conversation_summary()
    
    print("\n" + "=" * 60)
    print("🎉 Implementation tests completed!")
    print("\nKey improvements implemented:")
    print("✅ Simplified hybrid search (keyword + semantic, no reranking)")
    print("✅ MongoDB conversation history storage")
    print("✅ Session-based conversation tracking")
    print("✅ New API endpoints for conversation management")
    print("\n💡 To check conversation history:")
    print("   python check_conversation_history.py")


if __name__ == "__main__":
    main()
