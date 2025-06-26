#!/usr/bin/env python3
"""
Simple script to connect to remote MongoDB and insert imaginary chat session data.
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import random

# MongoDB connection URL
MONGO_URL = "***REMOVED***"

def connect_to_mongodb():
    """Connect to MongoDB and return database and collection objects."""
    try:
        # Create MongoDB client
        client = MongoClient(MONGO_URL)
        
        # Test the connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # Access the database (note: you mentioned 'trhugo' but URL shows 'Thrugo')
        db = client['Thrugo']  # Using the database name from the connection string
        
        # Access the chat_sessions collection
        collection = db['chat_sessions']
        
        return client, db, collection
    
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None, None, None

def generate_sample_session():
    """Generate a sample chat session with imaginary data."""
    session_id = str(uuid.uuid4())
    
    # Random session duration between 1-60 minutes
    duration_minutes = random.randint(1, 60)
    start_time = datetime.now() - timedelta(hours=random.randint(0, 24))
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Sample conversation messages
    sample_conversations = [
        [
            {"role": "user", "content": "Hi, I'm looking for concerts in New York this weekend"},
            {"role": "assistant", "content": "I'd be happy to help you find concerts in New York this weekend! Let me search for upcoming events."},
            {"role": "user", "content": "I prefer rock or pop music"},
            {"role": "assistant", "content": "Great! I found several rock and pop concerts this weekend. Here are some options..."}
        ],
        [
            {"role": "user", "content": "What comedy shows are happening in Los Angeles?"},
            {"role": "assistant", "content": "Let me find comedy shows in Los Angeles for you."},
            {"role": "user", "content": "Preferably something this Friday night"},
            {"role": "assistant", "content": "I found several comedy shows on Friday night in LA..."}
        ],
        [
            {"role": "user", "content": "Are there any jazz festivals coming up?"},
            {"role": "assistant", "content": "I'll search for upcoming jazz festivals for you."},
            {"role": "user", "content": "Within 100 miles of Chicago would be perfect"},
            {"role": "assistant", "content": "Here are some jazz festivals within 100 miles of Chicago..."}
        ]
    ]
    
    conversation = random.choice(sample_conversations)
    
    session_data = {
        "session_id": session_id,
        "user_id": f"user_{random.randint(1000, 9999)}",
        "start_time": start_time,
        "end_time": end_time,
        "duration_minutes": duration_minutes,
        "messages": conversation,
        "total_messages": len(conversation),
        "user_location": random.choice(["New York", "Los Angeles", "Chicago", "Miami", "Seattle"]),
        "event_searches_performed": random.randint(1, 5),
        "events_found": random.randint(0, 15),
        "session_outcome": random.choice(["completed", "abandoned", "escalated"]),
        "user_satisfaction": random.choice([1, 2, 3, 4, 5]),
        "created_at": datetime.now(),
        "metadata": {
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "device": random.choice(["desktop", "mobile", "tablet"]),
            "platform": random.choice(["Windows", "macOS", "iOS", "Android"])
        }
    }
    
    return session_data

def insert_sample_sessions(collection, num_sessions=5):
    """Insert multiple sample sessions into the database."""
    try:
        sessions = []
        for i in range(num_sessions):
            session = generate_sample_session()
            sessions.append(session)
        
        # Insert all sessions at once
        result = collection.insert_many(sessions)
        
        print(f"✅ Successfully inserted {len(result.inserted_ids)} sessions!")
        print(f"📝 Inserted session IDs: {result.inserted_ids}")
        
        return result.inserted_ids
    
    except Exception as e:
        print(f"❌ Error inserting sessions: {e}")
        return None

def query_sessions(collection, limit=5):
    """Query and display some sessions from the database."""
    try:
        print(f"\n📊 Fetching last {limit} sessions from the database:")
        sessions = collection.find().sort("created_at", -1).limit(limit)
        
        for i, session in enumerate(sessions, 1):
            print(f"\n--- Session {i} ---")
            print(f"Session ID: {session['session_id']}")
            print(f"User ID: {session['user_id']}")
            print(f"Start Time: {session['start_time']}")
            print(f"Duration: {session['duration_minutes']} minutes")
            print(f"Messages: {session['total_messages']}")
            print(f"Location: {session['user_location']}")
            print(f"Outcome: {session['session_outcome']}")
            print(f"Satisfaction: {session['user_satisfaction']}/5")
        
    except Exception as e:
        print(f"❌ Error querying sessions: {e}")

def main():
    """Main function to run the MongoDB test script."""
    print("🚀 Starting MongoDB connection test...")
    
    # Connect to MongoDB
    client, db, collection = connect_to_mongodb()
    
    if client is None or db is None or collection is None:
        print("❌ Failed to connect to MongoDB. Exiting.")
        return
    
    print(f"📍 Connected to database: {db.name}")
    print(f"📁 Using collection: chat_sessions")
    
    # Check current document count
    current_count = collection.count_documents({})
    print(f"📈 Current documents in collection: {current_count}")
    
    # Insert sample sessions
    print("\n💾 Inserting sample chat sessions...")
    inserted_ids = insert_sample_sessions(collection, num_sessions=3)
    
    if inserted_ids:
        # Query and display sessions
        query_sessions(collection, limit=3)
        
        # Show updated count
        new_count = collection.count_documents({})
        print(f"\n📈 Total documents in collection after insert: {new_count}")
    
    # Close the connection
    client.close()
    print("\n🔐 MongoDB connection closed.")

if __name__ == "__main__":
    main()
