"""
Script to run benchmark evaluations with parallel strategy support
"""

import sys
import os
import argparse
import json
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import agent framework modules
from agent.framework import AgentFramework
from agent.client import APIClient
from strategies.debate import DebateStrategy
from strategies.cooperative import CooperativeStrategy
from strategies.teacher_student import TeacherStudentStrategy

# Import benchmark modules
from evaluation.benchmarks.simple_bench import SimpleBenchmark
from evaluation.benchmarks.gpqa_benchmark import GPQABenchmark
from evaluation.benchmarks.aime_benchmark import AIMEBenchmark
from evaluation.benchmarks.livebench_benchmark import LiveBenchReasoningBenchmark
from evaluation.core import EvaluationManager

# Configure argument parser
parser = argparse.ArgumentParser(description='Run benchmark evaluations')
parser.add_argument('--benchmark', type=str, required=True, 
                    choices=['simple', 'gpqa-diamond', 'gpqa-experts', 'gpqa-extended', 'gpqa-main', 'aime', 'livebench'],
                    help='Benchmark to evaluate')
parser.add_argument('--strategy', type=str, nargs='+', default=['debate'],
                    choices=['debate', 'cooperative', 'teacher-student', 'all'],
                    help='Strategy or strategies to use for the evaluation. Use "all" to run all available strategies.')
parser.add_argument('--categories', type=str, nargs='+', default=None,
                    help='Specific LiveBench categories to evaluate (e.g., zebra_puzzle, spatial_reasoning)')
parser.add_argument('--questions', type=int, default=None,
                    help='Number of questions to evaluate')
parser.add_argument('--results-dir', type=str, default='./results',
                    help='Directory to save results')
parser.add_argument('--data-dir', type=str, default='./data/benchmarks',
                    help='Directory containing benchmark datasets')
parser.add_argument('--api-key', type=str, default=None,
                    help='API key for the model (or use API_KEY env var)')
parser.add_argument('--base-url', type=str, default=None,
                    help='Base URL for the API (or use API_BASE_URL env var)')
parser.add_argument('--model', type=str, default=None,
                    help='Model name to use (or use MODEL_NAME env var)')
parser.add_argument('--analyze', action='store_true',
                    help='Analyze existing results without running evaluations')
parser.add_argument('--result-file', type=str, default=None,
                    help='Result file to analyze (with --analyze flag)')
parser.add_argument('--parallel', action='store_true',
                    help='Run strategies in parallel (improves speed but increases API usage)')
parser.add_argument('--debug', action='store_true',
                    help='Enable debug output for troubleshooting')
parser.add_argument('--verbose', action='store_true',
                    help='Print detailed debug information about strategy selection')

async def main():
    """Run the benchmark evaluation"""
    args = parser.parse_args()
    
    # Enable debugging if requested
    if args.debug:
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Python path: {sys.path}")
    
    # Start timing
    overall_start_time = time.time()
    
    # Set up directories
    os.makedirs(args.results_dir, exist_ok=True)
    os.makedirs(args.data_dir, exist_ok=True)
    
    # Load API config
    api_config = {
        "api_key": args.api_key or os.environ.get("API_KEY"),
        "base_url": args.base_url or os.environ.get("API_BASE_URL"),
        "model_name": args.model or os.environ.get("MODEL_NAME")
    }
    
    if not api_config["api_key"]:
        print("Error: API key not provided. Use --api-key or set API_KEY environment variable.")
        return
        
    if not api_config["base_url"]:
        print("Error: Base URL not provided. Use --base-url or set API_BASE_URL environment variable.")
        return
        
    if not api_config["model_name"]:
        print("Error: Model name not provided. Use --model or set MODEL_NAME environment variable.")
        return
    
    # Initialize strategies
    strategies = {
        "debate": DebateStrategy(),
        "cooperative": CooperativeStrategy(),
        "teacher-student": TeacherStudentStrategy()
    }
    
    # Process the strategy argument
    strategy_ids = []
    if 'all' in args.strategy:
        strategy_ids = list(strategies.keys())
    else:
        strategy_ids = args.strategy
    
    if len(strategy_ids) > 1 and args.parallel:
        print(f"Running {len(strategy_ids)} strategies in parallel: {', '.join(strategy_ids)}")
    
    # Verify strategies are properly initialized (for verbose debugging)
    if args.verbose:
        print("\n--- STRATEGY VERIFICATION ---")
        for s_id, strategy in strategies.items():
            print(f"Strategy {s_id}: {strategy.__class__.__name__} - Name attribute: {strategy.name}")
            print(f"  System prompt A: {strategy.get_system_prompt_a()['content'][:50]}...")
            print(f"  System prompt B: {strategy.get_system_prompt_b()['content'][:50]}...")
    
    # Initialize framework with the first strategy - will be updated later for each run
    # or replaced with separate instances when running in parallel
    first_strategy = strategies[strategy_ids[0]]
    framework = AgentFramework(api_config, first_strategy)
    
    if args.verbose:
        print(f"\nInitialized framework with strategy: {first_strategy.name}")
        
    # Load the appropriate benchmark
    if args.benchmark == 'simple':
        json_path = os.path.join(args.data_dir, "simple_bench/questions.json")
        csv_path = os.path.join(args.data_dir, "simple_bench/questions.csv")
        
        if not os.path.exists(json_path) or not os.path.exists(csv_path):
            print(f"Error: Simple benchmark files not found at {json_path} or {csv_path}")
            return
            
        benchmark = SimpleBenchmark(json_path, csv_path)
        # Set the benchmark name for all strategies
        for s_id in strategy_ids:
            strategies[s_id].benchmark_name = "SimpleBench"
        
    elif args.benchmark.startswith('gpqa-'):
        variant = args.benchmark.split('-')[1]  # Extract variant (diamond, experts, etc.)
        csv_path = os.path.join(args.data_dir, f"gpqa/gpqa_{variant}.csv")
        
        if not os.path.exists(csv_path):
            print(f"Error: GPQA dataset file not found at {csv_path}")
            return
            
        benchmark = GPQABenchmark(csv_path, variant, args.questions)
        # Set the benchmark name for all strategies
        for s_id in strategy_ids:
            strategies[s_id].benchmark_name = "GPQA"

    elif args.benchmark == 'aime':
        benchmark = AIMEBenchmark(years_range=(2021, 2024), max_questions=args.questions)
        # Set the benchmark name for all strategies
        for s_id in strategy_ids:
            strategies[s_id].benchmark_name = "AIME"

    elif args.benchmark == 'livebench':
        # You can specify categories to test specific reasoning tasks
        categories = args.categories if hasattr(args, 'categories') else None
        benchmark = LiveBenchReasoningBenchmark(max_questions=args.questions, categories=categories)
        # Set the benchmark name for all strategies
        for s_id in strategy_ids:
            strategies[s_id].benchmark_name = "LiveBench"
        
    else:
        print(f"Error: Unknown benchmark: {args.benchmark}")
        return
    
    # Set the answer format for the framework
    framework.set_answer_format(benchmark.answer_format)
    
    # Initialize evaluation manager
    manager = EvaluationManager(benchmark, framework, strategies, args.results_dir)
    
    # Run evaluation
    try:
        if args.parallel and len(strategy_ids) > 1:
            # Run strategies in parallel
            start_time = time.time()
            results = await manager.run_parallel_evaluation(strategy_ids, args.questions)
            total_time = time.time() - start_time
            
            print("\n--- PARALLEL EVALUATION SUMMARY ---")
            print(f"Total execution time: {total_time:.2f} seconds")
            print(f"Strategies evaluated: {', '.join(results.keys())}")
            
            # Print summary of results
            print("\nResults by strategy:")
            for s_id, (run_id, result) in results.items():
                summary = result.get("summary", {})
                simulated_accuracy = summary.get("simulated_accuracy", 0) * 100
                dual_accuracy = summary.get("dual_accuracy", 0) * 100
                print(f"  - {s_id} (strategy: {strategies[s_id].name}): Single={simulated_accuracy:.1f}%, Dual={dual_accuracy:.1f}%, Run ID={run_id}")
                
            print("\nA comparison report has been generated for detailed analysis.")
        else:
            # Run strategies sequentially
            sequential_results = {}
            for s_id in strategy_ids:
                # Get the strategy
                strategy = strategies[s_id]
                if args.verbose:
                    print(f"\nApplying strategy {s_id} ({strategy.name}) to framework")
                    
                # Set the strategy on the framework
                framework.set_strategy(strategy)
                
                # Verify the strategy was set correctly
                if args.verbose:
                    print(f"Framework now using strategy: {framework.strategy.name}")
                
                # Run the evaluation
                print(f"Running evaluation with strategy: {s_id}")
                start_time = time.time()
                run_id, result = await manager.run_evaluation(s_id, args.questions)
                total_time = time.time() - start_time
                sequential_results[s_id] = (run_id, result)
                
                # Print summary for this strategy
                summary = result.get("summary", {})
                simulated_accuracy = summary.get("simulated_accuracy", 0) * 100
                dual_accuracy = summary.get("dual_accuracy", 0) * 100
                
                print(f"Evaluation complete for {s_id} ({strategy.name})")
                print(f"  Single Agent: {simulated_accuracy:.1f}%, Dual Agent: {dual_accuracy:.1f}%")
                print(f"  Run ID: {run_id}")
                print(f"  Execution time: {total_time:.2f} seconds")
            
            # If multiple strategies were run sequentially, generate a comparison report
            if len(sequential_results) > 1:
                await manager._save_comparison_report(sequential_results)
                print("\nA comparison report has been generated for all strategies.")
                
    except Exception as e:
        print(f"Error running evaluation: {e}")
        import traceback
        traceback.print_exc()
    
    # Print overall timing
    overall_time = time.time() - overall_start_time
    print(f"\nTotal script execution time: {overall_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())