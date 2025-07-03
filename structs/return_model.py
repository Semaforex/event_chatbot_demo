from typing import Any, Dict, Optional
from pydantic import BaseModel
from structs.return_event_model import ReturnEvent
from structs.return_parameters_model import ReturnParameters

class ReturnSearchDetails(BaseModel):
    found_more_events: bool
    parameters: ReturnParameters
    
    @classmethod
    def to_dict(cls, instance: "ReturnSearchDetails") -> Dict[str, Any]:
        return {
            "found_more_events": instance.found_more_events,
            "parameters": instance.parameters.to_dict()
        }


class Data(BaseModel):
    display_ids: list[str]
    events_found: list[ReturnEvent]
    search_details: list[ReturnSearchDetails]
    
    @classmethod
    def to_dict(cls, instance: "Data") -> Dict[str, Any]:
        return {
            "display_ids": instance.display_ids,
            "events_found": [event.to_dict() for event in instance.events_found],
            "search_details": ReturnSearchDetails.to_dict(instance.search_details)
        }


class ReturnModel(BaseModel):
    ai_response: str
    chat_id: str
    data: Optional[Data] = None
    
    
    @classmethod
    def to_dict(cls, instance: "ReturnModel") -> Dict[str, Any]:
        return {
            "ai_response": instance.ai_response,
            "chat_id": instance.chat_id,
            "data": Data.to_dict(instance.data) if instance.data else None
        }