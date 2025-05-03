from typing import Dict, List, Any, Optional, Tuple
import json
import os
import pandas as pd
import random
import re
from .base import Benchmark
from agent.utils import extract_answer

class GPQABenchmark(Benchmark):
    """Implementation of the GPQA benchmark"""
    
    def __init__(self, csv_path: str, variant: str = "diamond", subset_size: Optional[int] = None):
        """
        Initialize the GPQA benchmark
        
        Args:
            csv_path: Path to the CSV file containing GPQA data
            variant: Which GPQA variant to use ('diamond', 'experts', 'extended', 'main')
            subset_size: Number of questions to use (optional, if None use all)
        """
        super().__init__(name="GPQA", description=f"GPQA benchmark - {variant} variant")
        self.variant = variant
        self.csv_path = csv_path
        
        # Load the GPQA dataset
        # Convert list of question dicts to dict with question ID as key
        questions_list = self._load_data(csv_path, subset_size)
        self.data = {q['id']: q for q in questions_list}
    
    def _load_data(self, csv_path: str, subset_size: Optional[int]) -> List[Dict[str, Any]]:
        """
        Load data from the CSV file
        
        Args:
            csv_path: Path to the CSV file
            subset_size: Number of questions to sample (if None, use all)
            
        Returns:
            List of question dictionaries
        """
        try:
            # Load the CSV file
            df = pd.read_csv(csv_path)
            
            # GPQA-specific column names
            question_col = "Question"
            correct_answer_col = "Correct Answer"
            incorrect_answer1_col = "Incorrect Answer 1"
            incorrect_answer2_col = "Incorrect Answer 2"
            incorrect_answer3_col = "Incorrect Answer 3"
            id_col = "Record ID"
            domain_col = "High-level domain"
            subdomain_col = "Subdomain"
            difficulty_col = "Writer's Difficulty Estimate"
            
            # Verify all required columns exist
            required_cols = [question_col, correct_answer_col, 
                            incorrect_answer1_col, incorrect_answer2_col, 
                            incorrect_answer3_col]
                            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Convert DataFrame to list of dictionaries
            questions = []
            
            for idx, row in df.iterrows():
                # Extract the question text
                question_text = row[question_col]
                
                # Create answer options list
                all_options = [
                    row[correct_answer_col],  # Correct answer
                    row[incorrect_answer1_col],  # Incorrect option 1
                    row[incorrect_answer2_col],  # Incorrect option 2
                    row[incorrect_answer3_col]   # Incorrect option 3
                ]
                
                # Remove any NaN or empty options
                all_options = [opt for opt in all_options if pd.notna(opt) and str(opt).strip()]
                
                # Shuffle the options to randomize which one is correct
                random.shuffle(all_options)
                
                # Convert to labeled options (A, B, C, D)
                options = {}
                option_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                
                # Track which option contains the correct answer
                correct_answer_label = None
                correct_answer_text = row[correct_answer_col]
                
                for i, option in enumerate(all_options):
                    if i < len(option_labels):
                        label = option_labels[i]
                        options[label] = option
                        # Check if this is the correct answer
                        if option == correct_answer_text:
                            correct_answer_label = label
                
                # Format the question with options
                formatted_question = question_text + "\n\n"
                for key, value in options.items():
                    formatted_question += f"{key}. {value}\n"
                
                # Get ID (use Record ID if available, otherwise use index)
                question_id = str(row[id_col]) if id_col in df.columns and pd.notna(row[id_col]) else str(idx + 1)
                
                # Get domain and difficulty information if available
                category = row[domain_col] if domain_col in df.columns and pd.notna(row[domain_col]) else "unknown"
                subcategory = row[subdomain_col] if subdomain_col in df.columns and pd.notna(row[subdomain_col]) else ""
                if subcategory:
                    category = f"{category} - {subcategory}"
                
                difficulty = row[difficulty_col] if difficulty_col in df.columns and pd.notna(row[difficulty_col]) else "unknown"
                
                # Create question dict
                question_dict = {
                    "id": question_id,
                    "question": formatted_question,
                    "options": options,
                    "ground_truth": correct_answer_label,  # Now this will be randomized (A, B, C, or D)
                    "difficulty": difficulty,
                    "category": category,
                    "source": "GPQA"
                }
                
                questions.append(question_dict)
            
            # If subset_size is specified and less than the total number of questions,
            # randomly sample that many questions
            if subset_size is not None and subset_size < len(questions):
                questions = random.sample(questions, subset_size)
                
            print(f"Loaded {len(questions)} questions from GPQA {self.variant} dataset")
                
            return questions
            
        except Exception as e:
            print(f"Error loading GPQA data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def evaluate_answer(self, answer: str, ground_truth: str) -> bool:
        """
        Evaluate if an answer is correct
        
        Args:
            answer: The answer to evaluate
            ground_truth: The ground truth answer
            
        Returns:
            Boolean indicating if the answer is correct
        """
        return answer == ground_truth