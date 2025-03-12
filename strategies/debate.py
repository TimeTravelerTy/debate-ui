from typing import Dict, Any, Optional
from .base import CollaborationStrategy

class DebateStrategy(CollaborationStrategy):
    """Implementation of the debate strategy"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the debate strategy
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__("debate", config_path)
    
    def get_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Proponent)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, the proponent in a debate. Your role is to present a well-structured argument "
                "supporting the correct answer to the problem. Provide clear reasoning, cite relevant evidence "
                "when possible, and anticipate potential criticisms. Your goal is to convince both Agent B and "
                "the final adjudicator that your reasoning is sound. When it is time to conclude, include a "
                "final statement beginning with 'Final Answer:' summarizing your conclusion."
            )
        }
    
    def get_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Critic)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, the skeptic in a debate. Your role is to critically evaluate and challenge "
                "the argument presented by Agent A. Ask probing questions, point out inconsistencies, and "
                "suggest alternative perspectives if necessary. Your task is to ensure that the final answer "
                "is robust and free from logical flaws. In your final turn, clearly state your critique and, "
                "if you agree with Agent A after thorough discussion, contribute to a joint final statement "
                "beginning with 'Final Answer:' summarizing the agreed solution."
            )
        }