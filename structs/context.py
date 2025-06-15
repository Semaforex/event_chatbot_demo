from typing import Any
from structs.message import Message

class Context:
    def __init__(self, max_msgs: int = 15):
        self.max_msgs = max_msgs
        self.messages = []
        self.msg_count = 0
    
    def add_message(self, message: Message):
        if self.msg_count >= self.max_msgs:
            self.messages.pop(0)
            self.msg_count -= 1
            if self.messages[0].role == "tool":
                self.messages.pop(0)
                self.msg_count -= 1
        self.messages.append(message)
        self.msg_count += 1
        
    
    def get_messages(self):
        return self.messages
    
    def messages_for_api(self) -> list[dict[str, Any]]:
        messages_for_api: list[dict[str, Any]] = []
        for m in self.get_messages():
            if m.role == "system":
                messages_for_api.append({"role": m.role, "content": m.content})
            elif m.role == "user":
                messages_for_api.append({"role": m.role, "content": m.content})
            elif m.role == "assistant" and not m.tool_calls:
                messages_for_api.append({"role": m.role, "content": m.content})
            elif m.role == "assistant" and m.tool_calls:
                d = {
                    "role": m.role,
                    "content": m.content if m.content else "",
                    "tool_calls": m.tool_calls
                }
                # Usuń None
                d = {k: v for k, v in d.items() if v is not None}
                messages_for_api.append(d)
            elif m.role == "tool":
                d = {
                    "role": m.role,
                    "content": m.content,
                    "tool_call_id": m.tool_call_id
                }
                d = {k: v for k, v in d.items() if v is not None}
                messages_for_api.append(d)
        return messages_for_api

        
    def clear(self):
        self.messages = []
        self.msg_count = 0
    
    def __str__(self):
        return str(self.messages)
