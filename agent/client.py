from typing import Dict, List, Any, Optional, Union, Tuple
import time
import json
import asyncio
import requests
from openai import AsyncOpenAI, OpenAI

class APIClient:
    """Client for interacting with DeepSeek API with async support and token tracking"""
    
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
        
        # Initialize both sync and async clients
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            timeout=120.0  # Increased timeout for longer queries
        )
        
        self.async_client = AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            timeout=120.0  # Increased timeout for longer queries
        )
        
        self.model_name = config["model_name"]
        
        # Initialize token tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.request_count = 0
        
    def call_api(self, 
                messages: List[Dict[str, str]], 
                temperature: float = 0.7, 
                max_tokens: int = 1000) -> Tuple[str, Dict[str, int]]:
        """
        Call the API to generate a response (synchronous version)
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (generated_text, token_usage)
        """
        try:
            # Add retry mechanism with minimal backoff
            max_retries = 3
            retry_delay = 0.5  # Very short delay between retries
            
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
                    
                    # Extract token usage
                    token_usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                    
                    # Update tracking totals
                    self.total_prompt_tokens += token_usage["prompt_tokens"]
                    self.total_completion_tokens += token_usage["completion_tokens"]
                    self.total_tokens += token_usage["total_tokens"]
                    self.request_count += 1
                    
                    return raw_response.strip() if raw_response else "", token_usage
                    
                except (requests.exceptions.RequestException, 
                        requests.exceptions.ConnectionError,
                        requests.exceptions.Timeout) as e:
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        time.sleep(retry_delay)  # Minimal backoff
                    else:
                        raise e
                        
        except Exception as e:
            print(f"Error calling API: {e}")
            return f"API Error: {str(e)}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
    async def call_api_async(self, 
                messages: List[Dict[str, str]], 
                temperature: float = 0.7, 
                max_tokens: int = 1000) -> Tuple[str, Dict[str, int]]:
        """
        Call the API to generate a response (async version)
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (generated_text, token_usage)
        """
        # No delay as DeepSeek doesn't enforce rate limits
        try:
            # Add retry mechanism with minimal backoff
            max_retries = 3
            retry_delay = 0.5  # Very short delay between retries
            
            for attempt in range(max_retries):
                try:
                    response = await self.async_client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Extract response content
                    raw_response = response.choices[0].message.content
                    
                    # Extract token usage
                    token_usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                    
                    # Update tracking totals
                    self.total_prompt_tokens += token_usage["prompt_tokens"]
                    self.total_completion_tokens += token_usage["completion_tokens"]
                    self.total_tokens += token_usage["total_tokens"]
                    self.request_count += 1
                    
                    return raw_response.strip() if raw_response else "", token_usage
                    
                except Exception as e:
                    if attempt < max_retries - 1:  # Don't sleep on the last attempt
                        await asyncio.sleep(retry_delay)  # Minimal backoff
                    else:
                        raise e
                        
        except Exception as e:
            print(f"Error calling API asynchronously: {e}")
            return f"API Error: {str(e)}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get the current token usage statistics"""
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "request_count": self.request_count
        }
    
    def reset_token_counters(self) -> None:
        """Reset all token counters"""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.request_count = 0