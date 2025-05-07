import json
import os
import re
from transformers import AutoTokenizer
import glob
from typing import Dict, List, Any, Optional

# Initialize DeepSeek tokenizer for proper token counting
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-V3")

def extract_proper_answer(content: str) -> Optional[str]:
    """
    Extract the proper answer from message content, handling various formats from LiveBench.
    
    Args:
        content: Message content
    
    Returns:
        Extracted answer or None if not found
    """
    # Look for <solution>...</solution> format after "Final Answer" or "Answer"
    final_solution_match = re.search(r'final answer:\s+<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if final_solution_match:
        return final_solution_match.group(1).strip()
    
    solution_match = re.search(r'answer:\s+<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if solution_match:
        return solution_match.group(1).strip()
    
    # General <solution> tag anywhere
    general_solution_match = re.search(r'<solution>(.*?)</solution>', content, re.IGNORECASE | re.DOTALL)
    if general_solution_match:
        return general_solution_match.group(1).strip()
    
    # Final Answer with bold (support 2-5 asterisks)
    final_bold_match = re.search(r'final answer:\s+\*{2,5}(.*?)\*{2,5}', content, re.IGNORECASE)
    if final_bold_match:
        return final_bold_match.group(1).strip()
        
    # Answer with bold (support 2-5 asterisks)
    bold_match = re.search(r'answer:\s+\*{2,5}(.*?)\*{2,5}', content, re.IGNORECASE)
    if bold_match:
        return bold_match.group(1).strip()
    
    # Final Answer without formatting
    final_plain_match = re.search(r'final answer:\s+([\w\d\s,.;]+)', content, re.IGNORECASE)
    if final_plain_match:
        return final_plain_match.group(1).strip()
    
    # Answer without formatting
    plain_match = re.search(r'answer:\s+([\w\d\s,.;]+)', content, re.IGNORECASE)
    if plain_match:
        # Make sure this is actually the answer, not just a mention of "answer"
        answer_text = plain_match.group(1).strip()
        # Only accept if it's reasonably short and looks like an answer
        if len(answer_text.split()) <= 15:
            return answer_text
    
    # Handle numbered/comma-separated answers in solution-like format
    # This catches answers like "1, 2, 3, 4" or "yes, no, yes"
    list_pattern_match = re.search(r'answer:\s+((?:[\w-]+(?:,\s*[\w-]+)+))', content, re.IGNORECASE)
    if list_pattern_match:
        return list_pattern_match.group(1).strip()
    
    return None

def detect_convergence(messages: List[Dict[str, Any]]) -> bool:
    """
    Detect if there's convergence in answers from consecutive messages.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        True if convergence detected, False otherwise
    """
    # Need at least 2 consecutive answers to detect convergence
    if len(messages) < 2:
        return False
    
    # Get last 2 agent answers (skipping user/system messages)
    agent_messages = [msg for msg in messages if msg.get("role") == "assistant"]
    if len(agent_messages) < 2:
        return False
    
    last_two = agent_messages[-2:]
    
    # Extract answers from the last 2 agent messages
    answers = []
    for msg in last_two:
        answer = extract_proper_answer(msg.get("content", ""))
        if answer:
            answers.append(answer)
    
    # Check if we have 2 consecutive answers that match
    return len(answers) == 2 and answers[0] == answers[1]

def recount_tokens(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Recount tokens for a list of messages.
    
    Args:
        messages: List of message dictionaries
    
    Returns:
        Dictionary with token counts (prompt, completion, total)
    """
    prompt_tokens = 0
    completion_tokens = 0
    
    for msg in messages:
        content = msg.get("content", "")
        role = msg.get("role", "")
        
        # Count tokens
        token_count = len(tokenizer.encode(content))
        
        if role == "assistant":
            completion_tokens += token_count
        else:
            prompt_tokens += token_count
    
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    }

def process_log_file(log_path: str) -> Dict[str, Any]:
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    benchmark_name = log_data.get("benchmark", "")
    # Instantiate the correct benchmark object
    if benchmark_name.lower() == "livebench":
        from evaluation.benchmarks.livebench_benchmark import LiveBenchReasoningBenchmark
        benchmark_obj = LiveBenchReasoningBenchmark()
    
    # Process simulated messages
    simulated_messages = log_data.get("simulated_messages", [])
    truncated_sim_messages = []
    convergence_idx = None
    for i, msg in enumerate(simulated_messages):
        truncated_sim_messages.append(msg)
        # Only check for convergence after adding an assistant message
        if msg.get("role") == "assistant" and convergence_idx is None and detect_convergence(truncated_sim_messages):
            # Find the index of the last assistant message in truncated_sim_messages
            last_assistant_idx = None
            for j in range(len(truncated_sim_messages)-1, -1, -1):
                if truncated_sim_messages[j].get("role") == "assistant":
                    last_assistant_idx = j
                    break
            # Now, find the corresponding index in the full message list
            assistant_count = 0
            for k, m in enumerate(simulated_messages):
                if m.get("role") == "assistant":
                    if assistant_count == last_assistant_idx:
                        convergence_idx = k
                        break
                    assistant_count += 1
    if convergence_idx is not None:
        truncated_sim_messages = simulated_messages[:convergence_idx+1]
        truncated_sim_messages.append({
            "role": "system",
            "agent": "System",
            "content": f"(Interaction concluded early due to convergence on answer: {extract_proper_answer(simulated_messages[convergence_idx].get('content', ''))})"
        })

    # Process dual messages with robust convergence logic
    dual_messages = log_data.get("dual_messages", [])
    truncated_dual_messages = []
    convergence_idx = None
    for i, msg in enumerate(dual_messages):
        truncated_dual_messages.append(msg)
        # Only check for convergence after adding an assistant message
        if msg.get("role") == "assistant" and convergence_idx is None and detect_convergence(truncated_dual_messages):
            # Find the index of the last assistant message in truncated_dual_messages
            last_assistant_idx = None
            for j in range(len(truncated_dual_messages)-1, -1, -1):
                if truncated_dual_messages[j].get("role") == "assistant":
                    last_assistant_idx = j
                    break
            # Now, find the corresponding index in the full message list
            assistant_count = 0
            for k, m in enumerate(dual_messages):
                if m.get("role") == "assistant":
                    if assistant_count == last_assistant_idx:
                        convergence_idx = k
                        break
                    assistant_count += 1
    if convergence_idx is not None:
        truncated_dual_messages = dual_messages[:convergence_idx+1]
        truncated_dual_messages.append({
            "role": "system",
            "agent": "System",
            "content": f"(Debate concluded early due to convergence on answer: {extract_proper_answer(dual_messages[convergence_idx].get('content', ''))})"
        })

    # Recount tokens
    simulated_tokens = recount_tokens(truncated_sim_messages)
    dual_tokens = recount_tokens(truncated_dual_messages)
    
    # Extract final answers
    sim_answer = None
    dual_answer = None
    
    # Find the last non-system message for simulated and extract answer
    for msg in reversed(truncated_sim_messages):
        if msg.get("role") != "system" and msg.get("role") != "user":
            sim_answer = extract_proper_answer(msg.get("content", ""))
            break
    
    # Find the last non-system message for dual and extract answer
    for msg in reversed(truncated_dual_messages):
        if msg.get("role") != "system" and msg.get("role") != "user":
            dual_answer = extract_proper_answer(msg.get("content", ""))
            break
    
    # Analyze solution evolution
    from evaluation.solution_evolution import analyze_solution_evolution
    
    ground_truth = log_data.get("ground_truth", "")
    
    sim_evolution = analyze_solution_evolution(truncated_sim_messages, ground_truth, benchmark_obj)
    dual_evolution = analyze_solution_evolution(truncated_dual_messages, ground_truth, benchmark_obj)
    
    # Update log data
    updated_log = {
        **log_data,
        "simulated_messages": truncated_sim_messages,
        "dual_messages": truncated_dual_messages,
        "simulated_final_answer": sim_answer,
        "dual_final_answer": dual_answer,
        "simulated_tokens": simulated_tokens,
        "dual_tokens": dual_tokens,
        "simulated_evolution": sim_evolution,
        "dual_evolution": dual_evolution
    }
    
    return updated_log

def update_result_file(result_path: str, log_updates: Dict[str, Dict[str, Any]]):
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    # Update each result
    for i, result in enumerate(result_data.get("results", [])):
        log_id = result.get("simulated", {}).get("log_id")
        if log_id in log_updates:
            log_update = log_updates[log_id]
            
            # Update answers
            result["simulated"]["answer"] = log_update.get("simulated_final_answer", "No final answer found.")
            result["dual"]["answer"] = log_update.get("dual_final_answer", "No final answer found.")
            
            # Evaluate correctness
            ground_truth = result.get("ground_truth", "")
            result["simulated"]["correct"] = (result["simulated"]["answer"] == ground_truth)
            result["dual"]["correct"] = (result["dual"]["answer"] == ground_truth)
            
            # Update token counts
            result["simulated"]["tokens"] = log_update.get("simulated_tokens", {})
            result["dual"]["tokens"] = log_update.get("dual_tokens", {})
            
            # Update evolution data
            result["simulated"]["evolution"] = log_update.get("simulated_evolution", {})
            result["dual"]["evolution"] = log_update.get("dual_evolution", {})
    
    # Recalculate summary metrics
    total_questions = len(result_data.get("results", []))
    simulated_correct = sum(1 for r in result_data.get("results", []) if r.get("simulated", {}).get("correct", False))
    dual_correct = sum(1 for r in result_data.get("results", []) if r.get("dual", {}).get("correct", False))
    
    # Calculate token metrics
    simulated_prompt_tokens = sum(r.get("simulated", {}).get("tokens", {}).get("prompt_tokens", 0) for r in result_data.get("results", []))
    simulated_completion_tokens = sum(r.get("simulated", {}).get("tokens", {}).get("completion_tokens", 0) for r in result_data.get("results", []))
    dual_prompt_tokens = sum(r.get("dual", {}).get("tokens", {}).get("prompt_tokens", 0) for r in result_data.get("results", []))
    dual_completion_tokens = sum(r.get("dual", {}).get("tokens", {}).get("completion_tokens", 0) for r in result_data.get("results", []))
    
    # Update summary
    result_data["summary"] = {
        "total_questions": total_questions,
        "simulated_correct": simulated_correct,
        "dual_correct": dual_correct,
        "simulated_accuracy": simulated_correct / total_questions if total_questions > 0 else 0,
        "dual_accuracy": dual_correct / total_questions if total_questions > 0 else 0,
        "token_usage": {
            "simulated_tokens": simulated_prompt_tokens + simulated_completion_tokens,
            "dual_tokens": dual_prompt_tokens + dual_completion_tokens,
            "total_tokens": simulated_prompt_tokens + simulated_completion_tokens + dual_prompt_tokens + dual_completion_tokens
        },
        "completion_token_usage": {
            "simulated_completion_tokens": simulated_completion_tokens,
            "dual_completion_tokens": dual_completion_tokens,
            "total_completion_tokens": simulated_completion_tokens + dual_completion_tokens
        },
        "prompt_token_usage": {
            "simulated_prompt_tokens": simulated_prompt_tokens,
            "dual_prompt_tokens": dual_prompt_tokens,
            "total_prompt_tokens": simulated_prompt_tokens + dual_prompt_tokens
        }
    }
    print(f"Summary for {result_path}: {result_data['summary']}")  # Debug print
    
    # Try to update evolution summary if the module is available
    try:
        from evaluation.solution_evolution import get_analysis_summary
        result_data["evolution_summary"] = get_analysis_summary(result_data.get("results", []))
    except Exception as e:
        print(f"Error generating evolution summary: {e}")
    
    # Save updated result
    with open(result_path, 'w') as f:
        json.dump(result_data, f, indent=2)

def update_comparison_file(comparison_path: str, result_updates: Dict[str, Dict[str, Any]]):
    print(f"Updating comparison file: {comparison_path}")  # Debug print
    with open(comparison_path, 'r') as f:
        comparison_data = json.load(f)
    
    # Update each strategy's metrics
    for strategy_id, strategy_data in comparison_data.get("strategies", {}).items():
        run_id = strategy_data.get("run_id")
        if run_id in result_updates:
            result_update = result_updates[run_id]
            
            # Update summary
            strategy_data["summary"] = result_update.get("summary", {})
            
            # Update evolution summary if available
            if "evolution_summary" in result_update:
                strategy_data["evolution_summary"] = result_update.get("evolution_summary", {})
    
    # Update question-level details
    for question_id, question_data in comparison_data.get("questions", {}).items():
        for strategy_id, strategy_question_data in question_data.items():
            # Find the corresponding result
            for run_id, result_update in result_updates.items():
                if strategy_id in run_id:
                    for result in result_update.get("results", []):
                        if result.get("question_id") == question_id:
                            # Update simulated data
                            if "simulated" in strategy_question_data and "simulated" in result:
                                strategy_question_data["simulated"]["answer"] = result["simulated"]["answer"]
                                strategy_question_data["simulated"]["correct"] = result["simulated"]["correct"]
                                strategy_question_data["simulated"]["tokens"] = result["simulated"]["tokens"]
                                if "evolution" in result["simulated"]:
                                    strategy_question_data["simulated"]["evolution"] = result["simulated"]["evolution"]
                            
                            # Update dual data
                            if "dual" in strategy_question_data and "dual" in result:
                                strategy_question_data["dual"]["answer"] = result["dual"]["answer"]
                                strategy_question_data["dual"]["correct"] = result["dual"]["correct"]
                                strategy_question_data["dual"]["tokens"] = result["dual"]["tokens"]
                                if "evolution" in result["dual"]:
                                    strategy_question_data["dual"]["evolution"] = result["dual"]["evolution"]
    
    # Update token usage summaries
    comparison_data["token_usage"] = {}
    comparison_data["completion_token_usage"] = {}
    comparison_data["prompt_token_usage"] = {}
    
    total_tokens = 0
    total_completion_tokens = 0
    total_prompt_tokens = 0
    
    for strategy_id, strategy_data in comparison_data.get("strategies", {}).items():
        if "summary" in strategy_data and "token_usage" in strategy_data["summary"]:
            strategy_tokens = strategy_data["summary"]["token_usage"]["total_tokens"]
            comparison_data["token_usage"][strategy_id] = strategy_tokens
            total_tokens += strategy_tokens
        
        if "summary" in strategy_data and "completion_token_usage" in strategy_data["summary"]:
            strategy_completion_tokens = strategy_data["summary"]["completion_token_usage"]["total_completion_tokens"]
            comparison_data["completion_token_usage"][strategy_id] = strategy_completion_tokens
            total_completion_tokens += strategy_completion_tokens
        
        if "summary" in strategy_data and "prompt_token_usage" in strategy_data["summary"]:
            strategy_prompt_tokens = strategy_data["summary"]["prompt_token_usage"]["total_prompt_tokens"]
            comparison_data["prompt_token_usage"][strategy_id] = strategy_prompt_tokens
            total_prompt_tokens += strategy_prompt_tokens
    
    comparison_data["token_usage"]["total"] = total_tokens
    comparison_data["completion_token_usage"]["total"] = total_completion_tokens
    comparison_data["prompt_token_usage"]["total"] = total_prompt_tokens
    print(f"Token usage summary for {comparison_path}: {comparison_data['token_usage']}")  # Debug print
    
    # Save updated comparison
    with open(comparison_path, 'w') as f:
        json.dump(comparison_data, f, indent=2)

def main():
    # Paths
    results_dir = "./results"
    comparison_path = os.path.join(results_dir, "comparison_livebench_1746486625.json")
    if not os.path.exists(comparison_path):
        print(f"Comparison file not found: {comparison_path}")
        return
    print(f"Found comparison file: {comparison_path}")  # Debug print

    # Read comparison file and extract run_ids
    with open(comparison_path, 'r') as f:
        comparison_data = json.load(f)
    strategies = comparison_data.get("strategies", {})
    run_ids = []
    for strat in strategies.values():
        run_id = strat.get("run_id")
        if run_id:
            run_ids.append(run_id)
    print(f"Found run_ids: {run_ids}")  # Debug print

    # For each run_id, process the corresponding result file
    result_updates = {}
    all_log_updates = {}
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
            dual_log_id = result.get("dual", {}).get("log_id")
            if sim_log_id:
                log_ids.add(sim_log_id)
            if dual_log_id:
                log_ids.add(dual_log_id)
        print(f"  Found log_ids: {list(log_ids)[:5]}... (total {len(log_ids)})")  # Debug print
        # Process each log file
        log_updates = {}
        for log_id in log_ids:
            log_path = os.path.join(results_dir, f"log_{log_id}.json")
            if not os.path.exists(log_path):
                print(f"    Log file not found: {log_path}")
                continue
            log_updates[log_id] = process_log_file(log_path)
            all_log_updates[log_id] = log_updates[log_id]
        # Update the result file with the processed log data
        update_result_file(result_path, log_updates)
        # Reload the updated result file for updating the comparison file
        with open(result_path, 'r') as f:
            result_updates[run_id] = json.load(f)

    # Update the comparison file as before
    update_comparison_file(comparison_path, result_updates)

if __name__ == "__main__":
    main()


