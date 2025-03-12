from typing import Dict, Any, Optional
import json
import os

class CollaborationStrategy:
    """Base class for collaboration strategies"""
    
    def __init__(self, name: str, config_path: Optional[str] = None):
        """
        Initialize a collaboration strategy
        
        Args:
            name: Name of the strategy
            config_path: Path to configuration file (optional)
        """
        self.name = name
        
        # Load configuration from file if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Default configuration
            self.config = {
                "temperature": 0.7,
                "max_tokens": 1000,
                "num_turns": 5
            }
    
    def get_system_prompt_a(self) -> Dict[str, str]:
        """Get system prompt for Agent A"""
        # To be implemented by subclasses
        raise NotImplementedError("Subclasses must implement get_system_prompt_a")
    
    def get_system_prompt_b(self) -> Dict[str, str]:
        """Get system prompt for Agent B"""
        # To be implemented by subclasses
        raise NotImplementedError("Subclasses must implement get_system_prompt_b")
    
    def get_temperature(self) -> float:
        """Get temperature setting"""
        return self.config.get("temperature", 0.7)
    
    def get_max_tokens(self) -> int:
        """Get max tokens setting"""
        return self.config.get("max_tokens", 1000)
    
    def get_num_turns(self) -> int:
        """Get number of turns"""
        return self.config.get("num_turns", 5)