from abc import ABC, abstractmethod
from typing import Dict, Any, List
from structs.message import Message
from datetime import datetime

class BaseMemory(ABC):
    @abstractmethod
    def add_message(self, message: Message, response: str) -> None:
        """Add a message and response to memory"""
        pass
    
    @abstractmethod
    def get_memory(self) -> str:
        """Get the memory content"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the memory"""
        pass
