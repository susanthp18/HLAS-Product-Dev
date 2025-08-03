"""
Debug Conversation Service

Test the conversation service directly to see if it's working.
"""

from api.conversation_service import ConversationService
from api.conversation_models import MessageType
import traceback


def test_conversation_service():
    """Test the conversation service directly"""
    print("🔧 Testing Conversation Service Directly")
    print("=" * 50)
    
    try:
        # Initialize service
        print("1. Initializing conversation service...")
        service = ConversationService()
        print("✅ Service initialized successfully")
        
        # Create a session
        print("\n2. Creating a test session...")
        session = service.create_session(
            user_id="debug_user",
            platform="debug"
        )
        print(f"✅ Session created: {session.session_id}")
        
        # Add a user message
        print("\n3. Adding user message...")
        user_message = service.add_message(
            session_id=session.session_id,
            message_type=MessageType.USER,
            content="Test user message for debugging"
        )
        print(f"✅ User message added: {user_message.message_id}")
        
        # Add an assistant message
        print("\n4. Adding assistant message...")
        assistant_message = service.add_message(
            session_id=session.session_id,
            message_type=MessageType.ASSISTANT,
            content="Test assistant response for debugging",
            confidence_score=0.95,
            citations=[{"test": "citation"}],
            processing_time_ms=1234.5
        )
        print(f"✅ Assistant message added: {assistant_message.message_id}")
        
        # Get conversation history
        print("\n5. Retrieving conversation history...")
        history = service.get_conversation_history(session.session_id)
        if history:
            print(f"✅ History retrieved: {len(history.messages)} messages")
            for i, msg in enumerate(history.messages, 1):
                print(f"   {i}. [{msg.message_type.value}] {msg.content[:50]}...")
        else:
            print("❌ No history found")
        
        # Get summary
        print("\n6. Getting conversation summary...")
        summary = service.get_conversation_summary()
        if summary:
            print(f"✅ Summary retrieved:")
            print(f"   Total sessions: {summary.total_sessions}")
            print(f"   Total messages: {summary.total_messages}")
            print(f"   Active sessions: {summary.active_sessions}")
        else:
            print("❌ No summary available")
        
        # Close service
        service.close()
        print("\n✅ All tests passed! Conversation service is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing conversation service:")
        print(f"   {str(e)}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        return False


def test_mongodb_connection():
    """Test MongoDB connection directly"""
    print("\n🔧 Testing MongoDB Connection")
    print("=" * 50)
    
    try:
        from pymongo import MongoClient
        from config import Config
        
        print("1. Connecting to MongoDB...")
        client = MongoClient(Config.get_mongodb_url(), serverSelectionTimeoutMS=5000)
        
        print("2. Testing connection...")
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        print("3. Checking database and collections...")
        db = client[Config.MONGODB_DATABASE]
        messages_collection = db[Config.MONGODB_COLLECTION]
        sessions_collection = db[f"{Config.MONGODB_COLLECTION}_sessions"]
        
        print(f"✅ Database: {Config.MONGODB_DATABASE}")
        print(f"✅ Messages collection: {Config.MONGODB_COLLECTION}")
        print(f"✅ Sessions collection: {Config.MONGODB_COLLECTION}_sessions")
        
        # Test write operation
        print("4. Testing write operation...")
        test_doc = {"test": "document", "timestamp": "2024-01-01T00:00:00Z"}
        result = messages_collection.insert_one(test_doc)
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Clean up test document
        messages_collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection error:")
        print(f"   {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Main debug function"""
    print("🐛 Conversation Service Debug Tool")
    print("=" * 50)
    
    # Test MongoDB first
    mongodb_ok = test_mongodb_connection()
    
    if mongodb_ok:
        # Test conversation service
        service_ok = test_conversation_service()
        
        if service_ok:
            print("\n🎉 All tests passed!")
            print("The conversation service should be working properly.")
            print("\nIf the API still isn't storing conversations, check:")
            print("1. API server logs for errors")
            print("2. Make sure you're using session_id in API requests")
            print("3. Check if the conversation service is properly initialized in the API")
        else:
            print("\n❌ Conversation service has issues.")
    else:
        print("\n❌ MongoDB connection failed.")
        print("Make sure MongoDB is running:")
        print("docker run -d -p 27017:27017 --name mongodb mongo:latest")


if __name__ == "__main__":
    main()
