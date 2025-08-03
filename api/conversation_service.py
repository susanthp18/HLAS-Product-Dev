"""
Conversation History Service

MongoDB service for storing and retrieving conversation history.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from .conversation_models import (
    ConversationMessage, ConversationSession, ConversationHistory,
    ConversationSummary, MessageType
)
from config import Config


class ConversationService:
    """
    Service for managing conversation history in MongoDB
    """
    
    def __init__(self,
                 mongodb_url: str = None,
                 database_name: str = None,
                 collection_name: str = None):
        """Initialize MongoDB connection"""

        self.mongodb_url = mongodb_url or Config.get_mongodb_url()
        self.database_name = database_name or Config.MONGODB_DATABASE
        self.collection_name = collection_name or Config.MONGODB_COLLECTION

        print(f"🔧 ConversationService: Initializing MongoDB connection")
        print(f"   URL: {self.mongodb_url}")
        print(f"   Database: {self.database_name}")
        print(f"   Collection: {self.collection_name}")

        # Initialize MongoDB client
        self.client = MongoClient(self.mongodb_url)
        self.database: Database = self.client[self.database_name]
        self.messages_collection: Collection = self.database[self.collection_name]
        self.sessions_collection: Collection = self.database[f"{self.collection_name}_sessions"]

        print(f"✅ ConversationService: MongoDB connection established")

        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Indexes for messages collection
            self.messages_collection.create_index("session_id")
            self.messages_collection.create_index("timestamp")
            self.messages_collection.create_index([("session_id", 1), ("timestamp", 1)])
            
            # Indexes for sessions collection
            self.sessions_collection.create_index("session_id", unique=True)
            self.sessions_collection.create_index("last_activity")
            self.sessions_collection.create_index("is_active")
            
        except Exception as e:
            print(f"⚠️  ConversationService: Could not create indexes: {e}")
    
    def create_session(self,
                      user_id: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      ip_address: Optional[str] = None,
                      platform: str = "web") -> ConversationSession:
        """Create a new conversation session"""

        session_id = str(uuid.uuid4())
        print(f"📝 ConversationService: Creating new session {session_id}")
        print(f"   User ID: {user_id}")
        print(f"   Platform: {platform}")

        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            platform=platform
        )

        # Store session in database
        session_doc = session.model_dump()
        session_doc["_id"] = session_id
        result = self.sessions_collection.insert_one(session_doc)

        print(f"✅ ConversationService: Session stored in MongoDB with ID: {result.inserted_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve a conversation session"""
        
        session_doc = self.sessions_collection.find_one({"session_id": session_id})
        if session_doc:
            # Remove MongoDB _id field
            session_doc.pop("_id", None)
            return ConversationSession(**session_doc)
        return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update the last activity timestamp for a session"""
        
        result = self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {"last_activity": datetime.now(timezone.utc)},
                "$inc": {"message_count": 1}
            }
        )
        return result.modified_count > 0
    
    def add_message(self,
                   session_id: str,
                   message_type: MessageType,
                   content: str,
                   confidence_score: Optional[float] = None,
                   citations: Optional[List[Dict[str, Any]]] = None,
                   processing_time_ms: Optional[float] = None) -> ConversationMessage:
        """Add a message to a conversation"""

        message_id = str(uuid.uuid4())
        print(f"💬 ConversationService: Adding {message_type.value} message")
        print(f"   Session ID: {session_id}")
        print(f"   Message ID: {message_id}")
        print(f"   Content length: {len(content)} chars")
        if confidence_score:
            print(f"   Confidence: {confidence_score}")
        if citations:
            print(f"   Citations: {len(citations)}")

        message = ConversationMessage(
            message_id=message_id,
            session_id=session_id,
            message_type=message_type,
            content=content,
            confidence_score=confidence_score,
            citations=citations,
            processing_time_ms=processing_time_ms
        )

        # Store message in database
        message_doc = message.model_dump()
        # Convert enum to string for MongoDB
        message_doc["message_type"] = message_doc["message_type"].value
        message_doc["_id"] = message_id
        result = self.messages_collection.insert_one(message_doc)

        print(f"✅ ConversationService: Message stored in MongoDB with ID: {result.inserted_id}")

        # Update session activity
        updated = self.update_session_activity(session_id)
        if updated:
            print(f"✅ ConversationService: Session activity updated")
        else:
            print(f"⚠️  ConversationService: Failed to update session activity")

        return message
    
    def get_conversation_history(self, 
                               session_id: str,
                               limit: Optional[int] = None) -> Optional[ConversationHistory]:
        """Get complete conversation history for a session"""
        
        # Get session
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get messages
        query = {"session_id": session_id}
        cursor = self.messages_collection.find(query).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        messages = []
        for message_doc in cursor:
            message_doc.pop("_id", None)
            # Convert string back to enum for Pydantic
            if "message_type" in message_doc and isinstance(message_doc["message_type"], str):
                message_doc["message_type"] = MessageType(message_doc["message_type"])
            messages.append(ConversationMessage(**message_doc))
        
        return ConversationHistory(session=session, messages=messages)
    
    def get_recent_conversations(self, 
                               limit: int = 10,
                               days: int = 7) -> List[ConversationHistory]:
        """Get recent conversation histories"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get recent sessions
        sessions_cursor = self.sessions_collection.find(
            {"last_activity": {"$gte": cutoff_date}}
        ).sort("last_activity", DESCENDING).limit(limit)
        
        conversations = []
        for session_doc in sessions_cursor:
            session_doc.pop("_id", None)
            session = ConversationSession(**session_doc)
            
            # Get messages for this session
            messages_cursor = self.messages_collection.find(
                {"session_id": session.session_id}
            ).sort("timestamp", 1)
            
            messages = []
            for message_doc in messages_cursor:
                message_doc.pop("_id", None)
                # Convert string back to enum for Pydantic
                if "message_type" in message_doc and isinstance(message_doc["message_type"], str):
                    message_doc["message_type"] = MessageType(message_doc["message_type"])
                messages.append(ConversationMessage(**message_doc))
            
            conversations.append(ConversationHistory(session=session, messages=messages))
        
        return conversations
    
    def get_conversation_summary(self, days: int = 30) -> ConversationSummary:
        """Get summary statistics for conversations"""
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Count sessions
        total_sessions = self.sessions_collection.count_documents({})
        active_sessions = self.sessions_collection.count_documents({"is_active": True})
        
        # Count messages
        total_messages = self.messages_collection.count_documents({})
        
        # Calculate average session length
        pipeline = [
            {"$group": {
                "_id": "$session_id",
                "message_count": {"$sum": 1}
            }},
            {"$group": {
                "_id": None,
                "avg_length": {"$avg": "$message_count"}
            }}
        ]
        
        avg_result = list(self.messages_collection.aggregate(pipeline))
        average_session_length = avg_result[0]["avg_length"] if avg_result else 0.0
        
        # Get date range
        oldest_message = self.messages_collection.find_one({}, sort=[("timestamp", 1)])
        newest_message = self.messages_collection.find_one({}, sort=[("timestamp", -1)])
        
        date_range = {
            "start": oldest_message["timestamp"].isoformat() + "Z" if oldest_message else None,
            "end": newest_message["timestamp"].isoformat() + "Z" if newest_message else None
        }
        
        return ConversationSummary(
            total_sessions=total_sessions,
            total_messages=total_messages,
            active_sessions=active_sessions,
            average_session_length=round(average_session_length, 2),
            date_range=date_range
        )
    
    def close_session(self, session_id: str) -> bool:
        """Mark a session as inactive"""
        
        result = self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    def close(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        try:
            self.close()
        except Exception:
            pass
