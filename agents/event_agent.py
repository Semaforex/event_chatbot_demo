from agents.base_agent import BaseAgent
from openai import OpenAI
from typing import Dict, Any, Optional
from structs.context import Context
from structs.message import Message
from tools.event_categories import EventCategoriesAPI
from tools.event_details import TicketmasterEventDetailsAPI
from tools.event_search import EventSearchAPI
from agents.memory_agent import MemoryAgent
from tools.today_date import TodayDateTool
from memory.chat_memory import ChatMemory
from pathlib import Path
from services.event_api_service import format_events_for_llm, EventSearchResponse
import json
import re

class EventAgent(BaseAgent):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()
        today_date = TodayDateTool().run({})
        date_msg = f"Today's date: {today_date}.\n"
        system_prompt_path = Path(__file__).parent / "system_prompts" / "event_agent.txt"
        self.system_prompt = Message(
            role="system",
            content=date_msg+system_prompt_path.read_text()
        )
        
        # Initialize memory components
        self.memory = ChatMemory()        
        # Initialize tools
        event_categories_tool = EventCategoriesAPI()
        event_details_tool = TicketmasterEventDetailsAPI()
        event_search_tool = EventSearchAPI()
        self.tools = {
            # 'search_ticketmaster_events': event_search_tool,
            # 'get_ticketmaster_event_categories': event_categories_tool,
            # 'get_ticketmaster_event_details': event_details_tool,
            'search_events': event_search_tool,
        }
        self.memory_agent = MemoryAgent()

    def process(self, message: Message, context: Context) -> Dict[str, Any]:
        events_found = []
        context.add_message(message)
        
        memory_summary = self.memory.get_summary()
        today_date = TodayDateTool().run({})
        date_msg = f"Today's date: {today_date}.\n"
        enhanced_system_prompt = Message(
            role="system",
            content=date_msg+self.system_prompt.content + "\n\n" + 
                    "--- MEMORY SUMMARY ---\n" + 
                    memory_summary + "\n"
        )
        
        tools = [tool.tool_description for tool in self.tools.values()]
        
        messages_for_api = [{"role": "system", "content": enhanced_system_prompt.content}]
        messages_for_api.extend(context.messages_for_api())
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages_for_api,
                tools=tools
            )
            assistant_message = completion.choices[0].message
        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            context.add_message(
                Message(
                    role="assistant",
                    content="I'm sorry, I encountered an error while processing your request."
                )
            )
            self.memory.add_message(message, "Error processing request.")
            self.memory.update_summary(self.memory_agent.summarize_memory(self.memory))
            return {"context": context, "response": "Error processing request."}

        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                context.add_message(
                    Message(
                        role="assistant",
                        content="",
                        tool_calls=[
                            {
                                "id": str(getattr(tool_call, "id", "")),
                                "type": "function",
                                "function": {
                                    "name": str(getattr(tool_call.function, "name", "")),
                                    "arguments": str(getattr(tool_call.function, "arguments", ""))
                                }
                            }
                        ]
                    )
                )
                args = json.loads(tool_call.function.arguments)
                result = self.tools[tool_call.function.name].run(args)
                if isinstance(result, str):
                    result = {"message": result}
                elif isinstance(result, EventSearchResponse):
                    if len(events_found) == 0:
                        events_found = result.events
                    else:
                        events_found.extend(result.events)
                    result = {"events": format_events_for_llm(result)}
                    
                context.add_message(
                    Message(
                        role="tool",
                        tool_call_id=tool_call.id,
                        content=str(result)
                    )
                )
            
            # After processing all tool calls, get a final response
            # Refresh messages for API
            messages_for_api = [{"role": "system", "content": enhanced_system_prompt.content}]
            messages_for_api.extend(context.messages_for_api())
            
            completion = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages_for_api,
                tools=tools
            )
            assistant_message = completion.choices[0].message

        # Parse the assistant response as JSON according to system prompt format
        try:
            assistant_response_dict = json.loads(assistant_message.content) if assistant_message.content else {"resp": ' ', "ids": []}
        except (json.JSONDecodeError, TypeError):
            # Fallback if response is not in expected JSON format
            assistant_response_dict = {"resp": assistant_message.content or ' ', "ids": []}
        
        # Extract response text and IDs from the parsed dictionary
        response = assistant_response_dict.get("resp", ' ')
        ids_list = assistant_response_dict.get("ids", [])
        
        # Ensure ids_list is actually a list
        if not isinstance(ids_list, list):
            ids_list = []
        
        context.add_message(
            Message(
                role="assistant",
                content=response
            )
        )
        
        # Update memory with the user message and assistant response
        self.memory.add_message(message, response)
        # Update memory summary
        self.memory.update_summary(self.memory_agent.summarize_memory(self.memory))
        
        print(f"IDs extracted from response: {ids_list}")
        # Filter events_found to only include events whose id is in ids_list
        if ids_list and events_found:
            events_found = [event for event in events_found if getattr(event, "id", None) in ids_list]
        print(f"Events found after filtering: {events_found}")
        return {"context": context, "response": response, "events_found": events_found}
