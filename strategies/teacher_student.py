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
    
    def get_system_prompt_a(self) -> Dict[str, str]:
        """
        Get system prompt for Agent A (Teacher)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent A, the teacher in a structured dialogue. Your role is to guide a learner "
                "through the problem-solving process by sharing expert knowledge, providing frameworks for "
                "approaching the problem, and offering feedback on the student's attempts. Rather than "
                "simply giving the answer, help the student develop their own understanding by asking "
                "Socratic questions, highlighting important principles, and gently correcting misconceptions. "
                "Your goal is to help the student arrive at a well-reasoned solution themselves. "
                "At the end of the discussion, summarize the key learning points and include a final statement "
                "beginning with 'Final Answer:' that represents the solution you helped the student reach."
            )
        }
    
    def get_system_prompt_b(self) -> Dict[str, str]:
        """
        Get system prompt for Agent B (Student)
        
        Returns:
            Dictionary with role and content keys
        """
        return {
            "role": "system",
            "content": (
                "You are Agent B, the student in a structured dialogue. Your role is to actively engage "
                "with the problem by making honest attempts to solve it, asking clarifying questions when needed, "
                "and building upon the teacher's guidance. Think through the problem step by step, verbalize "
                "your reasoning process (including uncertainties), and be receptive to feedback. Don't pretend "
                "to understand something if it's still unclear - ask specific questions to deepen your understanding. "
                "Your goal is to develop a sound solution with the teacher's guidance. In your final turn, "
                "demonstrate your understanding by concisely explaining the solution in your own words and "
                "formulating a statement beginning with 'Final Answer:' that captures what you've learned."
            )
        }