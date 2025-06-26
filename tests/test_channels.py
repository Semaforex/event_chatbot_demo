#!/usr/bin/env python3
"""
Test script for channel-based chat system with MongoDB.
"""

from services.database_service import DatabaseContext
from datetime import datetime
import uuid

def test_channel_system():
    """Test creating and managing channels."""
    
    print("📺 Testing Channel-Based Chat System")
    print("=" * 40)
    
    try:
        with DatabaseContext() as db:
            # Create multiple channels
            channels = []
            for i in range(3):
                channel_id = f"channel_{uuid.uuid4().hex[:8]}"
                
                channel_data = {
                    "channel_id": channel_id,
                    "messages": [
                        {"role": "user", "content": f"Hello from channel {i+1}"},
                        {"role": "assistant", "content": f"Welcome to channel {i+1}! How can I help you with events today?"}
                    ],
                    "created_at": datetime.now(),
                    "last_updated": datetime.now(),
                    "message_count": 2,
                    "status": "active",
                    "test_channel": True
                }
                
                doc_id = db.save_chat_session(channel_data)
                channels.append(channel_id)
                print(f"📺 Created channel {i+1}: {channel_id} (DB ID: {doc_id})")
            
            print(f"\n📊 Total channels created: {len(channels)}")
            
            # Test retrieving all channels
            print(f"\n🔍 Retrieving all channels:")
            all_channels = db.get_all_sessions(limit=20)
            
            print(f"📚 Found {len(all_channels)} channels:")
            for i, channel in enumerate(all_channels, 1):
                channel_id = channel.get('channel_id', 'Unknown')
                message_count = channel.get('message_count', len(channel.get('messages', [])))
                created_at = channel.get('created_at', 'Unknown')
                print(f"  {i}. {channel_id} - {message_count} messages ({created_at})")
            
            # Test loading a specific channel
            if channels:
                test_channel_id = channels[0]
                print(f"\n🔄 Loading channel: {test_channel_id}")
                channel_data = db.get_chat_session(test_channel_id)
                
                if channel_data:
                    print(f"✅ Channel loaded successfully!")
                    print(f"   - Channel ID: {channel_data.get('channel_id')}")
                    print(f"   - Messages: {len(channel_data.get('messages', []))}")
                    print(f"   - Created: {channel_data['created_at']}")
                    
                    # Display messages
                    messages = channel_data.get('messages', [])
                    if messages:
                        print(f"   - Chat Preview:")
                        for msg in messages:
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
                            print(f"     {role}: {content}")
                else:
                    print("❌ Failed to load channel")
            
            # Test updating a channel with new messages
            if channels:
                test_channel_id = channels[0]
                print(f"\n📝 Adding messages to channel: {test_channel_id}")
                
                # Simulate adding new messages
                new_messages = [
                    {"role": "user", "content": "Can you find concerts in New York this weekend?"},
                    {"role": "assistant", "content": "I'll search for concerts in New York for this weekend. Let me find some options for you!"}
                ]
                
                # Get current messages and add new ones
                current_channel = db.get_chat_session(test_channel_id)
                if current_channel:
                    current_messages = current_channel.get('messages', [])
                    all_messages = current_messages + new_messages
                    
                    update_data = {
                        "messages": all_messages,
                        "last_updated": datetime.now(),
                        "message_count": len(all_messages),
                        "status": "active"
                    }
                    
                    success = db.update_session(test_channel_id, update_data)
                    if success:
                        print("✅ Channel updated with new messages!")
                        print(f"   - Total messages now: {len(all_messages)}")
                    else:
                        print("❌ Failed to update channel")
            
            # Get overall stats
            print(f"\n📈 Database Statistics:")
            stats = db.get_session_stats()
            for key, value in stats.items():
                print(f"   - {key}: {value}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

def test_channel_filtering():
    """Test filtering and sorting of channels."""
    
    print(f"\n🔍 Testing Channel Filtering & Sorting")
    print("=" * 40)
    
    try:
        with DatabaseContext() as db:
            # Get all channels and display them sorted
            all_channels = db.get_all_sessions(limit=10)
            
            if all_channels:
                print(f"📋 All Channels (sorted by last updated):")
                for i, channel in enumerate(all_channels, 1):
                    channel_id = channel.get('channel_id', 'Unknown')
                    last_updated = channel.get('last_updated', channel.get('created_at', 'Unknown'))
                    message_count = channel.get('message_count', 0)
                    status = channel.get('status', 'unknown')
                    
                    # Format date
                    if isinstance(last_updated, datetime):
                        date_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        date_str = str(last_updated)[:19] if last_updated != "Unknown" else "Unknown"
                    
                    print(f"   {i}. {channel_id}")
                    print(f"      Last Updated: {date_str}")
                    print(f"      Messages: {message_count} | Status: {status}")
                    print()
            else:
                print("No channels found in database")
                
    except Exception as e:
        print(f"❌ Channel filtering test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Channel System Tests...")
    print()
    
    # Run tests
    test_channel_system()
    test_channel_filtering()
    
    print(f"\n✅ All tests completed!")
    print(f"🌐 You can now test the Channel-based app at: http://localhost:8502")
    print(f"📺 Features:")
    print(f"   - Create new channels")
    print(f"   - Switch between existing channels")
    print(f"   - No user accounts needed")
    print(f"   - All conversations are automatically saved")
