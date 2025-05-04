#!/usr/bin/env python3
"""
Compare baseline results with agent-based results
"""

import sys
import os
import argparse
import json
from tabulate import tabulate

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_results(file_path):
    """Load results from a JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def compare_results(baseline_results, agent_results):
    """Compare baseline and agent results"""
    comparison = {
        "baseline": {
            "total_questions": baseline_results['summary']['total_questions'],
            "correct": baseline_results['summary']['correct'],
            "accuracy": baseline_results['summary']['accuracy'],
            "total_tokens": baseline_results['summary']['total_tokens'],
            "avg_tokens_per_question": baseline_results['summary']['average_tokens_per_question']
        },
        "agents": {},
        "detailed_comparison": []
    }
    
    # Process agent results - handle comparison report format
    if 'strategies' in agent_results:  # Comparison report format
        for strategy, data in agent_results['strategies'].items():
            comparison["agents"][strategy] = {
                "simulated_correct": data['summary']['simulated_correct'],
                "simulated_accuracy": data['summary']['simulated_accuracy'],
                "dual_correct": data['summary']['dual_correct'],
                "dual_accuracy": data['summary']['dual_accuracy'],
                "total_tokens": data['summary']['token_usage']['total_tokens']
            }
    else:  # Single strategy format
        strategy = agent_results.get('strategy', 'unknown')
        comparison["agents"][strategy] = {
            "simulated_correct": agent_results['summary']['simulated_correct'],
            "simulated_accuracy": agent_results['summary']['simulated_accuracy'],
            "dual_correct": agent_results['summary']['dual_correct'],
            "dual_accuracy": agent_results['summary']['dual_accuracy'],
            "total_tokens": agent_results['summary']['token_usage']['total_tokens']
        }
    
    # Question-by-question comparison
    baseline_questions = {}
    for r in baseline_results['results']:
        q_id = str(r['question_id'])  # Convert to string for consistency
        baseline_questions[q_id] = r
    
    # For agent results in comparison format, get question-level details
    if 'questions' in agent_results:  # Comparison report format
        for q_id_str, strategies in agent_results['questions'].items():
            if q_id_str in baseline_questions:
                baseline_correct = baseline_questions[q_id_str]['correct']
                
                q_comparison = {
                    "question_id": q_id_str,
                    "baseline_correct": baseline_correct,
                    "strategies": {}
                }
                
                for strategy, data in strategies.items():
                    q_comparison["strategies"][strategy] = {
                        "simulated_correct": data['simulated']['correct'],
                        "dual_correct": data['dual']['correct']
                    }
                
                comparison["detailed_comparison"].append(q_comparison)
            else:
                # Try converting the question ID
                for base_q_id in baseline_questions:
                    if str(base_q_id) == str(q_id_str) or str(q_id_str) == str(base_q_id):
                        baseline_correct = baseline_questions[base_q_id]['correct']
                        
                        q_comparison = {
                            "question_id": q_id_str,
                            "baseline_correct": baseline_correct,
                            "strategies": {}
                        }
                        
                        for strategy, data in strategies.items():
                            q_comparison["strategies"][strategy] = {
                                "simulated_correct": data['simulated']['correct'],
                                "dual_correct": data['dual']['correct']
                            }
                        
                        comparison["detailed_comparison"].append(q_comparison)
                        break
    else:  # Single strategy format - get from individual run results
        # Load the individual run result file based on run_id
        if 'strategies' in agent_results:
            # For each strategy, load its results file
            for strategy, data in agent_results['strategies'].items():
                run_id = data.get('run_id')
                if run_id:
                    results_file = f"./results/result_{run_id}.json"
                    try:
                        with open(results_file, 'r') as f:
                            strategy_results = json.load(f)
                            
                        for result in strategy_results['results']:
                            q_id = str(result['question_id'])
                            if q_id in baseline_questions:
                                baseline_correct = baseline_questions[q_id]['correct']
                                
                                # Find existing comparison for this question or create new
                                existing = None
                                for comp in comparison["detailed_comparison"]:
                                    if comp["question_id"] == q_id:
                                        existing = comp
                                        break
                                
                                if not existing:
                                    existing = {
                                        "question_id": q_id,
                                        "baseline_correct": baseline_correct,
                                        "strategies": {}
                                    }
                                    comparison["detailed_comparison"].append(existing)
                                
                                existing["strategies"][strategy] = {
                                    "simulated_correct": result['simulated']['correct'],
                                    "dual_correct": result['dual']['correct']
                                }
                    except:
                        pass
        else:
            # Single strategy file
            strategy = agent_results.get('strategy', 'unknown')
            for result in agent_results['results']:
                q_id = str(result['question_id'])
                if q_id in baseline_questions:
                    baseline_correct = baseline_questions[q_id]['correct']
                    
                    q_comparison = {
                        "question_id": q_id,
                        "baseline_correct": baseline_correct,
                        "strategies": {
                            strategy: {
                                "simulated_correct": result['simulated']['correct'],
                                "dual_correct": result['dual']['correct']
                            }
                        }
                    }
                    
                    comparison["detailed_comparison"].append(q_comparison)
    
    return comparison

def print_comparison(comparison):
    """Print comparison results in a formatted table"""
    print("\n=== AIME Baseline vs Agent Performance Comparison ===\n")
    
    # Overall summary
    baseline = comparison['baseline']
    print(f"Baseline Model Performance:")
    print(f"  Accuracy: {baseline['accuracy']:.1%} ({baseline['correct']}/{baseline['total_questions']})")
    print(f"  Tokens: {baseline['total_tokens']:,} (avg {baseline['avg_tokens_per_question']:.1f} per question)")
    print()
    
    # Agent performance table
    agent_data = []
    headers = ["Strategy", "Simulated Accuracy", "Dual Agent Accuracy", "Total Tokens", "Token Efficiency"]
    
    for strategy, data in comparison['agents'].items():
        sim_acc = f"{data['simulated_accuracy']:.1%} ({data['simulated_correct']}/{baseline['total_questions']})"
        dual_acc = f"{data['dual_accuracy']:.1%} ({data['dual_correct']}/{baseline['total_questions']})"
        tokens = f"{data['total_tokens']:,}"
        
        # Calculate token efficiency (correct answers per 1000 tokens)
        sim_efficiency = (data['simulated_correct'] / data['total_tokens']) * 1000 if data['total_tokens'] > 0 else 0
        dual_efficiency = (data['dual_correct'] / data['total_tokens']) * 1000 if data['total_tokens'] > 0 else 0
        efficiency = f"Sim: {sim_efficiency:.3f}, Dual: {dual_efficiency:.3f}"
        
        agent_data.append([strategy.capitalize(), sim_acc, dual_acc, tokens, efficiency])
    
    print("Agent Performance Comparison:")
    print(tabulate(agent_data, headers=headers, tablefmt="grid"))
    print()
    
    # Performance differences
    print("Performance Difference from Baseline:")
    diff_data = []
    diff_headers = ["Strategy", "Simulated Δ", "Dual Agent Δ", "Token Ratio"]
    
    for strategy, data in comparison['agents'].items():
        sim_diff = (data['simulated_accuracy'] - baseline['accuracy']) * 100
        dual_diff = (data['dual_accuracy'] - baseline['accuracy']) * 100
        token_ratio = data['total_tokens'] / baseline['total_tokens']
        
        sim_diff_str = f"{sim_diff:+.1f}%"
        dual_diff_str = f"{dual_diff:+.1f}%"
        token_ratio_str = f"{token_ratio:.2f}x"
        
        diff_data.append([strategy.capitalize(), sim_diff_str, dual_diff_str, token_ratio_str])
    
    print(tabulate(diff_data, headers=diff_headers, tablefmt="grid"))
    print()
    
    # Analysis of which questions benefit from agent approach
    baseline_correct_ids = []
    agent_correct_ids = {strategy: {'simulated': [], 'dual': []} for strategy in comparison['agents'].keys()}
    
    for q_comp in comparison['detailed_comparison']:
        q_id = q_comp['question_id']
        if q_comp['baseline_correct']:
            baseline_correct_ids.append(q_id)
        
        for strategy, results in q_comp['strategies'].items():
            if results['simulated_correct']:
                agent_correct_ids[strategy]['simulated'].append(q_id)
            if results['dual_correct']:
                agent_correct_ids[strategy]['dual'].append(q_id)
    
    print("Question Analysis:")
    print(f"Questions correct by baseline: {len(baseline_correct_ids)}")
    
    for strategy in comparison['agents'].keys():
        sim_correct = set(agent_correct_ids[strategy]['simulated'])
        dual_correct = set(agent_correct_ids[strategy]['dual'])
        baseline_set = set(baseline_correct_ids)
        
        sim_unique = sim_correct - baseline_set
        dual_unique = dual_correct - baseline_set
        baseline_unique = baseline_set - (sim_correct | dual_correct)
        
        print(f"\n{strategy.capitalize()} strategy:")
        print(f"  Simulated solved uniquely: {len(sim_unique)} questions")
        print(f"  Dual agent solved uniquely: {len(dual_unique)} questions")
        print(f"  Baseline solved but agents failed: {len(baseline_unique)} questions")
        
        if len(sim_unique) > 0:
            print(f"  Simulated unique questions: {list(sim_unique)[:5]}...")
        if len(dual_unique) > 0:
            print(f"  Dual unique questions: {list(dual_unique)[:5]}...")
        if len(baseline_unique) > 0:
            print(f"  Baseline unique questions: {list(baseline_unique)[:5]}...")
    
    print("\nDetailed Analysis:")
    print(f"Total questions analyzed: {len(comparison['detailed_comparison'])}")
    
    print("\nInsights:")
    print("- Agent approaches use significantly more tokens than baseline")
    print("- Agent approaches may solve different questions than baseline")
    print("- Dual agent setups often perform better than simulated dialogues")
    print("- Token efficiency varies by strategy")

def main():
    parser = argparse.ArgumentParser(description='Compare baseline results with agent-based results')
    parser.add_argument('--baseline', type=str, required=True,
                        help='Path to baseline results JSON file')
    parser.add_argument('--agents', type=str, required=True,
                        help='Path to agent results JSON file (single strategy or comparison)')
    parser.add_argument('--output', type=str, default=None,
                        help='Optional: Save comparison results to JSON file')
    
    args = parser.parse_args()
    
    try:
        # Load results
        baseline_results = load_results(args.baseline)
        agent_results = load_results(args.agents)
        
        # Compare results
        comparison = compare_results(baseline_results, agent_results)
        
        # Print comparison
        print_comparison(comparison)
        
        # Save comparison if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(comparison, f, indent=2)
            print(f"\nComparison results saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()