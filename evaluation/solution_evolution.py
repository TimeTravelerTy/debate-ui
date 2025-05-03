"""
Solution Evolution Analysis

This module provides functions to analyze how solutions evolve throughout agent dialogues,
examining both agreement between agents and correctness of answers.

The analysis tracks two key dimensions:

1. Agreement dimension:
   - Complete Agreement: Agents consistently reach consensus from the start
   - Resolved Disagreement: Agents converge after initial disagreement
   - Unresolved Disagreement: Disagreement persists to the final answer

2. Correctness dimension:
   - Stable Correct: Correct answer maintained by both agents throughout
   - Stable Incorrect: Incorrect answers throughout
   - Stable Correct (One Agent): One agent consistently maintains the correct answer
   - Improvement: Progression toward correct answer
   - Deterioration: Regression from correct to incorrect
   - Mixed Pattern: Complex patterns that don't fit other categories
"""

from typing import List, Dict, Any, Optional


def analyze_solution_evolution(messages: List[Dict[str, Any]], ground_truth: str, benchmark) -> Dict[str, Any]:
    """
    Analyze how the solution evolves throughout an agent dialogue.
    
    Args:
        messages: List of message dictionaries from the conversation
        ground_truth: The ground truth answer
        benchmark: Benchmark object with evaluate_answer method
        
    Returns:
        Dictionary with evolution analysis results
    """
    from agent.utils import extract_answer
    
    # Track answers by agent in order of appearance
    answer_history = []
    
    # Extract final answers from each message
    current_turn = 0
    for msg in messages:
        # Skip user and system messages
        if isinstance(msg, dict) and (msg.get("role") == "user" or msg.get("role") == "system"):
            continue
            
        # Get agent - handle different message formats
        agent = None
        if isinstance(msg, dict):
            # Try different possible keys for agent identification
            agent = msg.get("agent")
            if not agent and msg.get("role") == "assistant":
                # For simulated debates, extract agent from content
                content = msg.get("content", "")
                if content.startswith("Agent A:"):
                    agent = "Agent A"
                elif content.startswith("Agent B:"):
                    agent = "Agent B"
            
        if not agent or agent not in ["Agent A", "Agent B"]:
            continue
            
        # Get content - handle different message formats
        content = ""
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if agent == "Agent A" and content.startswith("Agent A:"):
                content = content[len("Agent A:"):].strip()
            elif agent == "Agent B" and content.startswith("Agent B:"):
                content = content[len("Agent B:"):].strip()
            
        answer = extract_answer(content)
        
        if answer:
            is_correct = benchmark.evaluate_answer(answer, ground_truth)
            answer_history.append({
                "turn": current_turn,
                "agent": agent,
                "answer": answer,
                "is_correct": is_correct
            })
            current_turn += 1
    
    # Determine agreement pattern
    agreement_pattern = determine_agreement_pattern(answer_history)
    
    # Determine correctness pattern
    correctness_pattern = determine_correctness_pattern(answer_history)
    
    return {
        "agreement_pattern": agreement_pattern,
        "correctness_pattern": correctness_pattern,
        "answer_history": answer_history
    }


def determine_agreement_pattern(answer_history: List[Dict[str, Any]]) -> str:
    """
    Determine the agreement pattern between agents based on their answers.
    
    Args:
        answer_history: List of dictionaries with answer info
        
    Returns:
        String describing the agreement pattern
    """
    if len(answer_history) < 2:
        return "Insufficient Data"
    
    # Group answers by agent
    agent_a_answers = [item["answer"] for item in answer_history if item["agent"] == "Agent A"]
    agent_b_answers = [item["answer"] for item in answer_history if item["agent"] == "Agent B"]
    
    # If one agent didn't provide any answers, we can't determine agreement
    if not agent_a_answers or not agent_b_answers:
        return "Insufficient Data"
    
    # Check for Complete Agreement
    # If the first answers from both agents match
    first_a = agent_a_answers[0]
    first_b = agent_b_answers[0]
    
    if first_a == first_b:
        # If all answers match, it's Complete Agreement
        all_answers = agent_a_answers + agent_b_answers
        if all(ans == first_a for ans in all_answers):
            return "Complete Agreement"
    
    # Check for Resolved Disagreement
    # If the last answers match but there was earlier disagreement
    last_a = agent_a_answers[-1]
    last_b = agent_b_answers[-1]
    
    if last_a == last_b:
        # There was earlier disagreement if either:
        # 1. First answers didn't match, or
        # 2. Any answer along the way didn't match the final answer
        if first_a != first_b or any(ans != last_a for ans in agent_a_answers[:-1] + agent_b_answers[:-1]):
            return "Resolved Disagreement"
        else:
            # If there was never any disagreement, it's Complete Agreement
            return "Complete Agreement"
    
    # If we get here, it's Unresolved Disagreement
    return "Unresolved Disagreement"


def determine_correctness_pattern(answer_history: List[Dict[str, Any]]) -> str:
    """
    Determine the correctness pattern throughout the dialogue.
    
    Args:
        answer_history: List of dictionaries with answer and correctness info
        
    Returns:
        String describing the correctness pattern
    """
    if not answer_history:
        return "Insufficient Data"
    
    # Group by agent
    agent_a_history = [item for item in answer_history if item["agent"] == "Agent A"]
    agent_b_history = [item for item in answer_history if item["agent"] == "Agent B"]
    
    # Check for Stable patterns across both agents
    all_answers_correct = all(item["is_correct"] for item in answer_history)
    all_answers_incorrect = all(not item["is_correct"] for item in answer_history)
    
    if all_answers_correct:
        return "Stable Correct"
    elif all_answers_incorrect:
        return "Stable Incorrect"
    
    # Check for improvement patterns within each agent
    # Check if Agent A started incorrect but finished correct
    if agent_a_history and len(agent_a_history) > 1:
        a_first_correct = agent_a_history[0]["is_correct"]
        a_last_correct = agent_a_history[-1]["is_correct"]
        if not a_first_correct and a_last_correct:
            return "Improvement"
        elif a_first_correct and not a_last_correct:
            return "Deterioration"
            
    # Check if Agent B started incorrect but finished correct
    if agent_b_history and len(agent_b_history) > 1:
        b_first_correct = agent_b_history[0]["is_correct"]
        b_last_correct = agent_b_history[-1]["is_correct"]
        if not b_first_correct and b_last_correct:
            return "Improvement"
        elif b_first_correct and not b_last_correct:
            return "Deterioration"
    
    # Check for Stable patterns in individual agents for entire conversation
    a_all_correct = all(item["is_correct"] for item in agent_a_history) if agent_a_history else False
    b_all_correct = all(item["is_correct"] for item in agent_b_history) if agent_b_history else False
    
    if a_all_correct or b_all_correct:
        return "Stable Correct (One Agent)"
    
    # Sort by turn number to analyze progression
    answer_history.sort(key=lambda x: x["turn"])
    
    # Split into first half and second half
    midpoint = len(answer_history) // 2
    first_half = answer_history[:midpoint]
    second_half = answer_history[midpoint:] if midpoint < len(answer_history) else []
    
    # Check for improvement (more correct answers in second half)
    first_half_correct_ratio = sum(1 for item in first_half if item["is_correct"]) / len(first_half) if first_half else 0
    second_half_correct_ratio = sum(1 for item in second_half if item["is_correct"]) / len(second_half) if second_half else 0
    
    if second_half_correct_ratio > first_half_correct_ratio:
        return "Improvement"
    elif second_half_correct_ratio < first_half_correct_ratio:
        return "Deterioration"
    
    # Check if final answers are correct
    final_correct = False
    for agent in ["Agent A", "Agent B"]:
        agent_history = [item for item in answer_history if item["agent"] == agent]
        if agent_history and agent_history[-1]["is_correct"]:
            final_correct = True
            break
            
    if final_correct:
        return "Mixed Pattern (Final Correct)"
    
    # If we can't classify it more specifically, return mixed
    return "Mixed Pattern"


def get_analysis_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of solution evolution analysis across multiple questions.
    
    Args:
        results: List of result dictionaries containing evolution analysis
        
    Returns:
        Dictionary with summary statistics
    """
    agreement_counts = {
        "Complete Agreement": 0,
        "Resolved Disagreement": 0,
        "Unresolved Disagreement": 0,
        "Insufficient Data": 0
    }
    
    correctness_counts = {
        "Stable Correct": 0,
        "Stable Incorrect": 0,
        "Stable Correct (One Agent)": 0,
        "Improvement": 0,
        "Deterioration": 0,
        "Mixed Pattern": 0,
        "Mixed Pattern (Final Correct)": 0,
        "Insufficient Data": 0
    }
    
    # Counters for simulated vs dual
    simulated_agreement = {"Complete Agreement": 0, "Resolved Disagreement": 0, "Unresolved Disagreement": 0}
    dual_agreement_counts = {"Complete Agreement": 0, "Resolved Disagreement": 0, "Unresolved Disagreement": 0}
    
    simulated_correctness = {"Stable Correct": 0, "Improvement": 0, "Deterioration": 0, "Stable Incorrect": 0}
    dual_correctness_counts = {"Stable Correct": 0, "Improvement": 0, "Deterioration": 0, "Stable Incorrect": 0}
    
    # Count patterns
    for result in results:
        # Simulated
        if "simulated" in result and "evolution" in result["simulated"]:
            sim_agreement = result["simulated"]["evolution"]["agreement_pattern"]
            sim_correctness = result["simulated"]["evolution"]["correctness_pattern"]
            
            if sim_agreement in agreement_counts:
                agreement_counts[sim_agreement] += 1
                if sim_agreement in simulated_agreement:
                    simulated_agreement[sim_agreement] += 1
                    
            if sim_correctness in correctness_counts:
                correctness_counts[sim_correctness] += 1
                if sim_correctness in simulated_correctness:
                    simulated_correctness[sim_correctness] += 1
        
        # Dual
        if "dual" in result and "evolution" in result["dual"]:
            dual_agreement_pattern = result["dual"]["evolution"]["agreement_pattern"]
            dual_correctness_pattern = result["dual"]["evolution"]["correctness_pattern"]
            
            if dual_agreement_pattern in agreement_counts:
                agreement_counts[dual_agreement_pattern] += 1
                if dual_agreement_pattern in dual_agreement_counts:
                    dual_agreement_counts[dual_agreement_pattern] += 1
                    
            if dual_correctness_pattern in correctness_counts:
                correctness_counts[dual_correctness_pattern] += 1
                if dual_correctness_pattern in dual_correctness_counts:
                    dual_correctness_counts[dual_correctness_pattern] += 1
    
    return {
        "agreement_counts": agreement_counts,
        "correctness_counts": correctness_counts,
        "simulated": {
            "agreement": simulated_agreement,
            "correctness": simulated_correctness
        },
        "dual": {
            "agreement": dual_agreement_counts,
            "correctness": dual_correctness_counts
        }
    }