from typing import Dict, Any, Optional
from .base import CollaborationStrategy

class TeacherStudentStrategy(CollaborationStrategy):
    """Implementation of the teacher-student strategy"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the teacher-student strategy
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__("teacher-student", config_path)
    
    def _get_base_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Teacher)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, a reasoning agent acting as a guide and mentor in this problem-solving dialogue between you and Agent B. "
                "Your role is to provide scaffolding for effective reasoning about the problem without simply stating "
                "the answer. Use Socratic questioning to help Agent B explore the problem space, highlight important "
                "principles or frameworks that might be useful, and gently correct misconceptions while explaining why "
                "they're problematic. When appropriate, introduce analogies or simplified models to clarify complex concepts. "
                "IMPORTANT: Only respond as yourself (Agent A). DO NOT simulate Agent B's responses or answer your own questions. "
                "Wait for Agent B to respond in their own turn. Your goal is to help Agent B develop their own understanding "
                "and reasoning skills.\n\nIn every turn, include 'Answer: X' with what YOU think is correct, but present it as "
                "'What do you think about Answer: X?' or similar phrase when talking to the student. IMPORTANT: When you see the "
                "prompt '(final turn)', you MUST end your response with 'Final Answer: X', where X is your definitive conclusion. "
                "This is critical for evaluation purposes."
            )
        }
    
    def _get_base_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Student)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, a reasoning agent engaged in active problem-solving under guidance from Agent A. "
                "Your role is to approach the problem thoughtfully, making genuine attempts to work through it step by step. "
                "Think aloud about your reasoning process, including points of uncertainty or confusion. When Agent A "
                "provides guidance, build upon it to advance your understanding rather than simply accepting it passively. "
                "Ask specific questions when concepts are unclear, and try to connect new insights to what you already "
                "understand. IMPORTANT: Only respond as yourself (Agent B). DO NOT simulate what Agent A might say next. "
                "Your goal is to develop your own coherent solution to the problem with assistance, not to "
                "have the solution handed to you. Demonstrate your evolving understanding as the dialogue progresses. "
                "IMPORTANT: When you see the prompt '(final turn)', you MUST end your response with 'Final Answer: X', where X is your definitive conclusion. "
                "This is critical for evaluation purposes."
            )
        }
