"""
Event API Service

This module provides a service for interacting with the event search API.
It uses Pydantic models for request and response validation.
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from env_config import get_swagger_api_key, get_geocode_api_key
from timezonefinder import TimezoneFinder
from services.geocode_api_service import geocode_address


from structs.event_related_models import Venue, Event, EventDate, EventImage, EventSearchResponse, EventSearchParams

BASE_URL = "https://event-search-staging.thrugo.com/api/events"



class EventApiService:
    """Service for interacting with the event search API."""
    
    def __init__(self, api_key: str = get_swagger_api_key()):
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
                # timezone = get_timezone(venues[0])
                timezone = event_data.get("timezone", None)
                event = Event(
                    timezone=timezone,
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
            except Exception as e:
                print(f"Error processing event data: {e}")
                # Skip events that can't be processed
                continue
        return events_data
    
def format_events_for_llm(events_response: EventSearchResponse) -> str:
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

    result += "\n\n"
    result += "\n".join(formatted_events)
    
    return result

def get_timezone(venue: Venue) -> Optional[str]:
    timezone = None
    if venue.address:
        v = venue.address
    elif venue.city:
        v = venue.city
    elif venue.name:
        v = venue.name
    elif venue.country:
        v = venue.country
    else:
        v = str(venue)
    if v:
        try:
            location = geocode_address(v, get_geocode_api_key())
            tff = TimezoneFinder()
            timezone = tff.timezone_at(lat=location.latitude, lng=location.longitude)
        except Exception:
            return None
    return timezone


