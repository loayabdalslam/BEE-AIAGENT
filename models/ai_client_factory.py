"""
Factory for creating AI clients.
"""
import logging
from typing import Optional

from models.base_client import BaseAIClient
from models.gemini_client import GeminiClient
from models.openai_client import OpenAIClient
from models.anthropic_client import AnthropicClient
from config import SELECTED_PROVIDER

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIClientFactory:
    """Factory for creating AI clients."""
    
    @staticmethod
    def create_client(provider: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None) -> BaseAIClient:
        """
        Create an AI client based on the provider.
        
        Args:
            provider: AI provider (gemini, openai, anthropic)
            api_key: API key for the provider
            model: Model to use
            
        Returns:
            AI client instance
        """
        # Use the selected provider from config if not specified
        provider = provider or SELECTED_PROVIDER
        
        try:
            if provider == "gemini":
                return GeminiClient(api_key, model)
            elif provider == "openai":
                return OpenAIClient(api_key, model)
            elif provider == "anthropic":
                return AnthropicClient(api_key, model)
            else:
                logger.warning(f"Unknown provider: {provider}. Falling back to Gemini.")
                return GeminiClient(api_key, model)
        except ImportError as e:
            # If the selected provider's package is not installed, try to fall back to another provider
            logger.warning(f"Error creating {provider} client: {e}")
            
            # Try to create clients in order: Gemini, OpenAI, Anthropic
            for fallback_provider in ["gemini", "openai", "anthropic"]:
                if fallback_provider != provider:
                    try:
                        if fallback_provider == "gemini":
                            return GeminiClient(api_key, model)
                        elif fallback_provider == "openai":
                            return OpenAIClient(api_key, model)
                        elif fallback_provider == "anthropic":
                            return AnthropicClient(api_key, model)
                    except ImportError:
                        continue
            
            # If all providers fail, raise an error
            raise ImportError("No AI provider packages are installed. Please install at least one of: google-generativeai, openai, anthropic")
