#!/usr/bin/env python3
"""
Script to regenerate evolution summary for existing comparison reports
"""

import os
import sys
import json
import argparse

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the fixed get_analysis_summary function
from evaluation.solution_evolution import get_analysis_summary

def regenerate_summary(results_dir=None, comparison_id=None):
    """
    Regenerate evolution summary for a comparison report
    
    Args:
        results_dir: Directory containing result files
        comparison_id: ID of the comparison to update (or all if None)
    """
    if results_dir is None:
        results_dir = os.environ.get("RESULTS_DIR", "./results")
    
    print(f"Looking for comparison files in {results_dir}")
    
    # Find comparison files
    comparison_files = []
    if comparison_id:
        # Look for a specific file
        file_path = os.path.join(results_dir, f"comparison_{comparison_id}.json")
        if os.path.exists(file_path):
            comparison_files.append(file_path)
        else:
            print(f"Comparison file not found: {file_path}")
            return
    else:
        # Look for all comparison files
        for file in os.listdir(results_dir):
            if file.startswith("comparison_") and file.endswith(".json"):
                comparison_files.append(os.path.join(results_dir, file))
    
    if not comparison_files:
        print("No comparison files found")
        return
    
    print(f"Found {len(comparison_files)} comparison files")
    
    # Process each comparison file
    for file_path in comparison_files:
        print(f"Processing {file_path}")
        
        # Load the comparison file
        with open(file_path, 'r') as f:
            comparison_data = json.load(f)
        
        # Extract question data
        questions = comparison_data.get("questions", {})
        print(f"Found {len(questions)} questions")
        
        # Prepare results for analysis
        for strategy_id, strategy_data in comparison_data.get("strategies", {}).items():
            print(f"Processing strategy: {strategy_id}")
            
            # Build results list for this strategy
            results = []
            for question_id, question_data in questions.items():
                if strategy_id in question_data:
                    question_result = {
                        "question_id": question_id,
                        "simulated": {},
                        "dual": {}
                    }
                    
                    # Get evolution data from question
                    if "simulated" in question_data[strategy_id] and "evolution" in question_data[strategy_id]["simulated"]:
                        question_result["simulated"]["evolution"] = question_data[strategy_id]["simulated"]["evolution"]
                    
                    if "dual" in question_data[strategy_id] and "evolution" in question_data[strategy_id]["dual"]:
                        question_result["dual"]["evolution"] = question_data[strategy_id]["dual"]["evolution"]
                    
                    # Only add if we have evolution data
                    if (question_result["simulated"].get("evolution") or question_result["dual"].get("evolution")):
                        results.append(question_result)
            
            if not results:
                print(f"No evolution data found for strategy {strategy_id}")
                continue
                
            print(f"Regenerating evolution summary for {len(results)} results")
            
            # Generate new evolution summary
            try:
                evolution_summary = get_analysis_summary(results)
                strategy_data["evolution_summary"] = evolution_summary
                print(f"Successfully regenerated evolution summary for {strategy_id}")
            except Exception as e:
                print(f"Error generating evolution summary for {strategy_id}: {e}")
                import traceback
                traceback.print_exc()
        
        # Save updated comparison file
        try:
            with open(file_path, 'w') as f:
                json.dump(comparison_data, f, indent=2)
            print(f"Updated comparison file: {file_path}")
        except Exception as e:
            print(f"Error saving comparison file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate evolution summary for comparison reports")
    parser.add_argument("--results-dir", type=str, default="./results", help="Directory containing result files")
    parser.add_argument("--comparison-id", type=str, default=None, help="ID of the comparison to update (or all if not specified)")
    
    args = parser.parse_args()
    regenerate_summary(args.results_dir, args.comparison_id)