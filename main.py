import streamlit as st
from agents.event_agent import EventAgent
from structs.context import Context
from structs.message import Message

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

def send_message():
    user_message = Message(role="user", content=st.session_state.user_input)
    result = st.session_state.agent.process(user_message, st.session_state.context)
    st.session_state.context = result["context"]
    response = result["response"]
    st.session_state.chat_history.append(("You", st.session_state.user_input))
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
