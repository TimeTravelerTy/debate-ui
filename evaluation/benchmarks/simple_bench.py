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
            description="Simple questions for humans that challenge LLMs",
            answer_format="letter"
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
    
        