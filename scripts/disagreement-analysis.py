#!/usr/bin/env python3
"""
Disagreement Analysis Script

This script analyzes productive vs. unproductive disagreements across benchmark runs:
- Productive disagreement: Resolved or unresolved disagreement that leads to correct answer
- Unproductive disagreement: Resolved or unresolved disagreement that leads to incorrect answer

The script processes the following comparison files:
- comparison_gpqa_1746399747.json
- comparison_aime_1746312436.json 
- comparison_livebench_1746486625.json

For each benchmark-strategy-agent combination, it computes:
- Number of productive disagreements
- Number of unproductive disagreements
- Ratio of productive to total disagreements
"""

import json
import os
import argparse
from collections import defaultdict
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np

def load_comparison_file(file_path):
    """Load a comparison JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_disagreements(comparison_data):
    """
    Analyze productive vs. unproductive disagreements in comparison data
    
    Args:
        comparison_data: Loaded comparison JSON data
        
    Returns:
        Dictionary with disagreement analysis results
    """
    results = {
        'benchmark': comparison_data.get('benchmark', 'Unknown'),
        'strategies': {}
    }
    
    # Process each strategy
    for strategy_id, strategy_data in comparison_data.get('strategies', {}).items():
        strategy_results = {
            'simulated': {
                'productive_disagreements': 0,
                'unproductive_disagreements': 0,
                'productive_resolved': 0,
                'unproductive_resolved': 0,
                'productive_unresolved': 0,
                'unproductive_unresolved': 0,
                'total_questions': 0
            },
            'dual': {
                'productive_disagreements': 0,
                'unproductive_disagreements': 0,
                'productive_resolved': 0,
                'unproductive_resolved': 0,
                'productive_unresolved': 0,
                'unproductive_unresolved': 0,
                'total_questions': 0
            }
        }
        
        # Process each question
        for question_id, question_data in comparison_data.get('questions', {}).items():
            if strategy_id not in question_data:
                continue
                
            # Get this strategy's data for the question
            strategy_question = question_data[strategy_id]
            
            # Check simulated agent
            if 'simulated' in strategy_question:
                simulated = strategy_question['simulated']
                is_correct = simulated.get('correct', False)
                
                # Check if we have evolution data with agreement pattern
                if 'evolution' in simulated:
                    agreement_pattern = simulated['evolution'].get('agreement_pattern', '')
                    
                    # Count disagreements (both resolved and unresolved)
                    if agreement_pattern in ['Resolved Disagreement', 'Unresolved Disagreement']:
                        strategy_results['simulated']['total_questions'] += 1
                        
                        if is_correct:
                            # Productive disagreement
                            strategy_results['simulated']['productive_disagreements'] += 1
                            
                            # Track specific type
                            if agreement_pattern == 'Resolved Disagreement':
                                strategy_results['simulated']['productive_resolved'] += 1
                            else:  # Unresolved
                                strategy_results['simulated']['productive_unresolved'] += 1
                        else:
                            # Unproductive disagreement
                            strategy_results['simulated']['unproductive_disagreements'] += 1
                            
                            # Track specific type
                            if agreement_pattern == 'Resolved Disagreement':
                                strategy_results['simulated']['unproductive_resolved'] += 1
                            else:  # Unresolved
                                strategy_results['simulated']['unproductive_unresolved'] += 1
            
            # Check dual agent
            if 'dual' in strategy_question:
                dual = strategy_question['dual']
                is_correct = dual.get('correct', False)
                
                # Check if we have evolution data with agreement pattern
                if 'evolution' in dual:
                    agreement_pattern = dual['evolution'].get('agreement_pattern', '')
                    
                    # Count disagreements (both resolved and unresolved)
                    if agreement_pattern in ['Resolved Disagreement', 'Unresolved Disagreement']:
                        strategy_results['dual']['total_questions'] += 1
                        
                        if is_correct:
                            # Productive disagreement
                            strategy_results['dual']['productive_disagreements'] += 1
                            
                            # Track specific type
                            if agreement_pattern == 'Resolved Disagreement':
                                strategy_results['dual']['productive_resolved'] += 1
                            else:  # Unresolved
                                strategy_results['dual']['productive_unresolved'] += 1
                        else:
                            # Unproductive disagreement
                            strategy_results['dual']['unproductive_disagreements'] += 1
                            
                            # Track specific type
                            if agreement_pattern == 'Resolved Disagreement':
                                strategy_results['dual']['unproductive_resolved'] += 1
                            else:  # Unresolved
                                strategy_results['dual']['unproductive_unresolved'] += 1
        
        # Calculate ratios for simulated approach
        simulated_total = (
            strategy_results['simulated']['productive_disagreements'] + 
            strategy_results['simulated']['unproductive_disagreements']
        )
        if simulated_total > 0:
            strategy_results['simulated']['productive_ratio'] = (
                strategy_results['simulated']['productive_disagreements'] / simulated_total
            )
        else:
            strategy_results['simulated']['productive_ratio'] = 0
        
        # Calculate ratios for dual approach
        dual_total = (
            strategy_results['dual']['productive_disagreements'] + 
            strategy_results['dual']['unproductive_disagreements']
        )
        if dual_total > 0:
            strategy_results['dual']['productive_ratio'] = (
                strategy_results['dual']['productive_disagreements'] / dual_total
            )
        else:
            strategy_results['dual']['productive_ratio'] = 0
        
        # Store results for this strategy
        results['strategies'][strategy_id] = strategy_results
    
    return results

def analyze_all_comparisons(results_dir, comparison_files):
    """
    Analyze disagreements across multiple comparison files
    
    Args:
        results_dir: Directory containing result files
        comparison_files: List of comparison file names
        
    Returns:
        List of analysis results, one per comparison file
    """
    all_results = []
    
    for filename in comparison_files:
        file_path = os.path.join(results_dir, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        # Load and analyze the comparison file
        comparison_data = load_comparison_file(file_path)
        if comparison_data:
            analysis = analyze_disagreements(comparison_data)
            all_results.append(analysis)
    
    return all_results

def print_summary_table(all_results):
    """
    Print a summary table of disagreement analysis results
    
    Args:
        all_results: List of analysis results
    """
    table_data = []
    headers = [
        "Benchmark", "Strategy", "Agent", 
        "Productive Disagreements", "Unproductive Disagreements", 
        "Productive Ratio", "Total Questions with Disagreement"
    ]
    
    for result in all_results:
        benchmark = result['benchmark']
        
        for strategy_id, strategy_data in result['strategies'].items():
            # Add row for simulated approach
            simulated = strategy_data['simulated']
            simulated_total = simulated['total_questions']
            simulated_productive = simulated['productive_disagreements']
            simulated_unproductive = simulated['unproductive_disagreements']
            simulated_ratio = simulated['productive_ratio']
            
            table_data.append([
                benchmark,
                strategy_id,
                "Simulated",
                simulated_productive,
                simulated_unproductive,
                f"{simulated_ratio:.2f}",
                simulated_total
            ])
            
            # Add row for dual approach
            dual = strategy_data['dual']
            dual_total = dual['total_questions']
            dual_productive = dual['productive_disagreements']
            dual_unproductive = dual['unproductive_disagreements']
            dual_ratio = dual['productive_ratio']
            
            table_data.append([
                benchmark,
                strategy_id,
                "Dual",
                dual_productive,
                dual_unproductive,
                f"{dual_ratio:.2f}",
                dual_total
            ])
    
    # Print the table
    print("\n=== Disagreement Analysis Summary ===\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def print_detailed_breakdown(all_results):
    """
    Print a detailed breakdown of disagreement types
    
    Args:
        all_results: List of analysis results
    """
    table_data = []
    headers = [
        "Benchmark", "Strategy", "Agent", 
        "Productive Resolved", "Productive Unresolved",
        "Unproductive Resolved", "Unproductive Unresolved",
        "Total"
    ]
    
    for result in all_results:
        benchmark = result['benchmark']
        
        for strategy_id, strategy_data in result['strategies'].items():
            # Add row for simulated approach
            simulated = strategy_data['simulated']
            table_data.append([
                benchmark,
                strategy_id,
                "Simulated",
                simulated['productive_resolved'],
                simulated['productive_unresolved'],
                simulated['unproductive_resolved'],
                simulated['unproductive_unresolved'],
                simulated['total_questions']
            ])
            
            # Add row for dual approach
            dual = strategy_data['dual']
            table_data.append([
                benchmark,
                strategy_id,
                "Dual",
                dual['productive_resolved'],
                dual['productive_unresolved'],
                dual['unproductive_resolved'],
                dual['unproductive_unresolved'],
                dual['total_questions']
            ])
    
    # Print the table
    print("\n=== Detailed Disagreement Breakdown ===\n")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def generate_disagreement_plots(all_results, output_dir=None):
    """
    Generate plots visualizing the disagreement analysis
    
    Args:
        all_results: List of analysis results
        output_dir: Directory to save plots (optional)
    """
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Prepare data for plotting
    benchmarks = []
    strategies = set()
    productive_sim = defaultdict(list)
    unproductive_sim = defaultdict(list)
    productive_dual = defaultdict(list)
    unproductive_dual = defaultdict(list)
    
    for result in all_results:
        benchmark = result['benchmark']
        benchmarks.append(benchmark)
        
        for strategy_id, strategy_data in result['strategies'].items():
            strategies.add(strategy_id)
            
            # Simulated data
            sim = strategy_data['simulated']
            productive_sim[strategy_id].append(sim['productive_disagreements'])
            unproductive_sim[strategy_id].append(sim['unproductive_disagreements'])
            
            # Dual data
            dual = strategy_data['dual']
            productive_dual[strategy_id].append(dual['productive_disagreements'])
            unproductive_dual[strategy_id].append(dual['unproductive_disagreements'])
    
    strategies = sorted(strategies)
    
    # Create productive vs. unproductive disagreement plots for each benchmark
    for i, benchmark in enumerate(benchmarks):
        plt.figure(figsize=(14, 8))
        
        # Set up bar positions
        num_strategies = len(strategies)
        bar_width = 0.15
        index = np.arange(4)  # 4 categories: Sim-Prod, Sim-Unprod, Dual-Prod, Dual-Unprod
        
        for j, strategy in enumerate(strategies):
            # Get data for this strategy and benchmark
            sim_prod = productive_sim[strategy][i] if i < len(productive_sim[strategy]) else 0
            sim_unprod = unproductive_sim[strategy][i] if i < len(unproductive_sim[strategy]) else 0
            dual_prod = productive_dual[strategy][i] if i < len(productive_dual[strategy]) else 0
            dual_unprod = unproductive_dual[strategy][i] if i < len(unproductive_dual[strategy]) else 0
            
            # Create bars
            position = index + (j * bar_width)
            plt.bar(position, [sim_prod, sim_unprod, dual_prod, dual_unprod], 
                   width=bar_width, label=strategy.capitalize())
        
        plt.xlabel('Disagreement Type')
        plt.ylabel('Number of Instances')
        plt.title(f'Productive vs. Unproductive Disagreements: {benchmark}')
        plt.xticks(index + ((num_strategies - 1) * bar_width / 2), 
                  ['Simulated\nProductive', 'Simulated\nUnproductive', 
                   'Dual\nProductive', 'Dual\nUnproductive'])
        plt.legend()
        plt.tight_layout()
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, f'disagreements_{benchmark}.png'))
        else:
            plt.show()
        
        plt.close()
    
    # Create productive ratio comparison chart across benchmarks
    plt.figure(figsize=(14, 8))
    
    # Set up bar positions
    num_benchmarks = len(benchmarks)
    bar_width = 0.15
    index = np.arange(num_benchmarks)
    
    for j, strategy in enumerate(strategies):
        sim_ratios = []
        dual_ratios = []
        
        # Get ratios for each benchmark
        for i, benchmark in enumerate(benchmarks):
            if i < len(all_results):
                result = all_results[i]
                if strategy in result['strategies']:
                    strategy_data = result['strategies'][strategy]
                    sim_ratios.append(strategy_data['simulated']['productive_ratio'])
                    dual_ratios.append(strategy_data['dual']['productive_ratio'])
                else:
                    sim_ratios.append(0)
                    dual_ratios.append(0)
            else:
                sim_ratios.append(0)
                dual_ratios.append(0)
        
        # Plot simulated ratios
        plt.bar(index + (j * bar_width * 2), sim_ratios, 
               width=bar_width, label=f'{strategy.capitalize()} (Simulated)')
        
        # Plot dual ratios
        plt.bar(index + (j * bar_width * 2) + bar_width, dual_ratios, 
               width=bar_width, label=f'{strategy.capitalize()} (Dual)')
    
    plt.xlabel('Benchmark')
    plt.ylabel('Productive Disagreement Ratio')
    plt.title('Productive Disagreement Ratio by Benchmark and Strategy')
    plt.xticks(index + (bar_width * (len(strategies) - 0.5)), benchmarks)
    plt.legend()
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(os.path.join(output_dir, 'productive_ratio_comparison.png'))
    else:
        plt.show()
    
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze productive vs. unproductive disagreements in benchmark results')
    parser.add_argument('--results-dir', type=str, default='./results',
                        help='Directory containing result files')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Directory to save plots')
    parser.add_argument('--skip-plots', action='store_true',
                        help='Skip generating plots')
    
    args = parser.parse_args()
    
    # Specific comparison files to analyze
    comparison_files = [
        "comparison_gpqa_1746399747.json",
        "comparison_aime_1746312436.json",
        "comparison_livebench_1746486625.json"
    ]
    
    # Analyze all comparisons
    all_results = analyze_all_comparisons(args.results_dir, comparison_files)
    
    # Print summary table
    print_summary_table(all_results)
    
    # Print detailed breakdown
    print_detailed_breakdown(all_results)
    
    # Generate plots
    if not args.skip_plots:
        try:
            generate_disagreement_plots(all_results, args.output_dir)
            if args.output_dir:
                print(f"\nPlots saved to: {args.output_dir}")
        except Exception as e:
            print(f"Error generating plots: {e}")
    
if __name__ == "__main__":
    main()