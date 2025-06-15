from abc import ABC, abstractmethod

class BaseTool(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get the description of the tool.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    
    @abstractmethod
    def run(self, params) -> str:
        """
        Run the tool with the given parameters.
        """
        raise NotImplementedError("Subclasses should implement this method.")