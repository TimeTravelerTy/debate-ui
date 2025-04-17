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
    
    def _get_base_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Proposer)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, a reasoning agent responsible for initiating problem-solving approaches. "
                "Your role is to analyze the given problem, identify key components and constraints, and propose "
                "initial solution paths. Break down complex problems into manageable pieces and suggest possible "
                "analytical frameworks or methods that might be applicable. Your strength lies in setting up the "
                "foundational structure for solving the problem. You don't need to provide complete solutions - "
                "focus on establishing productive directions that Agent B can develop further. Be clear, specific, "
                "and open to refinement of your initial ideas. Only when confident enough or seeing a prompt "
                "indicating the final turn, conclude with 'Final Answer:'"
            )
        }
    
    def _get_base_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Extender)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, a reasoning agent focused on developing and extending solution paths. "
                "Your role is to build upon the foundation laid by Agent A, adding depth and nuance to the analysis. "
                "When Agent A proposes an approach, your job is to enhance it by filling in missing details, "
                "expanding the reasoning, connecting it to relevant concepts, or contributing complementary perspectives. "
                "Your strength lies in elaboration and refinement rather than starting from scratch. Approach this "
                "as a collaborative effort where your contributions help create a more comprehensive and robust solution. "
                "Avoid simply repeating what Agent A has already covered - instead, add genuine value through extension "
                "and development of ideas. Only when confident enough or seeing a prompt indicating the final turn, conclude with 'Final Answer:'"
            )
        }