"""
Event API Service

This module provides a service for interacting with the event search API.
It uses Pydantic models for request and response validation.
"""

import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from config import SWAGGER_API_KEY

BASE_URL = "https://event-search-staging.thrugo.com/api/events"

class Venue(BaseModel):
    """Venue information for an event."""
    name: str = Field(..., description="Name of the venue")
    city: Optional[str] = Field(None, description="City where the venue is located")
    country: Optional[str] = Field(None, description="Country where the venue is located")
    country_code: Optional[str] = Field(None, description="ISO country code")
    address: Optional[str] = Field(None, description="Full address of the venue")

class EventDate(BaseModel):
    """Date and time information for an event."""
    start_date: str = Field(..., description="Start date of the event (ISO format)")
    start_time: Optional[str] = Field(None, description="Start time of the event")
    end_date: Optional[str] = Field(None, description="End date of the event (ISO format)")
    end_time: Optional[str] = Field(None, description="End time of the event")
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected ISO format (YYYY-MM-DD).")
        return v

class EventImage(BaseModel):
    """Image information for an event."""
    url: str = Field(..., description="URL of the event image")
    alt: Optional[str] = Field(None, description="Alternative text for the image")

class Event(BaseModel):
    """Detailed event information."""
    id: str = Field(..., description="Unique identifier for the event")
    name: str = Field(..., description="Name of the event")
    description: Optional[str] = Field(None, description="Description of the event")
    url: Optional[str] = Field(None, description="URL for event details or ticketing")
    dates: EventDate = Field(..., description="Date and time information")
    venues: List[Venue] = Field(default_factory=list, description="List of venues")
    images: List[EventImage] = Field(default_factory=list, description="List of event images")
    genre: Optional[str] = Field(None, description="Genre of the event")
    
    def format_summary(self) -> str:
        """Format the event as a summary string."""
        venue_str = ""
        if self.venues and len(self.venues) > 0:
            venue = self.venues[0]
            venue_parts = [venue.name]
            if venue.city:
                venue_parts.append(venue.city)
            if venue.country:
                venue_parts.append(venue.country)
            venue_str = ", ".join(venue_parts)
        
        date_str = self.dates.start_date
        time_str = self.dates.start_time if self.dates.start_time else ""
        
        return f"{self.name} at {venue_str} on {date_str} {time_str} - {self.url or ''}"

class EventSearchResponse(BaseModel):
    """Response from the event search API."""
    events: List[Event] = Field(default_factory=list, description="List of events")
    total_count: int = Field(0, description="Total number of events found")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of events per page")
    found_more_events: bool = Field(False, description="Indicates if there are more events available")

class EventSearchParams(BaseModel):
    """Parameters for searching events."""
    eventGenre: Optional[str] = Field(None, description="Genre of the event (e.g., 'Sports - Football')")
    eventLocationCity: Optional[str] = Field(None, description="City where the event takes place")
    eventLocationCountryCode: Optional[str] = Field(None, description="ISO country code of the event location")
    eventStartDate: Optional[str] = Field(None, description="Start date of the event in ISO format (yyyy-MM-dd)")
    eventEndDate: Optional[str] = Field(None, description="End date of the event in ISO format (yyyy-MM-dd)")
    eventName: Optional[str] = Field(None, description="Name of the event to search for")
    pageSize: Optional[int] = Field(50, description="Number of results per page (Min: 1, Max: 200, Default: 50)")
    
    @field_validator('eventStartDate', 'eventEndDate', mode='before')
    @classmethod
    def validate_date_format(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Expected format: YYYY-MM-DD")
        return v
    
    @field_validator('pageSize')
    @classmethod
    def validate_page_size(cls, v):
        if v is not None:
            if v < 1:
                return 1
            if v > 200:
                return 200
        return v

class EventApiService:
    """Service for interacting with the event search API."""
    
    def __init__(self, api_key: str = SWAGGER_API_KEY):
        """Initialize the service with API key."""
        self.api_key = api_key
        self.base_url = BASE_URL
    
    def search_events(self, params: EventSearchParams) -> EventSearchResponse:
        """
        Search for events using the provided parameters.
        
        Args:
            params: EventSearchParams object with search criteria
            
        Returns:
            EventSearchResponse: Structured response with event data
            
        Raises:
            ValueError: If the API request fails
        """
        headers = {"X-API-Key": self.api_key}
        
        # Convert Pydantic model to dict, excluding None values
        try:
            params_dict = params.model_dump(exclude_none=True)
        except AttributeError:
            # Fallback for older Pydantic versions (pre v2.0)
            params_dict = {k: v for k, v in params.__dict__.items() if v is not None}
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params_dict, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events_data = self._extract_events_from_response(data)
            
            return EventSearchResponse(
                events=events_data,
                total_count=len(events_data),
                page=1,
                page_size=params.pageSize or 50,
                found_more_events=data.get("foundMoreEvents", False)
            )
            
        except requests.RequestException as e:
            raise ValueError(f"Error contacting Event API: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error: {e}")
    
    def _extract_events_from_response(self, data: Dict[str, Any]) -> List[Event]:
        print(f"Extracting events from data: {data}")
        """
        Extract events from API response data, handling different response formats.
        
        Args:
            data: The JSON response data from the API
            
        Returns:
            List[Event]: Extracted event objects
        """
        events_data = []
        
        # Determine which key contains the events list
        events_list = []
        if "events" in data and isinstance(data.get("events"), list):
            events_list = data.get("events", [])
        elif "items" in data and isinstance(data.get("items"), list):
            events_list = data.get("items", [])
        else:
            return events_data
        
        for event_data in events_list:
            try:
                # Extract venue data
                venues = []
                venue_list = event_data.get("venues", [])
                if venue_list and isinstance(venue_list, list):
                    for venue_data in venue_list:
                        if isinstance(venue_data, dict):
                            # Handle full venue object
                            venues.append(Venue(
                                name=venue_data.get("name", "Unknown Venue"),
                                city=venue_data.get("city", {}).get("name") if isinstance(venue_data.get("city"), dict) else venue_data.get("city"),
                                country=venue_data.get("country", {}).get("name") if isinstance(venue_data.get("country"), dict) else venue_data.get("country"),
                                country_code=venue_data.get("country", {}).get("countryCode") if isinstance(venue_data.get("country"), dict) else None,
                                address=venue_data.get("address", {}).get("line1") if isinstance(venue_data.get("address"), dict) else venue_data.get("address")
                            ))
                        elif isinstance(venue_data, str):
                            # Handle venue as string
                            venues.append(Venue(
                                name=venue_data,
                                city=None,
                                country=None,
                                country_code=None,
                                address=None
                            ))
                
                # Process dates
                start_date = ""
                start_time = None
                end_date = None
                end_time = None
                
                if "startDateTime" in event_data:
                    iso_date = event_data.get("startDateTime", "")
                    if iso_date:
                        try:
                            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
                            start_date = dt.strftime("%Y-%m-%d")
                            start_time = dt.strftime("%H:%M:%S")
                        except ValueError:
                            # If date format is not standard ISO, use as is
                            start_date = iso_date
                elif "dates" in event_data:
                    dates_data = event_data.get("dates", {})
                    if isinstance(dates_data, dict):
                        start_data = dates_data.get("start", {})
                        if isinstance(start_data, dict):
                            start_date = start_data.get("localDate", "")
                            start_time = start_data.get("localTime")
                        end_data = dates_data.get("end", {})
                        if isinstance(end_data, dict):
                            end_date = end_data.get("localDate")
                            end_time = end_data.get("localTime")
                
                # Create EventDate object
                dates = EventDate(
                    start_date=start_date,
                    start_time=start_time,
                    end_date=end_date,
                    end_time=end_time
                )
                
                # Process images
                images = []
                if "images" in event_data and isinstance(event_data.get("images"), list):
                    for image_data in event_data.get("images", []):
                        if isinstance(image_data, dict):
                            images.append(EventImage(
                                url=image_data.get("url", ""),
                                alt=image_data.get("alt")
                            ))
                elif "image" in event_data and event_data.get("image"):
                    image_url = event_data.get("image")
                    if isinstance(image_url, str):
                        images.append(EventImage(url=image_url, alt=None))
                
                # Create Event object
                event = Event(
                    id=str(event_data.get("id", "")),
                    name=event_data.get("name", "Unknown Event"),
                    description=event_data.get("description"),
                    url=event_data.get("url"),
                    dates=dates,
                    venues=venues,
                    images=images,
                    genre=event_data.get("genre") or 
                        (event_data.get("classifications", [{}])[0].get("genre", {}).get("name") 
                         if event_data.get("classifications") and len(event_data.get("classifications", [])) > 0 
                         else None)
                )
                
                events_data.append(event)
            except Exception:
                # Skip events that can't be processed
                continue
        print(events_data)
        return events_data
    
    def format_events_for_llm(self, events_response: EventSearchResponse) -> str:
        """
        Format the events data in a way that's suitable for an LLM.
        
        Args:
            events_response: The structured event search response
            
        Returns:
            str: Formatted string representation of events
        """
        if not events_response.events:
            return "No events found for the given criteria."
        
        formatted_events = [event.format_summary() for event in events_response.events]
        
        result = f"Found {events_response.total_count} events. Showing {len(formatted_events)}:"
        if events_response.found_more_events:
            result += " (more events are available)"
        result += "\n\n"
        result += "\n".join(formatted_events)
        
        return result
