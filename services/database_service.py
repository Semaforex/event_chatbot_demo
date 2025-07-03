"""
Database service for storing chat sessions in MongoDB.
"""

from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for managing MongoDB connections and chat session storage."""
    
    def __init__(self, mongo_url: Optional[str] = None):
        """Initialize the database service."""
        self.mongo_url = mongo_url or os.getenv('MONGO_URL')
        self.client = None
        self.db = None
        self.chat_sessions = None
        
        if not self.mongo_url:
            raise ValueError("MONGO_URL must be provided either as parameter or environment variable")
    
    def connect(self) -> bool:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.mongo_url)
            # Test the connection
            self.client.admin.command('ping')
            
            # Initialize database and collections
            self.db = self.client['Thrugo']
            self.chat_sessions = self.db['chat_sessions']
            
            logger.info("Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def save_chat_session(self, session_data_or_channel_id, session_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Save or update a chat session to the database using upsert.
        
        Args:
            session_data_or_channel_id: Either session_data dict or channel_id string
            session_data: Optional session data when first param is channel_id
            
        Returns:
            The upserted document ID as string, or None if failed
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return None
            
            # Handle both calling patterns
            if isinstance(session_data_or_channel_id, dict):
                # Called as save_chat_session(session_data)
                final_session_data = session_data_or_channel_id
                channel_id = final_session_data.get('channel_id')
            else:
                # Called as save_chat_session(channel_id, session_data)
                channel_id = session_data_or_channel_id
                final_session_data = session_data or {}
                final_session_data['channel_id'] = channel_id
            
            if not channel_id:
                logger.error("channel_id is required for upsert operation")
                return None
            
            result = self.chat_sessions.update_one(
                {"channel_id": channel_id},
                {"$set": final_session_data},
                upsert=True
            )
            
            # Get the document ID (either inserted or existing)
            if result.upserted_id:
                doc_id = str(result.upserted_id)
                logger.info(f"Chat session inserted with ID: {doc_id}")
            else:
                # Find the existing document to get its ID
                existing_doc = self.chat_sessions.find_one({"channel_id": channel_id})
                doc_id = str(existing_doc['_id']) if existing_doc else None
                logger.info(f"Chat session updated for channel: {channel_id}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to save chat session: {e}")
            return None
    
    def get_chat_session(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chat session by channel ID. If no session exists, create a new one.
        
        Args:
            channel_id: The channel ID to search for
            
        Returns:
            The session document or None if failed
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return None
            
            session = self.chat_sessions.find_one({"channel_id": channel_id})
            
            # If session doesn't exist, create a new one
            if session is None:
                logger.info(f"Session not found for channel {channel_id}, creating new session")
                
                # Create new session data
                now_str = datetime.now().isoformat()
                new_session_data = {
                    "channel_id": channel_id,
                    "messages": [],
                    "created_at": now_str,
                    "last_updated": now_str,
                    "search_obj_list": [],
                    "message_count": 0,
                    "status": "active"
                }
                
                # Save the new session
                doc_id = self.save_chat_session(new_session_data)
                if doc_id:
                    # Retrieve the newly created session
                    session = self.chat_sessions.find_one({"channel_id": channel_id})
                    logger.info(f"Created and retrieved new session for channel: {channel_id}")
                else:
                    logger.error(f"Failed to create new session for channel: {channel_id}")
                    return None
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat session: {e}")
            return None

    def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all chat sessions/channels from the database.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session documents sorted by last_updated
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return []
            
            sessions = list(self.chat_sessions.find({}).sort("last_updated", -1).limit(limit))
            return sessions
            
        except Exception as e:
            #fallback
            logger.error(f"Failed to retrieve all sessions: {e}")
            return []

# Context manager for easy database operations
class DatabaseContext:
    """Context manager for database operations."""
    
    def __init__(self, mongo_url: Optional[str] = None):
        self.db_service = DatabaseService(mongo_url)
    
    def __enter__(self):
        if self.db_service.connect():
            return self.db_service
        else:
            raise ConnectionError("Failed to connect to database")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_service.disconnect()
