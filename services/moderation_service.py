"""
OpenAI Moderation Service.
This module provides functionality to check content using OpenAI's Moderation API.

The Moderation API helps identify potentially harmful content in text and images.
It supports multiple content categories like harassment, hate speech, self-harm,
sexual content, violence, and more.
"""

from typing import Dict, List, Optional, Union, Any
import logging
from openai import OpenAI
from env_config import get_openai_api_key

logger = logging.getLogger(__name__)

# Available moderation models
MODERATION_MODEL_OMNI = "omni-moderation-latest"  # Newer model with more categories and multi-modal support
MODERATION_MODEL_TEXT = "text-moderation-latest"   # Legacy model for text only

class ModerationService:
    """Service for checking content against OpenAI's Moderation API.
    
    This service uses OpenAI's moderation endpoint to detect potentially harmful
    content across multiple categories including harassment, hate speech, 
    self-harm, sexual content, violence, and illicit activities.
    """
    
    def __init__(self, model: str = MODERATION_MODEL_OMNI):
        """Initialize the moderation service with OpenAI client.
        
        Args:
            model: The moderation model to use. Defaults to the latest omni model.
                  Available options:
                  - omni-moderation-latest: Newer model with more categories and multi-modal support
                  - text-moderation-latest: Legacy model for text only
        """
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key is required for moderation service")
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def check_content(self, content: Union[str, List[str]]) -> Any:
        """
        Check if content violates OpenAI's content policy.
        
        Args:
            content: A string or list of strings to check
            
        Returns:
            OpenAI moderation response object
        """
        try:
            response = self.client.moderations.create(
                model=self.model,
                input=content
            )
            return response
        except Exception as e:
            logger.error(f"Error in moderation API: {e}")
            # Return a simple dict that matches the expected structure
            return {"id": "", "model": self.model, "results": [{"flagged": False}]}
    
    def is_flagged(self, content: Union[str, List[str]]) -> bool:
        """
        Check if content is flagged by the moderation API.
        
        Args:
            content: A string or list of strings to check
            
        Returns:
            True if content is flagged, False otherwise
        """
        try:
            response = self.check_content(content)
            # Check if any content is flagged - handle both dict and response object
            if hasattr(response, 'results'):
                # It's a response object
                return any(result.flagged for result in response.results)
            else:
                # It's a dict (fallback)
                return any(result.get("flagged", False) for result in response.get("results", []))
        except Exception as e:
            logger.error(f"Error checking moderation flag: {e}")
            # In case of error, default to not flagged to prevent blocking users
            return False
    
    def get_flagged_categories(self, content: Union[str, List[str]]) -> Dict[str, List[str]]:
        """
        Get detailed information about which categories were flagged.
        
        The API checks for categories including:
        - harassment: Harassment content
        - harassment/threatening: Harassment with threatening content
        - hate: Hate speech
        - hate/threatening: Hate speech with threatening content
        - illicit: Content promoting illicit activities
        - illicit/violent: Content promoting violent illicit activities
        - self-harm: Content related to self-harm
        - self-harm/intent: Content expressing intent to self-harm
        - self-harm/instructions: Content with instructions for self-harm
        - sexual: Sexual content
        - sexual/minors: Sexual content involving minors
        - violence: Violent content
        - violence/graphic: Graphic violent content
        
        Args:
            content: A string or list of strings to check
            
        Returns:
            Dictionary mapping content to list of flagged categories
        """
        try:
            response = self.check_content(content)
            results = {}
            
            # Handle single string input
            if isinstance(content, str):
                contents = [content]
            else:
                contents = content
            
            # Handle different response types
            if hasattr(response, 'results'):
                # It's a response object
                for i, c in enumerate(contents):
                    if i < len(response.results):
                        result = response.results[i]
                        if result.flagged:
                            # Get all flagged categories
                            categories = result.categories.model_dump()
                            flagged_categories = [
                                category for category, flagged in categories.items()
                                if flagged
                            ]
                            results[c] = flagged_categories
            else:
                # It's a dict (fallback)
                for i, c in enumerate(contents):
                    if i < len(response.get("results", [])):
                        result = response["results"][i]
                        if result.get("flagged", False):
                            # Get all flagged categories
                            categories = result.get("categories", {})
                            flagged_categories = [
                                category for category, flagged in categories.items()
                                if flagged
                            ]
                            results[c] = flagged_categories
            
            return results
        except Exception as e:
            logger.error(f"Error getting flagged categories: {e}")
            return {}
            
    def get_moderation_analysis(self, content: Union[str, List[str]]) -> Dict:
        """
        Get full moderation analysis including scores for each category.
        
        This method returns a comprehensive analysis with detailed scores for each
        moderation category, providing insight into why content may be flagged.
        
        Args:
            content: A string or list of strings to check
            
        Returns:
            Dictionary with detailed moderation analysis
        """
        try:
            response = self.check_content(content)
            
            # Convert API response to a standard dictionary format
            if hasattr(response, 'results'):
                # It's a response object
                analysis = {
                    "flagged": any(result.flagged for result in response.results),
                    "results": []
                }
                
                for result in response.results:
                    result_dict = {
                        "flagged": result.flagged,
                        "categories": result.categories.model_dump(),
                        "category_scores": result.category_scores.model_dump()
                    }
                    
                    # Add input types if available (omni model only)
                    if hasattr(result, 'category_applied_input_types'):
                        result_dict["category_applied_input_types"] = result.category_applied_input_types.model_dump()
                    
                    analysis["results"].append(result_dict)
            else:
                # It's a dict (fallback)
                analysis = {
                    "flagged": any(result.get("flagged", False) for result in response.get("results", [])),
                    "results": []
                }
                
                for result in response.get("results", []):
                    result_dict = {
                        "flagged": result.get("flagged", False),
                        "categories": result.get("categories", {}),
                        "category_scores": result.get("category_scores", {})
                    }
                    
                    # Add input types if available (omni model only)
                    if "category_applied_input_types" in result:
                        result_dict["category_applied_input_types"] = result.get("category_applied_input_types", {})
                    
                    analysis["results"].append(result_dict)
            
            return analysis
        except Exception as e:
            logger.error(f"Error getting moderation analysis: {e}")
            return {"flagged": False, "results": []}
            
    def get_category_description(self, category: str) -> str:
        """
        Get description for a specific moderation category.
        
        Args:
            category: The category name to get a description for
            
        Returns:
            Description of the category
        """
        descriptions = {
            "harassment": "Content that expresses, incites, or promotes harassing language towards any target.",
            "harassment_threatening": "Harassment content that also includes violence or serious harm towards any target.",
            "harassment/threatening": "Harassment content that also includes violence or serious harm towards any target.",
            "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
            "hate_threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
            "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
            "illicit": "Content that gives advice or instruction on how to commit illicit acts.",
            "illicit_violent": "Content about illicit acts that also includes references to violence or procuring a weapon.",
            "illicit/violent": "Content about illicit acts that also includes references to violence or procuring a weapon.",
            "self_harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
            "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
            "self_harm_intent": "Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm.",
            "self-harm/intent": "Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm.",
            "self_harm_instructions": "Content that encourages performing acts of self-harm or gives instructions on how to commit such acts.",
            "self-harm/instructions": "Content that encourages performing acts of self-harm or gives instructions on how to commit such acts.",
            "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity.",
            "sexual_minors": "Sexual content that includes an individual who is under 18 years old.",
            "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
            "violence": "Content that depicts death, violence, or physical injury.",
            "violence_graphic": "Content that depicts death, violence, or physical injury in graphic detail.",
            "violence/graphic": "Content that depicts death, violence, or physical injury in graphic detail."
        }
        
        return descriptions.get(category, f"Unknown category: {category}")
