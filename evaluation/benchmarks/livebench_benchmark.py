from typing import Dict, List, Any, Optional, Tuple
import os
import re
from datasets import load_dataset
import random
from .base import Benchmark

class LiveBenchReasoningBenchmark(Benchmark):
    """Implementation of the LiveBench reasoning benchmark"""
    
    def __init__(self, max_questions: Optional[int] = None, categories: Optional[List[str]] = None):
        """
        Initialize the LiveBench reasoning benchmark
        
        Args:
            max_questions: Maximum number of questions to return (optional)
            categories: List of categories to include (e.g., ['zebra_puzzle', 'spatial_reasoning'])
        """
        super().__init__(
            name="LiveBench", 
            description="LiveBench reasoning tasks for evaluating multi-agent debate",
            answer_format="custom"  # LiveBench has variable answer formats
        )
        self.max_questions = max_questions
        self.categories = categories
        self.data = None
        
    def load_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Load benchmark data from HuggingFace datasets
        
        Returns:
            Dictionary mapping question IDs to question data
        """
        try:
            # Load the LiveBench reasoning dataset
            dataset = load_dataset("livebench/reasoning", split="test")
            
            # Filter for desired categories if specified
            if self.categories:
                filtered_examples = [
                    ex for ex in dataset 
                    if ex.get('task') in self.categories or ex.get('category') in self.categories
                ]
            else:
                filtered_examples = list(dataset)
            
            # Apply random sampling if max_questions is specified
            if self.max_questions is not None and self.max_questions < len(filtered_examples):
                filtered_examples = random.sample(filtered_examples, self.max_questions)
            
            # Convert to the format expected by the base class
            result = {}
            for idx, example in enumerate(filtered_examples):
                # Extract question from turns
                turns = example.get('turns', [])
                if not turns or len(turns) == 0:
                    continue
                
                # Get the question text from the first turn
                question_text = turns[0]
                if not question_text:
                    continue
                
                # Create unique ID if not present
                question_id = str(example.get('question_id', f"livebench_{idx}"))
                
                # Extract category and task
                category = example.get('category', 'reasoning')
                task = example.get('task', 'unknown')
                
                # Get ground truth
                ground_truth = example.get('ground_truth', '')
                
                # Store in result dict with relevant metadata
                result[question_id] = {
                    'id': question_id,
                    'question': question_text,
                    'ground_truth': ground_truth,
                    'category': category,
                    'task': task,
                    'level': example.get('level', 0)
                }
            
            print(f"Loaded {len(result)} questions from LiveBench reasoning dataset")
            
            # Log distribution of tasks
            task_counts = {}
            for q_data in result.values():
                task = q_data.get('task', 'unknown')
                task_counts[task] = task_counts.get(task, 0) + 1
                
            print("Task distribution:")
            for task, count in sorted(task_counts.items()):
                print(f"  - {task}: {count} questions")
                
            return result
            
        except Exception as e:
            print(f"Error loading LiveBench dataset: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def evaluate_answer(self, answer: str, ground_truth: str) -> bool:
        """
        Evaluate if an answer is correct for LiveBench reasoning tasks
        
        Args:
            answer: The answer to evaluate
            ground_truth: The ground truth answer
            
        Returns:
            Boolean indicating if the answer is correct
        """
        if not answer or not ground_truth:
            return False
        
        # Extract answer from solution tags for zebra puzzles
        solution_match = re.search(r'<solution>(.*?)</solution>', answer, re.IGNORECASE | re.DOTALL)
        if solution_match:
            answer = solution_match.group(1).strip()
            
        # Extract answer from bold formatting for spatial/word tasks and comma-separated lists
        # This pattern handles numbers, phrases, and comma-separated lists in bold
        bold_match = re.search(r'\*\*([\w\s,]+)\*\*', answer, re.IGNORECASE)
        if bold_match:
            answer = bold_match.group(1).strip()
            
        # Clean and normalize both answers
        answer_clean = self._normalize_answer(answer)
        ground_truth_clean = self._normalize_answer(ground_truth)
        
        # For tasks with comma-separated items (like zebra puzzles or web of lies)
        if ',' in ground_truth_clean:
            # Split by commas and compare each element
            answer_parts = [part.strip() for part in answer_clean.split(',')]
            ground_truth_parts = [part.strip() for part in ground_truth_clean.split(',')]
            
            # Check if all parts match (order matters for these tasks)
            if len(answer_parts) != len(ground_truth_parts):
                return False
                
            return all(a == g for a, g in zip(answer_parts, ground_truth_parts))
        
        # For numeric answers
        if ground_truth_clean.isdigit():
            # Extract numbers from answer and check if any match
            numbers = re.findall(r'\b\d+\b', answer_clean)
            return any(num == ground_truth_clean for num in numbers)
            
        # For single word/phrase answers
        return answer_clean == ground_truth_clean
    
    def _normalize_answer(self, text: str) -> str:
        """
        Normalize an answer for comparison
        
        Args:
            text: The text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation except commas (important for lists)
        text = re.sub(r'[^\w\s,]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
        
    def get_answer_format_instruction(self) -> str:
        """Get human-readable instruction for answer format"""
        return "the exact answer format specified in the question (comma-separated lists, numbers, or phrases as required)"