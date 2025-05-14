#!/usr/bin/env python3
"""
Script to recalculate evolution patterns for GPQA and AIME runs
"""

import json
import os
import sys
from typing import Dict, Any

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary functions
from evaluation.solution_evolution import analyze_solution_evolution, get_analysis_summary

class DummyBenchmark:
    """Simple benchmark that just needs answer_format and evaluate_answer"""
    def __init__(self, name, answer_format):
        self.name = name
        self.answer_format = answer_format
        
    def evaluate_answer(self, answer, ground_truth):
        if not answer or not ground_truth:
            return False
            
        # Simple string comparison - adequate for recalculating patterns
        return str(answer).strip().upper() == str(ground_truth).strip().upper()

def process_log_file(log_path: str, benchmark_name: str) -> Dict[str, Any]:
    """Process a log file to update evolution patterns"""
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # Create a dummy benchmark with the correct answer format
    if benchmark_name == "GPQA":
        benchmark = DummyBenchmark("GPQA", "letter")
    elif benchmark_name == "AIME":
        benchmark = DummyBenchmark("AIME", "integer")
    else:
        print(f"Unknown benchmark: {benchmark_name}")
        return log_data
    
    # Get ground truth
    ground_truth = log_data.get("ground_truth", "")
    
    # Process simulated messages
    simulated_messages = log_data.get("simulated_messages", [])
    if simulated_messages:
        sim_evolution = analyze_solution_evolution(simulated_messages, ground_truth, benchmark)
        log_data["simulated_evolution"] = sim_evolution
    
    # Process dual messages
    dual_messages = log_data.get("dual_messages", [])
    if dual_messages:
        dual_evolution = analyze_solution_evolution(dual_messages, ground_truth, benchmark)
        log_data["dual_evolution"] = dual_evolution
    
    return log_data

def update_result_file(result_path: str, log_updates: Dict[str, Dict[str, Any]]):
    """Update a result file with new evolution patterns"""
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    # Update each result
    for result in result_data.get("results", []):
        log_id = result.get("simulated", {}).get("log_id")
        if log_id in log_updates:
            log_update = log_updates[log_id]
            
            # Update evolution data
            if "simulated_evolution" in log_update:
                result["simulated"]["evolution"] = log_update["simulated_evolution"]
            
            if "dual_evolution" in log_update:
                result["dual"]["evolution"] = log_update["dual_evolution"]
    
    # Update evolution summary
    result_data["evolution_summary"] = get_analysis_summary(result_data.get("results", []))
    
    # Save updated result
    with open(result_path, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"Updated result file: {result_path}")
    return result_data

def update_comparison_file(comparison_path: str, result_updates: Dict[str, Dict[str, Any]]):
    """Update a comparison file with new evolution patterns"""
    with open(comparison_path, 'r') as f:
        comparison_data = json.load(f)
    
    # Update each strategy's evolution summary
    for strategy_id, strategy_data in comparison_data.get("strategies", {}).items():
        run_id = strategy_data.get("run_id")
        if run_id in result_updates:
            result_update = result_updates[run_id]
            
            # Update evolution summary if available
            if "evolution_summary" in result_update:
                strategy_data["evolution_summary"] = result_update.get("evolution_summary", {})
    
    # Update question-level evolution data
    for question_id, question_data in comparison_data.get("questions", {}).items():
        for strategy_id, strategy_question_data in question_data.items():
            # Find the corresponding result
            for run_id, result_update in result_updates.items():
                if strategy_id in run_id:
                    for result in result_update.get("results", []):
                        if str(result.get("question_id")) == str(question_id):
                            # Update simulated evolution
                            if "simulated" in strategy_question_data and "evolution" in result["simulated"]:
                                strategy_question_data["simulated"]["evolution"] = result["simulated"]["evolution"]
                            
                            # Update dual evolution
                            if "dual" in strategy_question_data and "evolution" in result["dual"]:
                                strategy_question_data["dual"]["evolution"] = result["dual"]["evolution"]
    
    # Save updated comparison
    with open(comparison_path, 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    print(f"Updated comparison file: {comparison_path}")

def process_files():
    """Process comparison files and update evolution patterns"""
    results_dir = "./results"
    comparison_files = [
        os.path.join(results_dir, "comparison_gpqa_1746399747.json"), 
        os.path.join(results_dir, "comparison_aime_1746312436.json")
    ]
    
    for comparison_path in comparison_files:
        if not os.path.exists(comparison_path):
            print(f"Comparison file not found: {comparison_path}")
            continue
        
        print(f"Processing comparison file: {comparison_path}")
        
        # Determine benchmark type from filename
        benchmark_name = None
        if "gpqa" in comparison_path.lower():
            benchmark_name = "GPQA"
        elif "aime" in comparison_path.lower():
            benchmark_name = "AIME"
        else:
            print(f"Unknown benchmark type for file: {comparison_path}")
            continue
        
        # Read comparison file and extract run_ids
        with open(comparison_path, 'r') as f:
            comparison_data = json.load(f)
        
        strategies = comparison_data.get("strategies", {})
        run_ids = []
        for strat in strategies.values():
            run_id = strat.get("run_id")
            if run_id:
                run_ids.append(run_id)
        
        print(f"Found run_ids: {run_ids}")
        
        # For each run_id, process the corresponding result file
        result_updates = {}
        for run_id in run_ids:
            result_path = os.path.join(results_dir, f"result_{run_id}.json")
            if not os.path.exists(result_path):
                print(f"Result file not found: {result_path}")
                continue
            
            with open(result_path, 'r') as f:
                result_data = json.load(f)
            
            # Collect all log_ids from this result file
            log_ids = set()
            for result in result_data.get("results", []):
                sim_log_id = result.get("simulated", {}).get("log_id")
                if sim_log_id:
                    log_ids.add(sim_log_id)
            
            print(f"  Found {len(log_ids)} log_ids for run {run_id}")
            
            # Process each log file
            log_updates = {}
            for log_id in log_ids:
                log_path = os.path.join(results_dir, f"log_{log_id}.json")
                if not os.path.exists(log_path):
                    print(f"    Log file not found: {log_path}")
                    continue
                
                print(f"    Processing log: {log_id}")
                updated_log = process_log_file(log_path, benchmark_name)
                log_updates[log_id] = updated_log
                
                # Save updated log file
                with open(log_path, 'w') as f:
                    json.dump(updated_log, f, indent=2)
            
            # Update the result file with the processed log data
            updated_result = update_result_file(result_path, log_updates)
            result_updates[run_id] = updated_result
        
        # Update the comparison file
        update_comparison_file(comparison_path, result_updates)

if __name__ == "__main__":
    process_files()