from typing import Dict, Any, List, Optional
from memory.base_memory import BaseMemory
from structs.message import Message
from datetime import datetime
from tools.today_date import TodayDateTool
import json

class ChatMemory(BaseMemory):
    def __init__(self):
        self.messages: List[Message] = []
        today_date = TodayDateTool().run({})
        self.summary = f"Today's date: {today_date}.\nNo summary available."
    

    def add_message(self, message: Message, response: str) -> None:
        """Add a message and response to the memory"""
        if message.role == "user":
            today = datetime.now().strftime('%Y-%m-%d')
            user_msg = Message(role="user", content=f"[{today}] {message.content}")
            assistant_msg = Message(role="assistant", content=response)
            self.messages.append(user_msg)
            self.messages.append(assistant_msg)


    def get_memory(self) -> str:
        """Get the conversation memory as a string"""
        if not self.messages:
            return "No conversation history available."
        memory_str = ""
        for message in self.messages:
            if message.role == "user":
                memory_str += f"User: {message.content}\n"
            elif message.role == "assistant":
                memory_str += f"Assistant: {message.content}\n"
        return memory_str.strip() if memory_str else "No conversation history available."
            
    def get_messages(self):
        """Get the raw messages from memory"""
        return self.messages
    
    def clear(self) -> None:
        """Clear the memory"""
        self.messages = []
        self.user_preferences = {}
    
    def get_summary(self) -> str:
        """Get the current summary of the conversation"""
        return self.summary

    def update_summary(self, summary: str) -> None:
        """Update the summary of the conversation"""
        self.summary = summary
