"""
Fix evolution pattern classification in result files

This script:
1. Finds all comparison files in the results directory
2. Updates pattern classifications to better represent oscillating patterns:
   - "Improvement" → Stays "Improvement" only when final answer is correct
   - "Improvement" with incorrect final answer → "Mixed Pattern (Final Incorrect)"
   - "Deterioration" → Stays "Deterioration" only when final answer is incorrect
   - "Deterioration" with correct final answer → "Mixed Pattern (Final Correct)"
3. Updates both comparison files and individual result files
"""

import json
import os
import glob
from datetime import datetime
import re

def fix_evolution_pattern(file_path, backup=True):
    """Fix evolution pattern classification in a file"""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return False
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {file_path}")
        return False
    
    changes_made = False
    is_comparison = "strategies" in data and "questions" in data
    
    # Handle comparison files
    if is_comparison:
        for question_id, question_data in data["questions"].items():
            for strategy, strategy_data in question_data.items():
                # Fix simulated approach
                if "simulated" in strategy_data and "evolution" in strategy_data["simulated"]:
                    pattern = strategy_data["simulated"]["evolution"].get("correctness_pattern", "")
                    is_correct = strategy_data["simulated"].get("correct", False)
                    
                    # Update pattern if needed
                    if pattern == "Improvement" and not is_correct:
                        strategy_data["simulated"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                        changes_made = True
                        print(f"  Updated: Question {question_id}, Strategy {strategy}, Simulated: Improvement → Mixed Pattern (Final Incorrect)")
                    elif pattern == "Deterioration" and is_correct:
                        strategy_data["simulated"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                        changes_made = True
                        print(f"  Updated: Question {question_id}, Strategy {strategy}, Simulated: Deterioration → Mixed Pattern (Final Correct)")
                
                # Fix dual approach
                if "dual" in strategy_data and "evolution" in strategy_data["dual"]:
                    pattern = strategy_data["dual"]["evolution"].get("correctness_pattern", "")
                    is_correct = strategy_data["dual"].get("correct", False)
                    
                    # Update pattern if needed
                    if pattern == "Improvement" and not is_correct:
                        strategy_data["dual"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                        changes_made = True
                        print(f"  Updated: Question {question_id}, Strategy {strategy}, Dual: Improvement → Mixed Pattern (Final Incorrect)")
                    elif pattern == "Deterioration" and is_correct:
                        strategy_data["dual"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                        changes_made = True
                        print(f"  Updated: Question {question_id}, Strategy {strategy}, Dual: Deterioration → Mixed Pattern (Final Correct)")
        
        # Fix evolution summary if present
        for strategy, strategy_data in data.get("strategies", {}).items():
            if "evolution_summary" in strategy_data:
                summary = strategy_data["evolution_summary"]
                
                # Update correctness counts
                counts = summary.get("correctness_counts", {})
                
                # Add new pattern categories if they don't exist
                if "Mixed Pattern (Final Correct)" not in counts:
                    counts["Mixed Pattern (Final Correct)"] = 0
                if "Mixed Pattern (Final Incorrect)" not in counts:
                    counts["Mixed Pattern (Final Incorrect)"] = 0
                
                # Update simulated counts
                sim_counts = summary.get("simulated", {}).get("correctness", {})
                if "Mixed Pattern (Final Correct)" not in sim_counts:
                    sim_counts["Mixed Pattern (Final Correct)"] = 0
                if "Mixed Pattern (Final Incorrect)" not in sim_counts:
                    sim_counts["Mixed Pattern (Final Incorrect)"] = 0
                
                # Update dual counts
                dual_counts = summary.get("dual", {}).get("correctness", {})
                if "Mixed Pattern (Final Correct)" not in dual_counts:
                    dual_counts["Mixed Pattern (Final Correct)"] = 0
                if "Mixed Pattern (Final Incorrect)" not in dual_counts:
                    dual_counts["Mixed Pattern (Final Incorrect)"] = 0
                
                changes_made = True
    
    # Handle individual result files
    elif "results" in data:
        for result in data["results"]:
            # Fix simulated evolution
            if "simulated" in result and "evolution" in result["simulated"]:
                pattern = result["simulated"]["evolution"].get("correctness_pattern", "")
                is_correct = result["simulated"].get("correct", False)
                
                # Update pattern if needed
                if pattern == "Improvement" and not is_correct:
                    result["simulated"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                    changes_made = True
                    print(f"  Updated: Question {result.get('question_id')}, Simulated: Improvement → Mixed Pattern (Final Incorrect)")
                elif pattern == "Deterioration" and is_correct:
                    result["simulated"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                    changes_made = True
                    print(f"  Updated: Question {result.get('question_id')}, Simulated: Deterioration → Mixed Pattern (Final Correct)")
            
            # Fix dual evolution
            if "dual" in result and "evolution" in result["dual"]:
                pattern = result["dual"]["evolution"].get("correctness_pattern", "")
                is_correct = result["dual"].get("correct", False)
                
                # Update pattern if needed
                if pattern == "Improvement" and not is_correct:
                    result["dual"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                    changes_made = True
                    print(f"  Updated: Question {result.get('question_id')}, Dual: Improvement → Mixed Pattern (Final Incorrect)")
                elif pattern == "Deterioration" and is_correct:
                    result["dual"]["evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                    changes_made = True
                    print(f"  Updated: Question {result.get('question_id')}, Dual: Deterioration → Mixed Pattern (Final Correct)")
        
        # Fix evolution summary if present
        if "evolution_summary" in data:
            summary = data["evolution_summary"]
            
            # Update correctness counts
            counts = summary.get("correctness_counts", {})
            
            # Add new pattern categories if they don't exist
            if "Mixed Pattern (Final Correct)" not in counts:
                counts["Mixed Pattern (Final Correct)"] = 0
            if "Mixed Pattern (Final Incorrect)" not in counts:
                counts["Mixed Pattern (Final Incorrect)"] = 0
            
            # Update simulated counts
            sim_counts = summary.get("simulated", {}).get("correctness", {})
            if "Mixed Pattern (Final Correct)" not in sim_counts:
                sim_counts["Mixed Pattern (Final Correct)"] = 0
            if "Mixed Pattern (Final Incorrect)" not in sim_counts:
                sim_counts["Mixed Pattern (Final Incorrect)"] = 0
            
            # Update dual counts
            dual_counts = summary.get("dual", {}).get("correctness", {})
            if "Mixed Pattern (Final Correct)" not in dual_counts:
                dual_counts["Mixed Pattern (Final Correct)"] = 0
            if "Mixed Pattern (Final Incorrect)" not in dual_counts:
                dual_counts["Mixed Pattern (Final Incorrect)"] = 0
            
            changes_made = True
    
    # Handle log files
    elif ("simulated_messages" in data or "dual_messages" in data) and (
          "simulated_evolution" in data or "dual_evolution" in data):
        
        # Fix simulated evolution
        if "simulated_evolution" in data:
            pattern = data["simulated_evolution"].get("correctness_pattern", "")
            
            # Determine correctness from answer_history
            answer_history = data["simulated_evolution"].get("answer_history", [])
            final_correct = False
            if answer_history:
                final_correct = answer_history[-1].get("is_correct", False)
            
            # Update pattern if needed
            if pattern == "Improvement" and not final_correct:
                data["simulated_evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                changes_made = True
                print(f"  Updated: Log, Simulated: Improvement → Mixed Pattern (Final Incorrect)")
            elif pattern == "Deterioration" and final_correct:
                data["simulated_evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                changes_made = True
                print(f"  Updated: Log, Simulated: Deterioration → Mixed Pattern (Final Correct)")
        
        # Fix dual evolution
        if "dual_evolution" in data:
            pattern = data["dual_evolution"].get("correctness_pattern", "")
            
            # Determine correctness from answer_history
            answer_history = data["dual_evolution"].get("answer_history", [])
            final_correct = False
            if answer_history:
                final_correct = answer_history[-1].get("is_correct", False)
            
            # Update pattern if needed
            if pattern == "Improvement" and not final_correct:
                data["dual_evolution"]["correctness_pattern"] = "Mixed Pattern (Final Incorrect)"
                changes_made = True
                print(f"  Updated: Log, Dual: Improvement → Mixed Pattern (Final Incorrect)")
            elif pattern == "Deterioration" and final_correct:
                data["dual_evolution"]["correctness_pattern"] = "Mixed Pattern (Final Correct)"
                changes_made = True
                print(f"  Updated: Log, Dual: Deterioration → Mixed Pattern (Final Correct)")
    
    # Save changes if needed
    if changes_made:
        if backup:
            # Create backup
            backup_dir = os.path.join(os.path.dirname(file_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, f"{filename}.bak")
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  Backup saved to: {backup_path}")
        
        # Save updated file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Changes saved to: {file_path}")

    
    return changes_made

def update_evolution_category_counts(file_path):
    """Update the category counts in the evolution summary"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except:
        print(f"Error loading file: {file_path}")
        return False
    
    changes_made = False
    
    # Determine file type
    is_comparison = "strategies" in data and "questions" in data
    
    if is_comparison:
        # Recount patterns from questions
        for strategy_id, strategy_data in data["strategies"].items():
            if "evolution_summary" not in strategy_data:
                continue
                
            # Initialize counters
            correctness_counts = {
                # Correct patterns first
                "Stable Correct": 0,
                "Stable Correct (One Agent)": 0,
                "Improvement": 0,
                "Mixed Pattern (Final Correct)": 0,
                
                # Incorrect patterns next
                "Stable Incorrect": 0,
                "Deterioration": 0, 
                "Mixed Pattern (Final Incorrect)": 0,
                "Mixed Pattern": 0,
                
                # Other
                "Insufficient Data": 0
            }
            
            sim_correctness = correctness_counts.copy()
            dual_correctness = correctness_counts.copy()
            
            # Count patterns from questions
            for question_id, question_data in data["questions"].items():
                if strategy_id not in question_data:
                    continue
                
                strategy_question = question_data[strategy_id]
                
                # Count simulated patterns
                if "simulated" in strategy_question and "evolution" in strategy_question["simulated"]:
                    pattern = strategy_question["simulated"]["evolution"].get("correctness_pattern", "")
                    if pattern in sim_correctness:
                        sim_correctness[pattern] += 1
                        correctness_counts[pattern] += 1
                
                # Count dual patterns
                if "dual" in strategy_question and "evolution" in strategy_question["dual"]:
                    pattern = strategy_question["dual"]["evolution"].get("correctness_pattern", "")
                    if pattern in dual_correctness:
                        dual_correctness[pattern] += 1
                        correctness_counts[pattern] += 1
            
            # Update evolution summary
            strategy_data["evolution_summary"]["correctness_counts"] = correctness_counts
            strategy_data["evolution_summary"]["simulated"]["correctness"] = sim_correctness
            strategy_data["evolution_summary"]["dual"]["correctness"] = dual_correctness
            
            changes_made = True
    
    elif "results" in data and "evolution_summary" in data:
        # Recount patterns from results
        correctness_counts = {
            # Correct patterns first
            "Stable Correct": 0,
            "Stable Correct (One Agent)": 0,
            "Improvement": 0,
            "Mixed Pattern (Final Correct)": 0,
            
            # Incorrect patterns next
            "Stable Incorrect": 0,
            "Deterioration": 0, 
            "Mixed Pattern (Final Incorrect)": 0,
            "Mixed Pattern": 0,
            
            # Other
            "Insufficient Data": 0
        }
        
        sim_correctness = correctness_counts.copy()
        dual_correctness = correctness_counts.copy()
        
        # Count patterns from results
        for result in data["results"]:
            # Count simulated patterns
            if "simulated" in result and "evolution" in result["simulated"]:
                pattern = result["simulated"]["evolution"].get("correctness_pattern", "")
                if pattern in sim_correctness:
                    sim_correctness[pattern] += 1
                    correctness_counts[pattern] += 1
            
            # Count dual patterns
            if "dual" in result and "evolution" in result["dual"]:
                pattern = result["dual"]["evolution"].get("correctness_pattern", "")
                if pattern in dual_correctness:
                    dual_correctness[pattern] += 1
                    correctness_counts[pattern] += 1
        
        # Update evolution summary
        data["evolution_summary"]["correctness_counts"] = correctness_counts
        data["evolution_summary"]["simulated"]["correctness"] = sim_correctness
        data["evolution_summary"]["dual"]["correctness"] = dual_correctness
        
        changes_made = True
    
    # Save changes if needed
    if changes_made:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Updated counts in: {file_path}")
    
    return changes_made

def process_files(results_dir="./results", backup=True):
    """Process all result files in the directory"""
    # Find all comparison files
    comparison_pattern = os.path.join(results_dir, "comparison_*.json")
    comparison_files = glob.glob(comparison_pattern)
    
    # Find all result files
    result_pattern = os.path.join(results_dir, "result_*.json")
    result_files = glob.glob(result_pattern)
    
    # Find all log files
    log_pattern = os.path.join(results_dir, "log_*.json")
    log_files = glob.glob(log_pattern)
    
    # Process comparison files first
    print(f"\nProcessing {len(comparison_files)} comparison files...")
    comparison_changes = 0
    for file_path in comparison_files:
        if fix_evolution_pattern(file_path, backup):
            comparison_changes += 1
    
    # Process result files
    print(f"\nProcessing {len(result_files)} result files...")
    result_changes = 0
    for file_path in result_files:
        if fix_evolution_pattern(file_path, backup):
            result_changes += 1
    
    # Process log files
    print(f"\nProcessing {len(log_files)} log files...")
    log_changes = 0
    for file_path in log_files:
        if fix_evolution_pattern(file_path, backup):
            log_changes += 1
    
    # Update counts
    print("\nUpdating evolution category counts...")
    count_changes = 0
    for file_path in comparison_files:
        if update_evolution_category_counts(file_path):
            count_changes += 1
    
    for file_path in result_files:
        if update_evolution_category_counts(file_path):
            count_changes += 1
    
    # Print summary
    print("\n--- Summary ---")
    print(f"Comparison files updated: {comparison_changes}/{len(comparison_files)}")
    print(f"Result files updated: {result_changes}/{len(result_files)}")
    print(f"Log files updated: {log_changes}/{len(log_files)}")
    print(f"Files with updated counts: {count_changes}")
    
    return comparison_changes + result_changes + log_changes

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix evolution pattern classification in result files")
    parser.add_argument("--results-dir", type=str, default="./results", 
                        help="Directory containing result files")
    parser.add_argument("--no-backup", action="store_true", 
                        help="Skip creating backups of modified files")
    parser.add_argument("--specific-files", nargs="+", type=str, 
                        help="Process only specific files instead of all files in the directory")
    
    args = parser.parse_args()
    
    if args.specific_files:
        print(f"Processing {len(args.specific_files)} specific files...")
        changes = 0
        for file_path in args.specific_files:
            if fix_evolution_pattern(file_path, not args.no_backup):
                changes += 1
                update_evolution_category_counts(file_path)
        print(f"\nTotal files updated: {changes}/{len(args.specific_files)}")
    else:
        process_files(args.results_dir, not args.no_backup)

if __name__ == "__main__":
    main()