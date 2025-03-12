from typing import Dict, List, Any, Optional, Union
import time
import json
import requests
from openai import OpenAI

class APIClient:
    """Client for interacting with LLM APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize API client with configuration
        
        Args:
            config: Dictionary with API configuration
                - api_key: API key
                - base_url: Base URL for API
                - model_name: Model to use
        """
        self.config = config
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url")
        )
        self.model_name = config["model_name"]
        
    def call_api(self, 
                messages: List[Dict[str, str]], 
                temperature: float = 0.7, 
                max_tokens: int = 1000) -> str:
        """
        Call the API to generate a response
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            # Add retry mechanism with exponential backoff
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Extract response content
                    raw_response = response.choices[0].message.content
                    return raw_response.strip() if raw_response else ""
                    
                except (requests.exceptions.RequestException, 
                        requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout) as e:
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise e
                        
        except Exception as e:
            print(f"Error calling API: {e}")
            return f"API Error: {str(e)}"