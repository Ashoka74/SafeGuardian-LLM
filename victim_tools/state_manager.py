# state_manager.py

import streamlit as st
from typing import Dict, Any

class StateManager:
    def __init__(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def add_message(self, role: str, content: str):
        """Add a new message to the chat history."""
        st.session_state.messages.append({"role": role, "content": content})

    def display_messages(self):
        """Display all messages in the chat history."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def get_last_message(self) -> Dict[str, str]:
        """Get the last message from the chat history."""
        if st.session_state.messages:
            return st.session_state.messages[-1]
        return {"role": "", "content": ""}

    def clear_messages(self):
        """Clear all messages from the chat history."""
        st.session_state.messages = []

    def get_conversation_history(self) -> str:
        """Get the entire conversation history as a single string."""
        return "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

    def update_victim_info(self, new_info: Dict[str, Any]):
        """Update the victim information in the session state."""
        if 'victim_info' not in st.session_state:
            st.session_state.victim_info = {}
        st.session_state.victim_info.update(new_info)