import json
import re
import os
import pandas as pd
import random
from typing import Dict, List, Any, Optional, Tuple

from .base import Benchmark

class SimpleBenchmark(Benchmark):
    """Implementation of the SimpleBench benchmark"""
    
    def __init__(self, json_path: str, csv_path: Optional[str] = None):
        """
        Initialize the SimpleBench benchmark
        
        Args:
            json_path: Path to the JSON file with questions
            csv_path: Optional path to CSV file with additional data
        """
        super().__init__(
            name="SimpleBench", 
            description="Simple questions for humans that challenge LLMs"
        )
        self.json_path = json_path
        self.csv_path = csv_path
        self.data = None
        
    def load_data(self) -> Dict[int, Dict[str, Any]]:
        """
        Load benchmark data from JSON and optionally CSV
        
        Returns:
            Dictionary mapping question IDs to question data
        """
        # Check if JSON file exists
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON file not found: {self.json_path}")
            
        # Load from JSON
        with open(self.json_path, 'r') as f:
            json_data = json.load(f)
            data = {item["question_id"]: item for item in json_data["eval_data"]}
            
        # Optionally enhance with CSV data if provided
        if self.csv_path and os.path.exists(self.csv_path):
            try:
                df = pd.read_csv(self.csv_path)
                # Map additional data from CSV to enhance JSON data
                for _, row in df.iterrows():
                    q_id = int(row.get('id', 0))
                    if q_id in data:
                        # Add options data if available
                        options = {}
                        for i in range(1, 6):  # Options 1-5
                            option_key = f'option{i}'
                            if option_key in row:
                                options[f'option{i}'] = row[option_key]
                        
                        if options:
                            data[q_id]['options'] = options
            except Exception as e:
                print(f"Error loading CSV data: {e}")
                # Continue with just the JSON data
        
        return data
    
    def evaluate_response(self, question_id: int, response: str) -> Dict[str, Any]:
        """
        Extract answer from response and compare to ground truth
        
        Args:
            question_id: ID of the question
            response: Model response to evaluate
            
        Returns:
            Dictionary with evaluation results
        """
        # Ensure data is loaded
        if self.data is None:
            self.load_data()
            
        # Get question and ground truth
        question_data = self.data.get(question_id)
        if not question_data:
            return {
                "correct": False,
                "ground_truth": None,
                "extracted_answer": None,
                "error": f"Question ID {question_id} not found"
            }
            
        ground_truth = question_data["answer"]
        
        # Extract answer from response
        extracted_answer = self._extract_answer_letter(response)
        
        return {
            "correct": extracted_answer == ground_truth,
            "ground_truth": ground_truth,
            "extracted_answer": extracted_answer
        }
    
    def evaluate_answer(self, answer: str, ground_truth: str) -> bool:
        """
        Evaluate if an answer is correct
        
        Args:
            answer: The answer to evaluate
            ground_truth: The ground truth answer
            
        Returns:
            Boolean indicating if the answer is correct
        """
        extracted_answer = self._extract_answer_letter(answer)
        if not extracted_answer:
            return False
            
        return extracted_answer.upper() == ground_truth.upper()
        
    def _extract_answer_letter(self, response: str) -> Optional[str]:
        """Extract the answer letter (A-F) from the response, handling various formats"""
        # Match "Final Answer: X" format, including possible markdown formatting
        # This handles: Final Answer: A, Final Answer: *A*, Final Answer: **A**, etc.
        match = re.search(r"Final Answer:\s*\*{0,2}([A-F])\*{0,2}", response, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # Try to find "The answer is X" format
        match = re.search(r"[Tt]he answer is\s*\*{0,2}([A-F])\*{0,2}", response)
        if match:
            return match.group(1).upper()
        
        # Try to match a standalone letter that's likely to be the answer
        # Look for patterns like "Option A" or "Answer: B" or just "C."
        match = re.search(r"(?:[Oo]ption|[Aa]nswer|:)\s*\*{0,2}([A-F])\*{0,2}[\.|\s]", response)
        if match:
            return match.group(1).upper()
        
        # Last resort: look for any standalone A-F with word boundaries
        match = re.search(r"\b\*{0,2}([A-F])\*{0,2}\b", response, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        # No answer found
        return None
        