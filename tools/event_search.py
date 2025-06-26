from tools.base_tool import BaseTool
import json
from typing import Dict, Any
from services.event_api_service import EventApiService, EventSearchParams, EventSearchResponse
from typing import Optional


class EventSearchAPI(BaseTool):
    def __init__(self):
        with open("tools/descriptions/event_search.json", "r") as file:
            self.tool_description = json.load(file)
        self.event_service = EventApiService()

    def get_description(self) -> str:
        return self.tool_description["function"]["description"]

    def run(self, params: Dict[str, Any]) -> Optional[EventSearchResponse]:
        """
        Run the event search with the given parameters.
        Args:
            params (dict): Dictionary of search parameters.
        Returns:
            str: Summarized list of events or error message.
        """
        try:
            # Remove any testing parameters if they exist
            if "use_mock_data" in params:
                params.pop("use_mock_data")
            
            # Convert dict to Pydantic model for validation
            search_params = EventSearchParams(**params)
            
            # Use the service to get events
            events_response = self.event_service.search_events(search_params)
            
            # Format the response for LLM
            return events_response
            
        except Exception as e:
            return None