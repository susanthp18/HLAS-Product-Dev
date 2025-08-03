"""
MongoDB Setup Script

This script helps set up MongoDB for conversation history storage.
It creates the necessary database and collections with proper indexes.
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from config import Config


def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")
    
    try:
        client = MongoClient(Config.get_mongodb_url(), serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print(f"✅ MongoDB connection successful")
        print(f"   URL: {Config.get_mongodb_url()}")
        return client
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        print(f"   Make sure MongoDB is running on {Config.MONGODB_HOST}:{Config.MONGODB_PORT}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def setup_database_and_collections(client):
    """Set up database and collections"""
    print(f"\n🔧 Setting up database: {Config.MONGODB_DATABASE}")
    
    try:
        # Get database
        db = client[Config.MONGODB_DATABASE]
        
        # Create collections
        messages_collection = db[Config.MONGODB_COLLECTION]
        sessions_collection = db[f"{Config.MONGODB_COLLECTION}_sessions"]
        
        print(f"✅ Database and collections ready")
        print(f"   Messages collection: {Config.MONGODB_COLLECTION}")
        print(f"   Sessions collection: {Config.MONGODB_COLLECTION}_sessions")
        
        return messages_collection, sessions_collection
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return None, None


def create_indexes(messages_collection, sessions_collection):
    """Create database indexes for optimal performance"""
    print(f"\n🔧 Creating database indexes...")
    
    try:
        # Indexes for messages collection
        print("   Creating indexes for messages collection...")
        messages_collection.create_index("session_id")
        messages_collection.create_index("timestamp")
        messages_collection.create_index([("session_id", ASCENDING), ("timestamp", ASCENDING)])
        messages_collection.create_index("message_type")
        
        # Indexes for sessions collection
        print("   Creating indexes for sessions collection...")
        sessions_collection.create_index("session_id", unique=True)
        sessions_collection.create_index("last_activity")
        sessions_collection.create_index("is_active")
        sessions_collection.create_index("user_id")
        sessions_collection.create_index("platform")
        
        print(f"✅ Indexes created successfully")
        
    except OperationFailure as e:
        print(f"⚠️  Some indexes may already exist: {e}")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")


def show_collection_stats(messages_collection, sessions_collection):
    """Show collection statistics"""
    print(f"\n📊 Collection Statistics:")
    
    try:
        # Messages collection stats
        messages_count = messages_collection.count_documents({})
        print(f"   Messages: {messages_count}")
        
        # Sessions collection stats
        sessions_count = sessions_collection.count_documents({})
        active_sessions = sessions_collection.count_documents({"is_active": True})
        print(f"   Sessions: {sessions_count} (Active: {active_sessions})")
        
        # Show indexes
        print(f"\n📋 Indexes:")
        print(f"   Messages collection indexes:")
        for index in messages_collection.list_indexes():
            print(f"     - {index['name']}: {index.get('key', {})}")
        
        print(f"   Sessions collection indexes:")
        for index in sessions_collection.list_indexes():
            print(f"     - {index['name']}: {index.get('key', {})}")
            
    except Exception as e:
        print(f"❌ Error getting collection stats: {e}")


def test_basic_operations(messages_collection, sessions_collection):
    """Test basic database operations"""
    print(f"\n🧪 Testing basic database operations...")
    
    try:
        # Test session creation
        test_session = {
            "_id": "test_session_123",
            "session_id": "test_session_123",
            "user_id": "test_user",
            "start_time": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T00:00:00Z",
            "message_count": 0,
            "is_active": True,
            "platform": "test"
        }
        
        # Insert test session (replace if exists)
        sessions_collection.replace_one(
            {"session_id": "test_session_123"}, 
            test_session, 
            upsert=True
        )
        print("   ✅ Session insert/update test passed")
        
        # Test message creation
        test_message = {
            "_id": "test_message_123",
            "message_id": "test_message_123",
            "session_id": "test_session_123",
            "message_type": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Insert test message (replace if exists)
        messages_collection.replace_one(
            {"message_id": "test_message_123"}, 
            test_message, 
            upsert=True
        )
        print("   ✅ Message insert/update test passed")
        
        # Test queries
        session_result = sessions_collection.find_one({"session_id": "test_session_123"})
        message_result = messages_collection.find_one({"session_id": "test_session_123"})
        
        if session_result and message_result:
            print("   ✅ Query test passed")
        else:
            print("   ❌ Query test failed")
        
        # Clean up test data
        sessions_collection.delete_one({"session_id": "test_session_123"})
        messages_collection.delete_one({"message_id": "test_message_123"})
        print("   ✅ Cleanup completed")
        
    except Exception as e:
        print(f"   ❌ Database operation test failed: {e}")


def main():
    """Main setup function"""
    print("🚀 MongoDB Setup for HLAS Insurance Conversation History")
    print("=" * 60)
    
    # Test connection
    client = test_mongodb_connection()
    if not client:
        print("\n❌ Setup failed. Please ensure MongoDB is running.")
        print("\nTo start MongoDB with Docker:")
        print("docker run -d -p 27017:27017 --name mongodb mongo:latest")
        return
    
    # Setup database and collections
    messages_collection, sessions_collection = setup_database_and_collections(client)
    if messages_collection is None or sessions_collection is None:
        print("\n❌ Setup failed.")
        return
    
    # Create indexes
    create_indexes(messages_collection, sessions_collection)
    
    # Show statistics
    show_collection_stats(messages_collection, sessions_collection)
    
    # Test basic operations
    test_basic_operations(messages_collection, sessions_collection)
    
    # Close connection
    client.close()
    
    print("\n" + "=" * 60)
    print("🎉 MongoDB setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the API server: python start_api.py")
    print("2. Run tests: python test_implementation.py")
    print("3. The conversation history will be stored in:")
    print(f"   Database: {Config.MONGODB_DATABASE}")
    print(f"   Collections: {Config.MONGODB_COLLECTION}, {Config.MONGODB_COLLECTION}_sessions")


if __name__ == "__main__":
    main()
