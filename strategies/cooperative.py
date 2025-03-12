from typing import Dict, Any, Optional
from .base import CollaborationStrategy

class CooperativeStrategy(CollaborationStrategy):
    """Implementation of the cooperative strategy"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the cooperative strategy
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__("cooperative", config_path)
    
    def get_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Proposer)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, the proposer in a cooperative dialogue. Your role is to propose "
                "initial approaches and partial solutions to the problem. Break down the problem into "
                "manageable components, identify key constraints, and suggest potential solution strategies. "
                "You don't need to provide complete solutions - focus on initiating helpful directions "
                "that Agent B can build upon. Be clear and specific in your proposals. "
                "When it is time to conclude, work with Agent B to formulate a final statement beginning "
                "with 'Final Answer:' that represents your joint solution."
            )
        }
    
    def get_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Extender)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, the extender in a cooperative dialogue. Your role is to build upon "
                "and refine the initial proposals made by Agent A. Fill in gaps in reasoning, add depth "
                "to the analysis, and integrate additional perspectives. When Agent A suggests a direction, "
                "you should help develop it further, possibly adding more structure, examples, or connecting "
                "it to other relevant concepts. Your goal is not to critique but to enhance and strengthen "
                "the collective solution. In your final turn, work with Agent A to formulate a joint final "
                "statement beginning with 'Final Answer:' that captures your collaborative solution."
            )
        }