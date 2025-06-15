from openai import OpenAI
from typing import Dict, Any
from abc import ABC, abstractmethod
from structs.context import Context
from structs.message import Message

class BaseAgent(ABC):
    @abstractmethod
    def process(self, message: Message, context: Context) -> Dict[str, Any]:
        """
        Process a message and update the context.
        Returns a dictionary containing at least:
        - context: The updated context
        - response: The agent's response as a string
        """
        
        raise NotImplementedError("Subclasses should implement this method.")