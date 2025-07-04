from agents.base_agent import BaseAgent
from openai import OpenAI
from typing import Dict, Any, Optional
from structs.context import Context
from structs.message import Message
from structs.response_models import EventAgentResponse, EventAgentError
from tools.event_search import EventSearchAPI
from agents.memory_agent import MemoryAgent
from tools.today_date import TodayDateTool
from memory.chat_memory import ChatMemory
from pathlib import Path
from services.event_api_service import format_events_for_llm, EventSearchResponse
import json
import re
from pydantic import ValidationError

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
        event_search_tool = EventSearchAPI()
        self.tools = {
            'search_events': event_search_tool,
        }
        self.memory_agent = MemoryAgent()

    def process(self, message: Message, context: Context) -> Dict[str, Any]:
        events_found = []
        context.add_message(message)
        
        reminder_message = Message(
            role="system",
            content="Remember to always use the tools provided to search for events if the user asked for events in any way. Do not use events present in your context. Run the search again to avoid mistakes like events that are no longer in the database but still in your context",
        )
        context.add_message(reminder_message)
        
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
                tools=tools,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "event_agent_response",
                        "schema": EventAgentResponse.model_json_schema(),
                        "strict": True
                    }
                }
            )
            assistant_message = completion.choices[0].message
        except Exception as e:
            print(f"Error during OpenAI API call: {e}")
            # Create structured error response
            error_response = EventAgentError(
                resp="I'm sorry, I encountered an error while processing your request.",
                ids=[],
                error_type=type(e).__name__
            )
            context.add_message(
                Message(
                    role="assistant",
                    content=error_response.resp
                )
            )
            self.memory.add_message(message, error_response.resp)
            self.memory.update_summary(self.memory_agent.summarize_memory(self.memory))
            return {"context": context, "response": error_response.resp, "events_found": [], "search_params": []}
        return_objects = []
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
                    return_object = {"params": getattr(tool_call.function, "arguments", ""), "found_more": len(events_found) > 3}
                    return_objects.append(return_object)
                    if len(events_found) == 0:
                        events_found = [result.events]
                    else:
                        events_found.append(result.events)
                    result = {"events": format_events_for_llm(result)}
                    # appent listy obiektow  
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
            # Save messages_for_api to a text file for debugging
            with open("messages_for_api.txt", "w", encoding="utf-8") as f:
                for msg in messages_for_api:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            
            completion = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=messages_for_api,
                tools=tools,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "event_agent_response",
                        "schema": EventAgentResponse.model_json_schema(),
                        "strict": True
                    }
                }
            )
            assistant_message = completion.choices[0].message

        # Parse and validate the assistant response using Pydantic model
        try:
            if assistant_message.content:
                # Parse JSON and validate with Pydantic
                response_data = json.loads(assistant_message.content)
                validated_response = EventAgentResponse(**response_data)
                
                response = validated_response.resp
                ids_list = validated_response.ids
            else:
                # Fallback for empty content
                validated_response = EventAgentResponse(resp="I'm sorry, I couldn't process your request.", ids=[])
                response = validated_response.resp
                ids_list = validated_response.ids
                
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            print(f"Error parsing or validating response: {e}")
            # Create error response using the error model
            error_response = EventAgentError(
                resp="I'm sorry, I encountered an error while processing your request. Please try again.",
                ids=[],
                error_type=type(e).__name__
            )
            response = error_response.resp
            ids_list = error_response.ids
        
        context.add_message(
            Message(
                role="assistant",
                content=response
            )
        )
        
        self.memory.add_message(message, response)
        self.memory.update_summary(self.memory_agent.summarize_memory(self.memory))
        
        print(f"\n IDs extracted from response: {ids_list} \n")
        print(f"number of events found before filtering: {len(events_found)} \n")
        # Filter events_found to only include events whose id is in ids_list
        if len(ids_list) > 0 and len(events_found) > 0:
            print(ids_list)
            print([getattr(event, "id", None) for event in events_found])
            final_events_found = []
            for i, events in enumerate(events_found):
                temp_events = [event for event in events if getattr(event, "id", None) in ids_list]
                return_objects[i]["found_more"] = len(events) > 3 or len(temp_events) < len(events)
                final_events_found.extend(temp_events)
            events_found = final_events_found
        else:
            events_found = []
        print(f"Events found after filtering: {events_found}")
        if len(return_objects) == 0:
            return {"context": context, "response": response, "events_found": [], "search_params": []}
        return {"context": context, "response": response, "events_found": events_found, "search_params": return_objects}
