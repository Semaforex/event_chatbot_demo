import streamlit as st
from agents.event_agent import EventAgent
from structs.context import Context
from structs.message import Message
from services.moderation_service import ModerationService
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv(override=True)

st.set_page_config(page_title="Event Chat", page_icon=":speech_balloon:")

st.title("Event Chat")

if "agent" not in st.session_state:
    st.session_state.agent = EventAgent()
if "context" not in st.session_state:
    st.session_state.context = Context()
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

def send_message():
    user_input = st.session_state.user_input.strip()
    
    # Skip empty messages
    if not user_input:
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
                return
        except Exception as e:
            logger.error(f"Error during content moderation: {e}")
            # Continue with message processing if moderation fails
    
    # Process message normally if not flagged
    user_message = Message(role="user", content=user_input)
    result = st.session_state.agent.process(user_message, st.session_state.context)
    st.session_state.context = result["context"]
    response = result["response"]
    
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
    st.session_state.chat_history.append(("Assistant", response))
    st.session_state.user_input = ""

st.text_input("You:", key="user_input", on_change=send_message)

# Display chat history
for role, msg in st.session_state.chat_history:
    if role == "You":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**Assistant:** {msg}")

# Add a memory viewer in the sidebar if there are messages
if st.session_state.agent and hasattr(st.session_state.agent, "memory_agent"):
    with st.sidebar:
        summary = st.session_state.agent.memory.get_summary()
        st.subheader("Memory Summary")
        st.write(summary)
        
        # Add moderation debug section (hidden by default)
        with st.expander("Moderation Debug", expanded=False):
            st.caption("Analyze content with OpenAI Moderation API")
            debug_input = st.text_area("Enter text to check:")
            
            if st.button("Check Content") and debug_input and st.session_state.moderation_service:
                try:
                    analysis = st.session_state.moderation_service.get_moderation_analysis(debug_input)
                    st.json(analysis)
                except Exception as e:
                    st.error(f"Error analyzing content: {e}")
