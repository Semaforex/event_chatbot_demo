"""
Test script for the OpenAI Moderation Service.
This script demonstrates how to use the moderation service 
to check content against OpenAI's content policy.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(override=True)

def test_moderation_service():
    """Test the moderation service with various examples."""
    try:
        from services.moderation_service import ModerationService, MODERATION_MODEL_OMNI
        
        # Initialize the moderation service with the omni model (latest with multi-modal support)
        moderation_service = ModerationService(model=MODERATION_MODEL_OMNI)
        logger.info(f"Moderation service initialized successfully with model: {moderation_service.model}")
        
        # Test examples
        examples = [
            "I would like to find concerts in New York this weekend",  # Normal content
            "I want to make an evil bomb and hurt people",  # Harmful content
            "Tell me about music festivals in Miami",  # Normal content
        ]
        
        # Check each example
        for i, example in enumerate(examples):
            logger.info(f"\nTesting example {i+1}: {example}")
            
            # Check if content is flagged
            is_flagged = moderation_service.is_flagged(example)
            logger.info(f"Content flagged: {is_flagged}")
            
            # Get detailed analysis
            analysis = moderation_service.get_moderation_analysis(example)
            
            # Print flagged categories if any
            if is_flagged:
                flagged_categories = moderation_service.get_flagged_categories(example)
                logger.info(f"Flagged categories: {flagged_categories}")
                
                # Print descriptions for flagged categories
                for content, categories in flagged_categories.items():
                    for category in categories:
                        description = moderation_service.get_category_description(category)
                        logger.info(f"  {category}: {description}")
            
            # Print moderation scores for demonstration
            for result in analysis.get('results', []):
                logger.info("Category scores:")
                scores = result.get('category_scores', {})
                for category, score in scores.items():
                    # Handle None values safely
                    if score is not None:
                        logger.info(f"  {category}: {score:.4f}")
                    else:
                        logger.info(f"  {category}: None")
            
            logger.info("-" * 50)
        
    except Exception as e:
        logger.error(f"Error testing moderation service: {e}")
        raise

if __name__ == "__main__":
    test_moderation_service()
