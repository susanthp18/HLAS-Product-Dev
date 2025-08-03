"""
Check Conversation History in MongoDB

This script helps you view and analyze the conversation history stored in MongoDB.
"""

from pymongo import MongoClient, DESCENDING
from datetime import datetime, timedelta
import json
from config import Config


def connect_to_mongodb():
    """Connect to MongoDB"""
    try:
        client = MongoClient(Config.get_mongodb_url(), serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {Config.get_mongodb_url()}")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None


def show_database_stats(client):
    """Show database and collection statistics"""
    print(f"\n📊 Database Statistics")
    print("=" * 50)
    
    db = client[Config.MONGODB_DATABASE]
    messages_collection = db[Config.MONGODB_COLLECTION]
    sessions_collection = db[f"{Config.MONGODB_COLLECTION}_sessions"]
    
    # Count documents
    total_messages = messages_collection.count_documents({})
    total_sessions = sessions_collection.count_documents({})
    active_sessions = sessions_collection.count_documents({"is_active": True})
    
    print(f"Database: {Config.MONGODB_DATABASE}")
    print(f"Total Messages: {total_messages}")
    print(f"Total Sessions: {total_sessions}")
    print(f"Active Sessions: {active_sessions}")
    
    if total_messages > 0:
        # Get date range
        oldest = messages_collection.find_one({}, sort=[("timestamp", 1)])
        newest = messages_collection.find_one({}, sort=[("timestamp", -1)])
        
        if oldest and newest:
            print(f"Date Range: {oldest['timestamp']} to {newest['timestamp']}")
    
    return messages_collection, sessions_collection


def show_recent_sessions(sessions_collection, limit=5):
    """Show recent conversation sessions"""
    print(f"\n🕒 Recent Sessions (Last {limit})")
    print("=" * 50)
    
    sessions = sessions_collection.find({}).sort("last_activity", DESCENDING).limit(limit)
    
    for i, session in enumerate(sessions, 1):
        print(f"\n{i}. Session ID: {session['session_id']}")
        print(f"   User ID: {session.get('user_id', 'N/A')}")
        print(f"   Platform: {session.get('platform', 'N/A')}")
        print(f"   Start Time: {session['start_time']}")
        print(f"   Last Activity: {session['last_activity']}")
        print(f"   Message Count: {session.get('message_count', 0)}")
        print(f"   Active: {session.get('is_active', False)}")


def show_recent_messages(messages_collection, limit=10):
    """Show recent messages"""
    print(f"\n💬 Recent Messages (Last {limit})")
    print("=" * 50)
    
    messages = messages_collection.find({}).sort("timestamp", DESCENDING).limit(limit)
    
    for i, message in enumerate(messages, 1):
        msg_type = message['message_type']
        content = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
        timestamp = message['timestamp']
        session_id = message['session_id'][:8] + "..."  # Show first 8 chars

        print(f"\n{i}. [{msg_type.upper()}] {timestamp}")
        print(f"   Session: {session_id}")
        print(f"   Content: {content}")

        if msg_type == "assistant":
            confidence = message.get('confidence_score')
            citations = message.get('citations', [])
            if confidence:
                print(f"   Confidence: {confidence:.2f}")
            if citations:
                print(f"   Citations: {len(citations)}")


def show_conversation_by_session(messages_collection, sessions_collection, session_id):
    """Show full conversation for a specific session"""
    print(f"\n🗣️  Conversation for Session: {session_id}")
    print("=" * 50)
    
    # Get session info
    session = sessions_collection.find_one({"session_id": session_id})
    if not session:
        print(f"❌ Session {session_id} not found")
        return
    
    print(f"User ID: {session.get('user_id', 'N/A')}")
    print(f"Platform: {session.get('platform', 'N/A')}")
    print(f"Start Time: {session['start_time']}")
    print(f"Message Count: {session.get('message_count', 0)}")
    print(f"Active: {session.get('is_active', False)}")
    
    # Get messages
    messages = messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
    
    print(f"\n📝 Messages:")
    for i, message in enumerate(messages, 1):
        msg_type = message['message_type']
        content = message['content']
        timestamp = message['timestamp']

        print(f"\n{i}. [{msg_type.upper()}] {timestamp}")
        print(f"   {content}")

        if msg_type == "assistant":
            confidence = message.get('confidence_score')
            citations = message.get('citations', [])
            processing_time = message.get('processing_time_ms')

            if confidence:
                print(f"   📊 Confidence: {confidence:.2f}")
            if processing_time:
                print(f"   ⏱️  Processing Time: {processing_time:.1f}ms")
            if citations:
                print(f"   📚 Citations: {len(citations)}")


def search_conversations(messages_collection, search_term, limit=5):
    """Search for conversations containing a specific term"""
    print(f"\n🔍 Search Results for: '{search_term}' (Last {limit})")
    print("=" * 50)
    
    # Search in message content
    messages = messages_collection.find(
        {"content": {"$regex": search_term, "$options": "i"}}
    ).sort("timestamp", DESCENDING).limit(limit)
    
    for i, message in enumerate(messages, 1):
        msg_type = message['message_type']
        content = message['content']
        timestamp = message['timestamp']
        session_id = message['session_id'][:8] + "..."

        print(f"\n{i}. [{msg_type.upper()}] {timestamp}")
        print(f"   Session: {session_id}")
        print(f"   Content: {content}")


def main():
    """Main function"""
    print("🔍 MongoDB Conversation History Checker")
    print("=" * 50)
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    if not client:
        return
    
    try:
        # Show database stats
        messages_collection, sessions_collection = show_database_stats(client)
        
        # Show recent sessions
        show_recent_sessions(sessions_collection)
        
        # Show recent messages
        show_recent_messages(messages_collection)
        
        # Interactive menu
        while True:
            print(f"\n🎯 Options:")
            print("1. View specific session conversation")
            print("2. Search conversations")
            print("3. Show recent sessions")
            print("4. Show recent messages")
            print("5. Refresh stats")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                session_id = input("Enter session ID: ").strip()
                if session_id:
                    show_conversation_by_session(messages_collection, sessions_collection, session_id)
            
            elif choice == "2":
                search_term = input("Enter search term: ").strip()
                if search_term:
                    search_conversations(messages_collection, search_term)
            
            elif choice == "3":
                show_recent_sessions(sessions_collection)
            
            elif choice == "4":
                show_recent_messages(messages_collection)
            
            elif choice == "5":
                show_database_stats(client)
            
            elif choice == "6":
                break
            
            else:
                print("Invalid choice. Please try again.")
    
    finally:
        client.close()
        print("\n👋 Disconnected from MongoDB")


if __name__ == "__main__":
    main()
