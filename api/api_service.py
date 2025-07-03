"""
FastAPI service for Event Chatbot with multi-session support.
Provides REST API endpoints for channel management and chat functionality.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging
import json
import os
from dotenv import load_dotenv

# Import existing modules
from agents.event_agent import EventAgent
from structs.context import Context
from structs.message import Message
from services.moderation_service import ModerationService
from services.database_service import DatabaseService

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Event Chatbot API",
    description="Multi-session event chatbot with channel management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class CreateChannelResponse(BaseModel):
    channel_id: str
    status: str
    created_at: datetime

class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message content")

class SendMessageResponse(BaseModel):
    response: str
    events_found: List[Dict[str, Any]] = []
    search_params: List[Dict[str, Any]] = []
    message_id: str
    timestamp: datetime

class ChannelInfo(BaseModel):
    channel_id: str
    created_at: Optional[datetime]
    last_updated: Optional[datetime]
    message_count: int
    status: str

class GetChannelsResponse(BaseModel):
    channels: List[ChannelInfo]
    total_count: int

class ChatHistoryResponse(BaseModel):
    channel_id: str
    messages: List[Dict[str, Any]]
    total_messages: int

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool
    moderation_service_available: bool

# Global services (initialize once)
db_service: Optional[DatabaseService] = None
moderation_service: Optional[ModerationService] = None

def get_database_service() -> DatabaseService:
    """Dependency to get database service."""
    global db_service
    if db_service is None:
        try:
            db_service = DatabaseService()
            if not db_service.connect():
                raise HTTPException(status_code=500, detail="Failed to connect to database")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise HTTPException(status_code=500, detail="Database service unavailable")
    return db_service

def get_moderation_service() -> Optional[ModerationService]:
    """Dependency to get moderation service (optional)."""
    global moderation_service
    if moderation_service is None:
        try:
            moderation_service = ModerationService()
            logger.info("Moderation service initialized successfully")
        except Exception as e:
            logger.warning(f"Moderation service unavailable: {e}")
            moderation_service = None
    return moderation_service

def format_events_for_response(events) -> List[Dict[str, Any]]:
    """Format events for API response."""
    if not events:
        return []
    
    formatted_events = []
    for event in events:
        # Format venue information
        venue_info = "Venue not specified"
        if event.venues and len(event.venues) > 0:
            venue = event.venues[0]
            venue_parts = [venue.name]
            if venue.city:
                venue_parts.append(venue.city)
            if venue.country:
                venue_parts.append(venue.country)
            venue_info = ", ".join(venue_parts)
        
        # Format date and time
        date_time = event.dates.start_date
        if event.dates.start_time:
            date_time += f" at {event.dates.start_time}"
        
        event_data = {
            "id": getattr(event, 'id', None),
            "name": event.name,
            "venue": venue_info,
            "date_time": date_time,
            "url": event.url,
            "description": getattr(event, 'description', None)
        }
        formatted_events.append(event_data)
    
    return formatted_events

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(
    db_service: DatabaseService = Depends(get_database_service),
    mod_service: Optional[ModerationService] = Depends(get_moderation_service)
):
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        database_connected=db_service is not None,
        moderation_service_available=mod_service is not None
    )

@app.post("/channels", response_model=CreateChannelResponse)
async def create_channel(db_service: DatabaseService = Depends(get_database_service)):
    """Create a new chat channel."""
    try:
        channel_id = f"channel_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now()
        
        # Create channel data
        channel_data = {
            "channel_id": channel_id,
            "messages": [],
            "created_at": created_at,
            "last_updated": created_at,
            "search_obj_list": [],
            "displayed_ids": [],
            "message_count": 0,
            "status": "active"
        }
        
        # Save to database
        result = db_service.save_chat_session(channel_data)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create channel")
        
        logger.info(f"New channel created: {channel_id}")
        
        return CreateChannelResponse(
            channel_id=channel_id,
            status="created",
            created_at=created_at
        )
    
    except Exception as e:
        logger.error(f"Failed to create channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to create channel")

@app.get("/channels", response_model=GetChannelsResponse)
async def get_channels(
    limit: int = 50,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get list of all channels."""
    try:
        channels = db_service.get_all_sessions(limit=limit)
        
        channel_list = []
        for channel in channels:
            channel_info = ChannelInfo(
                channel_id=channel.get("channel_id", "unknown"),
                created_at=channel.get("created_at"),
                last_updated=channel.get("last_updated", channel.get("created_at")),
                message_count=channel.get("message_count", len(channel.get("messages", []))),
                status=channel.get("status", "active")
            )
            channel_list.append(channel_info)
        
        return GetChannelsResponse(
            channels=channel_list,
            total_count=len(channel_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve channels")

@app.get("/channels/{channel_id}", response_model=ChatHistoryResponse)
async def get_channel_history(
    channel_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Get chat history for a specific channel."""
    try:
        channel_data = db_service.get_chat_session(channel_id)
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        messages = channel_data.get("messages", [])
        
        return ChatHistoryResponse(
            channel_id=channel_id,
            messages=messages,
            total_messages=len(messages)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get channel history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve channel history")

@app.post("/channels/{channel_id}/messages", response_model=SendMessageResponse)
async def send_message(
    channel_id: str,
    request: SendMessageRequest,
    db_service: DatabaseService = Depends(get_database_service),
    mod_service: Optional[ModerationService] = Depends(get_moderation_service)
):
    """Send a message to a specific channel."""
    try:
        # Verify channel exists
        channel_data = db_service.get_chat_session(channel_id)
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        user_input = request.message.strip()
        
        # Content moderation check
        if mod_service:
            try:
                content_flagged = mod_service.is_flagged(user_input)
                if content_flagged:
                    flagged_categories = mod_service.get_flagged_categories(user_input)
                    categories_str = ", ".join(flagged_categories.get(user_input, []))
                    logger.warning(f"User message flagged by moderation API. Categories: {categories_str}")
                    
                    # Create moderation response
                    response_message = "I'm sorry, but I can't respond to that message as it may contain inappropriate content. Please try a different request."
                    
                    # Save messages to channel
                    messages = channel_data.get("messages", [])
                    messages.extend([
                        {"role": "user", "content": user_input, "timestamp": datetime.now()},
                        {"role": "assistant", "content": response_message, "timestamp": datetime.now()}
                    ])
                    
                    update_data = {
                        "messages": messages,
                        "last_updated": datetime.now(),
                        "message_count": len(messages),
                        "status": "active"
                    }
                    db_service.save_chat_session(channel_id, update_data)
                    
                    return SendMessageResponse(
                        response=response_message,
                        events_found=[],
                        search_params=[],
                        message_id=str(uuid.uuid4()),
                        timestamp=datetime.now()
                    )
                    
            except Exception as e:
                logger.error(f"Error during content moderation: {e}")
                # Continue with message processing if moderation fails
        
        # Initialize agent and context
        agent = EventAgent()
        context = Context()
        
        # Load existing conversation context
        messages = channel_data.get("messages", [])
        for msg in messages:
            if msg.get("role") == "user":
                context.add_message(Message(role="user", content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                context.add_message(Message(role="assistant", content=msg.get("content", "")))
        
        # Process the message
        user_message = Message(role="user", content=user_input)
        result = agent.process(user_message, context)
        
        # Extract results
        response = result["response"]
        events_found = result.get("events_found", [])
        search_params = result.get("search_params", [])
        raw_context = result.get("context", Context())
        
        # Log processing results
        logger.info(f"Event agent return object: {json.dumps({
            'channel_id': channel_id,
            'response_length': len(response) if isinstance(response, str) else 0,
            'events_found_count': len(events_found),
            'search_params': search_params,
            'context_message_count': len(raw_context.messages) if raw_context else 0
        }, indent=2)}")
        
        # Content moderation for response
        if mod_service:
            try:
                response_flagged = mod_service.is_flagged(response)
                if response_flagged:
                    logger.warning("Assistant response flagged by moderation API")
                    response = "I apologize, but I can't provide that information. Let me know if I can help with something else."
            except Exception as e:
                logger.error(f"Error during response moderation: {e}")
        
        # Ensure response is string
        if isinstance(response, dict):
            response = response.get("resp", str(response))
        
        # Format events for response
        formatted_events = format_events_for_response(events_found)
        
        # Update messages in database
        messages.extend([
            {"role": "user", "content": user_input, "timestamp": datetime.now()},
            {"role": "assistant", "content": response, "timestamp": datetime.now()}
        ])
        
        # Prepare update data
        update_data = {
            "messages": messages,
            "last_updated": datetime.now(),
            "message_count": len(messages),
            "status": "active",
            "raw_context": raw_context.messages_for_api() if raw_context else None
        }
        
        # Handle search parameters and displayed IDs (append as lists)
        if search_params is None:
            search_params = []
        prev_search_obj_list = channel_data.get("search_obj_list", [])
        update_data["search_obj_list"] = prev_search_obj_list + [search_params]
        
        if events_found is None:
            events_found = []
        prev_displayed_ids = channel_data.get("displayed_ids", [])
        update_data["displayed_ids"] = prev_displayed_ids + [[event.id for event in events_found if hasattr(event, 'id')]]
        
        # Save to database
        db_service.save_chat_session(channel_id, update_data)
        
        message_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        return SendMessageResponse(
            response=response,
            events_found=formatted_events,
            search_params=search_params,
            message_id=message_id,
            timestamp=timestamp
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@app.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """Delete a channel."""
    try:
        # Check if channel exists
        channel_data = db_service.get_chat_session(channel_id)
        if not channel_data:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Delete the channel (update status to deleted)
        update_data = {
            "status": "deleted",
            "last_updated": datetime.now()
        }
        
        db_service.save_chat_session(channel_id, update_data)
        
        return {"message": f"Channel {channel_id} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete channel: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete channel")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Event Chatbot API...")
    
    # Initialize database service
    try:
        global db_service
        db_service = DatabaseService()
        if db_service.connect():
            logger.info("Database service initialized successfully")
        else:
            logger.error("Failed to connect to database")
    except Exception as e:
        logger.error(f"Failed to initialize database service: {e}")
    
    # Initialize moderation service (optional)
    try:
        global moderation_service
        moderation_service = ModerationService()
        logger.info("Moderation service initialized successfully")
    except Exception as e:
        logger.warning(f"Moderation service unavailable: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down Event Chatbot API...")
    
    if db_service:
        db_service.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
