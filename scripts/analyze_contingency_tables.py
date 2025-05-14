#!/usr/bin/env python3
"""
Generate contingency tables for benchmarks comparing simulated vs dual-agent performance.

This script analyzes the specified comparison files and generates contingency tables
showing how many questions both approaches answered correctly/incorrectly, and where
they differed.

Usage:
  python analyze_contingency_tables.py [--results-dir RESULTS_DIR] [--output OUTPUT]

The script will analyze the following comparison files by default:
- comparison_livebench_1746486625.json
- comparison_gpqa_1746399747.json  
- comparison_aime_1746312436.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import math
from tabulate import tabulate

def load_comparison_file(file_path):
    """Load a comparison file from the given path"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON in file: {file_path}")
        return None

def create_contingency_table(comparison_data, strategy_id):
    """
    Create a contingency table for the given strategy
    
    Returns a tuple of (table, counts) where:
    - table is a 2x2 numpy array [[a, b], [c, d]] where:
      a = both correct, b = sim correct + dual incorrect
      c = sim incorrect + dual correct, d = both incorrect
    - counts is a dictionary with keys 'a', 'b', 'c', 'd' with the same values
    """
    # Initialize counters
    a, b, c, d = 0, 0, 0, 0
    
    # Get the questions for this strategy
    questions = comparison_data.get("questions", {})
    
    for question_id, question_data in questions.items():
        if strategy_id in question_data:
            strategy_question = question_data[strategy_id]
            
            # Get correctness for simulated and dual approaches
            sim_correct = strategy_question.get("simulated", {}).get("correct", False)
            dual_correct = strategy_question.get("dual", {}).get("correct", False)
            
            # Update the appropriate counter
            if sim_correct and dual_correct:
                a += 1  # Both correct
            elif sim_correct and not dual_correct:
                b += 1  # Simulated correct, dual incorrect
            elif not sim_correct and dual_correct:
                c += 1  # Simulated incorrect, dual correct
            else:
                d += 1  # Both incorrect
    
    # Create the contingency table
    table = np.array([[a, b], [c, d]])
    counts = {'a': a, 'b': b, 'c': c, 'd': d}
    
    return table, counts

def calculate_mcnemar_test(table):
    """
    Calculate McNemar's test manually for a 2x2 contingency table.
    
    Args:
        table: A 2x2 numpy array or list of lists
    
    Returns:
        p_value: The p-value for the test
    """
    # Extract b and c (discordant pairs)
    b = table[0][1]
    c = table[1][0]
    
    # If b + c is too small, can't perform the test
    if b + c < 10:
        # Use the exact binomial test for small samples
        # For a binomial with n=b+c and p=0.5 under the null hypothesis
        # The p-value is 2 * min(P(X ≤ min(b,c)), P(X ≥ max(b,c)))
        n = b + c
        k = min(b, c)
        if n == 0:
            return 1.0  # No disagreements, perfect agreement
        
        # Calculate exact binomial probability
        # P(X ≤ k) = sum_{i=0}^{k} binom(n,i) * 0.5^i * 0.5^(n-i)
        p_value = 0
        for i in range(k + 1):
            # Calculate binomial coefficient (n choose i)
            binom_coef = math.comb(n, i)
            # Calculate probability: binom_coef * 0.5^n
            p_value += binom_coef * (0.5 ** n)
        
        # Two-tailed test
        p_value = min(p_value * 2, 1.0)
    else:
        # Use chi-square approximation for larger samples
        # chi-square = (b - c)^2 / (b + c) with 1 degree of freedom
        chi_square = ((b - c) ** 2) / (b + c)
        
        # Convert chi-square to p-value using complementary error function
        # For 1 degree of freedom: p_value = 1 - CDF(chi_square)
        # Approximation: p_value = erfc(sqrt(chi_square/2)/sqrt(2))/2
        p_value = math.erfc(math.sqrt(chi_square/2)/math.sqrt(2))/2
        
    return p_value

def analyze_comparison(file_path, strategy_filter=None):
    """
    Analyze a comparison file and generate contingency tables for each strategy.
    
    Args:
        file_path: Path to the comparison file
        strategy_filter: Optional filter to only analyze specific strategies
        
    Returns:
        Dictionary mapping strategy IDs to their contingency table results
    """
    # Load the comparison file
    comparison_data = load_comparison_file(file_path)
    if not comparison_data:
        return None
    
    # Get benchmark name
    benchmark = comparison_data.get("benchmark", os.path.basename(file_path))
    
    # Dictionary to store results
    results = {
        "benchmark": benchmark,
        "strategies": {}
    }
    
    # Analyze each strategy
    for strategy_id in comparison_data.get("strategies", {}).keys():
        if strategy_filter and strategy_id not in strategy_filter:
            continue
        
        # Create contingency table
        table, counts = create_contingency_table(comparison_data, strategy_id)
        
        # Calculate McNemar's test if possible
        p_value = None
        try:
            # Only calculate if b+c > 0 (there's at least one disagreement)
            if counts['b'] + counts['c'] > 0:
                p_value = calculate_mcnemar_test(table)
        except Exception as e:
            print(f"Error calculating McNemar's test for {strategy_id}: {e}")
        
        # Calculate total questions and accuracies
        total = sum(counts.values())
        sim_accuracy = (counts['a'] + counts['b']) / total if total > 0 else 0
        dual_accuracy = (counts['a'] + counts['c']) / total if total > 0 else 0
        difference = dual_accuracy - sim_accuracy
        
        # Store results
        results["strategies"][strategy_id] = {
            "contingency_table": table.tolist(),
            "counts": counts,
            "total_questions": total,
            "simulated_accuracy": sim_accuracy,
            "dual_accuracy": dual_accuracy,
            "difference": difference,
            "mcnemar_p_value": p_value
        }
    
    return results

def print_contingency_tables(analysis_results):
    """Print contingency tables and statistics for each strategy"""
    if not analysis_results:
        return
    
    # Get benchmark name
    benchmark = analysis_results.get("benchmark", "Unknown")
    
    print(f"\n=== {benchmark} Benchmark Analysis ===\n")
    
    # Prepare data for summary table
    summary_data = []
    for strategy_id, strategy_results in analysis_results.get("strategies", {}).items():
        counts = strategy_results.get("counts", {})
        sim_accuracy = strategy_results.get("simulated_accuracy", 0) * 100
        dual_accuracy = strategy_results.get("dual_accuracy", 0) * 100
        difference = strategy_results.get("difference", 0) * 100
        p_value = strategy_results.get("mcnemar_p_value")
        
        # Format p-value with significance stars
        p_value_str = "N/A"
        significance = ""
        if p_value is not None:
            p_value_str = f"{p_value:.4f}"
            if p_value < 0.001:
                significance = "***"
            elif p_value < 0.01:
                significance = "**"
            elif p_value < 0.05:
                significance = "*"
        
        summary_data.append([
            strategy_id.capitalize(),
            f"{counts['a']} ({counts['a'] / (sum(counts.values()) or 1):.1%})",
            f"{counts['b']} ({counts['b'] / (sum(counts.values()) or 1):.1%})",
            f"{counts['c']} ({counts['c'] / (sum(counts.values()) or 1):.1%})",
            f"{counts['d']} ({counts['d'] / (sum(counts.values()) or 1):.1%})",
            f"{sim_accuracy:.1f}%",
            f"{dual_accuracy:.1f}%",
            f"{difference:+.1f}%" + (f" {significance}" if significance else ""),
            p_value_str + (f" {significance}" if significance else "")
        ])
    
    # Print summary table
    headers = [
        "Strategy", 
        "Both Correct (a)", 
        "Sim+ Dual- (b)", 
        "Sim- Dual+ (c)", 
        "Both Wrong (d)",
        "Sim Acc.",
        "Dual Acc.",
        "Difference",
        "p-value"
    ]
    print(tabulate(summary_data, headers=headers, tablefmt="pipe"))
    print()
    
    # Print detailed tables for each strategy
    for strategy_id, strategy_results in analysis_results.get("strategies", {}).items():
        print(f"\n{strategy_id.capitalize()} Strategy - Contingency Table:")
        
        counts = strategy_results.get("counts", {})
        total = sum(counts.values())
        
        table_data = [
            ["", "Dual Correct", "Dual Incorrect", "Total"],
            ["Simulated Correct", 
             f"{counts['a']} ({counts['a']/total:.1%})", 
             f"{counts['b']} ({counts['b']/total:.1%})",
             f"{counts['a'] + counts['b']} ({(counts['a'] + counts['b'])/total:.1%})"],
            ["Simulated Incorrect", 
             f"{counts['c']} ({counts['c']/total:.1%})", 
             f"{counts['d']} ({counts['d']/total:.1%})",
             f"{counts['c'] + counts['d']} ({(counts['c'] + counts['d'])/total:.1%})"],
            ["Total", 
             f"{counts['a'] + counts['c']} ({(counts['a'] + counts['c'])/total:.1%})", 
             f"{counts['b'] + counts['d']} ({(counts['b'] + counts['d'])/total:.1%})",
             f"{total} (100.0%)"]
        ]
        
        print(tabulate(table_data, tablefmt="grid"))
        
        # Calculate and print additional statistics
        sim_accuracy = strategy_results.get("simulated_accuracy", 0) * 100
        dual_accuracy = strategy_results.get("dual_accuracy", 0) * 100
        difference = strategy_results.get("difference", 0) * 100
        p_value = strategy_results.get("mcnemar_p_value")
        
        print(f"\nSimulated Accuracy: {sim_accuracy:.1f}%")
        print(f"Dual-Agent Accuracy: {dual_accuracy:.1f}%")
        print(f"Difference (Dual - Simulated): {difference:+.1f}%")
        
        if p_value is not None:
            significance = ""
            if p_value < 0.001:
                significance = "***"
            elif p_value < 0.01:
                significance = "**"
            elif p_value < 0.05:
                significance = "*"
            
            print(f"McNemar's Test p-value: {p_value:.4f} {significance}")
            print("Significance: * p<0.05, ** p<0.01, *** p<0.001")
            
            if p_value < 0.05:
                if counts['b'] < counts['c']:
                    print("Result: Dual-agent approach is statistically significantly better than simulated approach")
                else:
                    print("Result: Simulated approach is statistically significantly better than dual-agent approach")
            else:
                print("Result: No statistically significant difference between approaches")
        else:
            print("McNemar's Test: Not applicable (no disagreements)")

def create_comparison_table(benchmark_results):
    """Create a comparison table across benchmarks and strategies"""
    # Prepare table data
    data = []
    
    for benchmark_name, analysis_results in benchmark_results.items():
        for strategy_id, strategy_results in analysis_results.get("strategies", {}).items():
            counts = strategy_results.get("counts", {})
            total = sum(counts.values())
            
            # Skip if no data
            if total == 0:
                continue
                
            sim_accuracy = strategy_results.get("simulated_accuracy", 0) * 100
            dual_accuracy = strategy_results.get("dual_accuracy", 0) * 100
            difference = strategy_results.get("difference", 0) * 100
            p_value = strategy_results.get("mcnemar_p_value")
            
            # Format p-value with significance indicator
            sig_indicator = ""
            if p_value is not None:
                if p_value < 0.001:
                    sig_indicator = "***"
                elif p_value < 0.01:
                    sig_indicator = "**"
                elif p_value < 0.05:
                    sig_indicator = "*"
            
            # Determine winner
            winner = ""
            if difference > 0 and sig_indicator:
                winner = "Dual"
            elif difference < 0 and sig_indicator:
                winner = "Sim"
            
            data.append([
                benchmark_name,
                strategy_id.capitalize(),
                total,
                f"{counts['a']} ({counts['a']/total:.1%})",
                f"{counts['b']} ({counts['b']/total:.1%})",
                f"{counts['c']} ({counts['c']/total:.1%})",
                f"{counts['d']} ({counts['d']/total:.1%})",
                f"{sim_accuracy:.1f}%",
                f"{dual_accuracy:.1f}%",
                f"{difference:+.1f}%" + (f" {sig_indicator}" if sig_indicator else ""),
                winner
            ])
    
    # Sort by benchmark, then strategy
    data.sort(key=lambda x: (x[0], x[1]))
    
    # Print the table
    headers = [
        "Benchmark",
        "Strategy",
        "Total",
        "Both Correct",
        "Sim+ Dual-",
        "Sim- Dual+",
        "Both Wrong",
        "Sim Acc.",
        "Dual Acc.",
        "Diff.",
        "Winner"
    ]
    
    print("\n=== Cross-Benchmark Comparison ===\n")
    print(tabulate(data, headers=headers, tablefmt="pipe"))
    
    # Create pandas DataFrame for easier calculation
    df = pd.DataFrame(data, columns=headers)
    
    # Calculate aggregated results by benchmark
    benchmark_summary = df.groupby("Benchmark").agg({
        "Total": "sum", 
    }).reset_index()
    
    # Print benchmark summary
    print("\n=== Benchmark Summary ===\n")
    print(tabulate(benchmark_summary.values, headers=benchmark_summary.columns, tablefmt="pipe"))
    
    # Calculate aggregated results by strategy
    strategy_summary = df.groupby("Strategy").agg({
        "Total": "sum",
    }).reset_index()
    
    # Print strategy summary
    print("\n=== Strategy Summary ===\n")
    print(tabulate(strategy_summary.values, headers=strategy_summary.columns, tablefmt="pipe"))

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate contingency tables for benchmark comparisons")
    parser.add_argument("--results-dir", type=str, default="./results",
                        help="Directory containing result files")
    parser.add_argument("--output", type=str, default=None,
                        help="Output JSON file for analysis results")
    parser.add_argument("--files", nargs='+', type=str, 
                        default=["comparison_livebench_1746486625.json", 
                                 "comparison_gpqa_1746399747.json", 
                                 "comparison_aime_1746312436.json"],
                        help="List of comparison files to analyze")
    parser.add_argument("--strategies", nargs='+', type=str, default=None,
                        help="Optional filter to only analyze specific strategies")
    
    args = parser.parse_args()
    
    # Dictionary to store results
    all_results = {}
    
    # Analyze each comparison file
    for file_name in args.files:
        file_path = os.path.join(args.results_dir, file_name)
        
        print(f"Analyzing {file_path}...")
        benchmark_name = file_name.split('_')[1].split('.')[0].capitalize()
        
        analysis_results = analyze_comparison(file_path, args.strategies)
        if analysis_results:
            all_results[benchmark_name] = analysis_results
            print_contingency_tables(analysis_results)
    
    # Create comparison table across benchmarks
    if len(all_results) > 1:
        create_comparison_table(all_results)
    
    # Save results if output file specified
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(all_results, f, indent=2)
            print(f"\nAnalysis results saved to: {args.output}")
        except Exception as e:
            print(f"Error saving results: {e}")

if __name__ == "__main__":
    main()