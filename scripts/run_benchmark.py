"""
Script to run benchmark evaluations
"""

import sys
import os
import argparse
import json
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import agent framework modules
from agent.framework import AgentFramework
from agent.client import APIClient
from strategies.debate import DebateStrategy
from strategies.cooperative import CooperativeStrategy
from strategies.teacher_student import TeacherStudentStrategy

# Import benchmark modules
from evaluation.benchmarks.simple_bench import SimpleBenchmark
from evaluation.benchmarks.gpqa_benchmark import GPQABenchmark
from evaluation.core import EvaluationManager

# Configure argument parser
parser = argparse.ArgumentParser(description='Run benchmark evaluations')
parser.add_argument('--benchmark', type=str, required=True, 
                    choices=['simple', 'gpqa-diamond', 'gpqa-experts', 'gpqa-extended', 'gpqa-main'],
                    help='Benchmark to evaluate')
parser.add_argument('--strategy', type=str, default='debate', 
                    choices=['debate', 'cooperative', 'teacher-student'],
                    help='Strategy to use for the evaluation')
parser.add_argument('--questions', type=int, default=5,
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

async def main():
    """Run the benchmark evaluation"""
    args = parser.parse_args()
    
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
    
    # Get the selected strategy
    strategy = strategies[args.strategy]
    
    # Initialize framework
    framework = AgentFramework(api_config, strategy)
    
    # Load the appropriate benchmark
    if args.benchmark == 'simple':
        json_path = os.path.join(args.data_dir, "simple_bench/questions.json")
        csv_path = os.path.join(args.data_dir, "simple_bench/questions.csv")
        
        if not os.path.exists(json_path) or not os.path.exists(csv_path):
            print(f"Error: Simple benchmark files not found at {json_path} or {csv_path}")
            return
            
        benchmark = SimpleBenchmark(json_path, csv_path)
        # Set the benchmark name for the strategy
        strategy.benchmark_name = "SimpleBench"
        
    elif args.benchmark.startswith('gpqa-'):
        variant = args.benchmark.split('-')[1]  # Extract variant (diamond, experts, etc.)
        csv_path = os.path.join(args.data_dir, f"gpqa/gpqa_{variant}.csv")
        
        if not os.path.exists(csv_path):
            print(f"Error: GPQA dataset file not found at {csv_path}")
            return
            
        benchmark = GPQABenchmark(csv_path, variant, args.questions)
        # Set the benchmark name for the strategy
        strategy.benchmark_name = "GPQA"
        
    else:
        print(f"Error: Unknown benchmark: {args.benchmark}")
        return
    
    # Initialize evaluation manager
    manager = EvaluationManager(benchmark, framework, strategies, args.results_dir)
    
    # Run evaluation
    try:
        run_id, results = await manager.run_evaluation(args.strategy, args.questions)
        print(f"Evaluation complete. Run ID: {run_id}")
    except Exception as e:
        print(f"Error running evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())