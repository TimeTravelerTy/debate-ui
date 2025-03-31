import os
import sys
import asyncio
import argparse
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from evaluation.core import EvaluationManager
from evaluation.benchmarks.simple_bench import SimpleBenchmark
from agent.framework import AgentFramework
from agent.client import APIClient
from strategies.debate import DebateStrategy
from strategies.cooperative import CooperativeStrategy
from strategies.teacher_student import TeacherStudentStrategy

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a benchmark evaluation")
    parser.add_argument("--strategy", choices=["debate", "cooperative", "teacher-student"], 
                        default="debate", help="Strategy to use")
    parser.add_argument("--benchmark", default="simple", help="Benchmark to use")
    parser.add_argument("--max", type=int, default=None, help="Maximum number of questions")
    parser.add_argument("--output", default="./results", help="Output directory")
    
    args = parser.parse_args()
    
    # Load API credentials from environment or .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Setup API config
    api_config = {
        "api_key": os.environ.get("API_KEY"),
        "base_url": os.environ.get("API_BASE_URL"),
        "model_name": os.environ.get("MODEL_NAME", "deepseek-chat")
    }
    
    # Check for required environment variables
    if not api_config["api_key"]:
        print("Error: API_KEY environment variable not set")
        sys.exit(1)
    
    if not api_config["base_url"]:
        print("Error: API_BASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Using API: {api_config['base_url']} with model {api_config['model_name']}")
    
    # Initialize strategies
    strategies = {
        "debate": DebateStrategy(),
        "cooperative": CooperativeStrategy(),
        "teacher-student": TeacherStudentStrategy()
    }
    
    # Initialize API client
    client = APIClient(api_config)
    
    # Initialize framework with client and selected strategy
    framework = AgentFramework(api_config, strategies[args.strategy])
    
    # Initialize benchmark
    if args.benchmark == "simple":
        benchmark_dir = os.path.join("data", "benchmarks", "simple_bench")
        json_path = os.path.join(benchmark_dir, "questions.json")
        csv_path = os.path.join(benchmark_dir, "questions.csv")
        
        # Check if files exist
        if not os.path.exists(json_path):
            print(f"Error: Benchmark file not found: {json_path}")
            sys.exit(1)
            
        benchmark = SimpleBenchmark(json_path, csv_path if os.path.exists(csv_path) else None)
    else:
        print(f"Error: Unknown benchmark: {args.benchmark}")
        sys.exit(1)
        
    # Initialize evaluation manager
    manager = EvaluationManager(benchmark, framework, strategies, args.output)
    
    # Run evaluation
    print(f"Running {args.strategy} strategy on {args.benchmark} benchmark...")
    if args.max:
        print(f"Using maximum of {args.max} questions")
    
    start_time = datetime.now()
    run_id, results = await manager.run_evaluation(args.strategy, args.max)
    end_time = datetime.now()
    
    # Get the results
    result_path = os.path.join(args.output, f"result_{run_id}.json")
    with open(result_path, 'r') as f:
        result_data = json.load(f)
        
    summary = result_data["summary"]
    
    # Print results
    print(f"\nEvaluation complete in {end_time - start_time}")
    print(f"Run ID: {run_id}")
    print(f"Total questions: {summary['total_questions']}")
    print(f"Single agent accuracy: {summary['simulated_accuracy']:.2f} ({summary['simulated_correct']}/{summary['total_questions']})")
    print(f"Dual agent accuracy: {summary['dual_accuracy']:.2f} ({summary['dual_correct']}/{summary['total_questions']})")
    print(f"Results saved to {result_path}")
    
if __name__ == "__main__":
    asyncio.run(main())