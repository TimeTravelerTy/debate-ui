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
    
    def _get_base_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Proponent)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, a reasoning agent acting as the proponent in a structured dialogue. "
                "Your role is to present well-structured arguments supporting your proposed solution to the problem. "
                "Provide clear reasoning, cite relevant principles when applicable. Engage thoughtfully with critiques from Agent B, either by defending your "
                "original position with additional reasoning or by refining your answer based on valid criticisms. "
                "Remember that your goal is not to 'win' but to collaboratively reach the most accurate solution. "
                "IMPORTANT: When you see the prompt '(final turn)', you MUST end your response with 'Final Answer: X', where X is your definitive conclusion. "
                "This is critical for evaluation purposes.'"
            )
        }
    
    def _get_base_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Critic)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, a reasoning agent acting as the critic in a structured dialogue. "
                "Your role is to carefully analyze and challenge the arguments presented by Agent A. "
                "Ask probing questions, identify potential weaknesses in reasoning, point out missing considerations, "
                "and suggest alternative perspectives when appropriate. Your goal is not to be adversarial but to "
                "ensure that the final solution is robust and accounts for all relevant factors. Be constructive "
                "in your criticism, suggesting improvements rather than merely pointing out flaws. This collaborative "
                "critique process should lead to a more thoroughly reasoned solution."
                "IMPORTANT: When you see the prompt '(final turn)', you MUST end your response with 'Final Answer: X', where X is your definitive conclusion. "
                "This is critical for evaluation purposes."
            )
        }