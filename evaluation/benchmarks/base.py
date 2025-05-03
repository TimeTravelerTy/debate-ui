from typing import Dict, List, Any, Optional
import json
import os

class Benchmark:
    """Base class for all benchmarks"""
    
    def __init__(self, name: str, description: str, answer_format: str = "letter"):
        """
        Initialize a benchmark
        
        Args:
            name: Name of the benchmark
            description: Description of the benchmark
        """
        self.name = name
        self.description = description
        self.data = None
        self.answer_format = answer_format
        
    def load_data(self) -> Dict[int, Dict[str, Any]]:
        """
        Load benchmark data
        
        Returns:
            Dictionary mapping question IDs to question data
        """
        raise NotImplementedError("Subclasses must implement load_data")
    
    def get_answer_format_instruction(self) -> str:
        """Get human-readable instruction for answer format"""
        if self.answer_format == "letter":
            return "a single letter (A, B, C, etc.)"
        elif self.answer_format == "integer":
            return "an integer number only"
        elif self.answer_format == "word":
            return "a single word"
        else:
            return "your answer in the specified format"
        
    def get_questions(self, max_questions: Optional[int] = None) -> Dict[int, Dict[str, Any]]:
        """
        Return questions in the benchmark, optionally limited to max_questions
        
        Args:
            max_questions: Optional maximum number of questions to return
            
        Returns:
            Dictionary mapping question IDs to question data
        """
        if self.data is None:
            self.data = self.load_data()
            
        if max_questions is not None and max_questions < len(self.data):
            # Convert to list of tuples, slice, and convert back to dict
            items = list(self.data.items())[:max_questions]
            return dict(items)
        
        return self.data

    def get_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific question by ID
        
        Args:
            question_id: ID of the question
            
        Returns:
            Question data or None if not found
        """
        if self.data is None:
            self.data = self.load_data()
            
        return self.data.get(question_id)
        
    def evaluate_answer(self, answer: str, ground_truth: str) -> bool:
        """
        Default method to evaluate if an answer is correct.
        Subclasses should override this method if they need custom evaluation logic.
        
        Args:
            answer: The answer to evaluate
            ground_truth: The ground truth answer
            
        Returns:
            Boolean indicating if the answer is correct
        """
        # Default implementation - simple string comparison
        return answer.strip().upper() == ground_truth.strip().upper()