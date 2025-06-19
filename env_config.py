"""
Environment configuration for the application.
This module provides access to environment variables needed by the application.
"""

import os
from typing import Optional
import warnings

# Try to import from config.py if environment variables are not set
CONFIG = {}
try:
    import config
    CONFIG = {key: getattr(config, key) for key in dir(config) if not key.startswith('__')}
except ImportError:
    pass

def get_ticketmaster_api_key() -> str:
    """Get the Ticketmaster API key from environment variables or config."""
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key and "TICKETMASTER_API_KEY" in CONFIG:
        api_key = CONFIG["TICKETMASTER_API_KEY"]
        warnings.warn("Using TICKETMASTER_API_KEY from config.py instead of environment variable", UserWarning)
    if not api_key:
        raise EnvironmentError("TICKETMASTER_API_KEY not found in environment variables or config.py")
    return api_key

def get_swagger_api_key() -> str:
    """Get the Swagger API key from environment variables or config."""
    api_key = os.environ.get("SWAGGER_API_KEY")
    if not api_key and "SWAGGER_API_KEY" in CONFIG:
        api_key = CONFIG["SWAGGER_API_KEY"]
        warnings.warn("Using SWAGGER_API_KEY from config.py instead of environment variable", UserWarning)
    if not api_key:
        raise EnvironmentError("SWAGGER_API_KEY not found in environment variables or config.py")
    return api_key

def get_openai_api_key() -> Optional[str]:
    """Get the OpenAI API key from environment variables or config."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and "OPENAI_API_KEY" in CONFIG:
        api_key = CONFIG["OPENAI_API_KEY"]
        warnings.warn("Using OPENAI_API_KEY from config.py instead of environment variable", UserWarning)
    return api_key

def get_moderation_api_key() -> Optional[str]:
    """
    Get the OpenAI Moderation API key from environment variables or config.
    By default, this uses the same API key as the OpenAI API.
    """
    # First try a dedicated moderation API key if available
    api_key = os.environ.get("OPENAI_MODERATION_API_KEY")
    if not api_key and "OPENAI_MODERATION_API_KEY" in CONFIG:
        api_key = CONFIG["OPENAI_MODERATION_API_KEY"]
        warnings.warn("Using OPENAI_MODERATION_API_KEY from config.py instead of environment variable", UserWarning)
    
    # Fall back to the standard OpenAI API key
    if not api_key:
        api_key = get_openai_api_key()
    
    return api_key
