from typing import Optional, Any
import logging

from structs.return_model import ReturnModel, Data, ReturnSearchDetails
from structs.return_event_model import ReturnEvent
from structs.return_parameters_model import ReturnParameters
from structs.chat_message_dto import ChatMessageDto
from services.moderation_service import ModerationService
from agents.event_agent import EventAgent
from services.database_service import DatabaseService
from structs.context import Context
from structs.message import Message
from structs.event_related_models import EventSearchParams

import datetime
logger = logging.getLogger("message_processing_service")

def process_message_service(input: ChatMessageDto) -> ReturnModel:
    user_input = input.message
    channel_id = input.chat_id
    
    # moderation
    moderation_service = get_moderation_service()
    if moderation_service:
        is_flagged = moderation_service.is_flagged(user_input)
        if is_flagged:
            logging.warning(f"Message flagged as unsafe: {user_input}")
            return fail_response(channel_id)
    
    # database
    db_service = get_database_service()
    if not db_service:
        logging.error("Database service is not available.")
        return fail_response(channel_id)
    channel_data = db_service.get_chat_session(channel_id)
    if not channel_data:
        logging.error(f"Channel data not found for channel_id: {channel_id}")
        return fail_response(channel_id)
    
    # agent and context
    event_agent = get_event_agent()
    if not event_agent:
        logging.error("EventAgent is not available.")
        return fail_response(channel_id)
    context = get_context(channel_data)
    
    # process the message
    user_message = Message(role="user", content=user_input)
    result = event_agent.process(user_message, context)
    return_object = process_result(result, channel_id)
    if not return_object:
        logging.error(f"Failed to process result for channel_id: {channel_id}")
        return fail_response(channel_id)
    
    # save the updated context
    updated_data = get_updated_data(channel_data, result, user_input)
    db_service.save_chat_session(updated_data)
    
    # return the response
    return return_object
    
    
    
def fail_response(chat_id: str) -> ReturnModel:
    return ReturnModel(
        ai_response="I'm sorry, I cannot process your request at the moment.",
        chat_id=chat_id
    )

def get_moderation_service() -> Optional[ModerationService]:
    """Dependency to get moderation service (optional)."""
    try:
        moderation_service = ModerationService()
    except Exception as e:
        moderation_service = None
        logging.error(f"Failed to initialize ModerationService: {e}")
    return moderation_service

def get_database_service() -> Optional[DatabaseService]:
    """Dependency to get database service."""
    try:
        db_service = DatabaseService()
        if not db_service.connect():
            logging.error("Failed to connect to the database.")
            return None
    except Exception as e:
        logging.error(f"Failed to initialize DatabaseService: {e}")
        return None
    return db_service

def get_event_agent() -> Optional[EventAgent]:
    try:
        event_agent = EventAgent()
    except Exception as e:
        event_agent = None
        logging.error(f"Failed to initialize EventAgent: {e}")
    return event_agent

def get_context(channel_data: dict) -> Context:
    context = Context()
    
    messages = channel_data.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            context.add_message(Message(role="user", content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            context.add_message(Message(role="assistant", content=msg.get("content", "")))
    return context


def process_result(response: dict[str, Any], chat_id: str) -> Optional[ReturnModel]:
    ai_response = response.get("response", None)
    last_raw_context = response.get("context", None)
    events_found = response.get("events_found", [])
    search_params = response.get("search_params", [])
    if not ai_response or not last_raw_context:
        return None

    return ReturnModel(
        ai_response=ai_response,
        chat_id=chat_id,
        data=Data(
            display_ids=response.get("display_ids", []),
            events_found=[ReturnEvent.from_event(event) for event in events_found],
            search_details = [
                ReturnSearchDetails(
                    found_more_events=search.get("found_more", False),
                    parameters=ReturnParameters.from_event_search_params(EventSearchParams(**search.get("params", {})))
                ) for search in search_params
            ]
        )
    )

def get_updated_data(channel_data: dict, response: dict, user_msg: str) -> dict:
    updated_data = channel_data.copy()
    updated_data["messages"].append({
        "role": "user",
        "content": user_msg
    })
    updated_data["messages"].append({
        "role": "assistant",
        "content": response.get("response", "")
    })
    updated_data["message_count"] = len(updated_data["messages"])
    updated_data["last_updated"] = datetime.datetime.now().isoformat()  
    updated_data["raw_context"] = response.get("context", {}).messages_for_api()
    updated_data["displayed_ids"].append(response.get("display_ids", []))
    updated_data["search_obj_list"].append(response.get("search_params", []))
    return channel_data