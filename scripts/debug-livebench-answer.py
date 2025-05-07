"""
Debug script to examine why the answer extraction isn't working for a specific question.
This script focuses only on the LiveBench comparison file from 1746486625 and
examines question 1b317054fbe9c5448203b80b37b98eee6bf845143de64477ba2b8d6172168652.
"""

import json
import os
import re
import glob

def debug_question(comparison_file, question_id):
    """Debug the answer extraction for a specific question"""
    print(f"Debugging question {question_id} in {comparison_file}")
    
    try:
        # Load the comparison file
        with open(comparison_file, 'r') as f:
            comparison_data = json.load(f)
        
        # Check if the question exists
        if question_id not in comparison_data.get("questions", {}):
            print(f"Question {question_id} not found in comparison file")
            
            # Try to find similar questions
            similar_ids = []
            for q_id in comparison_data.get("questions", {}).keys():
                if question_id in q_id or q_id in question_id:
                    similar_ids.append(q_id)
            
            if similar_ids:
                print(f"Found similar question IDs: {similar_ids}")
                question_id = similar_ids[0]
                print(f"Using question {question_id} instead")
            else:
                # List all question IDs
                all_ids = list(comparison_data.get("questions", {}).keys())
                print(f"Available question IDs: {all_ids[:5]}...")
                return
        
        # Get the question data
        question_data = comparison_data["questions"][question_id]
        
        # Examine each strategy
        for strategy, strategy_data in question_data.items():
            print(f"\nStrategy: {strategy}")
            
            # Check simulated approach
            if "simulated" in strategy_data:
                sim_data = strategy_data["simulated"]
                print(f"  Simulated answer: {sim_data.get('answer', 'None')}")
                print(f"  Simulated correct: {sim_data.get('correct', False)}")
                
                # Check evolution if available
                if "evolution" in sim_data:
                    evolution = sim_data["evolution"]
                    print(f"  Agreement pattern: {evolution.get('agreement_pattern', 'N/A')}")
                    print(f"  Correctness pattern: {evolution.get('correctness_pattern', 'N/A')}")
                    
                    # Print answer history
                    answer_history = evolution.get("answer_history", [])
                    if answer_history:
                        print("\n  Answer history:")
                        for idx, entry in enumerate(answer_history):
                            correct = "✓" if entry.get("is_correct", False) else "✗"
                            print(f"    {idx+1}. {entry.get('agent', 'Unknown')}: {entry.get('answer', 'None')} - {correct}")
            
            # Check dual approach
            if "dual" in strategy_data:
                dual_data = strategy_data["dual"]
                print(f"\n  Dual answer: {dual_data.get('answer', 'None')}")
                print(f"  Dual correct: {dual_data.get('correct', False)}")
                
                # Check evolution if available
                if "evolution" in dual_data:
                    evolution = dual_data["evolution"]
                    print(f"  Agreement pattern: {evolution.get('agreement_pattern', 'N/A')}")
                    print(f"  Correctness pattern: {evolution.get('correctness_pattern', 'N/A')}")
                    
                    # Print answer history
                    answer_history = evolution.get("answer_history", [])
                    if answer_history:
                        print("\n  Answer history:")
                        for idx, entry in enumerate(answer_history):
                            correct = "✓" if entry.get("is_correct", False) else "✗"
                            print(f"    {idx+1}. {entry.get('agent', 'Unknown')}: {entry.get('answer', 'None')} - {correct}")
        
        # Find the result files that contain this question
        run_ids = []
        for strategy, strategy_data in comparison_data.get("strategies", {}).items():
            run_id = strategy_data.get("run_id")
            if run_id:
                run_ids.append(run_id)
        
        if run_ids:
            print("\nExamining result files:")
            
            for run_id in run_ids:
                result_file = os.path.join(os.path.dirname(comparison_file), f"result_{run_id}.json")
                if os.path.exists(result_file):
                    print(f"\nChecking result file: {result_file}")
                    
                    try:
                        with open(result_file, 'r') as f:
                            result_data = json.load(f)
                        
                        # Find the question in results
                        found = False
                        for idx, result in enumerate(result_data.get("results", [])):
                            result_question_id = str(result.get("question_id", ""))
                            
                            if result_question_id == question_id:
                                found = True
                                print(f"  Found question at index {idx}")
                                
                                # Get the ground truth
                                ground_truth = result.get("ground_truth", "")
                                print(f"  Ground truth: {ground_truth}")
                                
                                # Check simulated data
                                if "simulated" in result:
                                    print(f"  Simulated answer: {result['simulated'].get('answer', 'None')}")
                                
                                # Check dual data
                                if "dual" in result:
                                    print(f"  Dual answer: {result['dual'].get('answer', 'None')}")
                                
                                # Check if we have message data
                                if "simulated_messages" in result:
                                    print("\nExamining simulated messages:")
                                    messages = result["simulated_messages"]
                                    
                                    # Look for Final Answer patterns in all messages
                                    for msg_idx, msg in enumerate(messages):
                                        if "role" not in msg or msg["role"] in ["user", "system"]:
                                            continue
                                        
                                        content = msg.get("content", "")
                                        
                                        # Check for any Final Answer or Answer patterns
                                        final_match = re.search(r'Final Answer:\s*([^\n]+)', content, re.IGNORECASE)
                                        answer_match = re.search(r'(?<!Final )Answer:\s*([^\n]+)', content, re.IGNORECASE)
                                        
                                        if final_match:
                                            print(f"    Message {msg_idx}: Found 'Final Answer: {final_match.group(1).strip()}'")
                                        
                                        if answer_match:
                                            print(f"    Message {msg_idx}: Found 'Answer: {answer_match.group(1).strip()}'")
                                        
                                        # Also check for solution tags
                                        solution_match = re.search(r'<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
                                        if solution_match:
                                            print(f"    Message {msg_idx}: Found solution tag: {solution_match.group(1).strip()}")
                                        
                                        # Check for bold text
                                        bold_matches = re.findall(r'\*\*([\w\s,]+)\*\*', content, re.IGNORECASE)
                                        if bold_matches:
                                            for bold in bold_matches:
                                                print(f"    Message {msg_idx}: Found bold text: {bold.strip()}")
                                
                                if "dual_messages" in result:
                                    print("\nExamining dual messages:")
                                    messages = result["dual_messages"]
                                    
                                    # Look for Final Answer patterns in all messages
                                    for msg_idx, msg in enumerate(messages):
                                        if "role" not in msg or msg["role"] in ["user", "system"]:
                                            continue
                                        
                                        content = msg.get("content", "")
                                        
                                        # Check for any Final Answer or Answer patterns
                                        final_match = re.search(r'Final Answer:\s*([^\n]+)', content, re.IGNORECASE)
                                        answer_match = re.search(r'(?<!Final )Answer:\s*([^\n]+)', content, re.IGNORECASE)
                                        
                                        if final_match:
                                            print(f"    Message {msg_idx}: Found 'Final Answer: {final_match.group(1).strip()}'")
                                        
                                        if answer_match:
                                            print(f"    Message {msg_idx}: Found 'Answer: {answer_match.group(1).strip()}'")
                                        
                                        # Also check for solution tags
                                        solution_match = re.search(r'<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
                                        if solution_match:
                                            print(f"    Message {msg_idx}: Found solution tag: {solution_match.group(1).strip()}")
                                        
                                        # Check for bold text
                                        bold_matches = re.findall(r'\*\*([\w\s,]+)\*\*', content, re.IGNORECASE)
                                        if bold_matches:
                                            for bold in bold_matches:
                                                print(f"    Message {msg_idx}: Found bold text: {bold.strip()}")
                                
                                break
                        
                        if not found:
                            print(f"  Question {question_id} not found in result file")
                    
                    except Exception as e:
                        print(f"  Error examining result file: {e}")
                else:
                    print(f"  Result file not found: {result_file}")
    
    except Exception as e:
        print(f"Error debugging question: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug LiveBench answer extraction for a specific question")
    parser.add_argument("--comparison-file", type=str, default="../results/comparison_livebench_1746486625.json",
                        help="Path to the comparison file")
    parser.add_argument("--question-id", type=str, default="1b317054fbe9c5448203b80b37b98eee6bf845143de64477ba2b8d6172168652",
                        help="ID of the question to debug")
    
    args = parser.parse_args()
    
    debug_question(args.comparison_file, args.question_id)

if __name__ == "__main__":
    main()