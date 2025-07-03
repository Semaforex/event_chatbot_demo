from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from structs.event_related_models import EventSearchParams


@dataclass
class ReturnParameters:
    """Represents search parameters for event queries"""

    city: Optional[str] = None
    country: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    genre: Optional[str] = None
    keywords: Optional[List[str]] = None

    def __post_init__(self):
        # Convert timestamp from string if needed
        if isinstance(self.date_range_start, str):
            self.date_range_start = datetime.fromisoformat(self.date_range_start)

        if isinstance(self.date_range_end, str):
            self.date_range_end = datetime.fromisoformat(self.date_range_end)

    def update(self, new_params: Dict[str, Any]) -> bool:
        """
        Update parameters with new values
        Returns True if any parameters changed
        """
        changed = False

        # Force to always clear keywods if genre changes
        new_genre = new_params.get("genre", None)
        old_genre = getattr(self, "genre", None)

        if new_genre != old_genre:
            setattr(self, "keywords", None)
            changed = True

        # Update with new parameters
        for key, value in new_params.items():
            if hasattr(self, key):
                current_value = getattr(self, key)
                if current_value != value:
                    setattr(self, key, value)
                    changed = True

        return changed

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, ensuring dates are strings"""
        result = {}
        for key in self.__annotations__:
            value = getattr(self, key)
            if value is not None:
                if key in ("date_range_start", "date_range_end") and isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result

    def from_dict(self, data: dict) -> "ReturnParameters":
        return ReturnParameters(
            city=data.get("city", None),
            country=data.get("country", None),
            date_range_start=data.get("date_range_start", None),
            date_range_end=data.get("date_range_end", None),
            genre=data.get("genre", None),
            keywords=data.get("keywords", None),
        )

    def copy(self) -> "ReturnParameters":
        """Create a copy of the parameters"""
        return ReturnParameters(
            city=self.city,
            country=self.country,
            date_range_start=self.date_range_start,
            date_range_end=self.date_range_end,
            genre=self.genre,
            keywords=self.keywords.copy() if self.keywords else None,
        )
    
    @classmethod
    def from_event_search_params(cls, params: EventSearchParams) -> "ReturnParameters":
        """Create ReturnParameters from EventSearchParams"""
        start_date = params.eventStartDate
        end_date = params.eventEndDate
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        return cls(
            city=params.eventLocationCity,
            country=params.eventLocationCountryCode,
            genre=params.eventGenre,
            date_range_start=start_date if start_date else None,
            date_range_end=end_date if end_date else None,
            keywords=params.eventName.split(" ") if params.eventName else None # Keywords are not part of EventSearchParams
        )