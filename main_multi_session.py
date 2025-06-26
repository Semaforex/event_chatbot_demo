import streamlit as st
from agents.event_agent import EventAgent
from structs.context import Context
from structs.message import Message
from services.moderation_service import ModerationService
from services.database_service import DatabaseService
from dotenv import load_dotenv
import os
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(override=True)

st.set_page_config(page_title="Event Chat - Channels", page_icon=":speech_balloon:", layout="wide")

# Initialize database service
@st.cache_resource
def get_database_service():
    """Initialize and cache the database service."""
    try:
        db_service = DatabaseService()
        if db_service.connect():
            logger.info("Database service initialized successfully")
            return db_service
        else:
            logger.error("Failed to connect to database")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize database service: {e}")
        return None

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables."""
    if "db_service" not in st.session_state:
        st.session_state.db_service = get_database_service()
    
    if "current_channel_id" not in st.session_state:
        st.session_state.current_channel_id = None
    
    if "all_channels" not in st.session_state:
        st.session_state.all_channels = []
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "context" not in st.session_state:
        st.session_state.context = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    
    if "moderation_service" not in st.session_state:
        try:
            st.session_state.moderation_service = ModerationService()
            logger.info("Moderation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize moderation service: {e}")
            st.session_state.moderation_service = None

def load_all_channels():
    """Load all available channels from the database."""
    if not st.session_state.db_service:
        return []
    
    try:
        # Get all sessions/channels from database
        channels = st.session_state.db_service.get_all_sessions(limit=50)
        
        # Convert to channel format
        channel_list = []
        for channel in channels:
            channel_info = {
                "channel_id": channel.get("session_id", channel.get("channel_id", "unknown")),
                "created_at": channel.get("created_at"),
                "last_updated": channel.get("last_updated", channel.get("created_at")),
                "message_count": channel.get("message_count", len(channel.get("messages", []))),
                "status": channel.get("status", "active")
            }
            channel_list.append(channel_info)
        
        return channel_list
    except Exception as e:
        logger.error(f"Failed to load channels: {e}")
        return []

def create_new_channel():
    """Create a new chat channel."""
    channel_id = f"channel_{uuid.uuid4().hex[:8]}"
    st.session_state.current_channel_id = channel_id
    st.session_state.agent = EventAgent()
    st.session_state.context = Context()
    st.session_state.chat_history = []
    
    # Save empty channel to database
    channel_data = {
        "session_id": channel_id,  # Using session_id field for channel_id
        "channel_id": channel_id,  # Keep both for clarity
        "messages": [],
        "created_at": datetime.now(),
        "last_updated": datetime.now(),
        "message_count": 0,
        "status": "active"
    }
    
    if st.session_state.db_service:
        st.session_state.db_service.save_chat_session(channel_data)
    
    # Refresh channel list
    st.session_state.all_channels = load_all_channels()
    
    st.success(f"New channel created: **{channel_id}**")
    return channel_id

def load_channel(channel_id: str):
    """Load an existing chat channel."""
    if not st.session_state.db_service:
        st.error("Database connection not available")
        return False
    
    try:
        channel_data = st.session_state.db_service.get_chat_session(channel_id)
        if not channel_data:
            st.error("Channel not found")
            return False
        
        st.session_state.current_channel_id = channel_id
        st.session_state.agent = EventAgent()
        st.session_state.context = Context()
        
        # Load chat history
        messages = channel_data.get("messages", [])
        st.session_state.chat_history = []
        
        for msg in messages:
            if msg.get("role") == "user":
                st.session_state.chat_history.append(("You", msg.get("content", "")))
                # Add to context for the agent
                st.session_state.context.add_message(Message(role="user", content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                st.session_state.chat_history.append(("Assistant", msg.get("content", "")))
                st.session_state.context.add_message(Message(role="assistant", content=msg.get("content", "")))
        
        st.success(f"Channel loaded: **{channel_id}**")
        return True
    except Exception as e:
        st.error(f"Failed to load channel: {e}")
        return False

def save_current_channel():
    """Save the current channel to database."""
    if not st.session_state.db_service or not st.session_state.current_channel_id:
        return
    
    try:
        # Convert chat history to messages format
        messages = []
        for i in range(0, len(st.session_state.chat_history), 2):
            if i < len(st.session_state.chat_history):
                user_msg = st.session_state.chat_history[i]
                if user_msg[0] == "You":
                    messages.append({"role": "user", "content": user_msg[1]})
            
            if i + 1 < len(st.session_state.chat_history):
                assistant_msg = st.session_state.chat_history[i + 1]
                if assistant_msg[0] == "Assistant":
                    messages.append({"role": "assistant", "content": assistant_msg[1]})
        
        update_data = {
            "messages": messages,
            "last_updated": datetime.now(),
            "message_count": len(messages),
            "status": "active"
        }
        
        st.session_state.db_service.update_session(st.session_state.current_channel_id, update_data)
        
        # Refresh channel list
        st.session_state.all_channels = load_all_channels()
        
    except Exception as e:
        logger.error(f"Failed to save channel: {e}")

def format_events_display(events):
    """Format events for display with nice borders and formatting."""
    if not events:
        return ""
    
    formatted_events = []
    for i, event in enumerate(events, 1):
        # Format venue information
        venue_info = "Venue not specified"
        if event.venues and len(event.venues) > 0:
            venue = event.venues[0]
            venue_parts = [venue.name]
            if venue.city:
                venue_parts.append(venue.city)
            if venue.country:
                venue_parts.append(venue.country)
            venue_info = ", ".join(venue_parts)
        
        # Format date and time
        date_time = event.dates.start_date
        if event.dates.start_time:
            date_time += f" at {event.dates.start_time}"
        
        # Create the event card with border
        event_card = f"""
**Event {i}**
📅 **{event.name}**
📍 **Venue:** {venue_info}
🕒 **Date & Time:** {date_time}
🔗 **URL:** [View Event]({event.url})
"""
        
        if event.description:
            event_card += f"📝 **Description:** {event.description}\n"
        
        formatted_events.append(event_card)
    
    return "\n" + "─" * 50 + "\n" + "\n─────────────────────────────────────────────────\n".join(formatted_events) + "\n" + "─" * 50

def send_message():
    """Process and send a message in the current channel."""
    user_input = st.session_state.user_input.strip()
    
    # Skip empty messages
    if not user_input:
        return
    
    if not st.session_state.current_channel_id or not st.session_state.agent:
        st.error("Please create or select a channel first")
        return
        
    # Check moderation if service is available
    content_flagged = False
    if st.session_state.moderation_service:
        try:
            content_flagged = st.session_state.moderation_service.is_flagged(user_input)
            if content_flagged:
                # Get detailed information about flagged categories
                flagged_categories = st.session_state.moderation_service.get_flagged_categories(user_input)
                categories_str = ", ".join(flagged_categories.get(user_input, []))
                logger.warning(f"User message flagged by moderation API. Categories: {categories_str}")
                
                # Add user message to history but respond with moderation message
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("Assistant", "I'm sorry, but I can't respond to that message as it may contain inappropriate content. Please try a different request."))
                st.session_state.user_input = ""
                save_current_channel()
                return
        except Exception as e:
            logger.error(f"Error during content moderation: {e}")
            # Continue with message processing if moderation fails
    
    # Process message normally if not flagged
    user_message = Message(role="user", content=user_input)
    result = st.session_state.agent.process(user_message, st.session_state.context)
    st.session_state.context = result["context"]
    response = result["response"]
    events_found = result.get("events_found", [])
    
    # Optionally check the response with moderation API as well
    response_flagged = False
    if st.session_state.moderation_service:
        try:
            response_flagged = st.session_state.moderation_service.is_flagged(response)
            if response_flagged:
                logger.warning("Assistant response flagged by moderation API")
                response = "I apologize, but I can't provide that information. Let me know if I can help with something else."
        except Exception as e:
            logger.error(f"Error during response moderation: {e}")
    
    st.session_state.chat_history.append(("You", user_input))
    
    # Format events nicely if any were found
    events_display = format_events_display(events_found) if events_found else ""
    
    # Combine response text with formatted events (ensure response is clean text)
    if isinstance(response, dict):
        # If response is still a dict, extract the text part
        response = response.get("resp", str(response))
    
    assistant_message = response + events_display
    
    st.session_state.chat_history.append(("Assistant", assistant_message))
    st.session_state.user_input = ""
    
    # Save channel after each message
    save_current_channel()

def main():
    """Main application function."""
    initialize_session_state()
    
    st.title("📺 Event Chat - Channels")
    
    # Load all channels on startup
    if not st.session_state.all_channels:
        st.session_state.all_channels = load_all_channels()
    
    # Sidebar for channel management
    with st.sidebar:
        st.header("📺 Channel Management")
        
        # Create new channel
        if st.button("🆕 New Channel", use_container_width=True):
            create_new_channel()
            st.rerun()
        
        # Refresh channels button
        if st.button("� Refresh", use_container_width=True):
            st.session_state.all_channels = load_all_channels()
            st.rerun()
        
        st.write("---")
        
        # Display available channels
        if st.session_state.all_channels:
            st.subheader("📋 Available Channels")
            
            for channel in st.session_state.all_channels:
                channel_id = channel.get("channel_id", "Unknown")
                created_at = channel.get("created_at", "Unknown")
                last_updated = channel.get("last_updated")
                message_count = channel.get("message_count", 0)
                
                # Format date
                if isinstance(last_updated, datetime):
                    date_str = last_updated.strftime("%m/%d %H:%M")
                elif isinstance(created_at, datetime):
                    date_str = created_at.strftime("%m/%d %H:%M")
                else:
                    date_str = str(last_updated or created_at)[:16] if (last_updated or created_at) != "Unknown" else "Unknown"
                
                # Show current channel differently
                if channel_id == st.session_state.current_channel_id:
                    st.info(f"🟢 **{channel_id}**\n{date_str} | {message_count} msgs")
                else:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{channel_id}**\n{date_str} | {message_count} msgs")
                    with col2:
                        if st.button("📂", key=f"load_{channel_id}", help="Load channel"):
                            load_channel(channel_id)
                            st.rerun()
        else:
            st.info("No channels available. Create a new channel to get started!")
        
        # Database stats
        if st.session_state.db_service:
            st.write("---")
            st.subheader("📊 Database Stats")
            try:
                stats = st.session_state.db_service.get_session_stats()
                st.metric("Total Channels", stats.get("total_sessions", 0))
                st.metric("Channels Today", stats.get("sessions_today", 0))
            except:
                st.error("Could not load stats")
    
    # Main chat interface
    if not st.session_state.current_channel_id:
        st.info("👈 Please create a new channel or select an existing one to start chatting!")
        
        # Show some information about the app
        st.subheader("🌟 Welcome to Event Chat!")
        st.write("""
        This chatbot helps you find events, concerts, shows, and more! Here's what you can do:
        
        **🔧 Features:**
        - 🎯 Search for events by location, date, or type
        - 🎵 Find concerts, comedy shows, sports events, and more
        - 📅 Get detailed event information including dates, venues, and tickets
        - � Multiple channels - keep different conversations organized
        - � Persistent storage - your conversations are automatically saved
        
        **🚀 Getting Started:**
        1. Create a new channel or select an existing one
        2. Ask me about events you're interested in!
        
        **💡 Example questions:**
        - "What concerts are happening in New York this weekend?"
        - "Find comedy shows in Los Angeles"
        - "Are there any jazz festivals coming up?"
        - "What events are happening tonight near me?"
        """)
        
        # Show recent channels if any exist
        if st.session_state.all_channels:
            st.subheader("📚 Recent Channels")
            for channel in st.session_state.all_channels[:5]:
                channel_id = channel.get("channel_id", "Unknown")
                created_at = channel.get("created_at", "Unknown")
                message_count = channel.get("message_count", 0)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{channel_id}**")
                with col2:
                    st.write(f"{message_count} messages")
                with col3:
                    if st.button("Load", key=f"main_load_{channel_id}"):
                        load_channel(channel_id)
                        st.rerun()
    
    else:
        # Chat interface
        st.subheader(f"� Channel: {st.session_state.current_channel_id}")
        
        # Chat input
        st.text_input("You:", key="user_input", on_change=send_message, placeholder="Ask me about events...")
        
        # Display chat history
        if st.session_state.chat_history:
            st.write("---")
            for role, msg in st.session_state.chat_history:
                if role == "You":
                    st.markdown(f"**🙋‍♂️ You:** {msg}")
                else:
                    st.markdown(f"**🤖 Assistant:** {msg}")
        else:
            st.info("Start a conversation! Ask me about events, concerts, shows, or anything entertainment-related.")

if __name__ == "__main__":
    main()
