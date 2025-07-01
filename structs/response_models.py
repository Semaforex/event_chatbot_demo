"""
Response models for structured output validation using Pydantic.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional


class EventAgentResponse(BaseModel):
    """
    Structured response model for the Event Agent.
    
    This model ensures that the agent always returns responses in the correct format
    with proper validation instead of relying on manual JSON parsing.
    """
    resp: str = Field(
        ..., 
        description="The text response to the user's query about events",
        min_length=1,
        max_length=2000
    )
    ids: List[str] = Field(
        ...,
        description="List of event IDs that should be displayed to the user",
        max_length=15
    )
    
    @validator('resp')
    def validate_response_text(cls, v):
        """Validate that the response text is meaningful and not empty."""
        if not v or v.strip() == '':
            raise ValueError('Response text cannot be empty')
        return v.strip()
    
    @validator('ids')
    def validate_ids(cls, v):
        """Validate that all IDs are non-empty strings."""
        if v is None:
            return []
        
        # Handle case where v is not a list
        if not isinstance(v, list):
            return []
        
        # Filter out empty or invalid IDs
        valid_ids = []
        for item in v:
            if isinstance(item, str) and item.strip():
                valid_ids.append(item.strip())
        
        return valid_ids
    
    class Config:
        """Pydantic configuration."""
        # Forbid extra fields (this sets additionalProperties: false in JSON schema)
        extra = "forbid"
        # Validate assignments
        validate_assignment = True
        # Use enum values
        use_enum_values = True


class EventAgentError(BaseModel):
    """
    Error response model for when the Event Agent encounters issues.
    """
    resp: str = Field(
        ...,
        description="Error message explaining what went wrong"
    )
    ids: List[str] = Field(
        ...,
        description="Empty list for error responses"
    )
    error_type: Optional[str] = Field(
        ...,
        description="Type of error that occurred"
    )
    
    class Config:
        """Pydantic configuration."""
        # Forbid extra fields (this sets additionalProperties: false in JSON schema)
        extra = "forbid"
        # Validate assignments
        validate_assignment = True
