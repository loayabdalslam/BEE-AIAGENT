"""
Base client for AI providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseAIClient(ABC):
    """Abstract base class for AI provider clients."""
    
    @abstractmethod
    def generate_text(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate text using the AI model.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def generate_code(self, prompt: str, language: str = "python") -> str:
        """
        Generate code using the AI model.
        
        Args:
            prompt: The prompt describing the code to generate
            language: The programming language to generate code for
            
        Returns:
            Generated code
        """
        pass
    
    @abstractmethod
    def analyze_code(self, code: str) -> Dict:
        """
        Analyze code for quality, issues, and suggestions.
        
        Args:
            code: The code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        pass
