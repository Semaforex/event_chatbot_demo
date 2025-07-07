import streamlit as st
import json
from services.message_processing_service import process_message_service
from structs.chat_message_dto import ChatMessageDto

def main():
    st.title("Event Chatbot - Multi-Channel Messaging")
    st.write("Send messages to different channels and see the raw bot responses")
    
    # Create two columns for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        channel_id = st.text_input(
            "Channel ID", 
            placeholder="Enter channel ID (e.g., channel_123)",
            help="Unique identifier for the chat channel"
        )
    
    with col2:
        persona_id = st.text_input(
            "Persona ID", 
            value="default_persona",
            help="Persona identifier for the conversation"
        )
    
    # Message input
    message = st.text_area(
        "Message", 
        placeholder="Type your message here...",
        height=100
    )
    
    # Send button
    if st.button("Send Message", type="primary"):
        if not channel_id:
            st.error("Please enter a Channel ID")
        elif not message:
            st.error("Please enter a message")
        else:
            # Show loading spinner while processing
            with st.spinner("Processing message..."):
                try:
                    # Create the ChatMessageDto
                    chat_dto = ChatMessageDto(
                        message=message,
                        chat_id=channel_id,
                        persona_id=persona_id
                    )
                    
                    # Process the message
                    result = process_message_service(chat_dto)
                    
                    # Display results
                    st.success("Message processed successfully!")
                    
                    # Show the raw output in an expandable section
                    with st.expander("📋 Raw Response Output", expanded=True):
                        st.json(result.model_dump())
                    
                    # Show formatted response
                    st.subheader("🤖 Bot Response")
                    st.write(result.ai_response)
                    
                    # Show additional data if available
                    if result.data and result.data.events_found:
                        st.subheader("🎟️ Events Found")
                        for i, event in enumerate(result.data.events_found, 1):
                            with st.expander(f"Event {i}: {event.name}"):
                                st.write(f"**Date:** {event.start_date_time}")
                                st.write(f"**Description:** {event.description}")
                                if event.venue:
                                    st.write(f"**Venue:** {event.venue}")
                                if event.url:
                                    st.write(f"**URL:** {event.url}")
                    
                except Exception as e:
                    st.error(f"Error processing message: {str(e)}")
                    st.write("Error details:")
                    st.code(str(e))
    
    # Add some helpful information in the sidebar
    with st.sidebar:
        st.header("ℹ️ Information")
        st.write("""
        **How to use:**
        1. Enter a unique Channel ID
        2. Optionally change the Persona ID
        3. Type your message
        4. Click 'Send Message'
        
        **Note:** Each channel maintains its own conversation history.
        """)
        
        st.header("🔧 Current Configuration")
        st.write(f"**Channels active:** {len(st.session_state.get('channels', []))}")

if __name__ == "__main__":
    main()