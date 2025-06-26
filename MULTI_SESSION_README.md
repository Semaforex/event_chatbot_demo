# Event Chatbot Demo - Multi-Session Version

## 🚀 New Multi-Session Features

This enhanced version of the Event Chatbot includes MongoDB integration for user accounts and session management.

### 🌟 Key Features

- **👤 User Accounts**: Create new accounts or login with existing User IDs
- **💬 Multiple Sessions**: Each user can have multiple chat sessions
- **💾 Persistent Storage**: All conversations are saved to MongoDB
- **🔄 Session Management**: Load previous sessions and continue conversations
- **📊 Session Stats**: View database statistics and session counts

### 🛠️ Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   - MongoDB URL is already configured in `.env`
   - Make sure all API keys are set in `.env`

3. **Database Connection**:
   - Uses MongoDB Atlas cluster: `Thrugo` database
   - Collection: `chat_sessions`
   - Connection is automatically established

### 🎯 How to Use

#### Option 1: Multi-Session Streamlit App (Recommended)
```bash
python -m streamlit run main_multi_session.py --server.port 8502
```

#### Option 2: Original Single-Session App
```bash
python -m streamlit run main.py
```

### 📱 Multi-Session App Usage

1. **Create Account**: Click "Create New Account" to get a random User ID
2. **Login**: Enter your User ID to access your sessions
3. **New Session**: Click "New Session" to start a fresh conversation
4. **Load Session**: Click on any previous session to continue the conversation
5. **Chat**: Ask about events, concerts, shows, and more!

### 🧪 Testing

Run the test scripts to verify functionality:

```bash
# Test basic MongoDB connection
python mongodb_test.py

# Test user account and session management
python test_user_sessions.py

# Simple MongoDB operations
python simple_mongo.py
```

### 📂 File Structure

```
main_multi_session.py     # New multi-session Streamlit app
main.py                   # Original single-session app
services/database_service.py  # MongoDB integration service
mongodb_test.py           # MongoDB connection test
test_user_sessions.py     # User session management test
simple_mongo.py           # Simple MongoDB test
```

### 🔧 MongoDB Schema

Each chat session document contains:
```json
{
  "session_id": "session_12345678",
  "user_id": "user_87654321", 
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "created_at": "2025-06-26T10:30:00",
  "last_updated": "2025-06-26T10:35:00",
  "message_count": 2,
  "status": "active"
}
```

### 🌐 Access Points

- **Multi-Session App**: http://localhost:8502
- **Original App**: http://localhost:8501 (if running)

### 💡 Example User Flow

1. Open http://localhost:8502
2. Click "Create New Account" → Get User ID: `user_abc12345`
3. Click "New Session" → Get Session ID: `session_def67890`
4. Chat: "Find concerts in New York this weekend"
5. Create another session for different topics
6. Logout and login later using the same User ID
7. All your sessions and conversations are preserved!

### 🔍 Database Operations

The `DatabaseService` class provides:
- `save_chat_session()` - Save new sessions
- `get_chat_session()` - Load specific session
- `get_user_sessions()` - Get all user sessions
- `update_session()` - Update existing session
- `get_session_stats()` - Database statistics

### 🚨 Important Notes

- **Save Your User ID**: When you create an account, save the User ID! You'll need it to login again.
- **Automatic Saving**: Conversations are automatically saved after each message.
- **Session Persistence**: Sessions remain available across browser sessions and app restarts.
- **Database Connection**: Make sure MongoDB connection is working (test with `mongodb_test.py`).

Enjoy your enhanced Event Chatbot with multi-session support! 🎉
