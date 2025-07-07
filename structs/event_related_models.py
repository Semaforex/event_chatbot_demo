from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


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
    timezone: Optional[str] = Field(None, description="Timezone of the event location")
    
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
        
        return f"{self.name} at {venue_str} on {date_str} {time_str} - {self.url or ''} {f"(time zone: {self.timezone})" if self.timezone else ''} [event ID: {self.id}]"

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
            if v < 4:
                return 4
            if v > 20:
                return 20
        return v
