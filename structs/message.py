class Message:
    def __init__(self, role: str = None, content: str = None, tool_calls: list = None, tool_call_id: str = None):
        self.role = role
        self.content = content if content is not None else ""
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id

    def __str__(self):
        return f"{self.role}: {self.content}"

    def to_dict(self):
        d = {"role": self.role, "content": self.content}
        if self.tool_calls is not None:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d

    @classmethod
    def from_dict(cls, data: dict):
        role = data.get("role")
        content = data.get("content")
        tool_calls = data.get("tool_calls")
        tool_call_id = data.get("tool_call_id")
        return cls(role=role, content=content, tool_calls=tool_calls, tool_call_id=tool_call_id)
    
    def get_length(self):
        return len(self.content)

class MessageFactory:
    @staticmethod
    def create_from_dict(data: dict):
        return Message.from_dict(data)
