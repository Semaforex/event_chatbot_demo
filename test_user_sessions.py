#!/usr/bin/env python3
"""
Test script for user accounts and session management with MongoDB.
"""

from services.database_service import DatabaseContext
from datetime import datetime
import uuid

def test_user_session_management():
    """Test creating users and sessions."""
    
    print("🧪 Testing User Account & Session Management")
    print("=" * 50)
    
    try:
        with DatabaseContext() as db:
            # Create a test user
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            print(f"👤 Created test user: {user_id}")
            
            # Create multiple sessions for the user
            sessions = []
            for i in range(3):
                session_id = f"session_{uuid.uuid4().hex[:8]}"
                
                session_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "messages": [
                        {"role": "user", "content": f"Hello, this is test message {i+1}"},
                        {"role": "assistant", "content": f"Hi! This is response {i+1} from the assistant."}
                    ],
                    "created_at": datetime.now(),
                    "last_updated": datetime.now(),
                    "message_count": 2,
                    "status": "active",
                    "test_session": True
                }
                
                doc_id = db.save_chat_session(session_data)
                sessions.append(session_id)
                print(f"💬 Created session {i+1}: {session_id} (DB ID: {doc_id})")
            
            print(f"\n📊 Total sessions created: {len(sessions)}")
            
            # Test retrieving user sessions
            print(f"\n🔍 Retrieving sessions for user: {user_id}")
            user_sessions = db.get_user_sessions(user_id)
            
            print(f"📚 Found {len(user_sessions)} sessions:")
            for i, session in enumerate(user_sessions, 1):
                print(f"  {i}. {session['session_id']} - {session['message_count']} messages")
            
            # Test loading a specific session
            if sessions:
                test_session_id = sessions[0]
                print(f"\n🔄 Loading session: {test_session_id}")
                session_data = db.get_chat_session(test_session_id)
                
                if session_data:
                    print(f"✅ Session loaded successfully!")
                    print(f"   - Session ID: {session_data['session_id']}")
                    print(f"   - User ID: {session_data['user_id']}")
                    print(f"   - Messages: {len(session_data.get('messages', []))}")
                    print(f"   - Created: {session_data['created_at']}")
                    
                    # Display messages
                    messages = session_data.get('messages', [])
                    if messages:
                        print(f"   - Chat Preview:")
                        for msg in messages[:2]:  # Show first 2 messages
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
                            print(f"     {role}: {content}")
                else:
                    print("❌ Failed to load session")
            
            # Test updating a session
            if sessions:
                test_session_id = sessions[0]
                print(f"\n📝 Updating session: {test_session_id}")
                
                update_data = {
                    "status": "completed",
                    "final_message_count": 4,
                    "test_update": True
                }
                
                success = db.update_session(test_session_id, update_data)
                if success:
                    print("✅ Session updated successfully!")
                else:
                    print("❌ Failed to update session")
            
            # Get overall stats
            print(f"\n📈 Database Statistics:")
            stats = db.get_session_stats()
            for key, value in stats.items():
                print(f"   - {key}: {value}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

def test_multiple_users():
    """Test multiple users with different sessions."""
    
    print(f"\n🌐 Testing Multiple Users")
    print("=" * 30)
    
    try:
        with DatabaseContext() as db:
            users = []
            
            # Create 3 test users
            for i in range(3):
                user_id = f"testuser_{i+1}_{uuid.uuid4().hex[:6]}"
                users.append(user_id)
                
                # Create 1-3 sessions per user
                num_sessions = i + 1  # User 1 gets 1 session, User 2 gets 2, etc.
                
                for j in range(num_sessions):
                    session_id = f"session_{user_id}_{j+1}"
                    
                    session_data = {
                        "session_id": session_id,
                        "user_id": user_id,
                        "messages": [
                            {"role": "user", "content": f"User {i+1} message in session {j+1}"},
                            {"role": "assistant", "content": f"Response to user {i+1} in session {j+1}"}
                        ],
                        "created_at": datetime.now(),
                        "message_count": 2,
                        "user_number": i + 1,
                        "session_number": j + 1,
                        "multi_user_test": True
                    }
                    
                    db.save_chat_session(session_data)
                
                print(f"👤 User {i+1}: {user_id} ({num_sessions} sessions)")
            
            # Show sessions for each user
            print(f"\n📊 Session Summary:")
            for i, user_id in enumerate(users):
                user_sessions = db.get_user_sessions(user_id)
                print(f"   User {i+1} ({user_id}): {len(user_sessions)} sessions")
                
    except Exception as e:
        print(f"❌ Multi-user test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting MongoDB User & Session Tests...")
    print()
    
    # Run tests
    test_user_session_management()
    test_multiple_users()
    
    print(f"\n✅ All tests completed!")
    print(f"🌐 You can now test the Streamlit app at: http://localhost:8502")
