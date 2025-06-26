"""
Database service for storing chat sessions in MongoDB.
"""

from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional, Any
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
    
    def save_chat_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Save a chat session to the database.
        
        Args:
            session_data: Dictionary containing session information
            
        Returns:
            The inserted document ID as string, or None if failed
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return None
            
            # Add timestamp if not present
            if 'created_at' not in session_data:
                session_data['created_at'] = datetime.now()
            
            result = self.chat_sessions.insert_one(session_data)
            logger.info(f"Chat session saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to save chat session: {e}")
            return None
    
    def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chat session by session ID.
        
        Args:
            session_id: The session ID to search for
            
        Returns:
            The session document or None if not found
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return None
            
            session = self.chat_sessions.find_one({"session_id": session_id})
            return session
            
        except Exception as e:
            logger.error(f"Failed to retrieve chat session: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get chat sessions for a specific user.
        
        Args:
            user_id: The user ID to search for
            limit: Maximum number of sessions to return
            
        Returns:
            List of session documents
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return []
            
            sessions = list(self.chat_sessions.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to retrieve user sessions: {e}")
            return []
    
    def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing chat session.
        
        Args:
            session_id: The session ID to update
            update_data: Dictionary containing fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if self.chat_sessions is None:
                logger.error("Not connected to database")
                return False
            
            # Add update timestamp
            update_data['updated_at'] = datetime.now()
            
            result = self.chat_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Session {session_id} updated successfully")
            else:
                logger.warning(f"No session found with ID: {session_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get basic statistics about chat sessions.
        
        Returns:
            Dictionary containing session statistics
        """
        try:
            if self.chat_sessions is None or self.db is None:
                logger.error("Not connected to database")
                return {}
            
            total_sessions = self.chat_sessions.count_documents({})
            
            # Get sessions from last 24 hours
            yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            recent_sessions = self.chat_sessions.count_documents({
                "created_at": {"$gte": yesterday}
            })
            
            stats = {
                "total_sessions": total_sessions,
                "sessions_today": recent_sessions,
                "collection_name": self.chat_sessions.name,
                "database_name": self.db.name
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}

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

# Example usage function
def example_usage():
    """Example of how to use the database service."""
    
    # Using context manager (recommended)
    try:
        with DatabaseContext() as db:
            # Save a session
            session_data = {
                "session_id": "example_session_123",
                "user_id": "user_456",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ],
                "duration_minutes": 5,
                "event_searches": 2
            }
            
            session_id = db.save_chat_session(session_data)
            print(f"Saved session: {session_id}")
            
            # Get session stats
            stats = db.get_session_stats()
            print(f"Database stats: {stats}")
            
    except Exception as e:
        print(f"Database operation failed: {e}")

if __name__ == "__main__":
    example_usage()
