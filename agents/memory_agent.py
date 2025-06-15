from agents.base_agent import BaseAgent
from openai import OpenAI
from typing import Dict, Any, Optional
from structs.context import Context
from structs.message import Message
from memory.chat_memory import ChatMemory
from tools.today_date import TodayDateTool
from pathlib import Path
import json

class MemoryAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()
        
        system_prompt_path = Path(__file__).parent / "system_prompts" / "memory_agent.txt"
        self.system_prompt = Message(
            role="system",
            content=system_prompt_path.read_text()
        )
        
        # Include today's date tool
        self.today_date_tool = TodayDateTool()
        
    def summarize_memory(self, chat_memory: ChatMemory) -> str:
        """
        Summarize the conversation history and extract user preferences
        """
        # Get today's date
        today_date = self.today_date_tool.run({})
        
        # Get conversation history from memory
        memory_content = chat_memory.get_memory()
        current_summary = chat_memory.get_summary()
        if not current_summary:
            current_summary = "No previous summary available."
        
        if not memory_content or memory_content == "No conversation history available.":
            return f"Today's date: {today_date}\nMemory is empty. No summary can be created."
            
        # Create a message for summarization
        summarization_request = Message(
            role="user",
            content=f"Here is the current summary and most recent message/messages. Create a new summary "+
                f"that doesn't exclude any information from the previous one " +
                f"and adds information from the new messages. Include today's date " + 
                f"({today_date}):\nCurrent Summary\n{current_summary}\nRecent Messages\n{memory_content}"
        )
        
        # Create a temporary context for this request
        temp_context = Context()
        temp_context.add_message(summarization_request)
        temp_context.add_message(self.system_prompt)
        
        # Convert messages to proper format
        messages_for_api = temp_context.messages_for_api()
        
        # Get summary from the AI
        completion = self.client.chat.completions.create(
            model="gpt-4.1",
            messages=messages_for_api
        )
        
        summary = completion.choices[0].message.content
        if not summary:
            summary = "No summary generated."
        
        return summary
        
    def process(self, message: Message, context: Context) -> Dict[str, Any]:
        # """
        # Process memory summarization requests
        # """
        # # This is only here to satisfy the base class, but memory agent primarily uses summarize_memory
        # context.add_message(message)
        
        # # Convert messages to proper format
        # messages_for_api = []
        # for m in context.get_messages():
        #     if m.role == "system":
        #         messages_for_api.append({"role": m.role, "content": m.content})
        #     elif m.role == "user":
        #         messages_for_api.append({"role": m.role, "content": m.content})
        #     elif m.role == "assistant":
        #         messages_for_api.append({"role": m.role, "content": m.content})
        
        # completion = self.client.chat.completions.create(
        #     model="gpt-4.1",
        #     messages=messages_for_api
        # )
        
        # assistant_message = completion.choices[0].message
        # assistant_response = assistant_message.content if assistant_message.content else ""
        
        # context.add_message(
        #     Message(
        #         role="assistant",
        #         content=assistant_response
        #     )
        # )
        
        # return {"context": context, "response": assistant_response}
        return {"context": context, "response": ""}
