#!/usr/bin/env python3
"""
Simple MongoDB connection script - minimal version for quick testing.
"""

from pymongo import MongoClient
from datetime import datetime
import uuid

# MongoDB connection
MONGO_URL = "***REMOVED***"

def simple_insert():
    """Simple function to insert one document."""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URL)
        db = client['Thrugo']
        collection = db['chat_sessions']
        
        # Create a simple document
        document = {
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user_123",
            "message": "Hello from Python script!",
            "timestamp": datetime.now(),
            "test_run": True
        }
        
        # Insert the document
        result = collection.insert_one(document)
        print(f"✅ Document inserted with ID: {result.inserted_id}")
        
        # Query it back
        found_doc = collection.find_one({"_id": result.inserted_id})
        print(f"📄 Retrieved document: {found_doc}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simple_insert()
