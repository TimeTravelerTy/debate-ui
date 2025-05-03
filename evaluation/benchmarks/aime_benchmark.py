from typing import Dict, List, Any, Optional
from datasets import load_dataset
from .base import Benchmark

class AIMEBenchmark(Benchmark):
    """Implementation of the AIME benchmark"""
    
    def __init__(self, years_range=(2021, 2024), max_questions=100):
        """
        Initialize the AIME benchmark
        
        Args:
            years_range: Tuple of (start_year, end_year) inclusive  
            max_questions: Maximum number of questions to return
        """
        super().__init__(
            name="AIME", 
            description=f"AIME problems from {years_range[0]}-{years_range[1]}"
        )
        self.years_range = years_range
        self.max_questions = max_questions
        self.data = None
        self.answer_format = "integer"  # AIME answers are integers
        
    def load_data(self) -> Dict[int, Dict[str, Any]]:
        """
        Load AIME problems from specified year range
        
        Returns:
            Dictionary mapping question IDs to question data
        """
        try:
            # Load the comprehensive AIME dataset
            dataset = load_dataset("di-zhang-fdu/AIME_1983_2024")
            
            # Filter for desired years
            filtered_problems = []
            
            for item in dataset['train']:
                year = item.get('Year', 0)
                
                if self.years_range[0] <= year <= self.years_range[1]:
                    filtered_problems.append({
                        'id': item.get('ID', f"AIME_{year}_{item.get('Problem Number', '')}"),
                        'year': year,
                        'problem_number': item.get('Problem Number', ''),
                        'question': item.get('Question', ''),
                        'answer': item.get('Answer', ''),
                        'part': item.get('Part', '')
                    })
            
            # Sort by year and problem number for consistency
            filtered_problems.sort(key=lambda x: (x['year'], x['problem_number']))
            
            # Limit to max_questions
            if len(filtered_problems) > self.max_questions:
                filtered_problems = filtered_problems[:self.max_questions]
            
            # Convert to the format expected by the base class
            # Using problem ID as dictionary key
            result = {}
            for idx, problem in enumerate(filtered_problems):
                result[idx] = {
                    'id': problem['id'],
                    'question': problem['question'],
                    'answer': problem['answer'],
                    'year': problem['year'],
                    'problem_number': problem['problem_number'],
                    'part': problem['part']
                }
            
            print(f"Loaded {len(result)} AIME problems from years {self.years_range[0]}-{self.years_range[1]}")
            return result
            
        except Exception as e:
            print(f"Error loading AIME dataset: {e}")
            return {}
    
    def evaluate_answer(self, answer: str, ground_truth: str) -> bool:
        """
        Evaluate if an answer is correct for AIME problems
        
        Args:
            answer: The answer to evaluate
            ground_truth: The ground truth answer
            
        Returns:
            Boolean indicating if the answer is correct
        """
        # Clean both answers
        answer_clean = answer.strip()
        ground_truth_clean = ground_truth.strip()
        
        # Try to extract just the numerical answer
        import re
        
        # Pattern to match numerical answers (including possible leading zeros)
        num_pattern = r'\b\d+\b'
        
        answer_match = re.search(num_pattern, answer_clean)
        ground_truth_match = re.search(num_pattern, ground_truth_clean)
        
        if answer_match and ground_truth_match:
            # Compare numerical values (this handles leading zeros)
            return int(answer_match.group()) == int(ground_truth_match.group())
        
        # Fallback to exact string matching
        return answer_clean == ground_truth_clean