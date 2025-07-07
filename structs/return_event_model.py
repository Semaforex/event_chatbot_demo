from dataclasses import dataclass, field
from typing import Optional
from structs.event_related_models import Event


@dataclass
class ReturnEvent:
    """Represents an event with its details"""

    # Event ID
    id: str = field(default=None, metadata={"description": "Event ID"})

    # The name of the event
    name: str = field(default=None, metadata={"description": "The name of the event"})

    # The url to the event thumbnail image
    image: Optional[str] = field(
        default=None, metadata={"description": "The url to the event thumbnail image"}
    )

    # The description of the event
    description: Optional[str] = field(
        default=None, metadata={"description": "The description of the event"}
    )

    # The date of the event start
    start_date_time: Optional[str] = field(
        default=None, metadata={"description": "The date of the event start"}
    )

    timezone: Optional[str] = field(
        default=None, metadata={"description": "The timezone of the event"}
    )

    # The url to the event
    url: str = field(default=None, metadata={"description": "The url to the event"})

    # The venue of the event
    venue: Optional[str] = field(
        default=None, metadata={"description": "The venue of the event"}
    )

    def to_dict(self):
        """Convert the event to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "description": self.description,
            "start_date_time": self.start_date_time,
            "timezone": self.timezone,
            "url": self.url,
            "venue": self.venue,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReturnEvent":
        """Create an Event instance from a dictionary"""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            image=data.get("image"),
            description=data.get("description"),
            start_date_time=data.get("start_date_time"),
            timezone=data.get("timezone"),
            url=data.get("url"),
            venue=data.get("venue"),
        )
    
    @classmethod
    def from_event(cls, event: Event) -> "ReturnEvent":
        """Create an Event instance from an Event object"""
        return cls(
            id=event.id,
            name=event.name,
            image=event.images[0].url if event.images else None,
            description=event.description,
            start_date_time=event.dates.start_date + " " + (event.dates.start_time or ""),
            timezone=event.timezone if event.timezone else None,
            url=event.url if event.url else None,
            venue=event.venues[0].name if event.venues else None,
        )