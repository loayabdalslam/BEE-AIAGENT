"""
Client for interacting with the Azure OpenAI API.
"""
import logging
import json
from typing import Dict, Optional

try:
    import openai
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

from models.base_client import BaseAIClient
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_MODEL, DEFAULT_TEMPERATURE, MAX_OUTPUT_TOKENS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureOpenAIClient(BaseAIClient):
    """Client for interacting with Azure OpenAI's API."""
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the Azure OpenAI client.
        
        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint
            model: Azure OpenAI model to use
        """
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is not installed. Install it with 'pip install openai'")
            
        self.api_key = api_key or AZURE_OPENAI_API_KEY
        self.endpoint = endpoint or AZURE_OPENAI_ENDPOINT
        self.model = model or AZURE_OPENAI_MODEL
        
        if not self.api_key:
            raise ValueError("Azure OpenAI API key is required. Set it in .env file or pass it to the constructor.")
        
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint is required. Set it in .env file or pass it to the constructor.")
        
        # Initialize the Azure OpenAI client
        try:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version="2023-05-15",
                azure_endpoint=self.endpoint
            )
            logger.info(f"Successfully initialized Azure OpenAI client with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise
    
    def generate_text(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate text using the Azure OpenAI model.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Temperature for generation (0.0 to 1.0)
            
        Returns:
            Generated text response
        """
        try:
            # Set temperature if provided, otherwise use default
            temp = temperature if temperature is not None else DEFAULT_TEMPERATURE
            
            # Log the prompt for debugging
            logger.debug(f"Sending prompt to Azure OpenAI (length: {len(prompt)}):\\n{prompt[:500]}...")
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=MAX_OUTPUT_TOKENS
            )
            
            # Extract and log the response
            response_text = response.choices[0].message.content
            logger.debug(f"Received response from Azure OpenAI (length: {len(response_text)}):\\n{response_text[:500]}...")
            
            if not response_text or len(response_text.strip()) < 10:
                logger.warning(f"Received very short or empty response from Azure OpenAI: '{response_text}'")
            
            return response_text
        except Exception as e:
            error_msg = f"Error generating text with Azure OpenAI: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def generate_code(self, prompt: str, language: str = "python") -> str:
        """
        Generate code using the Azure OpenAI model with optimized settings for code.
        
        Args:
            prompt: The prompt describing the code to generate
            language: The programming language to generate code for
            
        Returns:
            Generated code
        """
        code_prompt = f"""
        Generate {language} code for the following task:
        
        {prompt}
        
        Provide only the code without explanations. Ensure the code is complete, well-structured, and follows best practices.
        """
        
        try:
            # Log the prompt for debugging
            logger.debug(f"Sending code prompt to Azure OpenAI (language: {language}, length: {len(code_prompt)}):\\n{code_prompt[:500]}...")
            
            # Generate response with lower temperature for more deterministic code
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": code_prompt}],
                temperature=0.1,  # Lower temperature for more deterministic code
                max_tokens=MAX_OUTPUT_TOKENS
            )
            
            # Extract and log the response
            response_text = response.choices[0].message.content
            logger.debug(f"Received code response from Azure OpenAI (length: {len(response_text)}):\\n{response_text[:500]}...")
            
            if not response_text or len(response_text.strip()) < 10:
                logger.warning(f"Received very short or empty code response from Azure OpenAI: '{response_text}'")
            
            return response_text
        except Exception as e:
            error_msg = f"Error generating code with Azure OpenAI: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def analyze_code(self, code: str) -> Dict:
        """
        Analyze code for quality, issues, and suggestions.
        
        Args:
            code: The code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis_prompt = f"""
        Analyze the following code for quality, potential issues, and suggestions for improvement:
        
        ```
        {code}
        ```
        
        Provide your analysis in the following JSON format:
        {{
            "issues": [
                {{
                    "severity": "high/medium/low",
                    "description": "Description of the issue",
                    "line": "line number or range",
                    "suggestion": "Suggested fix"
                }}
            ],
            "quality_score": "1-10",
            "suggestions": [
                "Suggestion 1",
                "Suggestion 2"
            ]
        }}
        
        Return ONLY the JSON without any additional text or explanation.
        """
        
        try:
            # Log the prompt for debugging
            logger.debug(f"Sending analysis prompt to Azure OpenAI (code length: {len(code)}):\\n{analysis_prompt[:500]}...")
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2,
                max_tokens=MAX_OUTPUT_TOKENS
            )
            
            # Extract and log the response
            response_text = response.choices[0].message.content
            logger.debug(f"Received analysis response from Azure OpenAI (length: {len(response_text)}):\\n{response_text[:500]}...")
            
            # Try to parse the response as JSON
            try:
                # Find JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis_json = json.loads(json_str)
                    return analysis_json
                else:
                    # If no JSON found, return the raw text
                    return {"analysis": response_text}
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                return {"analysis": response_text}
        except Exception as e:
            error_msg = f"Error analyzing code with Azure OpenAI: {str(e)}"
            logger.error(error_msg)
            # Return an error dictionary instead of raising an exception
            return {"error": error_msg}
