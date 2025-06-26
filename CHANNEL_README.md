# Event Chatbot - Channel-Based Version

## 📺 Channel-Based Chat System

This enhanced version of the Event Chatbot uses a channel-based approach for organizing conversations. No user accounts are needed - just create or switch between channels!

### 🌟 Key Features

- **📺 Channel System**: Each conversation is a separate channel with unique ID
- **🔄 Easy Switching**: Switch between existing channels instantly
- **💾 Auto-Save**: All conversations are automatically saved to MongoDB
- **🚀 No Registration**: No user accounts needed - just start chatting!
- **📊 Channel Overview**: View all channels with message counts and timestamps

### 🛠️ Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - MongoDB URL is configured in `.env`
   - Make sure all API keys are set in `.env`

3. **Database Connection**:
   - Uses MongoDB Atlas cluster: `Thrugo` database
   - Collection: `chat_sessions`
   - Automatic connection on startup

### 🎯 How to Use

#### Start the Channel-Based App
```bash
python -m streamlit run main_multi_session.py --server.port 8502
```

### 📱 App Usage

1. **Create Channel**: Click "🆕 New Channel" to start a fresh conversation
2. **Switch Channels**: Click "📂" next to any channel to load it
3. **Chat**: Ask about events, concerts, shows, and more!
4. **Auto-Save**: Messages are automatically saved after each interaction

### 🧪 Testing

Run the test scripts to verify functionality:

```bash
# Test channel system
python test_channels.py

# Test basic MongoDB connection  
python mongodb_test.py

# Simple MongoDB operations
python simple_mongo.py
```

### 📂 File Structure

```
main_multi_session.py         # Channel-based Streamlit app
services/database_service.py  # MongoDB integration service
test_channels.py              # Channel system test
mongodb_test.py               # MongoDB connection test
simple_mongo.py               # Simple MongoDB test
```

### 🔧 Channel Schema

Each channel document contains:
```json
{
  "session_id": "channel_12345678",
  "channel_id": "channel_12345678", 
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "created_at": "2025-06-26T16:30:00",
  "last_updated": "2025-06-26T16:35:00",
  "message_count": 2,
  "status": "active"
}
```

### 🌐 Access

- **Channel-Based App**: http://localhost:8502

### 💡 Example User Flow

1. Open http://localhost:8502
2. Click "🆕 New Channel" → Get Channel ID: `channel_abc12345`
3. Chat: "Find concerts in New York this weekend"
4. Create another channel for different topics: `channel_def67890`
5. Switch between channels using the sidebar
6. All conversations are preserved automatically!

### 📺 Channel Management

The sidebar shows:
- **New Channel**: Create fresh conversations
- **Channel List**: All available channels with:
  - Channel ID
  - Last updated timestamp
  - Message count
  - Quick load button
- **Database Stats**: Total channels and activity

### 🔍 Database Operations

The `DatabaseService` class provides:
- `save_chat_session()` - Save new channels
- `get_chat_session()` - Load specific channel
- `get_all_sessions()` - Get all channels
- `update_session()` - Update existing channel
- `get_session_stats()` - Database statistics

### 🚨 Key Changes from User-Based System

- ❌ **Removed**: User accounts, login/logout, user management
- ❌ **Removed**: Memory summary display
- ✅ **Added**: Channel-based organization
- ✅ **Added**: Global channel list (all channels visible)
- ✅ **Simplified**: One-click channel creation and switching

### 🎪 Features Available

- **🎯 Event Search**: Find concerts, shows, festivals by location/date
- **🎵 Music Events**: Rock, pop, jazz, classical concerts
- **🎭 Entertainment**: Comedy shows, theater, sports events
- **📅 Event Details**: Dates, venues, ticket information
- **📺 Multi-Channel**: Organize different event searches in separate channels

Enjoy your streamlined Event Chatbot with channel-based conversations! 🎉
